import pandas as pd
import streamlit as st

@st.cache_data(ttl=3600)
def cargar_infra():
    df = pd.read_csv('semana_detalle_coacalco.csv')
    
    # Identificador único de puerto
    df['ID_PUERTO'] = (
        df['OLT'].astype(str) + ' ' +
        df['F'].astype(str) + '/' +
        df['S'].astype(str) + '/' +
        df['P'].astype(str)
    )
    
    # Limpiar cuenta
    df['Cuenta'] = df['Cuenta'].astype(str).str.strip()
    
    return df