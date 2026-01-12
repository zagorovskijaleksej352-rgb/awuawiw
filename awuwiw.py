import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

# Konfiguracja połączenia
DB_URL = "sqlite:///magazyn.db"
engine = create_engine(DB_URL)

def init_db():
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS kategorie (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nazwa TEXT NOT NULL
            );
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS magazyn228 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nazwa TEXT NOT NULL,
                liczba INTEGER,
                cena NUMERIC,
                categorie INTEGER,
                FOREIGN KEY (categorie) REFERENCES kategorie (id)
            );
        """))
        conn.commit()

init_db()

st.set_page_config(page_title="Magazyn Pro", layout="wide")
st.title("📦 System Zarządzania Magazynem")

# --- SEKCJA: STATYSTYKI (NOWOŚĆ) ---
st.subheader("📊 Podsumowanie Magazynu")
df_stats = pd.read_sql("SELECT liczba, cena FROM magazyn228", engine)
if not df_stats.empty:
    total_items = df_stats['liczba'].sum()
    # Obliczanie wartości: suma (liczba * cena)
    total_value = (df_stats['liczba'] * df_stats['cena']).sum()
    
    col1, col2 = st.columns(2)
    col1.metric("Suma produktów", f"{total_items} szt.")
    col2.metric("Wartość magazynu", f"{total_value:,.2f} PLN")
else:
    st.info("Magazyn jest pusty.")

---

# --- SEKCJA 1: DODAWANIE ---
col_kat, col_prod = st.columns(2)

with col_kat:
    st.header("Dodaj Kategorię")
    with st.form("form_kategoria", clear_on_submit=True):
        kat_nazwa = st.text_input("Nazwa kategorii")
        submit_kat = st.form_submit_button("Zapisz kategorię")
        
        if submit_kat and kat_nazwa:
            with engine.connect() as conn:
                conn.execute(text("INSERT INTO kategorie (nazwa) VALUES (:n)"), {"n": kat_nazwa})
                conn.commit()
            st.success(f"Dodano: {kat_nazwa}")
            st.rerun()

with col_prod:
    st.header("Dodaj Produkt")
    df_kat = pd.read_sql("SELECT * FROM kategorie", engine)
    kategorie_dict = dict(zip(df_kat['nazwa'], df_kat['id']))

    with st.form("form_produkt", clear_on_submit=True):
        prod_nazwa = st.text_input("Nazwa produktu")
        prod_liczba = st.number_input("Liczba", step=1, value=0)
        prod_cena = st.number_input("Cena", step=0.01, format="%.2f")
        prod_kat_name = st.selectbox("Kategoria", options=list(kategorie_dict.keys()))
        submit_prod = st.form_submit_button("Dodaj produkt")
        
        if submit_prod and prod_nazwa:
            kat_id = kategorie_dict[prod_kat_name]
            with engine.connect() as conn:
                query = text("INSERT INTO magazyn228 (nazwa, liczba, cena, categorie) VALUES (:n, :l, :c, :k)")
                conn.execute(query, {"n": prod_nazwa, "l": prod_liczba, "c": prod_cena, "k": kat_id})
                conn.commit()
            st.success(f"Dodano: {prod_nazwa}")
            st.rerun()

---

# --- SEKCJA 3: PODGLĄD I USUWANIE (ULEPSZONE) ---
st.header("🔍 Zarządzanie Stanem Magazynowym")

query_view = """
    SELECT m.id, m.nazwa, m.liczba, m.cena, k.nazwa as kategoria 
    FROM magazyn228 m 
    LEFT JOIN kategorie k ON m.categorie = k.id
"""
df_view = pd.read_sql(query_view, engine)

if not df_view.empty:
    # Wyświetlanie danych z edytorem (możliwość usuwania)
    event = st.dataframe(
        df_view, 
        use_container_width=True, 
        hide_index=True,
        column_config={"id": None} # Ukrywamy ID przed użytkownikiem
    )
    
    # Funkcja usuwania wybranego produktu
    st.subheader("🗑️ Usuń produkt")
    product_to_delete = st.selectbox("Wybierz produkt do usunięcia", df_view['nazwa'].unique())
    if st.button("Usuń wybrany produkt", type="primary"):
        with engine.connect() as conn:
            conn.execute(text("DELETE FROM magazyn228 WHERE nazwa = :n"), {"n": product_to_delete})
            conn.commit()
        st.warning(f"Usunięto {product_to_delete}")
        st.rerun()
else:
    st.write("Brak danych do wyświetlenia.")
