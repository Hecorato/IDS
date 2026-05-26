import streamlit as st
import pandas as pd
from components.auth import check_login

st.set_page_config(page_title="Análisis de Soporte en Tiempo Real", layout="wide")

if not check_login():
    st.stop()

st.title("⚡ Análisis de Soporte en Tiempo Real")
st.markdown("---")

@st.cache_data(ttl=300)
def cargar_join():
    df_tickets = pd.read_csv('ids.csv', dtype={'CUENTA': str})
    df_tickets['CUENTA'] = (
        df_tickets['CUENTA']
        .str.strip()
        .str.replace('.0', '', regex=False)
        .str.zfill(10)
    )
    df_infra = pd.read_csv('semana_detalle_coacalco.csv', dtype={'Cuenta': str})
    df_infra['Cuenta'] = df_infra['Cuenta'].str.strip().str.zfill(10)
    df = df_tickets.merge(df_infra, left_on='CUENTA', right_on='Cuenta', how='left')
    df = df[df['ESTATUS'] != 'Cancelado']
    df['FECHA CREACION'] = pd.to_datetime(df['FECHA CREACION'])
    df['NUM_SEMANA'] = df['FECHA CREACION'].dt.isocalendar().week
    return df

df = cargar_join()

# ── FILTROS ───────────────────────────────────────────
semanas = sorted(df['NUM_SEMANA'].unique(), reverse=True)
fechas  = sorted(df['FECHA CREACION'].dt.date.unique(), reverse=True)

col1, col2, col3 = st.columns(3)
with col1:
    sem_sel = st.multiselect(
        'Semana:',
        options=semanas,
        default=[semanas[0]],
        key='sem_sel'
    )
with col2:
    fecha_sel = st.multiselect(
        'Día:',
        options=['Todos'] + [str(f) for f in fechas],
        default=['Todos'],
        key='fecha_sel'
    )
with col3:
    cuenta_buscar = st.text_input(
        "🔍 Buscar cuenta (opcional):",
        placeholder="Ej: 0135295039"
    ).strip()

# ── APLICAR FILTROS ───────────────────────────────────
df_f = df[df['NUM_SEMANA'].isin(sem_sel)] if sem_sel else df

if 'Todos' not in fecha_sel and fecha_sel:
    fechas_sel = [pd.to_datetime(f).date() for f in fecha_sel]
    df_f = df_f[df_f['FECHA CREACION'].dt.date.isin(fechas_sel)]

if cuenta_buscar:
    cuenta_buscar = cuenta_buscar.zfill(10)
    df_f = df_f[df_f['CUENTA'] == cuenta_buscar]

st.markdown("---")

if df_f.empty:
    st.warning("Sin tickets con los filtros seleccionados.")
    st.stop()

# ── KPIs ──────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
with col1:
    with st.container(border=True):
        st.caption("Total tickets")
        st.markdown(f"**{len(df_f):,}**")
with col2:
    with st.container(border=True):
        st.caption("Cuentas únicas")
        st.markdown(f"**{df_f['CUENTA'].nunique():,}**")
with col3:
    with st.container(border=True):
        st.caption("OLTs afectadas")
        st.markdown(f"**{df_f['OLT'].nunique():,}**")
with col4:
    with st.container(border=True):
        st.caption("QRs afectados")
        st.markdown(f"**{df_f['Código QR'].nunique():,}**")

st.markdown("---")

# ── TABS DE ANÁLISIS ──────────────────────────────────
tab_olt, tab_qr, tab_fsp, tab_detalle = st.tabs([
    "🏗️ Por OLT",
    "📡 Por QR",
    "🔌 Por FSP",
    "📋 Detalle tickets"
])

with tab_olt:
    df_olt = (
        df_f.groupby('OLT')
        .agg(
            Tickets=('CU