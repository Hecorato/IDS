import streamlit as st
import pandas as pd
from components.auth import check_login

st.set_page_config(page_title="Analisis de Soporte en Tiempo Real", layout="wide")

if not check_login():
    st.stop()

st.title("Analisis de Soporte en Tiempo Real")
st.markdown("---")

@st.cache_data(ttl=300)
def cargar_join():
    df_tickets = pd.read_csv('ids.csv', dtype={'CUENTA': str})
    df_tickets['CUENTA'] = df_tickets['CUENTA'].str.strip().str.replace('.0', '', regex=False).str.zfill(10)
    df_infra = pd.read_csv('semana_detalle_coacalco.csv', dtype={'Cuenta': str})
    df_infra['Cuenta'] = df_infra['Cuenta'].str.strip().str.zfill(10)
    df = df_tickets.merge(df_infra, left_on='CUENTA', right_on='Cuenta', how='left')
    df = df[df['ESTATUS'] != 'Cancelado']
    df['FECHA CREACION'] = pd.to_datetime(df['FECHA CREACION'])
    df['NUM_SEMANA'] = df['FECHA CREACION'].dt.isocalendar().week
    df['FSP'] = df['F'].astype(str) + '/' + df['S'].astype(str) + '/' + df['P'].astype(str)
    return df

df = cargar_join()

semanas = sorted(df['NUM_SEMANA'].unique(), reverse=True)
fechas = sorted(df['FECHA CREACION'].dt.date.unique(), reverse=True)

col1, col2, col3 = st.columns(3)
with col1:
    sem_sel = st.multiselect('Semana:', options=semanas, default=[semanas[0]])
with col2:
    fecha_sel = st.multiselect('Dia:', options=['Todos'] + [str(f) for f in fechas], default=['Todos'])
with col3:
    cuenta_buscar = st.text_input("Buscar cuenta (opcional):", placeholder="Ej: 0135295039").strip()

df_f = df[df['NUM_SEMANA'].isin(sem_sel)] if sem_sel else df

if 'Todos' not in fecha_sel and fecha_sel:
    fechas_sel = [pd.to_datetime(f).date() for f in fecha_sel]
    df_f = df_f[df_f['FECHA CREACION'].dt.date.isin(fechas_sel)]

if cuenta_buscar:
    df_f = df_f[df_f['CUENTA'] == cuenta_buscar.zfill(10)]

st.markdown("---")

if df_f.empty:
    st.warning("Sin tickets con los filtros seleccionados.")
    st.stop()

col1, col2, col3, col4 = st.columns(4)
with col1:
    with st.container(border=True):
        st.caption("Total tickets")
        st.markdown(f"**{len(df_f):,}**")
with col2:
    with st.container(border=True):
        st.caption("Cuentas unicas")
        st.markdown(f"**{df_f['CUENTA'].nunique():,}**")
with col3:
    with st.container(border=True):
        st.caption("OLTs afectadas")
        st.markdown(f"**{df_f['OLT'].nunique():,}**")
with col4:
    with st.container(border=True):
        st.caption("QRs afectados")
        st.markdown(f"**{df_f['Codigo QR'].nunique():,}**")

st.markdown("---")

tab_olt, tab_qr, tab_fsp, tab_detalle = st.tabs(["OLT", "QR", "FSP", "Detalle tickets"])

with tab_olt:
    df_olt = (
        df_f.groupby('OLT')
        .agg(
            Tickets=('CUENTA', 'count'),
            Cuentas=('CUENTA', 'nunique'),
            QRs=('Codigo QR', 'nunique'),
            Falla=('NIVEL2', lambda x: x.mode()[0])
        )
        .reset_index()
        .sort_values('Tickets', ascending=False)
    )
    st.dataframe(df_olt, use_container_width=True, height=400)

with tab_qr:
    df_qr = (
        df_f.groupby(['Codigo QR', 'OLT'])
        .agg(
            Tickets=('CUENTA', 'count'),
            Cuentas=('CUENTA', 'nunique'),
            Falla=('NIVEL2', lambda x: x.mode()[0]),
            Latitud=('Latitud', 'first'),
            Longitud=('Longitud', 'first'),
        )
        .reset_index()
        .sort_values('Tickets', ascending=False)
    )
    df_qr['Mapa'] = df_qr.apply(
        lambda r: f"https://www.google.com/maps?q={r['Latitud']},{r['Longitud']}"
        if pd.notna(r['Latitud']) and pd.notna(r['Longitud']) else None,
        axis=1
    )
    st.dataframe(
        df_qr,
        use_container_width=True,
        height=400,
        column_config={
            'Latitud': None,
            'Longitud': None,
            'Mapa': st.column_config.LinkColumn('Mapa'),
        }
    )

with tab_fsp:
    df_fsp = (
        df_f.groupby(['OLT', 'FSP'])
        .agg(
            Tickets=('CUENTA', 'count'),
            Cuentas=('CUENTA', 'nunique'),
            QRs=('Codigo QR', 'nunique'),
            Falla=('NIVEL2', lambda x: x.mode()[0])
        )
        .reset_index()
        .sort_values('Tickets', ascending=False)
    )
    st.dataframe(df_fsp, use_container_width=True, height=400)

with tab_detalle:
    cols = ['CUENTA', 'FECHA CREACION', 'NIVEL2', 'ESTATUS', 'OLT', 'Codigo QR', 'CLUSTER INSTALACION']
    st.dataframe(
        df_f[cols].sort_values('FECHA CREACION', ascending=False).reset_index(drop=True),
        use_container_width=True,
        height=400
    )

st.markdown("---")
with st.container(border=True):
    st.subheader("Mapa de afectacion")
    df_mapa = df_f[['Latitud', 'Longitud']].dropna().drop_duplicates()
    df_mapa = df_mapa.rename(columns={'Latitud': 'lat', 'Longitud': 'lon'})
    if not df_mapa.empty:
        st.map(df_mapa, zoom=11)
    else:
        st.info("Sin coordenadas disponibles.")

if st.button("Regresar al dashboard", key="regresar_analisis"):
    st.switch_page('app.py')