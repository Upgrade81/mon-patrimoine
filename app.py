import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pytz

st.set_page_config(page_title="Mon Portfolio PEA", layout="wide")

# --- PARAMÈTRES ---
st.sidebar.title("Configuration")
mode_discret = st.sidebar.checkbox("👁️ Mode Discret")

# 1. Données brutes
data = {
    'Ticker': ['CW8.PA', 'PMEU.PA', 'ESE.PA', 'WPEA.PA'],
    'Nom': ['Amundi World', 'Amundi Europe', 'BNPP S&P 500', 'iShares World'],
    'Quantité': [21, 683, 4380, 1995],
    'PRU': [477.41, 29.345, 25.8452, 5.0873]
}
df = pd.DataFrame(data)

# 2. Fonctions de récupération (Hybrid Scraping/API)
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
        return 0

def get_hist_price(ticker, days_back):
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period="1y") 
        target_date = datetime.now() - timedelta(days=days_back)
        idx = hist.index.get_indexer([target_date], method='nearest')[0]
        return hist['Close'].iloc[idx]
    except:
        return 0

# 3. Calculs
with st.spinner('Analyse des performances...'):
    # Prix Actuels
    df['Prix Actuel'] = df['Ticker'].apply(lambda x: get_boursorama_price(x) if x in ['CW8.PA', 'PMEU.PA'] else yf.Ticker(x).fast_info['last_price'])
    
    # Historiques pour variations
    df['Prix_1J'] = df['Ticker'].apply(lambda x: get_hist_price(x, 1))
    df['Prix_1M'] = df['Ticker'].apply(lambda x: get_hist_price(x, 30))
    df['Prix_1Y'] = df['Ticker'].apply(lambda x: get_hist_price(x, 365))

    # Valeurs et Performances
    df['Valeur Totale'] = df['Quantité'] * df['Prix Actuel']
    df['Plus-Value'] = df['Valeur Totale'] - (df['Quantité'] * df['PRU'])
    df['Var_1J'] = ((df['Prix Actuel'] - df['Prix_1J']) / df['Prix_1J']) * 100
    df['Var_1M'] = ((df['Prix Actuel'] - df['Prix_1M']) / df['Prix_1M']) * 100
    df['Var_1Y'] = ((df['Prix Actuel'] - df['Prix_1Y']) / df['Prix_1Y']) * 100
    df['Perf Globale %'] = ((df['Prix Actuel'] - df['PRU']) / df['PRU']) * 100

    paris_tz = pytz.timezone('Europe/Paris')
    now = datetime.now(paris_tz).strftime("%d/%m/%Y %H:%M:%S")

# 4. Affichage
st.title("📈 Dashboard Performance PEA")
st.caption(f"Dernière mise à jour : {now}")

total_v = df['Valeur Totale'].sum()
total_g = df['Plus-Value'].sum()

def format_val(val):
    return "********" if mode_discret else f"{val:,.2f} €".replace(',', ' ')

c1, c2, c3 = st.columns(3)
c1.metric("Capital Total", format_val(total_v))
c2.metric("Plus-Value Latente", format_val(total_g), delta=f"{df['Var_1J'].mean():.2f}% (24h)")
c3.metric("Performance Moyenne", f"{df['Perf Globale %'].mean():.2f}%")

st.divider()

# --- TABLEAU AVEC COULEURS ---
def color_sur_fond(val):
    color = '#ff4b4b' if val < 0 else '#09ab3b' # Rouge / Vert Streamlit
    return f'color: {color}; font-weight: bold'

display_df = df[['Nom', 'Quantité', 'Prix Actuel', 'Valeur Totale', 'Perf Globale %', 'Var_1J', 'Var_1M', 'Var_1Y']].copy()

if mode_discret:
    display_df['Prix Actuel'] = "********"
    display_df['Valeur Totale'] = "********"

st.subheader("Détail des actifs et Variations")
st.dataframe(display_df.style.applymap(color_sur_fond, subset=['Perf Globale %', 'Var_1J', 'Var_1M', 'Var_1Y'])
             .format({
                 'Prix Actuel': '{:.2f} €' if not mode_discret else '{}',
                 'Valeur Totale': '{:.2f} €' if not mode_discret else '{}',
                 'Perf Globale %': '{:.2f}%',
                 'Var_1J': '{:.2f}%',
                 'Var_1M': '{:.2f}%',
                 'Var_1Y': '{:.2f}%'
             }), use_container_width=True)

# Graphique de Performance
st.plotly_chart(px.bar(df, x='Nom', y='Perf Globale %', color='Perf Globale %', 
                       color_continuous_scale='RdYlGn',
                       title="Performance globale par actif (en %)"))
