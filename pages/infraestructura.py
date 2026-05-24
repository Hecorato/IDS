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
df['FECHA CREACION'] = pd.to_datetime(df['FECHA CREACION'])
df['DIA_SEMANA'] = df['FECHA CREACION'].dt.day_name()

dias_orden = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
dias_es = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']

col1, col2, col3 = st.columns(3)
with col1:
    top_n = st.slider("Mostrar top splitters:", min_value=5, max_value=30, value=10, step=5)
with col2:
    olts = ['Todas'] + sorted(df['OLT'].dropna().unique().tolist())
    olt_sel = st.selectbox("Filtrar por OLT:", options=olts, key="olt_sel")
with col3:
    dias_sel = st.multiselect(
        'Día:',
        options=['Todos'] + dias_es,
        default=['Todos'],
        key='dias_sel'
    )

df_filtrado = df if olt_sel == 'Todas' else df[df['OLT'] == olt_sel]

if 'Todos' not in dias_sel and dias_sel:
    dias_en = [dias_orden[dias_es.index(d)] for d in dias_sel]
    df_filtrado = df_filtrado[df_filtrado['DIA_SEMANA'].isin(dias_en)]

# ── TABLA SPLITTERS ───────────────────────────────────
df_splitters = (
    df_filtrado.groupby('Código QR')
    .agg(
        Tickets=('CUENTA', 'count'),
        Cuentas_unicas=('CUENTA', 'nunique'),
        OLT=('OLT', 'first'),
        Latitud=('Latitud', 'first'),
        Longitud=('Longitud', 'first'),
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
            'Latitud': st.column_config.NumberColumn('Latitud', format="%.6f"),
            'Longitud': st.column_config.NumberColumn('Longitud', format="%.6f"),
        }
    )

st.markdown("---")

# ── DETALLE POR SPLITTER ──────────────────────────────
with st.container(border=True):
    st.subheader("🔍 Detalle por splitter")

    qrs = df_splitters['Código QR'].tolist()
    qr_sel = st.selectbox("Selecciona un QR:", options=qrs, key="qr_sel")

    df_detalle = df_filtrado[df_filtrado['Código QR'] == qr_sel]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total tickets", f"{len(df_detalle):,}")
    col2.metric("Cuentas únicas", f"{df_detalle['CUENTA'].nunique():,}")
    col3.metric("OLT", df_detalle['OLT'].iloc[0] if not df_detalle.empty else "N/A")
    col4.metric("Falla más frecuente", df_detalle['NIVEL2'].mode()[0] if not df_detalle.empty else "N/A")

    # ── MAPA ──
    if not df_detalle.empty:
        lat = df_detalle['Latitud'].iloc[0]
        lon = df_detalle['Longitud'].iloc[0]
        if pd.notna(lat) and pd.notna(lon):
            st.subheader("📍 Ubicación del splitter")
            df_mapa = pd.DataFrame({'lat': [lat], 'lon': [lon]})
            st.map(df_mapa, zoom=15)
        else:
            st.warning("Sin coordenadas para este splitter.")

    st.markdown("---")

    # ── TICKETS DEL SPLITTER ──
    st.subheader("📋 Tickets asociados"import streamlit as st
import pandas as pd
import plotly.express as px
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

dias_orden = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
dias_es = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
dias_map = dict(zip(dias_orden, dias_es))

df['FECHA CREACION'] = pd.to_datetime(df['FECHA CREACION'])
df['DIA_SEMANA'] = df['FECHA CREACION'].dt.day_name().map(dias_map)

# ── FILTROS ───────────────────────────────────────────
col1, col2, col3 = st.columns(3)
with col1:
    top_n = st.slider("Mostrar top splitters:", min_value=5, max_value=30, value=10, step=5)
with col2:
    olts = ['Todas'] + sorted(df['OLT'].dropna().unique().tolist())
    olt_sel = st.selectbox("Filtrar por OLT:", options=olts, key="olt_sel")
with col3:
    dias_sel = st.multiselect('Día:', options=['Todos'] + dias_es, default=['Todos'])

df_filtrado = df if olt_sel == 'Todas' else df[df['OLT'] == olt_sel]

if 'Todos' not in dias_sel and dias_sel:
    df_filtrado = df_filtrado[df_filtrado['DIA_SEMANA'].isin(dias_sel)]

# ── TABLA SPLITTERS ───────────────────────────────────
df_splitters = (
    df_filtrado.groupby('Código QR')
    .agg(
        Tickets=('CUENTA', 'count'),
        Cuentas_unicas=('CUENTA', 'nunique'),
        OLT=('OLT', 'first'),
        Latitud=('Latitud', 'first'),
        Longitud=('Longitud', 'first'),
    )
    .reset_index()
    .sort_values('Tickets', ascending=False)
    .head(top_n)
)

df_splitters.insert(0, 'Ver', False)

with st.container(border=True):
    st.subheader(f"🚨 Top {top_n} Splitters con más tickets")
    st.caption("Marca el checkbox para ver el detalle del splitter")

    edited = st.data_editor(
        df_splitters,
        use_container_width=True,
        height=400,
        column_config={
            'Ver': st.column_config.CheckboxColumn('👁️', width='small'),
            'Código QR': st.column_config.TextColumn('QR', width='medium'),
            'Tickets': st.column_config.NumberColumn('Tickets', format="%d"),
            'Cuentas_unicas': st.column_config.NumberColumn('Cuentas únicas', format="%d"),
            'OLT': st.column_config.TextColumn('OLT', width='medium'),
            'Latitud': st.column_config.NumberColumn('Latitud', format="%.6f"),
            'Longitud': st.column_config.NumberColumn('Longitud', format="%.6f"),
        },
        disabled=[c for c in df_splitters.columns if c != 'Ver'],
        key="tabla_splitters"
    )

seleccionados = edited[edited['Ver'] == True]

st.markdown("---")

# ── DETALLE ───────────────────────────────────────────
if seleccionados.empty:
    st.info("☝️ Marca un splitter en la tabla para ver su detalle.")
else:
    qr_sel = seleccionados.iloc[0]['Código QR']
    df_detalle = df_filtrado[df_filtrado['Código QR'] == qr_sel]

    with st.container(border=True):
        st.subheader(f"📡 Splitter: {qr_sel}")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total tickets", f"{len(df_detalle):,}")
        col2.metric("Cuentas únicas", f"{df_detalle['CUENTA'].nunique():,}")
        col3.metric("OLT", df_detalle['OLT'].iloc[0] if not df_detalle.empty else "N/A")
        col4.metric("Falla más frecuente", df_detalle['NIVEL2'].mode()[0] if not df_detalle.empty else "N/A")

        st.markdown("---")

        col_mapa, col_dias = st.columns(2)

        # ── MAPA ──
        with col_mapa:
            st.subheader("📍 Ubicación")
            lat = df_detalle['Latitud'].iloc[0]
            lon = df_detalle['Longitud'].iloc[0]
            if pd.notna(lat) and pd.notna(lon):
                df_mapa = pd.DataFrame({'lat': [lat], 'lon': [lon]})
                st.map(df_mapa, zoom=15)
            else:
                st.warning("Sin coordenadas.")

        # ── TICKETS POR DÍA ──
        with col_dias:
            st.subheader("📅 Tickets por día")
            df_dias = (
                df_detalle.groupby('DIA_SEMANA')
                .size()
                .reset_index(name='Tickets')
            )
            df_dias['orden'] = df_dias['DIA_SEMANA'].map(
                {d: i for i, d in enumerate(dias_es)}
            )
            df_dias = df_dias.sort_values('orden')

            fig_dias = px.bar(
                df_dias,
                x='DIA_SEMANA',
                y='Tickets',
                text='Tickets',
                color_discrete_sequence=['#1f77b4']
            )
            fig_dias.update_traces(textposition='outside')
            fig_dias.update_layout(
                height=300,
                xaxis_title='',
                yaxis_title='Tickets',
                margin=dict(t=10, b=10)
            )
            st.plotly_chart(fig_dias, use_container_width=True)

        st.markdown("---")

        # ── CUENTAS AFECTADAS ──
        st.subheader("👥 Cuentas afectadas")
        df_cuentas = (
            df_detalle.groupby('CUENTA')
            .agg(
                Tickets=('NIVEL2', 'count'),
                Falla_frecuente=('NIVEL2', lambda x: x.mode()[0]),
                Ultimo_ticket=('FECHA CREACION', 'max')
            )
            .reset_index()
            .sort_values('Tickets', ascending=False)
        )
        st.dataframe(df_cuentas, use_container_width=True, height=300)

if st.button("← Regresar al dashboard", key="regresar_infra"):
    st.switch_page('app.py')
    df_tabla_detalle = df_detalle[['CUENTA', 'FECHA CREACION', 'NIVEL2', 'ESTATUS']].reset_index(drop=True)
    st.dataframe(df_tabla_detalle, use_container_width=True, height=250)

    st.markdown("---")

    # ── HISTORIAL POR CUENTA ──
    st.subheader("👤 Historial por cuenta")
    cuentas = sorted(df_detalle['CUENTA'].unique().tolist())
    cuenta_sel = st.selectbox("Selecciona una cuenta:", options=cuentas, key="cuenta_sel")

    df_historial = df[df['CUENTA'] == cuenta_sel][
        ['FECHA CREACION', 'NIVEL2', 'ESTATUS', 'Código QR', 'OLT']
    ].sort_values('FECHA CREACION', ascending=False).reset_index(drop=True)

    col1, col2 = st.columns(2)
    col1.metric("Total tickets de esta cuenta", f"{len(df_historial):,}")
    col2.metric("Splitters distintos", f"{df_historial['Código QR'].nunique():,}")

    st.dataframe(df_historial, use_container_width=True, height=250)

if st.button("← Regresar al dashboard", key="regresar_infra"):
    st.switch_page('app.py')