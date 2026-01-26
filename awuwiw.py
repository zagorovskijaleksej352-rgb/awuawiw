import streamlit as st
import pandas as pd
from supabase import create_client

# Pobieranie danych z Secrets
URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]

# Inicjalizacja klienta
supabase = create_client(URL, KEY)

st.set_page_config(page_title="Magazyn Pro", layout="wide")
st.title("📦 System Zarządzania Magazynem")

# --- FUNKCJE POMOCNICZE ---
def get_categories():
    res = supabase.table("kategorie").select("*").execute()
    return res.data

def get_products():
    # Pobieramy produkty razem z nazwą kategorii (join)
    res = supabase.table("magazyn228").select("id, nazwa, liczba, cena, kategorie(nazwa)").execute()
    return res.data

# --- WIDOK STATYSTYK ---
data = get_products()
if data:
    df = pd.json_normalize(data)
    # Zmiana nazw kolumn dla czytelności (zależy od struktury w Supabase)
    if 'kategorie.nazwa' in df.columns:
        df = df.rename(columns={'kategorie.nazwa': 'kategoria'})
    
    col1, col2 = st.columns(2)
    col1.metric("Suma produktów", int(df["liczba"].sum()))
    col2.metric("Wartość magazynu", f"{(df['liczba'] * df['cena']).sum():,.2f} PLN")
    
    st.divider()
    st.dataframe(df.drop(columns=['id'], errors='ignore'), use_container_width=True)
else:
    st.info("Magazyn jest pusty.")

# --- FORMULARZE ---
st.divider()
c1, c2 = st.columns(2)

with c1:
    st.subheader("➕ Dodaj kategorię")
    with st.form("kat_form", clear_on_submit=True):
        nowa_kat = st.text_input("Nazwa kategorii")
        if st.form_submit_button("Dodaj"):
            if nowa_kat:
                supabase.table("kategorie").insert({"nazwa": nowa_kat}).execute()
                st.rerun()

with c2:
    st.subheader("➕ Dodaj produkt")
    kategorie = get_categories()
    if kategorie:
        kat_map = {k['nazwa']: k['id'] for k in kategorie}
        with st.form("prod_form", clear_on_submit=True):
            p_nazwa = st.text_input("Nazwa produktu")
            p_ilosc = st.number_input("Ilość", min_value=0)
            p_cena = st.number_input("Cena", min_value=0.0)
            p_kat = st.selectbox("Kategoria", list(kat_map.keys()))
            if st.form_submit_button("Zapisz produkt"):
                supabase.table("magazyn228").insert({
                    "nazwa": p_nazwa, 
                    "liczba": p_ilosc, 
                    "cena": p_cena, 
                    "categorie": kat_map[p_kat]
                }).execute()
                st.rerun()

# --- USUWANIE ---
if data:
    st.divider()
    with st.expander("🗑️ Usuń produkt"):
        df_del = pd.DataFrame(data)
        wybrany = st.selectbox("Produkt do usunięcia", options=df_del['id'].tolist(),
                               format_func=lambda x: df_del[df_del['id']==x]['nazwa'].values[0])
        if st.button("Usuń trwale", type="primary"):
            supabase.table("magazyn228").delete().eq("id", wybrany).execute()
            st.rerun()
