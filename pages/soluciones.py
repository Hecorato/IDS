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
    df_ids = pd.read_csv('ids.csv', dtype={'CUENTA': str})
    df_ids['CUENTA'] = df_ids['CUENTA'].str.strip().str.replace('.0', '', regex=False).str.zfill(10)
    df_ids = df_ids[df_ids['ESTATUS'] != 'Cancelado']
    df_ids['FECHA CREACION'] = pd.to_datetime(df_ids['FECHA CREACION'])
    df_ids['NUM_SEMANA'] = df_ids['FECHA CREACION'].dt.isocalendar().week

    df_sap = pd.read_csv('base_sap_soluciones.csv', dtype={'Cuenta de Cliente': str}, encoding='latin1')
    df_sap.columns = df_sap.columns.str.strip()
    df_sap['Cuenta de Cliente'] = df_sap['Cuenta de Cliente'].str.strip().str.zfill(10)
    df_sap['Fecha de Ingreso'] = pd.to_datetime(df_sap['Fecha de Ingreso'], dayfirst=True, errors='coerce')
    df_sap['Costo Total'] = pd.to_numeric(
        df_sap['Costo Total'].astype(str).str.replace('$', '').str.replace(',', '').str.strip(), errors='coerce'
    )

    df_sap_os = df_sap.drop_duplicates(subset='Orden de Servicio')[['Cuenta de Cliente', 'Orden de Servicio', 'Causa del Soporte', 'Tipo de Servicio']]
    df_costo = df_sap.groupby('Orden de Servicio')['Costo Total'].sum().reset_index()
    df_costo.columns = ['Orden de Servicio', 'Costo_OS']
    df_sap_os = df_sap_os.merge(df_costo, on='Orden de Servicio', how='left')

    df = df_ids.merge(df_sap_os, left_on='CUENTA', right_on='Cuenta de Cliente', how='left')

    return df, df_sap

df, df_sap = cargar_datos()

# ── FILTRO SEMANA ─────────────────────────────────────
semanas = sorted(df['NUM_SEMANA'].unique(), reverse=True)
sem_sel = st.multiselect('Semana:', options=semanas, default=[semanas[0]])

df_f = df[df['NUM_SEMANA'].isin(sem_sel)] if sem_sel else df

if df_f.empty:
    st.warning("Sin datos.")
    st.stop()

st.markdown("---")

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
        st.markdown(f"**${costo:,.2f}**")

st.markdown("---")

# ── PASO 1: SELECCIONAR CAUSA ─────────────────────────
with st.container(border=True):
    st.subheader("Paso 1 — Selecciona una causa")
    causas = sorted(df_f['NIVEL2'].dropna().unique().tolist())
    causa_sel = st.selectbox("Causa:", options=causas, key="causa_sel")

    df_causa = df_f[df_f['NIVEL2'] == causa_sel]

    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.caption("Tickets con esta causa")
            st.markdown(f"**{len(df_causa):,}**")
    with col2:
        with st.container(border=True):
            st.caption("Cuentas afectadas")
            st.markdown(f"**{df_causa['CUENTA'].nunique():,}**")

st.markdown("---")


# ── PASO 2: SOLUCIONES APLICADAS ──────────────────────
with st.container(border=True):
    st.subheader("Paso 2 — Soluciones aplicadas")

    df_soluciones = (
        df_causa.dropna(subset=['Causa del Soporte'])
        .groupby('Causa del Soporte')
        .agg(
            OS=('Orden de Servicio', 'nunique'),
            Cuentas=('CUENTA', 'nunique'),
        )
        .reset_index()
        .sort_values('OS', ascending=False)
    )

    if df_soluciones.empty:
        st.info("Sin soluciones registradas en SAP para esta causa.")
    else:
        st.dataframe(
            df_soluciones,
            use_container_width=True,
            height=250,
            column_config={
                'Causa del Soporte': st.column_config.TextColumn('Solucion aplicada'),
                'OS': st.column_config.NumberColumn('OS', format="%d"),
                'Cuentas': st.column_config.NumberColumn('Cuentas', format="%d"),
            }
        ))

    if df_soluciones.empty:
        st.info("Sin soluciones registradas en SAP para esta causa.")
    else:
        st.dataframe(
            df_soluciones,
            use_container_width=True,
            height=250,
            column_config={
                'Causa del Soporte': st.column_config.TextColumn('Solucion aplicada'),
                'OS': st.column_config.NumberColumn('OS', format="%d"),
                'Cuentas': st.column_config.NumberColumn('Cuentas', format="%d"),
                'Costo': st.column_config.NumberColumn('Costo', format="$%.2f"),
            }
        )

st.markdown("---")

# ── PASO 3: CUENTAS AFECTADAS ─────────────────────────
with st.container(border=True):
    st.subheader("Paso 3 — Cuentas afectadas")

    df_cuentas = (
        df_causa.groupby('CUENTA')
        .agg(
            Tickets=('NIVEL2', 'count'),
            Cluster=('CLUSTER INSTALACION', 'first'),
            OS=('Orden de Servicio', 'first'),
            Solucion=('Causa del Soporte', 'first'),
            Costo=('Costo_OS', 'sum')
        )
        .reset_index()
        .sort_values('Tickets', ascending=False)
    )

    df_cuentas.insert(0, 'Ver detalle', False)

    edited = st.data_editor(
        df_cuentas,
        use_container_width=True,
        height=350,
        column_config={
            'Ver detalle': st.column_config.CheckboxColumn('Ver', width='small'),
            'CUENTA': st.column_config.TextColumn('Cuenta'),
            'Tickets': st.column_config.NumberColumn('Tickets', format="%d"),
            'Cluster': st.column_config.TextColumn('Cluster'),
            'OS': st.column_config.TextColumn('OS'),
            'Solucion': st.column_config.TextColumn('Solucion'),
            'Costo': st.column_config.NumberColumn('Costo', format="$%.2f"),
        },
        disabled=[c for c in df_cuentas.columns if c != 'Ver detalle'],
        key="tabla_cuentas"
    )

    seleccionadas = edited[edited['Ver detalle'] == True]

    if not seleccionadas.empty:
        st.markdown("---")
        for _, row in seleccionadas.iterrows():
            cuenta = row['CUENTA']
            with st.expander(f"Detalle cuenta: {cuenta} — {row['Cluster']}", expanded=True):
                os_cuenta = df_sap[df_sap['Cuenta de Cliente'] == cuenta]
                if os_cuenta.empty:
                    st.info("Sin materiales registrados en SAP.")
                else:
                    for os_id in os_cuenta['Orden de Servicio'].unique():
                        df_os = os_cuenta[os_cuenta['Orden de Servicio'] == os_id]
                        causa_sap = df_os['Causa del Soporte'].iloc[0]
                        costo_os = df_os['Costo Total'].sum()
                        st.markdown(f"**OS:** {os_id} | **Solucion:** {causa_sap} | **Costo:** ${costo_os:,.2f}")
                        st.dataframe(
                            df_os[['Descripcion de Material', 'Cantidad', 'Costo Total']].reset_index(drop=True),
                            use_container_width=True,
                            height=180
                        )

if st.button("Regresar al dashboard", key="regresar_semanal"):
    st.switch_page('app.py')