import streamlit as st
import pandas as pd
import plotly.express as px
from components.auth import check_login

st.set_page_config(page_title="Soporte vs Resolucion", layout="wide")

if not check_login():
    st.stop()

st.title("Soporte vs Resolucion")
st.markdown("---")

@st.cache_data(ttl=300)
def cargar_datos():
    df_ids = pd.read_csv('ids.csv', dtype={'CUENTA': str})
    df_ids['CUENTA'] = df_ids['CUENTA'].str.strip().str.replace('.0', '', regex=False).str.zfill(10)
    df_ids = df_ids[df_ids['ESTATUS'] != 'Cancelado']
    df_ids['FECHA CREACION'] = pd.to_datetime(df_ids['FECHA CREACION'])
    df_ids['NUM_SEMANA'] = df_ids['FECHA CREACION'].dt.isocalendar().week
    df_ids['DIA'] = df_ids['FECHA CREACION'].dt.date

    df_cierre = pd.read_csv('reporteCierreDiario.csv', dtype={'Cuenta': str})
    df_cierre['Cuenta'] = df_cierre['Cuenta'].str.strip().str.zfill(10)
    df_cierre['Fecha termino'] = pd.to_datetime(df_cierre['Fecha termino'], errors='coerce')
    df_cierre['NUM_SEMANA'] = df_cierre['Fecha termino'].dt.isocalendar().week
    df_cierre['DIA'] = df_cierre['Fecha termino'].dt.date

    return df_ids, df_cierre

df_ids, df_cierre = cargar_datos()

semanas_ids = set(df_ids['NUM_SEMANA'].dropna().unique())
semanas_cierre = set(df_cierre['NUM_SEMANA'].dropna().unique())
semanas = sorted(semanas_ids | semanas_cierre, reverse=True)

sem_sel = st.selectbox('Semana:', options=semanas, index=0)

df_ids_sem = df_ids[df_ids['NUM_SEMANA'] == sem_sel]
df_cierre_sem = df_cierre[df_cierre['NUM_SEMANA'] == sem_sel]

st.markdown("---")

col1, col2, col3 = st.columns(3)
with col1:
    with st.container(border=True):
        st.caption("Tickets ingresados")
        st.markdown(f"**{len(df_ids_sem):,}**")
with col2:
    with st.container(border=True):
        st.caption("Cierres realizados")
        st.markdown(f"**{len(df_cierre_sem):,}**")
with col3:
    with st.container(border=True):
        st.caption("Diferencia")
        dif = len(df_cierre_sem) - len(df_ids_sem)
        st.markdown(f"**{dif:+,}**")

st.markdown("---")

with st.container(border=True):
    st.subheader("Ingreso vs Resolucion por dia")

    df_ing_dia = df_ids_sem.groupby('DIA').size().reset_index(name='Tickets')
    df_ing_dia['Tipo'] = 'Ingreso'

    df_cie_dia = df_cierre_sem.groupby('DIA').size().reset_index(name='Tickets')
    df_cie_dia['Tipo'] = 'Cierre'

    df_comp = pd.concat([df_ing_dia, df_cie_dia])

    fig = px.line(
        df_comp, x='DIA', y='Tickets', color='Tipo', markers=True, text='Tickets',
        color_discrete_map={'Ingreso': '#e63946', 'Cierre': '#1f77b4'}
    )
    fig.update_traces(line=dict(shape='spline', smoothing=1.3), marker=dict(size=8), textposition='top center')
    fig.update_layout(height=350, xaxis_title='', yaxis_title='Tickets', legend=dict(orientation='h', y=1.1))
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

with st.container(border=True):
    st.subheader("Causas y soluciones aplicadas")

    if df_cierre_sem.empty:
        st.info("Sin cierres en esta semana.")
    else:
        causas = sorted(df_cierre_sem['Causa'].dropna().unique().tolist())
        causa_sel = st.selectbox("Causa:", options=causas, key="causa_resultado")

        df_causa = df_cierre_sem[df_cierre_sem['Causa'] == causa_sel]

        col1, col2 = st.columns(2)
        with col1:
            st.caption("Cierres con esta causa")
            st.markdown(f"**{len(df_causa):,}**")
        with col2:
            st.caption("Cuentas afectadas")
            st.markdown(f"**{df_causa['Cuenta'].nunique():,}**")

        st.markdown("---")

        df_soluciones = (
            df_causa.dropna(subset=['Solucion'])
            .groupby('Solucion')
            .agg(
                Cierres=('OS', 'nunique'),
                Cuentas=('Cuenta', 'nunique'),
            )
            .reset_index()
            .sort_values('Cierres', ascending=False)
        )

        if df_soluciones.empty:
            st.info("Sin soluciones registradas para esta causa.")
        else:
            st.dataframe(
                df_soluciones,
                use_container_width=True,
                height=250,
                column_config={
                    'Solucion': st.column_config.TextColumn('Solucion aplicada'),
                    'Cierres': st.column_config.NumberColumn('Cierres', format="%d"),
                    'Cuentas': st.column_config.NumberColumn('Cuentas', format="%d"),
                }
            )

        st.markdown("---")
        st.caption("Detalle de cuentas")
        cols_det = ['Cuenta', 'OS', 'Cluster', 'Nombre tecnico', 'Fecha termino', 'Solucion', 'QR asignado']
        cols_disp = [c for c in cols_det if c in df_causa.columns]
        st.dataframe(
            df_causa[cols_disp].sort_values('Fecha termino', ascending=False).reset_index(drop=True),
            use_container_width=True,
            height=350,
            column_config={'Fecha termino': st.column_config.DatetimeColumn('Fecha termino', format="DD/MM/YYYY HH:mm")}
        )

if st.button("Regresar al dashboard", key="regresar_resultado"):
    st.switch_page('app.py')