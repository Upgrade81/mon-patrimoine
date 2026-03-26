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

# --- Section AV1 Suravenir (Croissance Avenir) ---
data_av1 = {
    'Ticker': ['IE00BYX5NX33', 'FR00140081Y1'],
    'Nom': ['Fidelity MSCI World', 'Carmignac Crédit 2027'],
    'Quantité': [3751.4553, 38.7903],
    'PRU': [11.24, 109.29],
    'Enveloppe': 'AV Suravenir'
}

# --- Section AV2 Meilleurtaux (Spirica) ---
data_av2 = {
    'Ticker': ['LU1135865084', 'FIXED_EURO_NETISSIMA'], 
    'Nom': ['Amundi S&P 500 ETF', 'Fonds Euro Netissima'],
    'Quantité': [105.5002, 1],
    'PRU': [377.49, 10000.00],
    'Enveloppe': 'AV Meilleurtaux'
}

df_pea = pd.DataFrame(data_pea)
df_av1 = pd.DataFrame(data_av1)
df_av2 = pd.DataFrame(data_av2)

# 2. FONCTIONS DE RÉCUPÉRATION (SCRAPING & API)
def get_boursorama_price(symbol):
    # Mapping précis vers les pages Boursorama
    mapping = {
        'CW8.PA': 'trackers/cours/1rPCW8',
        'PMEU.PA': 'trackers/cours/1rPMEU',
        'IE00BYX5NX33': 'opcvm/cours/MP-833441',
        'FR00140081Y1': 'opcvm/cours/MP-441606',
        'LU1135865084': 'trackers/cours/1rP500' # L'identifiant pour ton S&P 500 Meilleurtaux
    }
    
    # Valeurs de secours (Fallbacks)
    fallbacks = {
        'IE00BYX5NX33': 12.16, 
        'FR00140081Y1': 126.56, 
        'LU1135865084': 410.97,
        'CW8.PA': 595.50, 
        'PMEU.PA': 35.265
    }

    try:
        url = f"https://www.boursorama.com/bourse/{mapping[symbol]}/"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0'}
        response = requests.get(url, headers=headers, timeout=7)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            price_tag = soup.find("span", {"class": "c-instrument c-instrument--last"})
            if price_tag:
                raw_price = price_tag.text.replace(" ", "").replace("\n", "").replace("€", "").strip()
                return float(raw_price)
    except:
        pass
    return fallbacks.get(symbol, 0)

def get_live_price(ticker):
    # Cas particulier : Fonds Euro Netissima (Valeur fixe car non coté)
    if ticker == 'FIXED_EURO_NETISSIMA':
        return 12725.89
        
    # Liste des actifs à scraper sur Boursorama (priorité à la précision)
    to_scrape = ['CW8.PA', 'PMEU.PA', 'IE00BYX5NX33', 'FR00140081Y1', 'LU1135865084']
    
    if ticker in to_scrape:
        return get_boursorama_price(ticker)
        
    # Autres actifs via Yahoo Finance (ESE, WPEA)
    try:
        t = yf.Ticker(ticker)
        price = t.fast_info['last_price']
        if price is None or price < 0.1:
            hist = t.history(period="1d")
            price = hist['Close'].iloc[-1]
        return price
    except:
        return 0

# 3. CALCULS
try:
    with st.spinner('Synchronisation du patrimoine complet...'):
        # Calcul par enveloppe
        for df in [df_pea, df_av1, df_av2]:
            df['Prix Actuel'] = df['Ticker'].apply(get_live_price)
            df['Valeur Totale'] = df['Quantité'] * df['Prix Actuel']
            df['Plus-Value'] = df['Valeur Totale'] - (df['Quantité'] * df['PRU'])
            df['Perf %'] = (df['Plus-Value'] / (df['Quantité'] * df['PRU'])) * 100

        # Totaux Globaux
        df_all = pd.concat([df_pea, df_av1, df_av2])
        total_patrimoine = df_all['Valeur Totale'].sum()
        total_pv = df_all['Plus-Value'].sum()

        paris_tz = pytz.timezone('Europe/Paris')
        now = datetime.now(paris_tz).strftime("%d/%m/%Y %H:%M:%S")

    # 4. AFFICHAGE
    st.title("🏦 Dashboard Patrimonial Consolidé")
    st.caption(f"Dernière synchronisation : **{now}**")

    def format_val(val, suffix="€"):
        if mode_discret: return "********"
        return f"{val:,.2f} {suffix}".replace(',', ' ')

    # Metrics Haut de page
    m1, m2, m3 = st.columns(3)
    m1.metric("Patrimoine Total", format_val(total_patrimoine))
    m2.metric("Plus-Value Latente", format_val(total_pv))
    m3.metric("Performance Globale", f"{(total_pv / (total_patrimoine - total_pv) * 100):.2f} %")

    st.divider()

    # Style Couleurs
    def style_perf(val):
        color = '#ff4b4b' if '-' in str(val) else '#09ab3b'
        return f'color: {color}; font-weight: bold'

    # Affichage des tableaux
    def display_table(df, title):
        st.subheader(title)
        disp = df.copy()
        if mode_discret:
            for col in ['PRU', 'Prix Actuel', 'Valeur Totale', 'Plus-Value']: disp[col] = "********"
        else:
            for col in ['PRU', 'Prix Actuel', 'Valeur Totale', 'Plus-Value']: disp[col] = disp[col].map('{:.2f} €'.format)
        st.dataframe(disp.style.applymap(style_perf, subset=['Perf %']).format({'Perf %': '{:.2f} %'}), use_container_width=True)

    display_table(df_pea, "📈 Portefeuille PEA")
    display_table(df_av1, "🛡️ Assurance Vie 1 - Suravenir")
    display_table(df_av2, "🛡️ Assurance Vie 2 - Meilleurtaux")

    # Graphiques
    st.divider()
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.plotly_chart(px.pie(df_all, values='Valeur Totale', names='Enveloppe', hole=0.4, title="Répartition par Enveloppe"), use_container_width=True)
    with col_g2:
        st.plotly_chart(px.pie(df_all, values='Valeur Totale', names='Nom', hole=0.4, title="Répartition par Actif"), use_container_width=True)

except Exception as e:
    st.error(f"Une erreur est survenue lors du calcul : {e}")
    
