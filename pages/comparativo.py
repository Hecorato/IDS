import pandas as pd
import plotly.express as px
import streamlit as st
from datetime import datetime
from components.auth import check_login
from data.loader import cargar_datos

st.set_page_config(page_title="Comparativo - Dashboard IDS", layout="wide")

if not check_login():
    st.stop()

hora_actual = datetime.now().strftime("%H:%M")
st.title(f"📊 Comparativo Semanal — Corte {hora_actual}")
st.markdown("---")

df = cargar_datos()
df['FECHA'] = pd.to_datetime(df['FECHA CREACION'])
df['DIA_SEMANA'] = df['FECHA'].dt.day_name()
df['NUM_SEMANA'] = df['FECHA'].dt.isocalendar().week
df['ANO'] = df['FECHA'].dt.isocalendar().year

semanas = sorted(df['NUM_SEMANA'].unique(), reverse=True)

if len(semanas) < 2:
    st.warning("Se necesitan al menos 2 semanas de datos")
    st.stop()

sem_actual = semanas[0]
sem_anterior = semanas[1]

st.subheader(f"Semana {sem_actual} vs Semana {sem_anterior}")

dias_orden = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
dias_es = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']

df_actual = df[df['NUM_SEMANA'] == sem_actual]
df_anterior = df[df['NUM_SEMANA'] == sem_anterior]

clusters = sorted(df['CLUSTER INSTALACION'].unique())

# Construir tabla comparativa
filas = []
for cluster in clusters:
    fila = {'Cluster': cluster}
    for dia_en, dia_es in zip(dias_orden, dias_es):
        actual = df_actual[(df_actual['CLUSTER INSTALACION'] == cluster) &
                           (df_actual['DIA_SEMANA'] == dia_en)].shape[0]
        anterior = df_anterior[(df_anterior['CLUSTER INSTALACION'] == cluster) &
                               (df_anterior['DIA_SEMANA'] == dia_en)].shape[0]
        fila[f'{dia_es} S{sem_anterior}'] = anterior
        fila[f'{dia_es} S{sem_actual}'] = actual
    filas.append(fila)

# Fila de totales
fila_total = {'Cluster': '📊 TOTAL'}
for dia_en, dia_es in zip(dias_orden, dias_es):
    actual = df_actual[df_actual['DIA_SEMANA'] == dia_en].shape[0]
    anterior = df_anterior[df_anterior['DIA_SEMANA'] == dia_en].shape[0]
    fila_total[f'{dia_es} S{sem_anterior}'] = anterior
    fila_total[f'{dia_es} S{sem_actual}'] = actual
filas.append(fila_total)

df_tabla = pd.DataFrame(filas)

# ── TABLA ─────────────────────────────────────────────
with st.container(border=True):
    st.subheader("📋 Tabla por Cluster y Día")
    st.dataframe(df_tabla.set_index('Cluster'), use_container_width=True, height=600)

st.markdown("---")

# ── GRÁFICA COMPARATIVA ───────────────────────────────
with st.container(border=True):
    st.subheader("📈 Total de tickets por día — Semana actual vs anterior")

    datos_grafica = []
    for dia_en, dia_es in zip(dias_orden, dias_es):
        actual = df_actual[df_actual['DIA_SEMANA'] == dia_en].shape[0]
        anterior = df_anterior[df_anterior['DIA_SEMANA'] == dia_en].shape[0]
        datos_grafica.append({'Día': dia_es, 'Tickets': anterior, 'Semana': f'Sem {sem_anterior}'})
        datos_grafica.append({'Día': dia_es, 'Tickets': actual, 'Semana': f'Sem {sem_actual}'})

    df_grafica = pd.DataFrame(datos_grafica)

    fig = px.bar(
        df_grafica,
        x='Día',
        y='Tickets',
        color='Semana',
        barmode='group',
        text='Tickets',
        color_discrete_map={
            f'Sem {sem_anterior}': '#a8c8e8',
            f'Sem {sem_actual}': '#1f77b4'
        }
    )
    fig.update_traces(textposition='outside')
    fig.update_layout(height=400, xaxis_title='', yaxis_title='Total Tickets')
    st.plotly_chart(fig, use_container_width=True)

if st.button("← Regresar al dashboard"):
    st.switch_page('app.py')