import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import requests
import re

st.set_page_config(page_title="Mon Portfolio PEA", layout="wide")

# 1. Données brutes
data = {
    'Ticker': ['CW8.PA', 'PMEU.PA', 'ESE.PA', 'WPEA.PA'],
    'Nom': ['Amundi World', 'Amundi Europe', 'BNPP S&P 500', 'iShares World'],
    'Quantité': [21, 683, 4380, 1995],
    'PRU': [477.41, 29.345, 25.8452, 5.0873]
}
df = pd.DataFrame(data)

# 2. Fonction de récupération ultra-robuste
def get_price(ticker):
    # Tentative Google Finance pour les tickers Amundi qui buggent
    if ticker in ['CW8.PA', 'PMEU.PA']:
        try:
            google_code = "CW8:EPA" if ticker == 'CW8.PA' else "PMEU:EPA"
            url = f"https://www.google.com/finance/quote/{google_code}"
            response = requests.get(url, timeout=5)
            match = re.search(r'data-last-price="([\d.]+)"', response.text)
            if match:
                return float(match.group(1))
        except:
            pass

    # Tentative Yahoo Finance pour les autres (ou en secours)
    try:
        t = yf.Ticker(ticker)
        p = t.fast_info['last_price']
        if p is None or p < 0.1:
            p = t.history(period="1d")['Close'].iloc[-1]
        return p
    except:
        return 0

# 3. Calculs
with st.spinner('Récupération des cours réels...'):
    df['Prix Actuel'] = df['Ticker'].apply(get_price)
    df['Valeur Totale'] = df['Quantité'] * df['Prix Actuel']
    df['Plus-Value'] = df['Valeur Totale'] - (df['Quantité'] * df['PRU'])
    df['Perf %'] = (df['Plus-Value'] / (df['Quantité'] * df['PRU'])) * 100

# 4. Affichage
st.title("📈 Suivi PEA Temps Réel")

total_v = df['Valeur Totale'].sum()
total_g = df['Plus-Value'].sum()

c1, c2 = st.columns(2)
c1.metric("Valeur Totale", f"{total_v:,.2f} €".replace(',', ' '))
c2.metric("Plus-Value Totale", f"{total_g:,.2f} €".replace(',', ' '), f"{(total_g/(total_v-total_g)*100):.2f}%")

st.dataframe(df.style.format({'PRU': '{:.2f} €', 'Prix Actuel': '{:.2f} €', 'Valeur Totale': '{:.2f} €', 'Plus-Value': '{:.2f} €', 'Perf %': '{:.2f}%'}), use_container_width=True)

st.plotly_chart(px.pie(df, values='Valeur Totale', names='Nom', title="Répartition"))
