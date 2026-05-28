import streamlit as st
import pandas as pd
import cloudinary
import cloudinary.uploader
import cloudinary.api
from components.auth import check_login

st.set_page_config(page_title="Infraestructura - Dashboard IDS", layout="wide")

if not check_login():
    st.stop()

cloudinary.config(
    cloud_name=st.secrets["cloudinary"]["cloud_name"],
    api_key=st.secrets["cloudinary"]["api_key"],
    api_secret=st.secrets["cloudinary"]["api_secret"]
)

st.title("🔧 Splitters Problemáticos")
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
    df_infra = pd.read_csv('semana_detalle_coacalco.csv', dtype={'Cuenta': str, 'F': str, 'S': str, 'P': str})
    df_infra['Cuenta'] = df_infra['Cuenta'].str.strip().str.zfill(10)
    df = df_tickets.merge(df_infra, left_on='CUENTA', right_on='Cuenta', how='left')
    df = df[df['ESTATUS'] != 'Cancelado']
    return df

@st.cache_data(ttl=3600)
def cargar_join():
    df_tickets = pd.read_csv('ids.csv', dtype={'CUENTA': str})
    df_tickets['CUENTA'] = (
        df_tickets['CUENTA']
        .str.strip()
        .str.replace('.0', '', regex=False)
        .str.zfill(10)
    )
    df_infra = pd.read_csv('semana_detalle_coacalco.csv', dtype={'Cuenta': str, 'F': str, 'S': str, 'P': str})
    df_infra['Cuenta'] = df_infra['Cuenta'].str.strip().str.zfill(10)
    df = df_tickets.merge(df_infra, left_on='CUENTA', right_on='Cuenta', how='left')
    df = df[df['ESTATUS'] != 'Cancelado']

    df_puertos = pd.read_csv('coacalco_nce.csv')
    df_puertos['CUENTA'] = df_puertos['Alias'].str.split('_').str[0].str.strip().str.zfill(10)
    df_puertos['FSP'] = df_puertos['Frame'].astype(str) + '/' + df_puertos['Slot'].astype(str) + '/' + df_puertos['Port'].astype(str)
    df_puertos['es_FH'] = df_puertos['Terminal Type'].str.contains('FH', na=False)
    df_puertos = df_puertos.rename(columns={
        'Device Name': 'OLT_NCE',
        'Running Status': 'Estado_ONT',
        'Terminal Type': 'Modelo',
        'SN': 'Serie'
    })
    df_puertos = df_puertos[['CUENTA', 'OLT_NCE', 'FSP', 'Estado_ONT', 'Modelo', 'Serie', 'es_FH']]
    df = df.merge(df_puertos, on='CUENTA', how='left')
    return df

df = cargar_join()
df['FECHA CREACION'] = pd.to_datetime(df['FECHA CREACION'])

col1, col2, col3 = st.columns(3)
with col1:
    top_n = st.slider("Mostrar top splitters:", min_value=5, max_value=30, value=10, step=5)
with col2:
    olts = ['Todas'] + sorted(df['OLT'].dropna().unique().tolist())
    olt_sel = st.selectbox("Filtrar por OLT:", options=olts, key="olt_sel")
with col3:
    fecha_min = df['FECHA CREACION'].dt.date.min()
    fecha_max = df['FECHA CREACION'].dt.date.max()
    rango_fechas = st.date_input(
        'Rango de fechas:',
        value=(fecha_min, fecha_max),
        min_value=fecha_min,
        max_value=fecha_max,
        key='rango_fechas'
    )

df_filtrado = df if olt_sel == 'Todas' else df[df['OLT'] == olt_sel]
if len(rango_fechas) == 2:
    df_filtrado = df_filtrado[
        (df_filtrado['FECHA CREACION'].dt.date >= rango_fechas[0]) &
        (df_filtrado['FECHA CREACION'].dt.date <= rango_fechas[1])
    ]

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

df_splitters['Mapa'] = df_splitters.apply(
    lambda r: f"https://www.google.com/maps?q={r['Latitud']},{r['Longitud']}"
    if pd.notna(r['Latitud']) and pd.notna(r['Longitud']) else None,
    axis=1
)
df_splitters.insert(0, 'Ver', False)
df_splitters['Estado'] = 'Sin asignar'

with st.container(border=True):
    st.subheader(f"🚨 Top {top_n} Splitters con más tickets")
    st.caption("Marca el checkbox para ver el detalle — edita el Estado directamente en la tabla")
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
            'Latitud': None,
            'Longitud': None,
            'Mapa': st.column_config.LinkColumn('📍 Mapa', width='small'),
            'Estado': st.column_config.SelectboxColumn(
                'Estado',
                options=['Sin asignar', 'Trabajado', 'En espera de accesos', 'VM'],
                width='medium'
            ),
        },
        disabled=[c for c in df_splitters.columns if c not in ['Ver', 'Estado']],
        key="tabla_splitters"
    )

seleccionados = edited[edited['Ver'] == True]
st.markdown("---")

if seleccionados.empty:
    st.info("☝️ Marca un splitter en la tabla para ver su detalle.")
else:
    qr_sel = seleccionados.iloc[0]['Código QR']
    df_detalle = df_filtrado[df_filtrado['Código QR'] == qr_sel]

    with st.container(border=True):
        st.subheader(f"📡 Splitter: {qr_sel}")

        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.caption("Total tickets")
            st.markdown(f"**{len(df_detalle):,}**")
        with col2:
            st.caption("Cuentas únicas")
            st.markdown(f"**{df_detalle['CUENTA'].nunique():,}**")
        with col3:
            st.caption("OLT")
            st.markdown(f"**{df_detalle['OLT'].iloc[0] if not df_detalle.empty else 'N/A'}**")
        with col4:
            st.caption("FSP")
            st.markdown(f"**{df_detalle['FSP'].iloc[0] if not df_detalle.empty else 'N/A'}**")
        with col5:
            st.caption("Falla más frecuente")
            st.markdown(f"**{df_detalle['NIVEL2'].mode()[0] if not df_detalle.empty else 'N/A'}**")

        st.markdown("---")
        col_mapa, col_dias = st.columns(2)

        with col_mapa:
            st.subheader("📍 Ubicación")
            lat = df_detalle['Latitud'].iloc[0]
            lon = df_detalle['Longitud'].iloc[0]
            if pd.notna(lat) and pd.notna(lon):
                st.markdown(f"[🗺️ Ver en Google Maps](https://www.google.com/maps?q={lat},{lon})")
                df_mapa = pd.DataFrame({'lat': [lat], 'lon': [lon]})
                st.map(df_mapa, zoom=15)
            else:
                st.warning("Sin coordenadas.")

        with col_dias:
            st.subheader("📅 Días con soporte")
            df_dias_detalle = (
                df_detalle.groupby(df_detalle['FECHA CREACION'].dt.date)
                .agg(
                    Tickets=('CUENTA', 'count'),
                    Cuentas=('CUENTA', lambda x: ', '.join(x.unique())),
                    FSP=('FSP', 'first')
                )
                .reset_index()
                .rename(columns={'FECHA CREACION': 'Fecha'})
                .sort_values('Fecha', ascending=False)
            )
            st.dataframe(
                df_dias_detalle,
                use_container_width=True,
                height=300,
                column_config={
                    'Fecha': st.column_config.DateColumn('Fecha', format="DD/MM/YYYY"),
                    'Tickets': st.column_config.NumberColumn('Tickets', format="%d"),
                    'FSP': st.column_config.TextColumn('FSP'),
                    'Cuentas': st.column_config.TextColumn('Cuentas afectadas'),
                }
            )

        st.markdown("---")
        st.subheader("🔁 Reincidencia por cuenta")

        df_reincidencia = (
            df_detalle.groupby('CUENTA')
            .agg(
                Total_tickets=('NIVEL2', 'count'),
                Primer_ticket=('FECHA CREACION', 'min'),
                Ultimo_ticket=('FECHA CREACION', 'max'),
                Falla_frecuente=('NIVEL2', lambda x: x.mode()[0]),
            )
            .reset_index()
            .sort_values('Total_tickets', ascending=False)
        )
        df_reincidencia['QR'] = qr_sel
        df_reincidencia['Reincidente'] = df_reincidencia['Total_tickets'] > 1
        df_reincidencia['Dias_entre_soporte'] = (
            df_reincidencia['Ultimo_ticket'] - df_reincidencia['Primer_ticket']
        ).dt.days

        reincidentes = df_reincidencia['Reincidente'].sum()
        col1, col2 = st.columns(2)
        with col1:
            st.caption("Cuentas reincidentes")
            st.markdown(f"**{reincidentes:,}**")
        with col2:
            st.caption("% reincidencia")
            st.markdown(f"**{reincidentes/len(df_reincidencia)*100:.1f}%**")

        st.dataframe(
            df_reincidencia,
            use_container_width=True,
            height=300,
            column_config={
                'QR': st.column_config.TextColumn('QR', width='medium'),
                'CUENTA': st.column_config.TextColumn('Cuenta'),
                'Total_tickets': st.column_config.NumberColumn('Total tickets', format="%d"),
                'Primer_ticket': st.column_config.DateColumn('Primer soporte', format="DD/MM/YYYY"),
                'Ultimo_ticket': st.column_config.DateColumn('Último soporte', format="DD/MM/YYYY"),
                'Dias_entre_soporte': st.column_config.NumberColumn('Días entre soporte', format="%d"),
                'Falla_frecuente': st.column_config.TextColumn('Falla frecuente'),
                'Reincidente': st.column_config.CheckboxColumn('Reincidente'),
            }
        )

        st.markdown("---")
        st.subheader("📸 Evidencias")

        tab_antes, tab_durante, tab_despues = st.tabs(["📷 Antes", "🔧 Durante", "✅ Después"])

        for tab, etapa in zip([tab_antes, tab_durante, tab_despues], ["antes", "durante", "despues"]):
            with tab:
                folder = f"evidencias/{qr_sel}/{etapa}"

                archivo = st.file_uploader(
                    "Subir imagen",
                    type=["jpg", "jpeg", "png"],
                    key=f"upload_{qr_sel}_{etapa}"
                )
                if archivo:
                    comentario = st.text_input(
                        "Comentario para esta imagen:",
                        placeholder="Ej: Potencia medida, splitter dañado...",
                        key=f"comentario_{qr_sel}_{etapa}"
                    )
                    if st.button("⬆️ Subir", key=f"btn_upload_{qr_sel}_{etapa}"):
                        with st.spinner("Subiendo..."):
                            try:
                                cloudinary.uploader.upload(
                                    archivo,
                                    folder=folder,
                                    public_id=f"{qr_sel}_{etapa}_{archivo.name}",
                                    context=f"comentario={comentario}" if comentario else None
                                )
                                st.success("✅ Subida correctamente")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")

                try:
                    recursos = cloudinary.api.resources(
                        type="upload",
                        prefix=folder,
                        max_results=10,
                        context=True
                    )
                    imagenes = recursos.get("resources", [])
                    if imagenes:
                        cols = st.columns(3)
                        for i, img in enumerate(imagenes):
                            with cols[i % 3]:
                                st.image(img["secure_url"], use_column_width=True)
                                meta = img.get("context", {}).get("custom", {})
                                if meta.get("comentario"):
                                    st.caption(meta["comentario"])
                                if st.button("🗑️ Eliminar", key=f"del_{img['public_id']}"):
                                    cloudinary.uploader.destroy(img["public_id"])
                                    st.rerun()
                    else:
                        st.info("Sin evidencias aún.")
                except Exception:
                    st.info("Sin evidencias aún.")

if st.button("← Regresar al dashboard", key="regresar_infra"):
    st.switch_page('app.py')