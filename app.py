import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Mon Dashboard Patrimoine", layout="wide")
st.title("📈 Mon Patrimoine en Temps Réel")

# --- 1. TES DONNÉES (Version Corrigée) ---
data = {
    'Enveloppe': ['PEA', 'PEA', 'PEA', 'PEA'],
    'Nom': [
        'Amundi MSCI World Swap', 
        'Amundi MSCI Europe PEA', 
        'BNPP Easy S&P 500 PEA', 
        'iShares MSCI Wld Swap PEA'
    ],
        'Ticker': [
        'CW8.PA',     # Amundi World (Fonctionne déjà)
        'PMEU',      # Amundi Europe (Ticker corrigé pour Bourse de Paris)
        'ESE.PA',     # BNPP S&P 500 (Fonctionne déjà)
        'WPEA.PA'     # iShares World Swap PEA (Le ticker le plus fiable pour ton ISIN)
    ],
    
    'Quantité': [21, 683, 4380, 1995],
    'PRU': [
        477.41,   # World
        29.345,   # Europe
        25.8452,  # S&P 500
        5.0873    # iShares
    ]
}


df = pd.DataFrame(data)

# --- 2. SYNCHRONISATION LIVE ---
st.sidebar.header("Paramètres")
refresh = st.sidebar.button("Rafraîchir les cours")

@st.cache_data(ttl=60) # Rafraîchit les données toutes les 60 secondes
def get_live_prices(tickers):
    prices = {}
    for t in tickers:
        try:
            stock = yf.Ticker(t)
            # Récupère le dernier prix de clôture
            prices[t] = stock.fast_info['last_price']
        except:
            prices[t] = 0
    return prices

try:
    with st.spinner('Récupération des cours en direct...'):
        live_prices = get_live_prices(df['Ticker'].tolist())
    
    # Calculs automatiques
    df['Prix Actuel'] = df['Ticker'].map(live_prices)
    df['Valeur Totale'] = df['Prix Actuel'] * df['Quantité']
    df['Plus-Value'] = (df['Prix Actuel'] - df['PRU']) * df['Quantité']
    df['Perf %'] = ((df['Prix Actuel'] - df['PRU']) / df['PRU']) * 100

    # --- 3. AFFICHAGE DES INDICATEURS CLÉS ---
    total_patrimoine = df['Valeur Totale'].sum()
    total_pv = df['Plus-Value'].sum()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Valeur Totale", f"{total_patrimoine:,.2f} €")
    col2.metric("Plus-Value Globale", f"{total_pv:,.2f} €", delta=f"{total_pv:,.2f}")
    col3.metric("Performance Moyenne", f"{(total_pv/(total_patrimoine-total_pv)*100):.2f} %")

    # --- 4. VISUALISATION ---
    st.divider()
    c1, c2 = st.columns([2, 1])
    
    with c1:
        st.write("### Détail de mes positions")
        # Formatage pour une lecture propre
        st.dataframe(df.style.format({
            'Prix Actuel': '{:.2f} €',
            'Valeur Totale': '{:.2f} €',
            'Plus-Value': '{:.2f} €',
            'Perf %': '{:.2f} %'
        }), use_container_width=True)

    with c2:
        st.write("### Répartition par Enveloppe")
        fig = px.pie(df, values='Valeur Totale', names='Enveloppe', hole=0.4)
        st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"Erreur lors de la synchronisation : {e}")
