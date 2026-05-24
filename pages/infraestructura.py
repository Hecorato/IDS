import streamlit as st
import pandas as pd
from components.auth import check_login

st.set_page_config(page_title="Infraestructura - Dashboard IDS", layout="wide")

if not check_login():
    st.stop()

st.title("🔧 Splitters Problemáticos")
st.markdown("---")

# ── CARGA ─────────────────────────────────────────────
@st.cache_data(ttl=3600)
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
    return df

df = cargar_join()

# ── FILTROS ───────────────────────────────────────────
col1, col2 = st.columns(2)
with col1:
    top_n = st.slider("Mostrar top splitters:", min_value=5, max_value=30, value=10, step=5)
with col2:
    olts = ['Todas'] + sorted(df['OLT'].dropna().unique().tolist())
    olt_sel = st.selectbox("Filtrar por OLT:", options=olts)

df_filtrado = df if olt_sel == 'Todas' else df[df['OLT'] == olt_sel]

# ── TABLA SPLITTERS ───────────────────────────────────
df_splitters = (
    df_filtrado.groupby('Código QR')
    .agg(
        Tickets=('CUENTA', 'count'),
        Cuentas_unicas=('CUENTA', 'nunique'),
        OLT=('OLT', 'first'),
    )
    .reset_index()
    .sort_values('Tickets', ascending=False)
    .head(top_n)
)

with st.container(border=True):
    st.subheader(f"🚨 Top {top_n} Splitters con más tickets")
    st.dataframe(
        df_splitters,
        use_container_width=True,
        height=400,
        column_config={
            'Código QR': st.column_config.TextColumn('QR', width='medium'),
            'Tickets': st.column_config.NumberColumn('Tickets', format="%d"),
            'Cuentas_unicas': st.column_config.NumberColumn('Cuentas únicas', format="%d"),
            'OLT': st.column_config.TextColumn('OLT', width='medium'),
        }
    )

st.markdown("---")

# ── DETALLE POR SPLITTER ──────────────────────────────
with st.container(border=True):
    st.subheader("🔍 Detalle por splitter")

    qrs = df_splitters['Código QR'].tolist()
    qr_sel = st.selectbox("Selecciona un QR:", options=qrs)

    df_detalle = df_filtrado[df_filtrado['Código QR'] == qr_sel]

    col1, col2, col3 = st.columns(3)
    col1.metric("Total tickets", f"{len(df_detalle):,}")
    col2.metric("Cuentas únicas", f"{df_detalle['CUENTA'].nunique():,}")
    col3.metric("OLT", df_detalle['OLT'].iloc[0] if not df_detalle.empty else "N/A")

    st.dataframe(
        df_detalle[['CUENTA', 'FECHA CREACION', 'NIVEL2', 'ESTATUS']].reset_index(drop=True),
        use_container_width=True,
        height=300
    )

if st.button("← Regresar al dashboard", key="regresar_infra"):
    st.switch_page('app.py')