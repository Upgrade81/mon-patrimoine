import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime
import pytz

st.set_page_config(page_title="Patrimoine Global Live", layout="wide")

# --- 1. CONFIGURATION DES ACTIFS ---
# Liste consolidée de tes positions (Quantités réelles issues de tes captures)
assets = [
    # PEA
    {'Ticker': 'CW8.PA', 'Qt': 21, 'Env': 'PEA', 'Nom': 'Amundi World'},
    {'Ticker': 'PMEU.PA', 'Qt': 683, 'Env': 'PEA', 'Nom': 'Amundi Europe'},
    {'Ticker': 'ESE.PA', 'Qt': 4380, 'Env': 'PEA', 'Nom': 'BNPP S&P 500'},
    {'Ticker': 'WPEA.PA', 'Qt': 1995, 'Env': 'PEA', 'Nom': 'iShares World'},
    # AV Suravenir
    {'Ticker': '0P0001CLDK.F', 'Qt': 3751.4553, 'Env': 'AV Suravenir', 'Nom': 'Fidelity World'},
    {'Ticker': '0P0001P1UF.F', 'Qt': 38.7903, 'Env': 'AV Suravenir', 'Nom': 'Carmignac 2027'},
    # AV Spirica
    {'Ticker': 'LU1135865084', 'Qt': 105.5002, 'Env': 'AV Spirica', 'Nom': 'Amundi S&P 500'},
    {'Ticker': 'FIXED', 'Qt': 1, 'Val': 12725.89, 'Env': 'AV Spirica', 'Nom': 'Fonds Euro Netissima'},
    # AV 4d
    {'Ticker': 'FR0011550185', 'Qt': 607.1548, 'Env': 'AV 4d', 'Nom': 'BNP S&P 500 (4d)'},
    {'Ticker': '0P0001P1UF.F', 'Qt': 36.0204, 'Env': 'AV 4d', 'Nom': 'Carmignac 2027 (4d)'},
    {'Ticker': 'FR0007054358', 'Qt': 8.6056, 'Env': 'AV 4d', 'Nom': 'Amundi Stoxx 50'}
]

# --- 2. INTERFACE UTILISATEUR ---
st.title("🏦 Suivi du Patrimoine Global")

period_choice = st.select_slider(
    "Choisir la période de visualisation :",
    options=["1 Jour", "1 Semaine", "1 Mois", "Année en cours", "1 An"]
)

# Mapping pour Yahoo Finance
period_map = {
    "1 Jour": ("1d", "1m"),
    "1 Semaine": ("5d", "30m"),
    "1 Mois": ("1mo", "1d"),
    "Année en cours": ("ytd", "1d"),
    "1 An": ("1y", "1d")
}
y_period, y_interval = period_map[period_choice]

# --- 3. CALCUL DU PATRIMOINE HISTORIQUE ---
@st.cache_data(ttl=3600)
def get_global_history(p, i):
    hist_data = pd.DataFrame()
    
    for asset in assets:
        if asset['Ticker'] == 'FIXED':
            continue
        try:
            # Récupération des cours de clôture
            s = yf.Ticker(asset['Ticker']).history(period=p, interval=i)['Close']
            # Calcul de la valeur de la ligne (Cours * Quantité)
            hist_data[asset['Nom']] = s * asset['Qt']
        except:
            pass
            
    # On ajoute le fonds Euro (fixe) et on somme tout
    total_series = hist_data.sum(axis=1) + 12725.89
    return total_series

try:
    with st.spinner('Mise à jour des cours en direct...'):
        history = get_global_history(y_period, y_interval)
        df_plot = history.reset_index()
        df_plot.columns = ['Date', 'Valeur']
        
        # Métriques de performance
        val_actuelle = df_plot['Valeur'].iloc[-1]
        val_debut = df_plot['Valeur'].iloc[0]
        variation = val_actuelle - val_debut
        variation_pct = (variation / val_debut) * 100

    # --- 4. AFFICHAGE DES INDICATEURS ---
    col1, col2, col3 = st.columns(3)
    col1.metric("Valeur Totale", f"{val_actuelle:,.2f} €".replace(',', ' '))
    col2.metric(f"Variation ({period_choice})", f"{variation:+,.2f} €".replace(',', ' '), delta=f"{variation_pct:.2f}%")
    col3.metric("Dernière MAJ", df_plot['Date'].iloc[-1].strftime('%d/%m %H:%M'))

    # --- 5. GRAPHIQUE D'ÉVOLUTION ---
    fig = px.area(
        df_plot, x='Date', y='Valeur',
        title=f"Évolution de votre capital total ({period_choice})",
        color_discrete_sequence=['#2ecc71']
    )
    
    fig.update_layout(
        hovermode="x unified",
        yaxis_title="Montant (€)",
        xaxis_title=None,
        template="plotly_white"
    )
    
    st.plotly_chart(fig, use_container_width=True)

    # --- 6. RÉPARTITION ACTUELLE ---
    st.divider()
    c1, c2 = st.columns(2)
    
    # Préparation des données pour les graphiques de répartition
    current_values = []
    for asset in assets:
        if asset['Ticker'] == 'FIXED':
            p = 1.0
            v = asset['Val']
        else:
            p = yf.Ticker(asset['Ticker']).fast_info['last_price']
            v = p * asset['Qt']
        current_values.append({'Nom': asset['Nom'], 'Env': asset['Env'], 'Valeur': v})
    
    df_res = pd.DataFrame(current_values)

    with c1:
        st.subheader("Répartition par Enveloppe")
        st.plotly_chart(px.pie(df_res, values='Valeur', names='Env', hole=0.4), use_container_width=True)
    
    with c2:
        st.subheader("Répartition par Actif")
        st.plotly_chart(px.pie(df_res, values='Valeur', names='Nom', hole=0.4), use_container_width=True)

except Exception as e:
    st.error(f"Erreur technique : {e}")
    
