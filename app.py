import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz

st.set_page_config(page_title="Mon Patrimoine Live", layout="wide")

# --- 1. CONFIGURATION DES ACTIFS ---
# On garde tes quantités exactes et tes PRU pour le calcul de performance
assets = [
    # PEA
    {'Ticker': 'CW8.PA', 'Qt': 21, 'PRU': 477.41, 'Env': 'PEA', 'Nom': 'Amundi World'},
    {'Ticker': 'PMEU.PA', 'Qt': 683, 'PRU': 29.345, 'Env': 'PEA', 'Nom': 'Amundi Europe'},
    {'Ticker': 'ESE.PA', 'Qt': 4380, 'PRU': 25.8452, 'Env': 'PEA', 'Nom': 'BNPP S&P 500'},
    {'Ticker': 'WPEA.PA', 'Qt': 1995, 'PRU': 5.0873, 'Env': 'PEA', 'Nom': 'iShares World'},
    # AV Suravenir
    {'Ticker': '0P0001CLDK.F', 'Qt': 3751.4553, 'PRU': 11.24, 'Env': 'AV Suravenir', 'Nom': 'Fidelity World'},
    {'Ticker': '0P0001P1UF.F', 'Qt': 38.7903, 'PRU': 109.29, 'Env': 'AV Suravenir', 'Nom': 'Carmignac 2027'},
    # AV Spirica
    {'Ticker': 'LU1135865084', 'Qt': 105.5002, 'PRU': 377.49, 'Env': 'AV Spirica', 'Nom': 'Amundi S&P 500'},
    {'Ticker': 'FIXED', 'Qt': 1, 'Val': 12725.89, 'PRU': 10000.00, 'Env': 'AV Spirica', 'Nom': 'Fonds Euro Netissima'},
    # AV 4d
    {'Ticker': 'FR0011550185', 'Qt': 607.1548, 'PRU': 27.87, 'Env': 'AV 4d', 'Nom': 'BNP S&P 500 (4d)'},
    {'Ticker': '0P0001P1UF.F', 'Qt': 36.0204, 'PRU': 109.49, 'Env': 'AV 4d', 'Nom': 'Carmignac 2027 (4d)'},
    {'Ticker': 'FR0007054358', 'Qt': 8.6056, 'PRU': 49.40, 'Env': 'AV 4d', 'Nom': 'Amundi Stoxx 50'}
]

# --- 2. RÉCUPÉRATION DES DONNÉES ---
def get_live_data(asset):
    if asset['Ticker'] == 'FIXED':
        return asset['Val'], 0.0, 2.8  # Prix fixe, Var Jour 0, Var YTD estimée
    
    try:
        s = yf.Ticker(asset['Ticker'])
        fast = s.fast_info
        price = fast['last_price']
        
        # Variation Jour
        v_jour = ((price - fast['previous_close']) / fast['previous_close']) * 100
        
        # Variation YTD (Année en cours 2026)
        h = s.history(start="2026-01-01")
        v_ytd = ((price - h['Close'].iloc[0]) / h['Close'].iloc[0]) * 100 if not h.empty else 0.0
        
        return price, v_jour, v_ytd
    except:
        return 0.0, 0.0, 0.0

# --- 3. CALCULS ET AFFICHAGE ---
st.title("🏦 Récapitulatif du Patrimoine Global")

try:
    with st.spinner('Actualisation des cours...'):
        results = []
        for a in assets:
            p, vj, vy = get_live_data(a)
            val_totale = p * a['Qt']
            pv = val_totale - (a['PRU'] * a['Qt'])
            perf_globale = (pv / (a['PRU'] * a['Qt'])) * 100
            
            results.append({
                'Nom': a['Nom'],
                'Enveloppe': a['Env'],
                'Prix Actuel': p,
                'Valeur Totale': val_totale,
                'Plus-Value': pv,
                'Var. Jour': vj,
                'Var. YTD': vy,
                'Perf. Totale': perf_globale
            })

        df = pd.DataFrame(results)
        total_patrimoine = df['Valeur Totale'].sum()
        total_pv = df['Plus-Value'].sum()

    # Métriques Haut de Page
    m1, m2, m3 = st.columns(3)
    m1.metric("Patrimoine Global", f"{total_patrimoine:,.2f} €".replace(',', ' '))
    m2.metric("Plus-Value Latente", f"{total_pv:,.2f} €".replace(',', ' '))
    m3.metric("Performance Globale", f"{(total_pv / (total_patrimoine - total_pv) * 100):.2f} %")

    st.divider()

    # Affichage par enveloppe
    def style_performance(v):
        color = '#09ab3b' if v >= 0 else '#ff4b4b'
        return f'color: {color}; font-weight: bold'

    for env in df['Enveloppe'].unique():
        st.subheader(f"📍 {env}")
        sub_df = df[df['Enveloppe'] == env][['Nom', 'Valeur Totale', 'Plus-Value', 'Var. Jour', 'Var. YTD', 'Perf. Totale']]
        
        st.dataframe(
            sub_df.style.applymap(style_performance, subset=['Var. Jour', 'Var. YTD', 'Perf. Totale'])
            .format({
                'Valeur Totale': '{:,.2f} €',
                'Plus-Value': '{:,.2f} €',
                'Var. Jour': '{:+.2f} %',
                'Var. YTD': '{:+.2f} %',
                'Perf. Totale': '{:+.2f} %'
            }),
            use_container_width=True,
            hide_index=True
        )

    st.caption(f"Dernière mise à jour : {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

except Exception as e:
    st.error(f"Erreur lors de la mise à jour : {e}")
