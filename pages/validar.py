import streamlit as st
import pandas as pd

st.title("Validación Join")

df_tickets = pd.read_csv('ids.csv', dtype={'CUENTA': str})
df_infra = pd.read_csv('semana_detalle_coacalco.csv', dtype={'Cuenta': str})

df_tickets['CUENTA'] = df_tickets['CUENTA'].str.strip().str.zfill(10)
df_infra['Cuenta'] = df_infra['Cuenta'].astype(str).str.strip().str.zfill(10)

df_join = df_tickets.merge(df_infra, left_on='CUENTA', right_on='Cuenta', how='left')

total = len(df_tickets)
con_match = df_join['OLT'].notna().sum()
sin_match = total - con_match

col1, col2, col3 = st.columns(3)
col1.metric("Total tickets", f"{total:,}")
col2.metric("Con match", f"{con_match:,}", f"{con_match/total*100:.1f}%")
col3.metric("Sin match", f"{sin_match:,}", f"{sin_match/total*100:.1f}%")

st.write("Ejemplos CUENTA tickets:", df_tickets['CUENTA'].head(5).tolist())
st.write("Ejemplos Cuenta infra:", df_infra['Cuenta'].head(5).tolist())