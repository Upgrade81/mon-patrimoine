import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pytz
import time

st.set_page_config(page_title="Mon Patrimoine Global", layout="wide")

# --- PARAMÈTRES ---
st.sidebar.title("Configuration")
mode_discret = st.sidebar.checkbox("👁️ Mode Discret")

# 1. DONNÉES BRUTES
data_pea = {
    'Ticker': ['CW8.PA', 'PMEU.PA', 'ESE.PA', 'WPEA.PA'],
    'Nom': ['Amundi World', 'Amundi Europe', 'BNPP S&P 500', 'iShares World'],
    'Quantité': [21, 683, 4380, 1995],
    'PRU': [477.41, 29.345, 25.8452, 5.0873],
    'Enveloppe': 'PEA'
}

data_av1 = {
    'Ticker': ['IE00BYX5NX33', 'FR00140081Y1'],
    'Nom': ['Fidelity MSCI World', 'Carmignac Crédit 2027'],
    'Quantité': [3751.4553, 38.7903],
    'PRU': [11.24, 109.29],
    'Enveloppe': 'AV Suravenir'
}

data_av2 = {
    'Ticker': ['LU1135865084', 'FIXED_EURO_NETISSIMA'], 
    'Nom': ['Amundi S&P 500 ETF', 'Fonds Euro Netissima'],
    'Quantité': [105.5002, 1],
    'PRU': [377.49, 10000.00],
    'Enveloppe': 'AV Meilleurtaux (Spirica)'
}

data_av3 = {
    'Ticker': ['FR0011550185', 'FR00140081Y1_AV3', 'FR0007054358'],
    'Nom': ['BNP Easy S&P 500', 'Carmignac Crédit 2027', 'Amundi Euro Stoxx 50'],
    'Quantité': [607.1548, 36.0204, 8.6056],
    'PRU': [27.87, 109.49, 49.40],
    'Enveloppe': 'AV Meilleurtaux (4d)'
}

# 2. FONCTIONS DE RÉCUPÉRATION ROBUSTES
def get_boursorama_price(symbol):
    clean_symbol = symbol.replace('_AV3', '')
    mapping = {
        'CW8.PA': 'trackers/cours/1rPCW8', 'PMEU.PA': 'trackers/cours/1rPMEU',
        'ESE.PA': 'trackers/cours/1rPESE', 'WPEA.PA': 'trackers/cours/1rPWPEA',
        'IE00BYX5NX33': 'opcvm/cours/MP-833441', 'FR00140081Y1': 'opcvm/cours/MP-441606',
        'LU1135865084': 'trackers/cours/1rP500', 'FR0011550185': 'trackers/cours/1rPESE',
        'FR0007054358': 'trackers/cours/1rPMSE'
    }
    try:
        url = f"https://www.boursorama.com/bourse/{mapping[clean_symbol]}/"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            tag = soup.find("span", {"class": "c-instrument c-instrument--last"})
            if tag:
                return float(tag.text.replace(" ", "").replace("\n", "").replace("€", "").strip())
    except:
        pass
    return None

def get_live_price(ticker):
    if ticker == 'FIXED_EURO_NETISSIMA': return 12725.89 #
    
    # Tentative 1 : Boursorama
    price = get_boursorama_price(ticker)
    if price: return price
    
    # Tentative 2 : Yahoo Finance (pour le PEA surtout)
    try:
        y_ticker = ticker.replace('_AV3', '')
        # Mapping spécifique pour les fonds d'assurance vie sur Yahoo si besoin
        yahoo_mapping = {'IE00BYX5NX33': '0P0001CLDK.F', 'FR00140081Y1': '0P0001P1UF.F'}
        t = yf.Ticker(yahoo_mapping.get(y_ticker, y_ticker))
        price = t.fast_info['last_price']
        if price and price > 0.1: return price
    except:
        pass

    # Tentative 3 : Dernières valeurs connues (Fallbacks)
    fallbacks = {
        'CW8.PA': 595.50, 'PMEU.PA': 35.26, 'ESE.PA': 25.85, 'WPEA.PA': 5.09,
        'IE00BYX5NX33': 12.16, 'FR00140081Y1': 126.56, 'LU1135865084': 410.97,
        'FR0011550185': 28.84, 'FR0007054358': 63.19
    }
    return fallbacks.get(ticker.replace('_AV3', ''), 0)

# 3. CALCULS ET AFFICHAGE
try:
    with st.spinner('Récupération des cours...'):
        dfs = [pd.DataFrame(data_pea), pd.DataFrame(data_av1), pd.DataFrame(data_av2), pd.DataFrame(data_av3)]
        for df in dfs:
            df['Prix Actuel'] = df['Ticker'].apply(get_live_price)
            df['Valeur Totale'] = df['Quantité'] * df['Prix Actuel']
            df['Plus-Value'] = df['Valeur Totale'] - (df['Quantité'] * df['PRU'])
            df['Perf %'] = (df['Plus-Value'] / (df['Quantité'] * df['PRU'])) * 100

        df_all = pd.concat(dfs)
        total_p = df_all['Valeur Totale'].sum()
        total_pv = df_all['Plus-Value'].sum()

    st.title("🏦 Mon Patrimoine Global")
    m1, m2, m3 = st.columns(3)
    m1.metric("Patrimoine Global", f"{total_p:,.2f} €".replace(',', ' ') if not mode_discret else "****")
    m2.metric("Plus-Value Totale", f"{total_pv:,.2f} €".replace(',', ' ') if not mode_discret else "****")
    m3.metric("Performance", f"{(total_pv / (total_p - total_pv) * 100):.2f} %")

    st.divider()
    
    def display_table(df, title):
        st.subheader(title)
        st.dataframe(df.style.format({'Perf %': '{:.2f} %'}), use_container_width=True)

    display_table(dfs[0], "💼 PEA")
    display_table(dfs[1], "🛡️ AV Suravenir")
    display_table(dfs[2], "🛡️ AV Meilleurtaux (Spirica)")
    display_table(dfs[3], "🛡️ AV Meilleurtaux (4d)")

except Exception as e:
    st.error(f"Erreur d'affichage : {e}")
    
