import streamlit as st
import pandas as pd
from components.auth import check_login

st.set_page_config(page_title="Soporte Semanal", layout="wide")

if not check_login():
    st.stop()

st.title("Soporte Semanal")
st.markdown("---")

@st.cache_data(ttl=3600)
def cargar_datos():
    # IDS
    df_ids = pd.read_csv('ids.csv', dtype={'CUENTA': str})
    df_ids['CUENTA'] = df_ids['CUENTA'].str.strip().str.replace('.0', '', regex=False).str.zfill(10)
    df_ids = df_ids[df_ids['ESTATUS'] != 'Cancelado']
    df_ids['FECHA CREACION'] = pd.to_datetime(df_ids['FECHA CREACION'])
    df_ids['NUM_SEMANA'] = df_ids['FECHA CREACION'].dt.isocalendar().week

    # SAP
    df_sap = pd.read_csv('base_sap_soluciones.csv', dtype={'Cuenta de Cliente': str}, encoding='latin1')
    df_sap.columns = df_sap.columns.str.strip()
    df_sap['Cuenta de Cliente'] = df_sap['Cuenta de Cliente'].str.strip().str.zfill(10)
    df_sap['Fecha de Ingreso'] = pd.to_datetime(df_sap['Fecha de Ingreso'], dayfirst=True, errors='coerce')
    df_sap['Costo Total'] = pd.to_numeric(
        df_sap['Costo Total'].astype(str).str.replace('$', '').str.replace(',', '').str.strip(), errors='coerce'
    )

    # Costo por OS
    df_costo_os = df_sap.groupby('Orden de Servicio')['Costo Total'].sum().reset_index()
    df_costo_os.columns = ['Orden de Servicio', 'Costo_OS']

    # SAP deduplicado por OS
    df_sap_os = df_sap.drop_duplicates(subset='Orden de Servicio')
    df_sap_os = df_sap_os.merge(df_costo_os, on='Orden de Servicio', how='left')

    # JOIN IDS + SAP
    df = df_ids.merge(
        df_sap_os[['Cuenta de Cliente', 'Orden de Servicio', 'Causa del Soporte', 'Tipo de Servicio', 'Geocerca', 'Costo_OS']],
        left_on='CUENTA',
        right_on='Cuenta de Cliente',
        how='left'
    )

    return df, df_sap

df, df_sap = cargar_datos()

# ── FILTROS ───────────────────────────────────────────
semanas = sorted(df['NUM_SEMANA'].unique(), reverse=True)
sem_sel = st.multiselect('Semana:', options=semanas, default=[semanas[0]])

df_f = df[df['NUM_SEMANA'].isin(sem_sel)] if sem_sel else df

if df_f.empty:
    st.warning("Sin datos.")
    st.stop()

st.markdown("---")

# ── KPIs ──────────────────────────────────────────────
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
        st.caption("Con OS en SAP")
        st.markdown(f"**{df_f['Orden de Servicio'].notna().sum():,}**")
with col4:
    with st.container(border=True):
        st.caption("Costo total")
        costo = df_f['Costo_OS'].sum()
        st.markdown(f"**${costo:,.2f}**" if costo > 0 else "**$0.00**")

st.markdown("---")

# ── ARBOL: CAUSA → CUENTA → OS → MATERIALES ──────────
with st.container(border=True):
    st.subheader("Arbol de soporte por causa")

    causas = sorted(df_f['NIVEL2'].dropna().unique().tolist())
    causa_sel = st.selectbox("Selecciona una causa:", options=causas)

    df_causa = df_f[df_f['NIVEL2'] == causa_sel]

    col1, col2 = st.columns(2)
    with col1:
        st.caption("Tickets con esta causa")
        st.markdown(f"**{len(df_causa):,}**")
    with col2:
        st.caption("Cuentas afectadas")
        st.markdown(f"**{df_causa['CUENTA'].nunique():,}**")

    st.markdown("---")

    cuentas_causa = sorted(df_causa['CUENTA'].unique().tolist())
    cuenta_sel = st.selectbox("Selecciona una cuenta:", options=cuentas_causa, key="cuenta_arbol")

    df_cuenta = df_causa[df_causa['CUENTA'] == cuenta_sel]

    st.markdown(f"**Cuenta: {cuenta_sel}**")
    st.caption(f"Cluster: {df_cuenta['CLUSTER INSTALACION'].iloc[0] if 'CLUSTER INSTALACION' in df_cuenta.columns else 'N/A'}")

    os_list = df_cuenta['Orden de Servicio'].dropna().unique().tolist()

    if not os_list:
        st.info("Esta cuenta no tiene OS en SAP para el periodo seleccionado.")
    else:
        for os in os_list:
            with st.expander(f"OS: {os}"):
                df_os = df_sap[df_sap['Orden de Servicio'] == os]
                if not df_os.empty:
                    causa_sap = df_os['Causa del Soporte'].iloc[0]
                    tipo = df_os['Tipo de Servicio'].iloc[0]
                    costo_total = df_os['Costo Total'].sum()
                    st.markdown(f"**Causa SAP:** {causa_sap}")
                    st.markdown(f"**Tipo:** {tipo}")
                    st.markdown(f"**Costo total:** ${costo_total:,.2f}")
                    st.dataframe(
                        df_os[['Descripcion de Material', 'Cantidad', 'Costo Total']].reset_index(drop=True),
                        use_container_width=True,
                        height=200
                    )

if st.button("Regresar al dashboard", key="regresar_semanal"):
    st.switch_page('app.py')