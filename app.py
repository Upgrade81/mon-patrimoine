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

# --- NOUVELLE SECTION AV2 Meilleurtaux (Spirica) ---
# Ticker Yahoo pour LU1135865084 est 500.PA. 
# Le Fonds Euro est traité comme valeur fixe.
data_av2 = {
    'Ticker': ['500.PA', 'FIXED_EURO_NETISSIMA'],
    'Nom': ['Amundi S&P 500 ETF', 'Fonds Euro Netissima'],
    'Quantité': [105.5002, 1], # Quantité = 1 pour fonds euro
    'PRU': [377.49, 10000.00], # Investissement initial netissima = 10k
    'Enveloppe': 'AV Meilleurtaux'
}

df_pea = pd.DataFrame(data_pea)
df_av1 = pd.DataFrame(data_av1)
df_av2 = pd.DataFrame(data_av2)

# 2. FONCTIONS DE RÉCUPÉRATION
def get_boursorama_price(symbol):
    mapping = {
        'CW8.PA': 'trackers/cours/1rPCW8',
        'PMEU.PA': 'trackers/cours/1rPMEU',
        'IE00BYX5NX33': 'opcvm/cours/MP-833441',
        'FR00140081Y1': 'opcvm/cours/MP-441606'
    }
    fallbacks = {'IE00BYX5NX33': 12.16, 'FR00140081Y1': 126.56, 'CW8.PA': 595.50, 'PMEU.PA': 35.265}
    try:
        url = f"https://www.boursorama.com/bourse/{mapping[symbol]}/"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        price_tag = soup.find("span", {"class": "c-instrument c-instrument--last"})
        return float(price_tag.text.replace(" ", "").replace("\n", "").replace("€", ""))
    except:
        return fallbacks.get(symbol, 0)

def get_live_price(ticker):
    # Fallback spécifique pour fonds Euro Netissima
    if ticker == 'FIXED_EURO_NETISSIMA':
        return 12725.89

    if ticker in ['CW8.PA', 'PMEU.PA', 'IE00BYX5NX33', 'FR00140081Y1']:
        return get_boursorama_price(ticker)
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
        # Calcul PEA
        df_pea['Prix Actuel'] = df_pea['Ticker'].apply(get_live_price)
        df_pea['Valeur Totale'] = df_pea['Quantité'] * df_pea['Prix Actuel']
        df_pea['Plus-Value'] = df_pea['Valeur Totale'] - (df_pea['Quantité'] * df_pea['PRU'])
        df_pea['Perf %'] = (df_pea['Plus-Value'] / (df_pea['Quantité'] * df_pea['PRU'])) * 100

        # Calcul AV1
        df_av1['Prix Actuel'] = df_av1['Ticker'].apply(get_live_price)
        df_av1['Valeur Totale'] = df_av1['Quantité'] * df_av1['Prix Actuel']
        df_av1['Plus-Value'] = df_av1['Valeur Totale'] - (df_av1['Quantité'] * df_av1['PRU'])
        df_av1['Perf %'] = (df_av1['Plus-Value'] / (df_av1['Quantité'] * df_av1['PRU'])) * 100

        # Calcul AV2
        df_av2['Prix Actuel'] = df_av2['Ticker'].apply(get_live_price)
        df_av2['Valeur Totale'] = df_av2['Quantité'] * df_av2['Prix Actuel']
        df_av2['Plus-Value'] = df_av2['Valeur Totale'] - (df_av2['Quantité'] * df_av2['PRU'])
        df_av2['Perf %'] = (df_av2['Plus-Value'] / (df_av2['Quantité'] * df_av2['PRU'])) * 100

        # Global
        total_patrimoine = df_pea['Valeur Totale'].sum() + df_av1['Valeur Totale'].sum() + df_av2['Valeur Totale'].sum()
        total_pv = df_pea['Plus-Value'].sum() + df_av1['Plus-Value'].sum() + df_av2['Plus-Value'].sum()

        paris_tz = pytz.timezone('Europe/Paris')
        now = datetime.now(paris_tz).strftime("%d/%m/%Y %H:%M:%S")

    # 4. AFFICHAGE
    st.title("🏦 Dashboard Patrimonial Consolidé")
    st.caption(f"Dernière synchronisation : **{now}**")

    def format_val(val, suffix="€"):
        if mode_discret: return "********"
        return f"{val:,.2f} {suffix}".replace(',', ' ')

    m1, m2, m3 = st.columns(3)
    m1.metric("Patrimoine Total", format_val(total_patrimoine))
    m2.metric("Plus-Value Latente", format_val(total_pv))
    m3.metric("Performance Globale", f"{(total_pv / (total_patrimoine - total_pv) * 100):.2f} %")

    st.divider()

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

    display_table(df_pea, "📈 Portefeuille PEA")
    display_table(df_av1, "🛡️ Assurance Vie 1 - Suravenir")
    display_table(df_av2, "🛡️ Assurance Vie 2 - Meilleurtaux")

    col_g1, col_g2 = st.columns(2)
    with col_g1:
        df_total = pd.concat([df_pea, df_av1, df_av2])
        st.plotly_chart(px.pie(df_total, values='Valeur Totale', names='Enveloppe', hole=0.4, title="Par Enveloppe"), use_container_width=True)
    with col_g2:
        st.plotly_chart(px.pie(df_total, values='Valeur Totale', names='Nom', hole=0.4, title="Par Actif"), use_container_width=True)

except Exception as e:
    st.error(f"Une erreur est survenue : {e}")
    
