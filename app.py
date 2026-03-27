import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Patrimoine Global - Google Finance", layout="wide")

# --- 1. CONFIGURATION DES ACTIFS ---
# Mapping Google Finance (Format -> MARCHE:TICKER)
assets = [
    {'GKey': 'EPA:CW8', 'Qt': 21, 'PRU': 477.41, 'Env': 'PEA', 'Nom': 'Amundi World'},
    {'GKey': 'EPA:PMEU', 'Qt': 683, 'PRU': 29.345, 'Env': 'PEA', 'Nom': 'Amundi Europe'},
    {'GKey': 'EPA:ESE', 'Qt': 4380, 'PRU': 25.8452, 'Env': 'PEA', 'Nom': 'BNPP S&P 500'},
    {'GKey': 'EPA:WPEA', 'Qt': 1995, 'PRU': 5.0873, 'Env': 'PEA', 'Nom': 'iShares World'},
    # Pour les fonds AV, Google Finance est limité, on utilise un fallback fixe ou Yahoo
    {'GKey': 'MUTF_FR:0P0001CLDK', 'Qt': 3751.4553, 'PRU': 11.24, 'Env': 'AV Suravenir', 'Nom': 'Fidelity World'},
    {'GKey': 'MUTF_FR:0P0001P1UF', 'Qt': 38.7903, 'PRU': 109.29, 'Env': 'AV Suravenir', 'Nom': 'Carmignac 2027'},
    {'GKey': 'EPA:500', 'Qt': 105.5002, 'PRU': 377.49, 'Env': 'AV Spirica', 'Nom': 'Amundi S&P 500'},
    {'GKey': 'FIXED', 'Qt': 1, 'Val': 12725.89, 'PRU': 10000.00, 'Env': 'AV Spirica', 'Nom': 'Fonds Euro Netissima'},
    {'GKey': 'EPA:ESE', 'Qt': 607.1548, 'PRU': 27.87, 'Env': 'AV 4d', 'Nom': 'BNP S&P 500 (4d)'},
    {'GKey': 'MUTF_FR:0P0001P1UF', 'Qt': 36.0204, 'PRU': 109.49, 'Env': 'AV 4d', 'Nom': 'Carmignac 2027 (4d)'},
    {'GKey': 'EPA:MSE', 'Qt': 8.6056, 'PRU': 49.40, 'Env': 'AV 4d', 'Nom': 'Amundi Stoxx 50'}
]

# Prix au 01/01/2026 pour le calcul YTD (Manuel pour garantir la précision)
PREVIOUS_CLOSE_YTD = {
    'EPA:CW8': 585.40, 'EPA:PMEU': 34.82, 'EPA:ESE': 28.55, 'EPA:WPEA': 5.06,
    'MUTF_FR:0P0001CLDK': 11.95, 'MUTF_FR:0P0001P1UF': 125.10, 'EPA:500': 405.20, 'EPA:MSE': 62.10
}

def scrape_google_finance(ticker):
    if ticker == 'FIXED':
        return 0, 0 # Le fonds euro est géré à part
    
    url = f"https://www.google.com/finance/quote/{ticker}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Scraping du prix actuel
        price_classes = ["YMl9u", "fx96qc"] # Classes dynamiques de Google
        price = None
        for c in price_classes:
            tag = soup.find("div", {"class": c})
            if tag:
                price = float(tag.text.replace('€', '').replace(',', '').replace('\xa0', '').strip())
                break
        
        # Scraping de la variation jour (en %)
        var_tag = soup.find("div", {"class": ["Jw7Cdb", "V73p9e"]})
        var_jour = 0.0
        if var_tag:
            var_text = var_tag.text.replace('%', '').replace('+', '').replace(',', '.')
            var_jour = float(var_text.split('(')[-1].replace(')', ''))
            
        return price, var_jour
    except:
        return None, 0.0

# --- 2. TRAITEMENT ---
st.title("🏦 Dashboard Patrimoine - Google Scraping")

with st.spinner('Extraction des données Google Finance...'):
    results = []
    for a in assets:
        if a['GKey'] == 'FIXED':
            p, vj = a['Val'], 0.0
        else:
            p, vj = scrape_google_finance(a['GKey'])
        
        if p:
            val_totale = p * a['Qt']
            pv_euros = val_totale - (a['PRU'] * a['Qt'])
            perf_totale = (pv_euros / (a['PRU'] * a['Qt'])) * 100
            
            # Calcul YTD basé sur notre dictionnaire fixe
            price_jan = PREVIOUS_CLOSE_YTD.get(a['GKey'], p)
            var_ytd = ((p - price_jan) / price_jan) * 100
            
            results.append({
                'Nom': a['Nom'], 'Env': a['Env'], 'Valeur': val_totale,
                'PV': pv_euros, 'Var. Jour': vj, 'Var. YTD': var_ytd, 'Perf. Totale': perf_totale
            })

    df = pd.DataFrame(results)

# --- 3. AFFICHAGE ---
total_v = df['Valeur'].sum()
total_pv = df['PV'].sum()

c1, c2, c3 = st.columns(3)
c1.metric("Capital Total", f"{total_v:,.2f} €".replace(',', ' '))
c2.metric("Plus-Value", f"{total_pv:,.2f} €".replace(',', ' '))
c3.metric("Performance", f"{(total_pv/(total_v-total_pv)*100):.2f} %")

st.divider()

for env in df['Env'].unique():
    st.subheader(f"📍 {env}")
    sub = df[df['Env'] == env].drop(columns='Env')
    
    st.dataframe(
        sub.style.format({
            'Valeur': '{:,.2f} €', 'PV': '{:,.2f} €',
            'Var. Jour': '{:+.2f}%', 'Var. YTD': '{:+.2f}%', 'Perf. Totale': '{:+.2f}%'
        }).applymap(lambda x: 'color: #09ab3b' if x > 0 else 'color: #ff4b4b', 
                   subset=['Var. Jour', 'Var. YTD', 'Perf. Totale']),
        use_container_width=True, hide_index=True
    )
    
