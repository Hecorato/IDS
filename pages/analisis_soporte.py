import streamlit as st
import pandas as pd
from components.auth import check_login

st.set_page_config(page_title="Análisis de Soporte en Tiempo Real", layout="wide")

if not check_login():
    st.stop()

st.title("⚡ Análisis de Soporte en Tiempo Real")
st.markdown("---")

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
df['FECHA CREACION'] = pd.to_datetime(df['FECHA CREACION'])

# ── BUSCADOR ──────────────────────────────────────────
cuenta = st.text_input(
    "🔍 Ingresa el número de cuenta:",
    placeholder="Ej: 0135295039"
).strip().zfill(10)

if not cuenta or cuenta == '0000000000':
    st.info("Ingresa una cuenta para analizar.")
    st.stop()

# ── DATOS DEL CLIENTE ─────────────────────────────────
df_cliente = df[df['CUENTA'] == cuenta]

if df_cliente.empty:
    st.error(f"❌ Cuenta `{cuenta}` no encontrada en el sistema.")
    st.stop()

# Datos de infraestructura
infra = df_cliente.iloc[0]
qr = infra.get('Código QR', 'N/A')
olt = infra.get('OLT', 'N/A')
lat = infra.get('Latitud', None)
lon = infra.get('Longitud', None)
f = infra.get('F', 'N/A')
s = infra.get('S', 'N/A')
p = infra.get('P', 'N/A')
fsp = f"{f}/{s}/{p}"
cluster = infra.get('CLUSTER INSTALACION', 'N/A')

# ── UBICACIÓN ─────────────────────────────────────────
with st.container(border=True):
    st.subheader("📍 Ubicación del cliente")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.caption("Cluster")
        st.markdown(f"**{cluster}**")
    with col2:
        st.caption("OLT")
        st.markdown(f"**{olt}**")
    with col3:
        st.caption("FSP")
        st.markdown(f"**{fsp}**")
    with col4:
        st.caption("QR")
        st.markdown(f"**{qr}**")

    if pd.notna(lat) and pd.notna(lon):
        st.markdown(f"[🗺️ Ver en Google Maps](https://www.google.com/maps?q={lat},{lon})")

st.markdown("---")

# ── ANÁLISIS ZONAL ────────────────────────────────────
df_qr  = df[df['Código QR'] == qr] if qr != 'N/A' else pd.DataFrame()
df_fsp = df[(df['OLT'] == olt) & (df['F'] == infra.get('F')) & 
            (df['S'] == infra.get('S')) & (df['P'] == infra.get('P'))] if olt != 'N/A' else pd.DataFrame()
df_olt = df[df['OLT'] == olt] if olt != 'N/A' else pd.DataFrame()

col1, col2, col3, col4 = st.columns(4)
with col1:
    with st.container(border=True):
        st.caption("Tickets del cliente")
        st.markdown(f"**{len(df_cliente):,}**")
with col2:
    with st.container(border=True):
        st.caption(f"Tickets en QR {qr}")
        st.markdown(f"**{len(df_qr):,}**")
with col3:
    with st.container(border=True):
        st.caption(f"Tickets en FSP {fsp}")
        st.markdown(f"**{len(df_fsp):,}**")
with col4:
    with st.container(border=True):
        st.caption(f"Tickets en OLT")
        st.markdown(f"**{len(df_olt):,}**")

st.markdown("---")

# ── DETALLE POR NIVEL ─────────────────────────────────
tab_cliente, tab_qr, tab_fsp, tab_olt = st.tabs([
    f"👤 Cliente ({len(df_cliente)})",
    f"📡 QR ({len(df_qr)})",
    f"🔌 FSP ({len(df_fsp)})",
    f"🏗️ OLT ({len(df_olt)})"
])

cols_mostrar = ['CUENTA', 'FECHA CREACION', 'NIVEL2', 'ESTATUS', 'CLUSTER INSTALACION']

with tab_cliente:
    st.dataframe(
        df_cliente[cols_mostrar].sort_values('FECHA CREACION', ascending=False).reset_index(drop=True),
        use_container_width=True, height=300
    )

with tab_qr:
    if df_qr.empty:
        st.info("Sin datos para este QR.")
    else:
        col1, col2 = st.columns(2)
        col1.metric("Cuentas únicas", df_qr['CUENTA'].nunique())
        col2.metric("Falla más frecuente", df_qr['NIVEL2'].mode()[0])
        st.dataframe(
            df_qr[cols_mostrar].sort_values('FECHA CREACION', ascending=False).reset_index(drop=True),
            use_container_width=True, height=300
        )

with tab_fsp:
    if df_fsp.empty:
        st.info("Sin datos para este FSP.")
    else:
        col1, col2 = st.columns(2)
        col1.metric("Cuentas únicas", df_fsp['CUENTA'].nunique())
        col2.metric("QRs afectados", df_fsp['Código QR'].nunique())
        st.dataframe(
            df_fsp[cols_mostrar].sort_values('FECHA CREACION', ascending=False).reset_index(drop=True),
            use_container_width=True, height=300
        )

with tab_olt:
    if df_olt.empty:
        st.info("Sin datos para esta OLT.")
    else:
        col1, col2, col3 = st.columns(3)
        col1.metric("Cuentas únicas", df_olt['CUENTA'].nunique())
        col2.metric("QRs afectados", df_olt['Código QR'].nunique())
        col3.metric("Falla más frecuente", df_olt['NIVEL2'].mode()[0])
        st.dataframe(
            df_olt[cols_mostrar].sort_values('FECHA CREACION', ascending=False).reset_index(drop=True),
            use_container_width=True, height=300
        )

# ── MAPA ──────────────────────────────────────────────
if pd.notna(lat) and pd.notna(lon):
    st.markdown("---")
    with st.container(border=True):
        st.subheader("🗺️ Mapa de afectación en la zona")
        df_mapa = df_qr[['Latitud', 'Longitud', 'CUENTA']].dropna().drop_duplicates()
        df_mapa = df_mapa.rename(columns={'Latitud': 'lat', 'Longitud': 'lon'})
        if not df_mapa.empty:
            st.map(df_mapa, zoom=15)

if st.button("← Regresar al dashboard", key="regresar_analisis"):
    st.switch_page('app.py')