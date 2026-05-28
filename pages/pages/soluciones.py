import streamlit as st
import pandas as pd
import plotly.express as px
from components.auth import check_login

st.set_page_config(page_title="Analisis de Soluciones", layout="wide")

if not check_login():
    st.stop()

st.title("Analisis de Causas y Soluciones")
st.markdown("---")

@st.cache_data(ttl=3600)
def cargar_sap():
    df = pd.read_csv('base_sap_soluciones.csv', dtype={'Cuenta de Cliente': str})
    df['Cuenta de Cliente'] = df['Cuenta de Cliente'].str.strip().str.zfill(10)
    df['Fecha de Ingreso'] = pd.to_datetime(df['Fecha de Ingreso'], dayfirst=True, errors='coerce')
    df['Costo Total'] = pd.to_numeric(df['Costo Total'].astype(str).str.replace('$', '').str.replace(',', '').str.strip(), errors='coerce')
    df['Costo Unitario'] = pd.to_numeric(df['Costo Unitario'].astype(str).str.replace('$', '').str.replace(',', '').str.strip(), errors='coerce')
    return df

@st.cache_data(ttl=3600)
def cargar_tickets():
    df = pd.read_csv('ids.csv', dtype={'CUENTA': str})
    df['CUENTA'] = df['CUENTA'].str.strip().str.replace('.0', '', regex=False).str.zfill(10)
    return df[['CUENTA', 'CLUSTER INSTALACION', 'NIVEL2']].drop_duplicates(subset='CUENTA')

df_sap = cargar_sap()
df_tickets = cargar_tickets()

# ── JOIN CON TICKETS ──────────────────────────────────
df = df_sap.merge(df_tickets, left_on='Cuenta de Cliente', right_on='CUENTA', how='left')

# ── DEDUPLICAR POR OS PARA CAUSAS ─────────────────────
df_os = df.drop_duplicates(subset='Orden de Servicio')

# ── SUMAR COSTO POR OS ────────────────────────────────
df_costo = df.groupby('Orden de Servicio')['Costo Total'].sum().reset_index()
df_costo.columns = ['Orden de Servicio', 'Costo_OS']
df_os = df_os.merge(df_costo, on='Orden de Servicio', how='left')

# ── FILTROS ───────────────────────────────────────────
col1, col2 = st.columns(2)
with col1:
    tipo_sel = st.multiselect(
        'Tipo de servicio:',
        options=['Todos'] + sorted(df_os['Tipo de Servicio'].dropna().unique().tolist()),
        default=['Todos']
    )
with col2:
    geocerca_sel = st.multiselect(
        'Geocerca:',
        options=['Todos'] + sorted(df_os['Geocerca'].dropna().unique().tolist()),
        default=['Todos']
    )

df_f = df_os.copy()
if 'Todos' not in tipo_sel and tipo_sel:
    df_f = df_f[df_f['Tipo de Servicio'].isin(tipo_sel)]
if 'Todos' not in geocerca_sel and geocerca_sel:
    df_f = df_f[df_f['Geocerca'].isin(geocerca_sel)]

if df_f.empty:
    st.warning("Sin datos con los filtros seleccionados.")
    st.stop()

# ── KPIs ──────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
with col1:
    with st.container(border=True):
        st.caption("Total OS")
        st.markdown(f"**{len(df_f):,}**")
with col2:
    with st.container(border=True):
        st.caption("Cuentas unicas")
        st.markdown(f"**{df_f['Cuenta de Cliente'].nunique():,}**")
with col3:
    with st.container(border=True):
        st.caption("Costo total")
        st.markdown(f"**${df_f['Costo_OS'].sum():,.2f}**")
with col4:
    with st.container(border=True):
        st.caption("Costo promedio por OS")
        st.markdown(f"**${df_f['Costo_OS'].mean():,.2f}**")

st.markdown("---")

# ── TABS ──────────────────────────────────────────────
tab_causas, tab_materiales, tab_costo, tab_detalle = st.tabs([
    "Causas", "Materiales", "Costo", "Detalle"
])

with tab_causas:
    st.subheader("Top causas de soporte")
    df_causas = (
        df_f.groupby('Causa del Soporte')
        .agg(
            OS=('Orden de Servicio', 'count'),
            Cuentas=('Cuenta de Cliente', 'nunique'),
            Costo=('Costo_OS', 'sum')
        )
        .reset_index()
        .sort_values('OS', ascending=True)
    )
    colores = {
        causa: '#e63946' if i == len(df_causas) - 1 else '#1f77b4'
        for i, causa in enumerate(df_causas['Causa del Soporte'])
    }
    fig = px.bar(
        df_causas.tail(15),
        x='OS',
        y='Causa del Soporte',
        orientation='h',
        text='OS',
        color='Causa del Soporte',
        color_discrete_map=colores
    )
    fig.update_traces(textposition='outside')
    fig.update_layout(height=500, showlegend=False, xaxis_title='Ordenes de Servicio', yaxis_title='')
    st.plotly_chart(fig, use_container_width=True)

with tab_materiales:
    st.subheader("Materiales mas usados")
    df_mat = (
        df.groupby('Descripcion de Material')
        .agg(
            Cantidad=('Cantidad', 'sum'),
            OS=('Orden de Servicio', 'nunique'),
            Costo=('Costo Total', 'sum')
        )
        .reset_index()
        .sort_values('Cantidad', ascending=False)
        .head(20)
    )
    st.dataframe(
        df_mat,
        use_container_width=True,
        height=400,
        column_config={
            'Descripcion de Material': st.column_config.TextColumn('Material'),
            'Cantidad': st.column_config.NumberColumn('Cantidad', format="%d"),
            'OS': st.column_config.NumberColumn('OS', format="%d"),
            'Costo': st.column_config.NumberColumn('Costo', format="$%.2f"),
        }
    )

with tab_costo:
    st.subheader("Costo por causa")
    df_costo_causa = (
        df_f.groupby('Causa del Soporte')
        .agg(
            OS=('Orden de Servicio', 'count'),
            Costo_total=('Costo_OS', 'sum'),
            Costo_promedio=('Costo_OS', 'mean')
        )
        .reset_index()
        .sort_values('Costo_total', ascending=False)
    )
    st.dataframe(
        df_costo_causa,
        use_container_width=True,
        height=400,
        column_config={
            'Causa del Soporte': st.column_config.TextColumn('Causa'),
            'OS': st.column_config.NumberColumn('OS', format="%d"),
            'Costo_total': st.column_config.NumberColumn('Costo total', format="$%.2f"),
            'Costo_promedio': st.column_config.NumberColumn('Costo promedio', format="$%.2f"),
        }
    )

with tab_detalle:
    cols = ['Orden de Servicio', 'Cuenta de Cliente', 'Fecha de Ingreso', 'Causa del Soporte', 'Tipo de Servicio', 'Geocerca', 'Costo_OS', 'CLUSTER INSTALACION']
    cols_disp = [c for c in cols if c in df_f.columns]
    st.dataframe(
        df_f[cols_disp].sort_values('Fecha de Ingreso', ascending=False).reset_index(drop=True),
        use_container_width=True,
        height=400
    )

if st.button("Regresar al dashboard", key="regresar_soluciones"):
    st.switch_page('app.py')