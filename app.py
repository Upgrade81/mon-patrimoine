import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pytz

st.set_page_config(page_title="Mon Patrimoine Global", layout="wide")

# --- PARAMÈTRES ---
st.sidebar.title("Configuration")
mode_discret = st.sidebar.checkbox("👁️ Mode Discret")

# 1. DONNÉES BRUTES
# --- Section PEA ---
data_pea = {
    'Ticker': ['CW8.PA', 'PMEU.PA', 'ESE.PA', 'WPEA.PA'],
    'Nom': ['Amundi World', 'Amundi Europe', 'BNPP S&P 500', 'iShares World'],
    'Quantité': [21, 683, 4380, 1995],
    'PRU': [477.41, 29.345, 25.8452, 5.0873],
    'Enveloppe': 'PEA'
}

# --- Section AV Suravenir (Croissance Avenir) ---
# Tickers Yahoo : Fidelity World (0P00015W2W.F) et Carmignac 2027 (0P0001OV87.F)
data_av = {
    'Ticker': ['0P00015W2W.F', '0P0001OV87.F'],
    'Nom': ['Fidelity MSCI World', 'Carmignac Crédit 2027'],
    'Quantité': [3751.4553, 38.7903],
    'PRU': [11.24, 109.29],
    'Enveloppe': 'AV Suravenir'
}

df_pea = pd.DataFrame(data_pea)
df_av = pd.DataFrame(data_av)

# 2. FONCTIONS DE RÉCUPÉRATION
def get_boursorama_price(ticker):
    codes = {'CW8.PA': '1rPCW8', 'PMEU.PA': '1rPMEU'}
    try:
        url = f"https://www.boursorama.com/bourse/trackers/cours/{codes[ticker]}/"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        price_tag = soup.find("span", {"class": "c-instrument c-instrument--last"})
        return float(price_tag.text.replace(" ", ""))
    except:
        fallback = {'CW8.PA': 595.50, 'PMEU.PA': 35.265}
        return fallback.get(ticker, 0)

def get_live_price(ticker):
    if ticker in ['CW8.PA', 'PMEU.PA']:
        return get_boursorama_price(ticker)
    try:
        t = yf.Ticker(ticker)
        price = t.fast_info['last_price']
        if price is None or price < 0.01:
            hist = t.history(period="5d") # Marge pour fonds AV qui cotent moins souvent
            price = hist['Close'].iloc[-1]
        return price
    except:
        return 0

# 3. CALCULS
with st.spinner('Mise à jour du patrimoine complet...'):
    # Calcul PEA
    df_pea['Prix Actuel'] = df_pea['Ticker'].apply(get_live_price)
    df_pea['Valeur Totale'] = df_pea['Quantité'] * df_pea['Prix Actuel']
    df_pea['Plus-Value'] = df_pea['Valeur Totale'] - (df_pea['Quantité'] * df_pea['PRU'])
    df_pea['Perf %'] = (df_pea['Plus-Value'] / (df_pea['Quantité'] * df_pea['PRU'])) * 100

    # Calcul AV
    df_av['Prix Actuel'] = df_av['Ticker'].apply(get_live_price)
    df_av['Valeur Totale'] = df_av['Quantité'] * df_av['Prix Actuel']
    df_av['Plus-Value'] = df_av['Valeur Totale'] - (df_av['Quantité'] * df_av['PRU'])
    df_av['Perf %'] = (df_av['Plus-Value'] / (df_av['Quantité'] * df_av['PRU'])) * 100

    # Global
    total_patrimoine = df_pea['Valeur Totale'].sum() + df_av['Valeur Totale'].sum()
    total_plus_value = df_pea['Plus-Value'].sum() + df_av['Plus-Value'].sum()

    paris_tz = pytz.timezone('Europe/Paris')
    now = datetime.now(paris_tz).strftime("%d/%m/%Y %H:%M:%S")

# 4. AFFICHAGE
st.title("🏦 Dashboard Patrimonial")
st.caption(f"Dernière synchronisation : **{now}**")

def format_val(val, suffix="€"):
    if mode_discret: return "********"
    return f"{val:,.2f} {suffix}".replace(',', ' ')

# --- METRIQUES GLOBALES ---
m1, m2, m3 = st.columns(3)
m1.metric("Patrimoine Total", format_val(total_patrimoine))
m2.metric("Plus-Value Latente", format_val(total_plus_value))
m3.metric("Performance Globale", f"{(total_plus_value / (total_patrimoine - total_plus_value) * 100):.2f} %")

st.divider()

# --- FONCTION DE STYLE ---
def style_perf(val):
    color = '#ff4b4b' if '-' in str(val) else '#09ab3b'
    return f'color: {color}; font-weight: bold'

def display_table(df, title):
    st.subheader(title)
    disp = df.copy()
    if mode_discret:
        for col in ['PRU', 'Prix Actuel', 'Valeur Totale', 'Plus-Value']: disp[col] = "********"
    else:
        for col in ['PRU', 'Prix Actuel', 'Valeur Totale', 'Plus-Value']: disp[col] = disp[col].map('{:.2f} €'.format)
    
    st.dataframe(disp.style.applymap(style_perf, subset=['Perf %']).format({'Perf %': '{:.2f} %'}), use_container_width=True)

# --- AFFICHAGE DES SECTIONS ---
display_table(df_pea, "📈 Portefeuille PEA")
display_table(df_av, "🛡️ Assurance Vie - Suravenir")

# --- GRAPHIQUES ---
col_g1, col_g2 = st.columns(2)

with col_g1:
    df_total = pd.concat([df_pea, df_av])
    fig1 = px.pie(df_total, values='Valeur Totale', names='Enveloppe', hole=0.4, title="Répartition par Enveloppe")
    st.plotly_chart(fig1, use_container_width=True)

with col_g2:
    fig2 = px.pie(df_total, values='Valeur Totale', names='Nom', hole=0.4, title="Répartition par Actif")
    st.plotly_chart(fig2, use_container_width=True)
    
