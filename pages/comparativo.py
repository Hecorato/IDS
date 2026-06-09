import pandas as pd
import plotly.express as px
import streamlit as st
import requests
from datetime import timezone, timedelta
from components.auth import check_login
from data.loader import cargar_datos

st.set_page_config(page_title="Comparativo - Dashboard IDS", layout="wide")

if not check_login():
    st.stop()

def obtener_hora_actualizacion():
    try:
        token = st.secrets["github"]["token"]
        repo = st.secrets["github"]["repo"]
        url = f"https://api.github.com/repos/{repo}/commits?path=ids.csv&per_page=1"
        headers = {"Authorization": f"token {token}"}
        r = requests.get(url, headers=headers)
        fecha_utc = r.json()[0]['commit']['committer']['date']
        cdmx = timezone(timedelta(hours=-6))
        fecha = pd.to_datetime(fecha_utc).astimezone(cdmx)
        return fecha.strftime("%H:%M")
    except:
        return "N/A"

hora_corte = obtener_hora_actualizacion()
st.title(f"Comparativo Semanal — Corte {hora_corte}")
st.markdown("---")

df = cargar_datos()
df['FECHA'] = pd.to_datetime(df['FECHA CREACION'])
df['DIA_SEMANA'] = df['FECHA'].dt.day_name()
df['NUM_SEMANA'] = df['FECHA'].dt.isocalendar().week
df['FECHA APERTURA'] = pd.to_datetime(df['FECHA APERTURA'], dayfirst=True, errors='coerce')
df['HORA'] = df['FECHA APERTURA'].dt.hour

semanas = sorted(df['NUM_SEMANA'].unique(), reverse=True)

if len(semanas) < 2:
    st.warning("Se necesitan al menos 2 semanas de datos")
    st.stop()

sem_actual = semanas[0]
sem_anterior = semanas[1]

st.subheader(f"Semana {sem_actual} vs Semana {sem_anterior}")

col1, col2 = st.columns(2)
with col1:
    with st.container(border=True):
        total_anterior = len(df[df['NUM_SEMANA'] == sem_anterior])
        st.metric(f"Semana {sem_anterior}", f"{total_anterior:,} tickets")
with col2:
    with st.container(border=True):
        total_actual = len(df[df['NUM_SEMANA'] == sem_actual])
        diferencia = total_actual - total_anterior
        st.metric(f"Semana {sem_actual}", f"{total_actual:,} tickets", delta=f"{diferencia:+,}", delta_color="inverse")

st.markdown("---")

dias_orden = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
dias_es = ['Lunes', 'Martes', 'Miercoles', 'Jueves', 'Viernes', 'Sabado', 'Domingo']

df_actual = df[df['NUM_SEMANA'] == sem_actual]
df_anterior = df[df['NUM_SEMANA'] == sem_anterior]

clusters = sorted(df['CLUSTER INSTALACION'].unique())

filas = []
for cluster in clusters:
    fila = {'Cluster': cluster}
    for dia_en, dia_es in zip(dias_orden, dias_es):
        actual = df_actual[(df_actual['CLUSTER INSTALACION'] == cluster) & (df_actual['DIA_SEMANA'] == dia_en)].shape[0]
        anterior = df_anterior[(df_anterior['CLUSTER INSTALACION'] == cluster) & (df_anterior['DIA_SEMANA'] == dia_en)].shape[0]
        fila[f'{dia_es} S{sem_anterior}'] = anterior
        fila[f'{dia_es} S{sem_actual}'] = actual
    filas.append(fila)

fila_total = {'Cluster': 'TOTAL'}
for dia_en, dia_es in zip(dias_orden, dias_es):
    fila_total[f'{dia_es} S{sem_anterior}'] = df_anterior[df_anterior['DIA_SEMANA'] == dia_en].shape[0]
    fila_total[f'{dia_es} S{sem_actual}'] = df_actual[df_actual['DIA_SEMANA'] == dia_en].shape[0]
filas.append(fila_total)

df_tabla = pd.DataFrame(filas)

with st.container(border=True):
    st.subheader("Tabla por Cluster y Dia")
    cols = [c for c in df_tabla.columns if c != 'Cluster']
    st.dataframe(
        df_tabla.set_index('Cluster'),
        use_container_width=True,
        height=400,
        column_config={col: st.column_config.NumberColumn(col, format="%d", width="small") for col in cols}
    )

st.markdown("---")

with st.container(border=True):
    st.subheader("Total de tickets por dia — Semana actual vs anterior")

    datos_grafica = []
    for dia_en, dia_es in zip(dias_orden, dias_es):
        actual = df_actual[df_actual['DIA_SEMANA'] == dia_en].shape[0]
        anterior = df_anterior[df_anterior['DIA_SEMANA'] == dia_en].shape[0]
        datos_grafica.append({'Dia': dia_es, 'Tickets': anterior, 'Semana': f'Sem {sem_anterior}'})
        datos_grafica.append({'Dia': dia_es, 'Tickets': actual, 'Semana': f'Sem {sem_actual}'})

    df_grafica = pd.DataFrame(datos_grafica)

    fig = px.line(
        df_grafica, x='Dia', y='Tickets', color='Semana',
        markers=True, text='Tickets',
        color_discrete_map={
            f'Sem {sem_anterior}': '#a8c8e8',
            f'Sem {sem_actual}': '#1f77b4'
        }
    )
    fig.update_traces(line=dict(shape='spline', smoothing=1.3), marker=dict(size=8), textposition='top center')
    fig.update_layout(height=300, xaxis_title='', yaxis_title='Total Tickets', legend=dict(orientation='h', y=1.1))
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

with st.container(border=True):
    st.subheader(f"Tickets por hora del dia — Corte {hora_corte}")

    col_dia, col_sems, col_estatus = st.columns([1, 2, 1])
    with col_dia:
        dia_seleccionado = st.selectbox('Dia:', options=dias_es, index=0, key='filtro_hora_dia')
    with col_sems:
        sems_seleccionadas = st.multiselect('Semanas a comparar:', options=semanas, default=semanas[:2])
    with col_estatus:
        estatus_grupos = st.multiselect(
            'Estatus:',
            options=['En trabajo', 'Cerrados', 'Cancelados'],
            default=['En trabajo', 'Cerrados', 'Cancelados']
        )

    dia_en_seleccionado = dias_orden[dias_es.index(dia_seleccionado)]

    if not sems_seleccionadas:
        st.warning("Selecciona al menos una semana.")
        st.stop()

    mapa_estatus = {
        'En trabajo': ['Agendado', 'Confirmado', 'Inicio'],
        'Cerrados': ['Completado'],
        'Cancelados': ['Cancelado']
    }
    estatus_sel = []
    for grupo in estatus_grupos:
        estatus_sel += mapa_estatus[grupo]

    df_hora_filtrado = df[df['ESTATUS'].isin(estatus_sel)] if estatus_sel else df

    cols_kpi = st.columns(len(sems_seleccionadas))
    for i, sem in enumerate(sems_seleccionadas):
        total = len(df_hora_filtrado[(df_hora_filtrado['NUM_SEMANA'] == sem) & (df_hora_filtrado['DIA_SEMANA'] == dia_en_seleccionado)])
        with cols_kpi[i]:
            with st.container(border=True):
                st.metric(f"Sem {sem}", f"{total:,} tickets")

    df_base = df[
        (df['DIA_SEMANA'] == dia_en_seleccionado) &
        (df['NUM_SEMANA'] == sem_actual)
    ]

    en_trabajo = df_base[df_base['ESTATUS'].isin(mapa_estatus['En trabajo'])]
    cerrados = df_base[df_base['ESTATUS'].isin(mapa_estatus['Cerrados'])]
    cancelados = df_base[df_base['ESTATUS'].isin(mapa_estatus['Cancelados'])]

    col1, col2, col3 = st.columns(3)
    with col1:
        with st.container(border=True):
            st.markdown(f"<p style='color:gray;font-size:13px;margin-bottom:4px'>En trabajo</p><p style='font-size:36px;font-weight:bold;text-align:center;margin:0'>{len(en_trabajo):,}</p>", unsafe_allow_html=True)
    with col2:
        with st.container(border=True):
            st.markdown(f"<p style='color:gray;font-size:13px;margin-bottom:4px'>Cerrados</p><p style='font-size:36px;font-weight:bold;text-align:center;margin:0'>{len(cerrados):,}</p>", unsafe_allow_html=True)
    with col3:
        with st.container(border=True):
            st.markdown(f"<p style='color:gray;font-size:13px;margin-bottom:4px'>Cancelados</p><p style='font-size:36px;font-weight:bold;text-align:center;margin:0'>{len(cancelados):,}</p>", unsafe_allow_html=True)

    df_horas = pd.concat([
        df_hora_filtrado[(df_hora_filtrado['NUM_SEMANA'] == sem) & (df_hora_filtrado['DIA_SEMANA'] == dia_en_seleccionado)]
        .groupby('HORA').size().reset_index(name='Tickets').assign(Semana=f'Sem {sem}')
        for sem in sems_seleccionadas
    ])

    fig_hora = px.line(df_horas, x='HORA', y='Tickets', color='Semana', markers=True, text='Tickets')
    fig_hora.update_traces(line=dict(shape='spline', smoothing=1.3), marker=dict(size=8), textposition='top center')
    fig_hora.update_layout(
        height=450, xaxis_title='Hora del dia', yaxis_title='Total Tickets',
        xaxis=dict(tickmode='linear', tick0=0, dtick=1),
        legend=dict(orientation='h', y=1.1)
    )
    st.plotly_chart(fig_hora, use_container_width=True)

st.markdown("---")

with st.container(border=True):
    st.subheader("Fallas por tipo (NIVEL2)")

    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    with col_f1:
        top_n = st.slider("Mostrar top:", min_value=5, max_value=30, value=10, step=5, key='slider_nivel2')
    with col_f2:
        sems_nivel2 = st.multiselect('Semana:', options=semanas, default=[sem_actual], key='sems_nivel2')
    with col_f3:
        dias_nivel2 = st.multiselect('Dia:', options=['Todos'] + dias_es, default=['Todos'], key='dias_nivel2')
    with col_f4:
        clusters_nivel2 = st.multiselect('Cluster:', options=['Todos'] + clusters, default=['Todos'], key='clusters_nivel2')

    df_n2 = df[df['NUM_SEMANA'].isin(sems_nivel2)] if sems_nivel2 else df

    if 'Todos' not in dias_nivel2 and dias_nivel2:
        dias_en_n2 = [dias_orden[dias_es.index(d)] for d in dias_nivel2]
        df_n2 = df_n2[df_n2['DIA_SEMANA'].isin(dias_en_n2)]

    if 'Todos' not in clusters_nivel2 and clusters_nivel2:
        df_n2 = df_n2[df_n2['CLUSTER INSTALACION'].isin(clusters_nivel2)]

    if df_n2.empty:
        st.warning("No hay datos con los filtros seleccionados.")
    else:
        df_nivel2 = (
            df_n2.groupby('NIVEL2')
            .size()
            .reset_index(name='Tickets')
            .sort_values('Tickets', ascending=True)
            .tail(top_n)
        )

        colores = {
            falla: '#e63946' if i == len(df_nivel2) - 1 else '#1f77b4'
            for i, falla in enumerate(df_nivel2['NIVEL2'])
        }

        fig_nivel2 = px.bar(
            df_nivel2, x='Tickets', y='NIVEL2', orientation='h',
            text='Tickets', color='NIVEL2', color_discrete_map=colores
        )
        fig_nivel2.update_traces(textposition='outside')
        fig_nivel2.update_layout(
            height=80 + top_n * 28, xaxis_title='Total Tickets', yaxis_title='',
            margin=dict(l=10, r=40, t=10, b=10), showlegend=False
        )
        st.plotly_chart(fig_nivel2, use_container_width=True)

if st.button("Regresar al dashboard", key="regresar_final"):
    st.switch_page('app.py')