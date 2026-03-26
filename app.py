import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Mon Portfolio PEA", layout="wide")

# 1. Données brutes (PRU et Quantités conformes à ton relevé)
data = {
    'Ticker': ['CW8.PA', 'PMEU.PA', 'ESE.PA', 'WPEA.PA'],
    'Nom': ['Amundi World', 'Amundi Europe', 'BNPP S&P 500', 'iShares World'],
    'Quantité': [21, 683, 4380, 1995],
    'PRU': [477.41, 29.345, 25.8452, 5.0873]
}

df = pd.DataFrame(data)

# 2. Fonction de récupération du prix en temps réel
def get_live_price(ticker):
    try:
        t = yf.Ticker(ticker)
        # Tentative 1 : Prix direct
        price = t.fast_info['last_price']
        # Tentative 2 : Si Tentative 1 échoue ou renvoie 0
        if price is None or price < 0.1:
            hist = t.history(period="1d")
            price = hist['Close'].iloc[-1]
        return price
    except:
        return 0

# 3. Calculs
with st.spinner('Actualisation des cours en direct...'):
    df['Prix Actuel'] = df['Ticker'].apply(get_live_price)
    df['Valeur Totale'] = df['Quantité'] * df['Prix Actuel']
    df['Plus-Value'] = df['Valeur Totale'] - (df['Quantité'] * df['PRU'])
    df['Perf %'] = (df['Plus-Value'] / (df['Quantité'] * df['PRU'])) * 100

total_portefeuille = df['Valeur Totale'].sum()
total_gain_abs = df['Plus-Value'].sum()

# 4. Affichage du Dashboard
st.title("📈 Suivi PEA Temps Réel")

col1, col2 = st.columns(2)
col1.metric("Valeur Totale", f"{total_portefeuille:,.2f} €".replace(',', ' '))
col2.metric("Plus-Value Totale", f"{total_gain_abs:,.2f} €".replace(',', ' '), f"{ (total_gain_abs/(total_portefeuille-total_gain_abs)*100):.2f}%")

st.dataframe(df.style.format({
    'PRU': '{:.4f} €',
    'Prix Actuel': '{:.3f} €',
    'Valeur Totale': '{:.2f} €',
    'Plus-Value': '{:.2f} €',
    'Perf %': '{:.2f}%'
}), use_container_width=True)

# Graphique de répartition
fig = px.pie(df, values='Valeur Totale', names='Nom', title="Répartition du Portefeuille")
st.plotly_chart(fig)
