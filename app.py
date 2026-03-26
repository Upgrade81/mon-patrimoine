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
# (Inchangées pour garder tes PRU et quantités exactes)
data_pea = {'Ticker': ['CW8.PA', 'PMEU.PA', 'ESE.PA', 'WPEA.PA'], 'Nom': ['Amundi World', 'Amundi Europe', 'BNPP S&P 500', 'iShares World'], 'Quantité': [21, 683, 4380, 1995], 'PRU': [477.41, 29.345, 25.8452, 5.0873], 'Enveloppe': 'PEA'}
data_av1 = {'Ticker': ['IE00BYX5NX33', 'FR00140081Y1'], 'Nom': ['Fidelity MSCI World', 'Carmignac Crédit 2027'], 'Quantité': [3751.4553, 38.7903], 'PRU': [11.24, 109.29], 'Enveloppe': 'AV Suravenir'}
data_av2 = {'Ticker': ['LU1135865084', 'FIXED_EURO_NETISSIMA'], 'Nom': ['Amundi S&P 500 ETF', 'Fonds Euro Netissima'], 'Quantité': [105.5002, 1], 'PRU': [377.49, 10000.00], 'Enveloppe': 'AV Meilleurtaux (Spirica)'}
data_av3 = {'Ticker': ['FR0011550185', 'FR00140081Y1_AV3', 'FR0007054358'], 'Nom': ['BNP Easy S&P 500', 'Carmignac Crédit 2027', 'Amundi Euro Stoxx 50'], 'Quantité': [607.1548, 36.0204, 8.6056], 'PRU': [27.87, 109.49, 49.40], 'Enveloppe': 'AV Meilleurtaux (4d)'}

# 2. FONCTION DE RÉCUPÉRATION AVANCÉE
def get_stock_data(ticker):
    """Retourne (Prix Actuel, Var Jour %, Var YTD %)"""
    clean_t = ticker.replace('_AV3', '')
    
    # Fallback pour Fonds Euro
    if ticker == 'FIXED_EURO_NETISSIMA':
        return 12725.89, 0.0, 2.5 # 2.5% YTD estimé pour le fonds euro
    
    # Tentative via Yahoo Finance (plus simple pour l'historique YTD)
    try:
        # Mapping spécifique pour fonds AV sur Yahoo
        y_map = {'IE00BYX5NX33': '0P0001CLDK.F', 'FR00140081Y1': '0P0001P1UF.F'}
        target = y_map.get(clean_t, clean_t)
        
        stock = yf.Ticker(target)
        # Prix actuel
        price = stock.fast_info['last_price']
        
        # Variation Jour
        prev_close = stock.fast_info['previous_close']
        var_day = ((price - prev_close) / prev_close) * 100 if prev_close else 0.0
        
        # Variation YTD (depuis le 1er Janvier 2026)
        hist_ytd = stock.history(start="2026-01-01")
        if not hist_ytd.empty:
            first_price = hist_ytd['Close'].iloc[0]
            var_ytd = ((price - first_price) / first_price) * 100
        else:
            var_ytd = 0.0
            
        return price, var_day, var_ytd
    except:
        # Fallback si Yahoo échoue : on retourne le prix de tes captures et 0%
        fallbacks = {'CW8.PA': 595.50, 'IE00BYX5NX33': 12.16, 'LU1135865084': 410.97, 'FR0011550185': 28.84}
        return fallbacks.get(clean_t, 0.0), 0.0, 0.0

# 3. CALCULS
try:
    with st.spinner('Analyse des performances en cours...'):
        all_dfs = []
        for d in [data_pea, data_av1, data_av2, data_av3]:
            df = pd.DataFrame(d)
            # Application de la fonction sur chaque ligne
            results = df['Ticker'].apply(get_stock_data)
            df['Prix Actuel'], df['Var. Jour'], df['Var. YTD'] = zip(*results)
            
            # Calculs standards
            df['Valeur Totale'] = df['Quantité'] * df['Prix Actuel']
            df['Plus-Value'] = df['Valeur Totale'] - (df['Quantité'] * df['PRU'])
            df['Perf Global %'] = (df['Plus-Value'] / (df['Quantité'] * df['PRU'])) * 100
            all_dfs.append(df)

        df_final = pd.concat(all_dfs)
        total_patrimoine = df_final['Valeur Totale'].sum()
        total_pv = df_final['Plus-Value'].sum()

    # 4. AFFICHAGE
    st.title("🏦 Dashboard Patrimonial Haute Précision")
    
    # Metrics Globales
    m1, m2, m3 = st.columns(3)
    m1.metric("Patrimoine Total", f"{total_patrimoine:,.2f} €".replace(',', ' ') if not mode_discret else "****")
    m2.metric("Plus-Value Latente", f"{total_pv:,.2f} €".replace(',', ' ') if not mode_discret else "****")
    m3.metric("Performance Totale", f"{(total_pv / (total_patrimoine - total_pv) * 100):.2f} %")

    st.divider()

    # Style des colonnes de performance
    def color_perf(val):
        color = '#09ab3b' if val >= 0 else '#ff4b4b'
        return f'color: {color}; font-weight: bold'

    def display_styled_table(df, title):
        st.subheader(title)
        # Sélection et ordre des colonnes
        cols = ['Nom', 'Valeur Totale', 'Perf Global %', 'Var. Jour', 'Var. YTD']
        disp = df[cols].copy()
        
        if mode_discret:
            disp['Valeur Totale'] = "****"
        else:
            disp['Valeur Totale'] = disp['Valeur Totale'].map('{:,.2f} €'.format).str.replace(',', ' ')

        st.dataframe(
            disp.style.applymap(color_perf, subset=['Perf Global %', 'Var. Jour', 'Var. YTD'])
            .format({'Perf Global %': '{:.2f}%', 'Var. Jour': '{:.2f}%', 'Var. YTD': '{:.2f}%'}),
            use_container_width=True
        )

    # Affichage des 4 enveloppes
    display_styled_table(all_dfs[0], "💼 Plan d'Épargne Actions")
    display_styled_table(all_dfs[1], "🛡️ AV Suravenir (Croissance)")
    display_styled_table(all_dfs[2], "🛡️ AV Meilleurtaux (Spirica)")
    display_styled_table(all_dfs[3], "🛡️ AV Meilleurtaux (4d)")

except Exception as e:
    st.error(f"Erreur lors de l'actualisation : {e}")
    
