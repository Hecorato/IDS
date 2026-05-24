import streamlit as st
import pandas as pd
from data.loader import cargar_datos

st.title("Validación Join")

df_tickets = cargar_datos()
df_infra = pd.read_csv('semana_detalle_coacalco.csv')

df_tickets['CUENTA'] = df_tickets['CUENTA'].astype(str).str.strip().str.zfill(10)
df_infra['Cuenta'] = df_infra['Cuenta'].astype(str).str.strip().str.zfill(10)

df_join = df_tickets.merge(df_infra, left_on='CUENTA', right_on='Cuenta', how='left')

total = len(df_tickets)
con_match = df_join['OLT'].notna().sum()
sin_match = total - con_match

col1, col2, col3 = st.columns(3)
col1.metric("Total tickets", f"{total:,}")
col2.metric("Con match", f"{con_match:,}", f"{con_match/total*100:.1f}%")
col3.metric("Sin match", f"{sin_match:,}", f"{sin_match/total*100:.1f}%")