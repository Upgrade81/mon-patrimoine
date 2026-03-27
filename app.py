import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Patrimoine Boursorama Live", layout="wide")

# --- 1. CONFIGURATION DES ACTIFS (URLs Boursorama) ---
assets = [
    # PEA
    {'Url': 'https://www.boursorama.com/bourse/etf/cours/1rACW8/', 'Qt': 21, 'PRU': 477.41, 'Env': 'PEA', 'Nom': 'Amundi World'},
    {'Url': 'https://www.boursorama.com/bourse/etf/cours/1rAPMEU/', 'Qt': 683, 'PRU': 29.345, 'Env': 'PEA', 'Nom': 'Amundi Europe'},
    {'Url': 'https://www.boursorama.com/bourse/etf/cours/1rAESE/', 'Qt': 4380, 'PRU': 25.8452, 'Env': 'PEA', 'Nom': 'BNPP S&P 500'},
    {'Url': 'https://www.boursorama.com/bourse/etf/cours/1rAWPEA/', 'Qt': 1995, 'PRU': 5.0873, 'Env': 'PEA', 'Nom': 'iShares World'},
    # AV Suravenir
    {'Url': 'https://www.boursorama.com/bourse/opcvm/cours/0P0001CLDK/', 'Qt': 3751.4553, 'PRU': 11.24, 'Env': 'AV Suravenir', 'Nom': 'Fidelity World'},
    {'Url': 'https://www.boursorama.com/bourse/opcvm/cours/0P0001P1UF/', 'Qt': 38.7903, 'PRU': 109.29, 'Env': 'AV Suravenir', 'Nom': 'Carmignac 2027'},
    # AV Spirica
    {'Url': 'https://www.boursorama.com/bourse/etf/cours/1rALU1135865084/', 'Qt': 105.5002, 'PRU': 377.49, 'Env': 'AV Spirica', 'Nom': 'Amundi S&P 500'},
    {'Url': 'FIXED', 'Qt': 1, 'Val': 12725.89, 'PRU': 10000.00, 'Env': 'AV Spirica', 'Nom': 'Fonds Euro Netissima'},
    # AV 4d
    {'Url': 'https://www.boursorama.com/bourse/etf/cours/1rAFR0011550185/', 'Qt': 607.1548, 'PRU': 27.87, 'Env': 'AV 4d', 'Nom': 'BNP S&P 500 (4d)'},
    {'Url': 'https://www.boursorama.com/bourse/opcvm/cours/0P0001P1UF/', 'Qt': 36.0204, 'PRU': 109.49, 'Env': 'AV 4d', 'Nom': 'Carmignac 2027 (4d)'},
    {'Url': 'https://www.boursorama.com/bourse/etf/cours/1rAFR0007054358/', 'Qt': 8.6056, 'PRU': 49.40, 'Env': 'AV 4d', 'Nom': 'Amundi Stoxx 50'}
]

def scrape_boursorama(url):
    if url == 'FIXED': return None
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. Extraction du prix
        price_tag = soup.find("span", class_="c-instrument--last")
        price = float(price_tag.text.replace(" ", "").strip())
        
        # 2. Extraction Var Jour
        var_day_tag = soup.find("span", class_="c-instrument--variation")
        var_day = float(var_day_tag.text.replace("%", "").strip())
        
        # 3. Extraction Var YTD (Performance au 1er janvier)
        # Boursorama affiche souvent la perf YTD dans une liste de détails
        ytd = 0.0
        ytd_tags = soup.find_all("span", class_="c-list-details__value")
        for tag in ytd_tags:
            if "%" in tag.text and ("+ " in tag.text or "- " in tag.text):
                # On prend souvent la première variation de période longue trouvée qui ressemble au YTD
                if "janv." in tag.parent.text.lower() or "1er" in tag.parent.text.lower():
                    ytd = float(tag.text.replace("%", "").replace(" ", "").strip())
                    break
        
        return price, var_day, ytd
    except:
        return None, 0.0, 0.0

# --- 2. CALCULS ---
st.title("🏦 Dashboard Patrimoine - Source Boursorama")

with st.spinner('Scraping Boursorama en cours...'):
    results = []
    for a in assets:
        if a['Url'] == 'FIXED':
            p, vj, vy = a['Val'], 0.0, 1.5 # Perf estimée fonds euro
        else:
            p, vj, vy = scrape_boursorama(a['Url'])
        
        if p:
            val_totale = p * a['Qt']
            pv_euros = val_totale - (a['PRU'] * a['Qt'])
            perf_tot = (pv_euros / (a['PRU'] * a['Qt'])) * 100
            
            results.append({
                'Nom': a['Nom'], 'Env': a['Env'], 'Valeur': val_totale,
                'PV': pv_euros, 'Var. Jour': vj, 'Var. YTD': vy, 'Perf. Totale': perf_tot
            })

    df = pd.DataFrame(results)

# --- 3. AFFICHAGE ---
t_val = df['Valeur'].sum()
t_pv = df['PV'].sum()

c1, c2, c3 = st.columns(3)
c1.metric("Total", f"{t_val:,.2f} €".replace(',', ' '))
c2.metric("Plus-Value", f"{t_pv:,.2f} €".replace(',', ' '))
c3.metric("Performance", f"{(t_pv/(t_val-t_pv)*100):.2f} %")

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

st.info(f"Dernière extraction Boursorama : {datetime.now().strftime('%H:%M:%S')}")
