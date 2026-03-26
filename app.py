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

# 2. Fonction de récupération hybride (Yahoo + Secours Google pour PMEU)
def get_live_price(ticker):
    # CAS SPÉCIFIQUE : AMUNDI EUROPE (FR0013412038)
    if ticker == 'PMEU.PA':
        try:
            # On va chercher le prix directement sur Google Finance qui est juste
            url = "https://www.google.com/finance/quote/PMEU:EPA"
            response = requests.get(url)
            # On extrait le prix via une expression régulière
            match = re.search(r'data-last-price="([\d.]+)"', response.text)
            if match:
                return float(match.group(1))
        except:
            pass
            
    # CAS GÉNÉRAUX : YAHOO FINANCE
    try:
        t = yf.Ticker(ticker)
        price = t.fast_info['last_price']
        if price is None or price < 0.1:
            hist = t.history(period="1d")
            price = hist['Close'].iloc[-1]
        return price
    except:
        return 0

# 3. Calculs
with st.spinner('Actualisation des cours...'):
    df['Prix Actuel'] = df['Ticker'].apply(get_live_price)
    df['Valeur Totale'] = df['Quantité'] * df['Prix Actuel']
    df['Plus-Value'] = df['Valeur Totale'] - (df['Quantité'] * df['PRU'])
    df['Perf %'] = (df['Plus-Value'] / (df['Quantité'] * df['PRU'])) * 100

total_portefeuille = df['Valeur Totale'].sum()
total_gain_abs = df['Plus-Value'].sum()

# 4. Affichage
st.title("📈 Suivi PEA Temps Réel")

col1, col2 = st.columns(2)
col1.metric("Valeur Totale", f"{total_portefeuille:,.2f} €".replace(',', ' '))
col2.metric("Plus-Value Totale", f"{total_gain_abs:,.2f} €".replace(',', ' '), f"{ (total_gain_abs/(total_portefeuille-total_gain_abs)*100):.2f}%")

st.dataframe(df.style.format({
    'PRU': '{:.4f} €', 'Prix Actuel': '{:.3f} €',
    'Valeur Totale': '{:.2f} €', 'Plus-Value': '{:.2f} €', 'Perf %': '{:.2f}%'
}), use_container_width=True)

fig = px.pie(df, values='Valeur Totale', names='Nom', title="Répartition du Portefeuille")
st.plotly_chart(fig)
