import streamlit as st
import pandas as pd

st.title("Validar Puertos")

df_puertos = pd.read_csv('puertos.csv', dtype={'CUENTA': str})
df_puertos = pd.read_csv('coacalco_nce.csv', dtype={'CUENTA': str})

df_tickets['CUENTA'] = df_tickets['CUENTA'].str.strip().str.replace('.0', '', regex=False).str.zfill(10)
df_puertos['CUENTA'] = df_puertos['CUENTA'].str.strip().str.zfill(10)

st.write("Ejemplos CUENTA puertos:", df_puertos['CUENTA'].head(5).tolist())
st.write("Ejemplos CUENTA tickets:", df_tickets['CUENTA'].head(5).tolist())

df_join = df_tickets.merge(df_puertos, on='CUENTA', how='left')
total = len(df_tickets)
con_match = df_join['OLT'].notna().sum() if 'OLT' in df_join.columns else df_join['Device Name'].notna().sum()
sin_match = total - con_match

col1, col2, col3 = st.columns(3)
col1.metric("Total tickets", f"{total:,}")
col2.metric("Con match", f"{con_match:,}", f"{con_match/total*100:.1f}%")
col3.metric("Sin match", f"{sin_match:,}", f"{sin_match/total*100:.1f}%")