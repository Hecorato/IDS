import streamlit as st
import pandas as pd
import urllib.parse

st.set_page_config(page_title="Soporte en Campo", layout="wide")

st.title("Reincidencia de Soporte")
st.caption(f"Actualizado: {pd.Timestamp.now().strftime('%d/%m/%Y %H:%M')}")
st.markdown("---")

@st.cache_data(ttl=300)
def cargar_datos():
    df_tickets = pd.read_csv('ids.csv', dtype={'CUENTA': str})
    df_tickets['CUENTA'] = df_tickets['CUENTA'].str.strip().str.replace('.0', '', regex=False).str.zfill(10)
    df_infra = pd.read_csv('semana_detalle_coacalco.csv', dtype={'Cuenta': str})
    df_infra['Cuenta'] = df_infra['Cuenta'].str.strip().str.zfill(10)
    df = df_tickets.merge(df_infra, left_on='CUENTA', right_on='Cuenta', how='left')
    df = df[df['ESTATUS'] != 'Cancelado']
    df_puertos = pd.read_csv('coacalco_nce.csv')
    df_puertos['CUENTA'] = df_puertos['Alias'].str.split('_').str[0].str.strip().str.zfill(10)
    df_puertos['FSP'] = df_puertos['Frame'].astype(str) + '/' + df_puertos['Slot'].astype(str) + '/' + df_puertos['Port'].astype(str)
    df_puertos = df_puertos.rename(columns={'Device Name': 'OLT_NCE'})
    df_puertos = df_puertos[['CUENTA', 'OLT_NCE', 'FSP']]
    df = df.merge(df_puertos, on='CUENTA', how='left')
    df['FECHA APERTURA'] = pd.to_datetime(df['FECHA APERTURA'], dayfirst=True, errors='coerce')
    df['FECHA CREACION'] = pd.to_datetime(df['FECHA CREACION'])
    df['NUM_SEMANA'] = df['FECHA CREACION'].dt.isocalendar().week
    col_qr = [c for c in df.columns if 'QR' in c]
    if col_qr:
        df = df.rename(columns={col_qr[0]: 'QR'})
    return df

df = cargar_datos()

# ── FILTROS ───────────────────────────────────────────
semanas = sorted(df['NUM_SEMANA'].unique(), reverse=True)
fechas = sorted(df['FECHA CREACION'].dt.date.unique(), reverse=True)

col1, col2 = st.columns(2)
with col1:
    sem_sel = st.multiselect('Semana:', options=semanas, default=[semanas[0]])
with col2:
    fecha_sel = st.multiselect('Dia:', options=['Todos'] + [str(f) for f in fechas], default=['Todos'])

df_f = df[df['NUM_SEMANA'].isin(sem_sel)] if sem_sel else df

if 'Todos' not in fecha_sel and fecha_sel:
    fechas_sel = [pd.to_datetime(f).date() for f in fecha_sel]
    df_f = df_f[df_f['FECHA CREACION'].dt.date.isin(fechas_sel)]

if df_f.empty:
    st.warning("Sin tickets con los filtros seleccionados.")
    st.stop()

# ── REINCIDENCIA ──────────────────────────────────────
cuentas_periodo = df_f['CUENTA'].unique()
df_historial = df[df['CUENTA'].isin(cuentas_periodo)].copy()

df_reincidencia = (
    df_historial.groupby('CUENTA')
    .agg(
        Soportes_acumulados=('NIVEL2', 'count'),
        Primer_soporte=('FECHA APERTURA', 'min'),
        Ultimo_soporte=('FECHA APERTURA', 'max'),
        Falla_frecuente=('NIVEL2', lambda x: x.mode()[0]),
        OLT=('OLT_NCE', 'first'),
        QR=('QR', 'first'),
        Cluster=('CLUSTER INSTALACION', 'first'),
        Latitud=('Latitud', 'first'),
        Longitud=('Longitud', 'first'),
    )
    .reset_index()
    .sort_values('Soportes_acumulados', ascending=False)
)

df_reincidencia['Reincidente'] = df_reincidencia['Soportes_acumulados'] > 1
df_reincidencia['Dias_entre_soporte'] = (
    df_reincidencia['Ultimo_soporte'] - df_reincidencia['Primer_soporte']
).dt.days
df_reincidencia['Ubicacion_splitter'] = df_reincidencia.apply(
    lambda r: f"https://www.google.com/maps/place/{r['Latitud']},{r['Longitud']}"
    if pd.notna(r['Latitud']) and pd.notna(r['Longitud']) else None, axis=1
)

df_campo = df_reincidencia[df_reincidencia['Reincidente']].copy()

col1, col2 = st.columns(2)
with col1:
    with st.container(border=True):
        st.caption("Cuentas reincidentes")
        st.markdown(f"**{len(df_campo):,}**")
with col2:
    with st.container(border=True):
        st.caption("% reincidencia")
        total = len(df_reincidencia)
        st.markdown(f"**{len(df_campo)/total*100:.1f}%**")

st.markdown("---")

st.dataframe(
    df_campo.drop(columns=['Latitud', 'Longitud', 'Reincidente']),
    use_container_width=True,
    height=500,
    column_config={
        'CUENTA': st.column_config.TextColumn('Cuenta'),
        'Soportes_acumulados': st.column_config.NumberColumn('Soportes', format="%d"),
        'Primer_soporte': st.column_config.DatetimeColumn('Primer soporte', format="DD/MM/YYYY HH:mm"),
        'Ultimo_soporte': st.column_config.DatetimeColumn('Ultimo soporte', format="DD/MM/YYYY HH:mm"),
        'Dias_entre_soporte': st.column_config.NumberColumn('Dias', format="%d"),
        'Falla_frecuente': st.column_config.TextColumn('Falla'),
        'OLT': st.column_config.TextColumn('OLT'),
        'QR': st.column_config.TextColumn('QR'),
        'Cluster': st.column_config.TextColumn('Cluster'),
        'Ubicacion_splitter': st.column_config.LinkColumn('📍 Splitter'),
    }
)

st.markdown("---")

if not df_campo.empty:
    mensaje = f"*Reincidencia de soporte - {pd.Timestamp.now().strftime('%d/%m/%Y %H:%M')}*\n\n"
    for _, row in df_campo.head(10).iterrows():
        mensaje += f"📍 *{row['CUENTA']}*\n"
        mensaje += f"   Soportes: {int(row['Soportes_acumulados'])} | Falla: {row['Falla_frecuente']}\n"
        mensaje += f"   OLT: {row['OLT']} | QR: {row['QR']}\n"
        mensaje += f"   Cluster: {row['Cluster']}\n"
        if pd.notna(row.get('Latitud')) and pd.notna(row.get('Longitud')):
            mensaje += f"   📌 Splitter {row['QR']}: https://www.google.com/maps/place/{row['Latitud']},{row['Longitud']}\n"
        mensaje += "\n"
    import urllib.parse
    url_wa = f"https://wa.me/?text={urllib.parse.quote(mensaje)}"
    st.link_button("📲 Compartir por WhatsApp", url_wa)