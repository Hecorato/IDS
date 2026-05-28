import streamlit as st
import pandas as pd
import plotly.express as px
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
    df_puertos = pd.read_csv('coacalco_nce.csv')
    df_puertos['CUENTA'] = df_puertos['Alias'].str.split('_').str[0].str.strip().str.zfill(10)
    df_puertos['FSP'] = df_puertos['Frame'].astype(str) + '/' + df_puertos['Slot'].astype(str) + '/' + df_puertos['Port'].astype(str)
    df_puertos = df_puertos.rename(columns={'Device Name': 'OLT_NCE', 'Terminal Type': 'Modelo', 'SN': 'Serie'})
    df_puertos = df_puertos[['CUENTA', 'OLT_NCE', 'FSP', 'Modelo', 'Serie']]
    df = df.merge(df_puertos, on='CUENTA', how='left')
    df['FECHA CREACION'] = pd.to_datetime(df['FECHA CREACION'])
    df['NUM_SEMANA'] = df['FECHA CREACION'].dt.isocalendar().week
    df['FECHA APERTURA'] = pd.to_datetime(df['FECHA APERTURA'], dayfirst=True, errors='coerce')
    df['HORA'] = df['FECHA APERTURA'].dt.hour
    col_qr = [c for c in df.columns if 'QR' in c]
    if col_qr:
        df = df.rename(columns={col_qr[0]: 'QR'})
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
        st.markdown(f"**{df_f['OLT_NCE'].nunique():,}**")
with col4:
    with st.container(border=True):
        st.caption("QRs afectados")
        st.markdown(f"**{df_f['QR'].nunique():,}**")

st.markdown("---")

tab_olt, tab_qr, tab_fsp, tab_detalle = st.tabs(["OLT", "QR", "FSP", "Detalle tickets"])

with tab_olt:
    df_olt = (
        df_f.groupby('OLT_NCE')
        .agg(Tickets=('CUENTA', 'count'), Cuentas=('CUENTA', 'nunique'), QRs=('QR', 'nunique'), Falla=('NIVEL2', lambda x: x.mode()[0]))
        .reset_index().sort_values('Tickets', ascending=False)
    )
    st.dataframe(df_olt, use_container_width=True, height=400)

with tab_qr:
    df_qr = (
        df_f.groupby(['QR', 'OLT_NCE'])
        .agg(Tickets=('CUENTA', 'count'), Cuentas=('CUENTA', 'nunique'), Falla=('NIVEL2', lambda x: x.mode()[0]), Latitud=('Latitud', 'first'), Longitud=('Longitud', 'first'))
        .reset_index().sort_values('Tickets', ascending=False)
    )
    df_qr['Mapa'] = df_qr.apply(
        lambda r: f"https://www.google.com/maps?q={r['Latitud']},{r['Longitud']}"
        if pd.notna(r['Latitud']) and pd.notna(r['Longitud']) else None, axis=1
    )
    st.dataframe(df_qr, use_container_width=True, height=400,
        column_config={'Latitud': None, 'Longitud': None, 'Mapa': st.column_config.LinkColumn('Mapa')})

with tab_fsp:
    df_fsp = (
        df_f.groupby(['OLT_NCE', 'FSP'])
        .agg(Tickets=('CUENTA', 'count'), Cuentas=('CUENTA', 'nunique'), QRs=('QR', 'nunique'), Falla=('NIVEL2', lambda x: x.mode()[0]))
        .reset_index().sort_values('Tickets', ascending=False)
    )
    st.dataframe(df_fsp, use_container_width=True, height=400)

with tab_detalle:
    cols = ['CUENTA', 'FECHA CREACION', 'NIVEL2', 'ESTATUS', 'OLT_NCE', 'FSP', 'QR', 'Modelo', 'CLUSTER INSTALACION']
    cols_disp = [c for c in cols if c in df_f.columns]
    st.dataframe(df_f[cols_disp].sort_values('FECHA CREACION', ascending=False).reset_index(drop=True), use_container_width=True, height=400)

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


    st.markdown("---")

with st.container(border=True):
    st.subheader("Reincidencia por cuenta")
    st.caption("Cuentas del periodo seleccionado que ya tuvieron soporte en dias anteriores")

    # Tickets del periodo filtrado
    cuentas_periodo = df_f['CUENTA'].unique()

    # Buscar esas cuentas en TODO el historial
    df_historial = df[df['CUENTA'].isin(cuentas_periodo)].copy()

    df_reincidencia = (
        df_historial.groupby('CUENTA')
        .agg(
            Total_tickets=('NIVEL2', 'count'),
            Primer_ticket=('FECHA CREACION', 'min'),
            Ultimo_ticket=('FECHA CREACION', 'max'),
            Falla_frecuente=('NIVEL2', lambda x: x.mode()[0]),
            OLT=('OLT_NCE', 'first'),
            QR=('QR', 'first'),
            Cluster=('CLUSTER INSTALACION', 'first'),
        )
        .reset_index()
        .sort_values('Total_tickets', ascending=False)
    )

    df_reincidencia['Reincidente'] = df_reincidencia['Total_tickets'] > 1
    df_reincidencia['Dias_entre_soporte'] = (
        df_reincidencia['Ultimo_ticket'] - df_reincidencia['Primer_ticket']
    ).dt.days

    reincidentes = df_reincidencia['Reincidente'].sum()
    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.caption("Cuentas reincidentes")
            st.markdown(f"**{reincidentes:,}**")
    with col2:
        with st.container(border=True):
            st.caption("% reincidencia")
            st.markdown(f"**{reincidentes/len(df_reincidencia)*100:.1f}%**")

    st.dataframe(
        df_reincidencia,
        use_container_width=True,
        height=400,
        column_config={
            'CUENTA': st.column_config.TextColumn('Cuenta'),
            'Total_tickets': st.column_config.NumberColumn('Total tickets', format="%d"),
            'Primer_ticket': st.column_config.DateColumn('Primer soporte', format="DD/MM/YYYY"),
            'Ultimo_ticket': st.column_config.DateColumn('Ultimo soporte', format="DD/MM/YYYY"),
            'Dias_entre_soporte': st.column_config.NumberColumn('Dias entre soporte', format="%d"),
            'Falla_frecuente': st.column_config.TextColumn('Falla frecuente'),
            'OLT': st.column_config.TextColumn('OLT'),
            'QR': st.column_config.TextColumn('QR'),
            'Cluster': st.column_config.TextColumn('Cluster'),
            'Reincidente': st.column_config.CheckboxColumn('Reincidente'),
        }
    )