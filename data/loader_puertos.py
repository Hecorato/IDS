import pandas as pd
import streamlit as st

@st.cache_data(ttl=3600)
def cargar_puertos():
    df = pd.read_csv('coacalco_nce.csv')
    df['CUENTA'] = df['Alias'].str.split('_').str[0].str.strip().str.zfill(10)
    df['NOMBRE'] = df['Alias'].str.split('_', n=1).str[1]
    df['FSP'] = df['Frame'].astype(str) + '/' + df['Slot'].astype(str) + '/' + df['Port'].astype(str)
    df['es_FH'] = df['Terminal Type'].str.contains('FH', na=False)
    df = df.rename(columns={
        'Device Name': 'OLT',
        'Running Status': 'Estado_ONT',
        'Vendor ID': 'Fabricante',
        'Terminal Type': 'Modelo',
        'SN': 'Serie'
    })
    df = df[['CUENTA', 'OLT', 'FSP', 'Estado_ONT', 'Modelo', 'Serie', 'Fabricante', 'es_FH', 'NOMBRE']]
    return df