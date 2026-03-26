import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pytz

st.set_page_config(page_title="Mon Portfolio PEA", layout="wide")

# --- SIDEBAR : MODE DISCRET ---
st.sidebar.title("Paramètres")
mode_discret = st.sidebar.checkbox("👁️ Mode Discret (Masquer montants)")

# 1. Données brutes
data = {
    'Ticker': ['CW8.PA', 'PMEU.PA', 'ESE.PA', 'WPEA.PA'],
    'Nom': ['Amundi World', 'Amundi Europe', 'BNPP S&P 500', 'iShares World'],
    'Quantité': [21, 683, 4380, 1995],
    'PRU': [477.41, 29.345, 25.8452, 5.0873]
}
df = pd.DataFrame(data)

# 2. Fonctions de récupération
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
        if price is None or price < 0.1:
            hist = t.history(period="1d")
            price = hist['Close'].iloc[-1]
        return price
    except:
        return 0

# 3. Calculs et Horodatage
with st.spinner('Mise à jour des flux...'):
    df['Prix Actuel'] = df['Ticker'].apply(get_live_price)
    df['Valeur Totale'] = df['Quantité'] * df['Prix Actuel']
    df['Plus-Value'] = df['Valeur Totale'] - (df['Quantité'] * df['PRU'])
    df['Perf %'] = (df['Plus-Value'] / (df['Quantité'] * df['PRU'])) * 100
    
    paris_tz = pytz.timezone('Europe/Paris')
    now = datetime.now(paris_tz).strftime("%d/%m/%Y %H:%M:%S")

# 4. Affichage des Metrics
st.title("📈 Mon Patrimoine PEA")
st.caption(f"Dernière actualisation : **{now}**")

total_v = df['Valeur Totale'].sum()
total_g = df['Plus-Value'].sum()
perf_globale = (total_g / (total_v - total_g)) * 100

def format_val(val, suffix="€"):
    if mode_discret:
        return "********"
    return f"{val:,.2f} {suffix}".replace(',', ' ')

c1, c2, c3 = st.columns(3)
c1.metric("Valeur Totale", format_val(total_v))
c2.metric("Plus-Value Totale", format_val(total_g))
c3.metric("Performance Globale", f"{perf_globale:.2f} %")

st.divider()

# --- TABLEAU FORMATE ---
# Copie pour affichage afin de ne pas casser les calculs
display_df = df.copy()
if mode_discret:
    cols_to_hide = ['PRU', 'Prix Actuel', 'Valeur Totale', 'Plus-Value']
    for col in cols_to_hide:
        display_df[col] = "********"
else:
    # Formatage classique
    display_df['PRU'] = display_df['PRU'].map('{:.2f} €'.format)
    display_df['Prix Actuel'] = display_df['Prix Actuel'].map('{:.2f} €'.format)
    display_df['Valeur Totale'] = display_df['Valeur Totale'].map('{:.2f} €'.format)
    display_df['Plus-Value'] = display_df['Plus-Value'].map('{:.2f} €'.format)

display_df['Perf %'] = display_df['Perf %'].map('{:.2f} %'.format)

st.dataframe(display_df, use_container_width=True)

# Graphique (On masque les chiffres dans le graphique si mode discret)
fig = px.pie(df, values='Valeur Totale', names='Nom', hole=0.4, title="Répartition du Portefeuille")
if mode_discret:
    fig.update_traces(textinfo='none', hovertemplate=None)

st.plotly_chart(fig)
