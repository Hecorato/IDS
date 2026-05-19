import pandas as pd
import plotly.express as px
import streamlit as st
from components.auth import check_login
from data.loader import cargar_datos
from data.merger import cargar_soluciones, hacer_merge

st.set_page_config(page_title="Detalle - Dashboard IDS", layout="wide")

if not check_login():
    st.stop()

# Recuperar fecha del click
if 'fecha_detalle' not in st.session_state:
    st.warning("Selecciona un día desde el dashboard principal")
    st.stop()

fecha = pd.to_datetime(st.session_state['fecha_detalle']).date()

st.title(f"📅 Detalle del {fecha}")
st.markdown("---")

# Cargar y mergear datos
df_tickets = cargar_datos()
df_soluciones = cargar_soluciones()
df = hacer_merge(df_tickets, df_soluciones)

# Filtrar por fecha
df_dia = df[df['FECHA CREACION'] == fecha]
st.write("Tickets OS ejemplo:", df_tickets['OS'].head(3).tolist())
st.write("Soluciones OS ejemplo:", df_soluciones['OS'].head(3).tolist())
st.write("Registros después del merge con datos:", df_dia[df_dia['Causa'].notna()].shape[0])

# KPIs
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total tickets", len(df_dia))
with col2:
    st.metric("Clusters afectados", df_dia['CLUSTER INSTALACION'].nunique())
with col3:
    completados = df_dia[df_dia['COMPLETADO'] == True].shape[0] if 'COMPLETADO' in df_dia.columns else 0
    st.metric("Completados", completados)

st.markdown("---")

# Módulo 1 — Tickets por Cluster
with st.container(border=True):
    st.subheader("🏘️ Tickets por Cluster")
    df_cluster = df_dia.groupby('CLUSTER INSTALACION').size().reset_index(name='TOTAL')
    df_cluster = df_cluster.sort_values('TOTAL', ascending=False)
    fig1 = px.bar(df_cluster, x='TOTAL', y='CLUSTER INSTALACION',
                  orientation='h', color='CLUSTER INSTALACION', text='TOTAL')
    fig1.update_layout(showlegend=False, height=400)
    fig1.update_traces(showlegend=False, textposition='outside')
    st.plotly_chart(fig1, use_container_width=True)

# Módulo 2 — Causas y Soluciones lado a lado
col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        st.subheader("⚠️ Causas")
        if 'Causa' in df_dia.columns:
            df_causas = df_dia.groupby('Causa').size().reset_index(name='TOTAL')
            df_causas = df_causas.sort_values('TOTAL', ascending=False).head(10)
            fig2 = px.bar(df_causas, x='TOTAL', y='Causa',
                          orientation='h', color='Causa', text='TOTAL')
            fig2.update_layout(showlegend=False, height=400)
            fig2.update_traces(showlegend=False, textposition='outside')
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Sin datos de causas para este día")

with col2:
    with st.container(border=True):
        st.subheader("🔧 Soluciones")
        if 'Solucion' in df_dia.columns:
            df_sol = df_dia.groupby('Solucion').size().reset_index(name='TOTAL')
            df_sol = df_sol.sort_values('TOTAL', ascending=False).head(10)
            fig3 = px.bar(df_sol, x='TOTAL', y='Solucion',
                          orientation='h', color='Solucion', text='TOTAL')
            fig3.update_layout(showlegend=False, height=400)
            fig3.update_traces(showlegend=False, textposition='outside')
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info("Sin datos de soluciones para este día")

st.markdown("---")

# Botón regresar
if st.button("← Regresar al dashboard"):
    st.switch_page('app.py')