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

# 1. DONNÉES BRUTES CONSOLIDÉES
# --- Section PEA ---
data_pea = {
    'Ticker': ['CW8.PA', 'PMEU.PA', 'ESE.PA', 'WPEA.PA'],
    'Nom': ['Amundi World', 'Amundi Europe', 'BNPP S&P 500', 'iShares World'],
    'Quantité': [21, 683, 4380, 1995],
    'PRU': [477.41, 29.345, 25.8452, 5.0873],
    'Enveloppe': 'PEA'
}

# --- Section AV1 Suravenir (Croissance Avenir) ---
data_av1 = {
    'Ticker': ['IE00BYX5NX33', 'FR00140081Y1'],
    'Nom': ['Fidelity MSCI World', 'Carmignac Crédit 2027'],
    'Quantité': [3751.4553, 38.7903],
    'PRU': [11.24, 109.29],
    'Enveloppe': 'AV Suravenir'
}

# --- Section AV2 Meilleurtaux (Spirica) ---
data_av2 = {
    'Ticker': ['LU1135865084', 'FIXED_EURO_NETISSIMA'], 
    'Nom': ['Amundi S&P 500 ETF', 'Fonds Euro Netissima'],
    'Quantité': [105.5002, 1],
    'PRU': [377.49, 10000.00],
    'Enveloppe': 'AV Meilleurtaux (Spirica)'
}

# --- Section AV3 Meilleurtaux (Placement Vie 4d) ---
data_av3 = {
    'Ticker': ['FR0011550185', 'FR00140081Y1_AV3', 'FR0007054358'],
    'Nom': ['BNP Easy S&P 500', 'Carmignac Crédit 2027', 'Amundi Euro Stoxx 50'],
    'Quantité': [607.1548, 36.0204, 8.6056],
    'PRU': [27.87, 109.49, 49.40],
    'Enveloppe': 'AV Meilleurtaux (4d)'
}

df_pea = pd.DataFrame(data_pea)
df_av1 = pd.DataFrame(data_av1)
df_av2 = pd.DataFrame(data_av2)
df_av3 = pd.DataFrame(data_av3)

# 2. FONCTIONS DE RÉCUPÉRATION (SCRAPING PRIORITAIRE)
def get_boursorama_price(symbol):
    # Nettoyage du ticker si nécessaire (pour les doublons comme Carmignac)
    clean_symbol = symbol.replace('_AV3', '')
    
    mapping = {
        'CW8.PA': 'trackers/cours/1rPCW8',
        'PMEU.PA': 'trackers/cours/1rPMEU',
        'IE00BYX5NX33': 'opcvm/cours/MP-833441', # Fidelity
        'FR00140081Y1': 'opcvm/cours/MP-441606', # Carmignac
        'LU1135865084': 'trackers/cours/1rP500',  # Amundi S&P 500 (Spirica)
        'FR0011550185': 'trackers/cours/1rPESE',  # BNPP S&P 500 (4d)
        'FR0007054358': 'trackers/cours/1rPMSE'   # Amundi Stoxx 50 (4d)
    }
    
    fallbacks = {
        'IE00BYX5NX33': 12.16, 'FR00140081Y1': 126.56, 'LU1135865084': 410.97,
        'FR0011550185': 28.84, 'FR0007054358': 63.19
    }

    try:
        url = f"https://www.boursorama.com/bourse/{mapping[clean_symbol]}/"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=7)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            price_tag = soup.find("span", {"class": "c-instrument c-instrument--last"})
            if price_tag:
                return float(price_tag.text.replace(" ", "").replace("\n", "").replace("€", "").strip())
    except:
        pass
    return fallbacks.get(clean_symbol, 0)

def get_live_price(ticker):
    if ticker == 'FIXED_EURO_NETISSIMA': return 12725.89
    
    # On scrape tout ce qui est en AV ou ETF Amundi/BNP complexes
    to_scrape = ['CW8.PA', 'PMEU.PA', 'IE00BYX5NX33', 'FR00140081Y1', 'LU1135865084', 'FR0011550185', 'FR00140081Y1_AV3', 'FR0007054358']
    
    if ticker in to_scrape:
        return get_boursorama_price(ticker)
        
    try:
        t = yf.Ticker(ticker)
        price = t.fast_info['last_price']
        return price if price and price > 0.1 else t.history(period="1d")['Close'].iloc[-1]
    except:
        return 0

# 3. CALCULS
try:
    with st.spinner('Actualisation du patrimoine...'):
        for df in [df_pea, df_av1, df_av2, df_av3]:
            df['Prix Actuel'] = df['Ticker'].apply(get_live_price)
            df['Valeur Totale'] = df['Quantité'] * df['Prix Actuel']
            df['Plus-Value'] = df['Valeur Totale'] - (df['Quantité'] * df['PRU'])
            df['Perf %'] = (df['Plus-Value'] / (df['Quantité'] * df['PRU'])) * 100

        df_all = pd.concat([df_pea, df_av1, df_av2, df_av3])
        total_p = df_all['Valeur Totale'].sum()
        total_pv = df_all['Plus-Value'].sum()
        now = datetime.now(pytz.timezone('Europe/Paris')).strftime("%d/%m/%Y %H:%M:%S")

    # 4. AFFICHAGE
    st.title("📈 Dashboard Patrimonial Consolidé")
    st.caption(f"Dernière MAJ : {now}")

    def format_val(val):
        return "********" if mode_discret else f"{val:,.2f} €".replace(',', ' ')

    m1, m2, m3 = st.columns(3)
    m1.metric("Patrimoine Global", format_val(total_p))
    m2.metric("Plus-Value Totale", format_val(total_pv))
    m3.metric("Performance", f"{(total_pv / (total_p - total_pv) * 100):.2f} %")

    st.divider()

    def style_perf(val):
        return f"color: {'#ff4b4b' if '-' in str(val) else '#09ab3b'}; font-weight: bold"

    def display_table(df, title):
        st.subheader(title)
        disp = df.copy()
        cols = ['PRU', 'Prix Actuel', 'Valeur Totale', 'Plus-Value']
        if mode_discret:
            for c in cols: disp[c] = "********"
        else:
            for c in cols: disp[c] = disp[c].map('{:.2f} €'.format)
        st.dataframe(disp.style.applymap(style_perf, subset=['Perf %']).format({'Perf %': '{:.2f} %'}), use_container_width=True)

    display_table(df_pea, "💼 PEA")
    display_table(df_av1, "🛡️ AV Suravenir")
    display_table(df_av2, "🛡️ AV Meilleurtaux (Spirica)")
    display_table(df_av3, "🛡️ AV Meilleurtaux (Placement 4d)")

    st.divider()
    c_g1, c_g2 = st.columns(2)
    with c_g1: st.plotly_chart(px.pie(df_all, values='Valeur Totale', names='Enveloppe', hole=0.4, title="Par Enveloppe"))
    with c_g2: st.plotly_chart(px.pie(df_all, values='Valeur Totale', names='Nom', hole=0.4, title="Par Actif"))

except Exception as e:
    st.error(f"Erreur : {e}")
    
