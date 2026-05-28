import pandas as pd
import streamlit as st

@st.cache_data(ttl=3600)
def cargar_puertos():
    df = pd.read_csv('puertos.csv', dtype={'CUENTA': str})
    df['CUENTA'] = df['CUENTA'].str.strip().str.zfill(10)
    df = df.rename(columns={
        'Device Name': 'OLT',
        'Running Status': 'Estado',
        'Vendor ID': 'Fabricante',
        'Terminal Type': 'Modelo'
    })
    df['es_FH'] = df['Modelo'].str.contains('FH', na=False)
    return df