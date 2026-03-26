import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import requests
from bs4 import BeautifulSoup

st.set_page_config(page_title="Mon Portfolio PEA", layout="wide")

# 1. Données brutes
data = {
    'Ticker': ['CW8.PA', 'PMEU.PA', 'ESE.PA', 'WPEA.PA'],
    'Nom': ['Amundi World', 'Amundi Europe', 'BNPP S&P 500', 'iShares World'],
    'Quantité': [21, 683, 4380, 1995],
    'PRU': [477.41, 29.345, 25.8452, 5.0873]
}
df = pd.DataFrame(data)

# 2. Fonction de secours pour Amundi Europe via Boursorama
def get_pmeu_price():
    try:
        url = "https://www.boursorama.com/bourse/trackers/cours/1rPMEU/"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        # On cherche la balise qui contient le cours actuel
        price_tag = soup.find("span", {"class": "c-instrument c-instrument--last"})
        return float(price_tag.text.replace(" ", ""))
    except:
        return 35.265 # Prix de secours si Boursorama bloque

def get_live_price(ticker):
    if ticker == 'PMEU.PA':
        return get_pmeu_price()
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
with st.spinner('Connexion aux places boursières...'):
    df['Prix Actuel'] = df['Ticker'].apply(get_live_price)
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

st.dataframe(df.style.format({'PRU': '{:.4f} €', 'Prix Actuel': '{:.3f} €', 'Valeur Totale': '{:.2f} €', 'Plus-Value': '{:.2f} €', 'Perf %': '{:.2f}%'}), use_container_width=True)
st.plotly_chart(px.pie(df, values='Valeur Totale', names='Nom', title="Répartition"))
