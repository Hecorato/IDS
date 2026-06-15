import streamlit as st
import pandas as pd
import plotly.express as px
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

@st.cache_data(ttl=300)
def cargar_cierre():
    df_cierre = pd.read_csv('reporteCierreDiario.csv', dtype={'Cuenta': str})
    df_cierre['Cuenta'] = df_cierre['Cuenta'].str.strip().str.zfill(10)
    df_cierre['Fecha termino'] = pd.to_datetime(df_cierre['Fecha termino'], errors='coerce')
    return df_cierre

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
    url_wa = f"https://wa.me/?text={urllib.parse.quote(mensaje)}"
    st.link_button("📲 Compartir por WhatsApp", url_wa)

st.markdown("---")

with st.container(border=True):
    st.subheader("Auditoria de Conectores — Top tecnicos")
    st.caption("Tecnicos cuyo trabajo previo derivo en una reincidencia dentro de 60 dias")

    df_cierre = cargar_cierre()
    df_conectores = df_cierre[df_cierre['Solucion'].str.contains('Conector', case=False, na=False)].copy()
    df_conectores = df_conectores.dropna(subset=['Fecha termino']).sort_values(['Cuenta', 'Fecha termino'])

    if df_conectores.empty:
        st.info("Sin registros relacionados a conectores.")
    else:
        df_conectores['Dias_desde_anterior'] = (
            df_conectores.groupby('Cuenta')['Fecha termino'].diff().dt.days
        )
        df_conectores['Reincidencia_60d'] = df_conectores['Dias_desde_anterior'] <= 60

        cuentas_reincidentes = df_conectores[df_conectores['Reincidencia_60d']]['Cuenta'].unique()

        if len(cuentas_reincidentes) == 0:
            st.info("Sin reincidencias en 60 dias.")
        else:
            df_conectores['Tecnico_anterior'] = df_conectores.groupby('Cuenta')['Nombre tecnico'].shift(1)
            df_conectores['Fecha_anterior'] = df_conectores.groupby('Cuenta')['Fecha termino'].shift(1)
            df_fallas = df_conectores[df_conectores['Reincidencia_60d']].dropna(subset=['Tecnico_anterior'])

            df_top_tecnicos = (
                df_fallas.groupby('Tecnico_anterior')
                .agg(
                    Reincidencias=('OS', 'count'),
                    Cuentas=('Cuenta', 'nunique')
                )
                .reset_index()
                .sort_values('Reincidencias', ascending=True)
                .tail(10)
            )

            colores_tec = {
                t: '#e63946' if i == len(df_top_tecnicos) - 1 else '#1f77b4'
                for i, t in enumerate(df_top_tecnicos['Tecnico_anterior'])
            }

            fig_tecnicos = px.bar(
                df_top_tecnicos, x='Reincidencias', y='Tecnico_anterior', orientation='h',
                text='Reincidencias', color='Tecnico_anterior', color_discrete_map=colores_tec
            )
            fig_tecnicos.update_traces(textposition='outside')
            fig_tecnicos.update_layout(
                height=80 + 10 * 35, xaxis_title='Instalaciones que tuvieron retrabajo (60 dias)', yaxis_title='',
                showlegend=False, margin=dict(l=10, r=40, t=10, b=10)
            )

            evento_tec = st.plotly_chart(
                fig_tecnicos,
                use_container_width=True,
                on_select="rerun",
                key="chart_tecnicos"
            )

            if evento_tec and evento_tec.selection and evento_tec.selection.points:
                tecnico_sel = evento_tec.selection.points[0]['y']

                with st.container(border=True):
                    st.markdown(f"**Instalaciones de {tecnico_sel} que requirieron retrabajo (60 dias)**")

                    df_cuentas_tec = df_fallas[df_fallas['Tecnico_anterior'] == tecnico_sel].copy()

                    df_cuentas_tec = df_cuentas_tec[
                        ['Cuenta', 'Cluster', 'Fecha_anterior', 'Fecha termino', 'Nombre tecnico', 'Dias_desde_anterior']
                    ].rename(columns={'Nombre tecnico': 'Tecnico_que_regreso', 'Fecha_anterior': 'Primera_atencion'}).sort_values('Fecha termino', ascending=False)

                    st.dataframe(
                        df_cuentas_tec,
                        use_container_width=True,
                        height=250,
                        column_config={
                            'Cuenta': st.column_config.TextColumn('Cuenta'),
                            'Cluster': st.column_config.TextColumn('Cluster'),
                            'Primera_atencion': st.column_config.DatetimeColumn(f'{tecnico_sel} atendio el', format="DD/MM/YYYY HH:mm"),
                            'Fecha termino': st.column_config.DatetimeColumn('Regreso por falla el', format="DD/MM/YYYY HH:mm"),
                            'Tecnico_que_regreso': st.column_config.TextColumn('Quien regreso'),
                            'Dias_desde_anterior': st.column_config.NumberColumn('Dias entre visitas', format="%d"),
                        }
                    )

            
            st.markdown("---")

with st.container(border=True):
    st.subheader("Linea de tiempo por cuenta")
    st.caption("Cuentas ordenadas por numero de toques (atenciones de conector)")

    df_cuentas_rec = df_conectores[df_conectores['Cuenta'].isin(cuentas_reincidentes)].sort_values(['Cuenta', 'Fecha termino'])

    df_resumen_toques = (
        df_cuentas_rec.groupby('Cuenta')
        .agg(Toques=('OS', 'count'), Cluster=('Cluster', 'first'))
        .reset_index()
        .sort_values('Toques', ascending=False)
    )

    opciones_cuenta = df_resumen_toques['Cuenta'].tolist()

    cuenta_sel_tl = st.selectbox(
        "Selecciona una cuenta:",
        options=opciones_cuenta,
        format_func=lambda c: f"{c} — {df_resumen_toques[df_resumen_toques['Cuenta']==c]['Cluster'].values[0]} ({df_resumen_toques[df_resumen_toques['Cuenta']==c]['Toques'].values[0]} toques)",
        key="cuenta_timeline_sel"
    )

    df_cuenta_tl = df_cuentas_rec[df_cuentas_rec['Cuenta'] == cuenta_sel_tl].reset_index(drop=True)

    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.caption("Toques totales")
            st.markdown(f"**{len(df_cuenta_tl):,}**")
    with col2:
        with st.container(border=True):
            st.caption("Cluster")
            st.markdown(f"**{df_cuenta_tl['Cluster'].iloc[0]}**")

    st.markdown("---")

    df_vertical = df_cuenta_tl[['Fecha termino', 'Nombre tecnico', 'Empresa(proveedor)', 'Solucion', 'Dias_desde_anterior']].copy()
    df_vertical.insert(0, 'Atencion', range(1, len(df_vertical) + 1))

    st.dataframe(
        df_vertical,
        use_container_width=True,
        height=250,
        column_config={
            'Atencion': st.column_config.NumberColumn('No.', format="%d"),
            'Fecha termino': st.column_config.DatetimeColumn('Fecha', format="DD/MM/YYYY HH:mm"),
            'Nombre tecnico': st.column_config.TextColumn('Tecnico'),
            'Empresa(proveedor)': st.column_config.TextColumn('Empresa'),
            'Solucion': st.column_config.TextColumn('Solucion'),
            'Dias_desde_anterior': st.column_config.NumberColumn('Dias desde anterior', format="%d"),
        }
    )

    st.markdown("---")
    st.caption("Resumen de todas las cuentas con reincidencia (ordenado por toques)")
    st.dataframe(
        df_resumen_toques,
        use_container_width=True,
        height=300,
        column_config={
            'Cuenta': st.column_config.TextColumn('Cuenta'),
            'Toques': st.column_config.NumberColumn('Toques', format="%d"),
            'Cluster': st.column_config.TextColumn('Cluster'),
        }
    )
            