import streamlit as st
import pandas as pd
from supabase import create_client, Client

# =========================
# KONFIGURACJA SUPABASE
# =========================
# Pobieranie danych z Twoich zmiennych
SUPABASE_URL = "https://qtrkgylsneizqdctssjx.supabase.com"
SUPABASE_KEY = "sb_publishable_CnTSduyMKnVWDcfnANakmQ_TEHd8PCB" # Upewnij się, że to Service Role Key, jeśli chcesz zapisywać dane

# Inicjalizacja klienta
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# =========================
# UI
# =========================
st.set_page_config(page_title="Magazyn Pro", layout="wide")
st.title("📦 System Zarządzania Magazynem (Native Supabase)")

# =========================
# STATYSTYKI
# =========================
st.subheader("📊 Podsumowanie Magazynu")

# Pobieranie danych przez API Supabase
response = supabase.table("magazyn228").select("liczba, cena").execute()
data = response.data

if data:
    df_stats = pd.DataFrame(data)
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
        if st.form_submit_button("Zapisz"):
            if kat_nazwa.strip():
                # Zapis przez API
                res = supabase.table("kategorie").insert({"nazwa": kat_nazwa.strip()}).execute()
                st.success(f"Dodano kategorię!")
                st.rerun()

# --- PRODUKTY ---
with col_prod:
    st.header("➕ Dodaj produkt")
    
    # Pobierz kategorie do selectboxa
    kat_res = supabase.table("kategorie").select("*").execute()
    kategorie = kat_res.data

    if not kategorie:
        st.warning("Najpierw dodaj kategorię")
    else:
        kategorie_dict = {k["nazwa"]: k["id"] for k in kategorie}
        
        with st.form("form_produkt", clear_on_submit=True):
            p_nazwa = st.text_input("Nazwa produktu")
            p_liczba = st.number_input("Ilość", min_value=0)
            p_cena = st.number_input("Cena", min_value=0.0)
            p_kat_name = st.selectbox("Kategoria", list(kategorie_dict.keys()))
            
            if st.form_submit_button("Dodaj"):
                new_prod = {
                    "nazwa": p_nazwa,
                    "liczba": p_liczba,
                    "cena": p_cena,
                    "categorie": kategorie_dict[p_kat_name]
                }
                supabase.table("magazyn228").insert(new_prod).execute()
                st.success("Produkt dodany!")
                st.rerun()

st.divider()

# =========================
# WIDOK I USUWANIE
# =========================
st.header("🔍 Stan magazynu")

# Pobieranie złączonych danych (Join w Supabase API)
view_res = supabase.table("magazyn228").select("id, nazwa, liczba, cena, kategorie(nazwa)").execute()
view_data = view_res.data

if view_data:
    # Obróbka danych dla ładniejszej tabeli
    display_data = []
    for item in view_data:
        display_data.append({
            "ID": item["id"],
            "Nazwa": item["nazwa"],
            "Liczba": item["liczba"],
            "Cena": item["cena"],
            "Kategoria": item["kategorie"]["nazwa"] if item.get("kategorie") else "Brak"
        })
    
    df_view = pd.DataFrame(display_data)
    st.dataframe(df_view.drop(columns="ID"), use_container_width=True)

    # Usuwanie
    with st.expander("🗑️ Usuń produkt"):
        to_delete = st.selectbox("Wybierz produkt", options=df_view["ID"].tolist(), 
                                format_func=lambda x: df_view[df_view["ID"] == x]["Nazwa"].values[0])
        if st.button("Potwierdź usunięcie", type="primary"):
            supabase.table("magazyn228").delete().eq("id", to_delete).execute()
            st.rerun()
