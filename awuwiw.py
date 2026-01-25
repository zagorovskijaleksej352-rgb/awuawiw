import streamlit as st
import pandas as pd
from dotenv import load_dotenv
import os
load_dotenv()
from sqlalchemy import create_engine, text

try:
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    st.success("Połączono z Supabase ✅")
except Exception as e:
    st.error(f"Błąd połączenia: {e}")
    st.stop()

# =========================
# KONFIGURACJA BAZY
# =========================
DB_URL = os.getenv("SUPABASE_DB_URL") or st.secrets["SUPABASE_DB_URL"]
engine = create_engine(DB_URL, future=True, pool_pre_ping=True)

def init_db():
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS kategorie (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nazwa TEXT UNIQUE NOT NULL
            )
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS magazyn228 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nazwa TEXT NOT NULL,
                liczba INTEGER NOT NULL,
                cena REAL NOT NULL,
                categorie INTEGER,
                FOREIGN KEY (categorie) REFERENCES kategorie(id)
            )
        """))

init_db()

# =========================
# UI
# =========================
st.set_page_config(page_title="Magazyn Pro", layout="wide")
st.title("📦 System Zarządzania Magazynem")

# =========================
# STATYSTYKI
# =========================
st.subheader("📊 Podsumowanie Magazynu")

df_stats = pd.read_sql("SELECT liczba, cena FROM magazyn228", engine)

if not df_stats.empty:
    total_items = int(df_stats["liczba"].sum())
    total_value = (df_stats["liczba"] * df_stats["cena"]).sum()

    col1, col2 = st.columns(2)
    col1.metric("Suma produktów", f"{total_items} szt.")
    col2.metric("Wartość magazynu", f"{total_value:,.2f} PLN")
else:
    st.info("Magazyn jest pusty.")

st.divider()

# =========================
# DODAWANIE
# =========================
col_kat, col_prod = st.columns(2)

# --- KATEGORIE ---
with col_kat:
    st.header("➕ Dodaj kategorię")

    with st.form("form_kategoria", clear_on_submit=True):
        kat_nazwa = st.text_input("Nazwa kategorii")
        submit_kat = st.form_submit_button("Zapisz")

        if submit_kat:
            if kat_nazwa.strip() == "":
                st.error("Podaj nazwę kategorii")
            else:
                try:
                    with engine.begin() as conn:
                        conn.execute(
                            text("INSERT INTO kategorie (nazwa) VALUES (:n)"),
                            {"n": kat_nazwa.strip()}
                        )
                    st.success(f"Dodano kategorię: {kat_nazwa}")
                    st.rerun()
                except Exception:
                    st.warning("Taka kategoria już istnieje")

# --- PRODUKTY ---
with col_prod:
    st.header("➕ Dodaj produkt")

    df_kat = pd.read_sql("SELECT * FROM kategorie", engine)

    if df_kat.empty:
        st.warning("Najpierw dodaj kategorię")
    else:
        kategorie_dict = dict(zip(df_kat["nazwa"], df_kat["id"]))

        with st.form("form_produkt", clear_on_submit=True):
            prod_nazwa = st.text_input("Nazwa produktu")
            prod_liczba = st.number_input("Ilość", min_value=0, step=1)
            prod_cena = st.number_input("Cena (PLN)", min_value=0.0, step=0.01)
            prod_kat_name = st.selectbox("Kategoria", list(kategorie_dict.keys()))
            submit_prod = st.form_submit_button("Dodaj")

            if submit_prod:
                if prod_nazwa.strip() == "":
                    st.error("Podaj nazwę produktu")
                else:
                    with engine.begin() as conn:
                        conn.execute(
                            text("""
                                INSERT INTO magazyn228
                                (nazwa, liczba, cena, categorie)
                                VALUES (:n, :l, :c, :k)
                            """),
                            {
                                "n": prod_nazwa.strip(),
                                "l": int(prod_liczba),
                                "c": float(prod_cena),
                                "k": kategorie_dict[prod_kat_name],
                            },
                        )
                    st.success(f"Dodano produkt: {prod_nazwa}")
                    st.rerun()

st.divider()

# =========================
# PODGLĄD + USUWANIE
# =========================
st.header("🔍 Stan magazynu")

query = """
    SELECT 
        m.id,
        m.nazwa,
        m.liczba,
        m.cena,
        k.nazwa AS kategoria
    FROM magazyn228 m
    LEFT JOIN kategorie k ON m.categorie = k.id
"""

df_view = pd.read_sql(query, engine)

if df_view.empty:
    st.info("Brak produktów w magazynie")
else:
    st.dataframe(
        df_view.drop(columns="id"),
        use_container_width=True,
        hide_index=True
    )

    st.subheader("🗑️ Usuń produkt")

    product_map = {
        f"{row.nazwa} (ID {row.id})": row.id
        for _, row in df_view.iterrows()
    }

    selected = st.selectbox("Wybierz produkt", list(product_map.keys()))

    if st.button("Usuń", type="primary"):
        with engine.begin() as conn:
            conn.execute(
                text("DELETE FROM magazyn228 WHERE id = :id"),
                {"id": product_map[selected]}
            )
        st.warning("Produkt usunięty")
        st.rerun()

