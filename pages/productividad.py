import streamlit as st
import pandas as pd
import plotly.express as px
from data.loader import cargar_cierre
from components.auth import check_login

# ── Tipos de trabajo relevantes ──
TIPOS_VALIDOS = ["Cierre", "Detenciones", "Gasa", "Mantenimiento Mayor", "Poste", "Ruta"]
EMPRESAS = ["CCQ 3", "DISACONNECT", "DISARO", "RCE 3", "SOLVO COMUNICACIONES 3"]

st.set_page_config(page_title="Productividad - Dashboard IDS", layout="wide")

if not check_login():
    st.stop()

st.title("📊 Productividad de Cuadrillas")
st.markdown("---")

df_raw = cargar_cierre()
if df_raw is None or df_raw.empty:
    st.warning("No hay datos de cierre cargados. Ve a Admin para subir el archivo.")
    st.stop()

df = df_raw.copy()

# ── Limpieza ──
df.columns = df.columns.str.strip()

df["Nombre tecnico"] = (
    df["Nombre tecnico"]
    .astype(str)
    .str.replace(r"[\n\r\t]+", " ", regex=True)
    .str.strip()
)

df["Fecha termino"] = (
    df["Fecha termino"]
    .astype(str)
    .str.replace(r"[\t\n\r]+", "", regex=True)
    .str.strip()
)
df["Fecha termino"] = pd.to_datetime(df["Fecha termino"], dayfirst=True, errors="coerce")
df = df.dropna(subset=["Fecha termino"])

df["Fecha"] = df["Fecha termino"].dt.date
df["Semana"] = df["Fecha termino"].dt.to_period("W").apply(lambda r: r.start_time.date())

df = df[df["Tipo"].isin(TIPOS_VALIDOS)]
df = df[df["Empresa(proveedor)"].isin(EMPRESAS)]

if df.empty:
    st.info("No hay OTs con los tipos de trabajo configurados.")
    st.stop()

# ── Filtros ──
with st.container(border=True):
    col1, col2, col3 = st.columns(3)

    with col1:
        empresa_sel = st.selectbox("Empresa", ["Todas"] + EMPRESAS)
    with col2:
        semanas = sorted(df["Semana"].unique(), reverse=True)
        semana_sel = st.selectbox("Semana (inicio de semana)", ["Todas"] + [str(s) for s in semanas])
    with col3:
        dias = sorted(df["Fecha"].unique(), reverse=True)
        dia_sel = st.selectbox("Día", ["Todos"] + [str(d) for d in dias])

dff = df.copy()
if empresa_sel != "Todas":
    dff = dff[dff["Empresa(proveedor)"] == empresa_sel]
if semana_sel != "Todas":
    dff = dff[dff["Semana"].astype(str) == semana_sel]
if dia_sel != "Todos":
    dff = dff[dff["Fecha"].astype(str) == dia_sel]

if dff.empty:
    st.info("Sin datos para los filtros seleccionados.")
    st.stop()

# ── KPIs ──
st.markdown("### Resumen")
with st.container(border=True):
    total_ots = len(dff)
    conteos_tipo = dff["Tipo"].value_counts()

    kpi_cols = st.columns(len(TIPOS_VALIDOS) + 1)
    kpi_cols[0].metric("Total OTs", total_ots)
    for i, tipo in enumerate(TIPOS_VALIDOS):
        kpi_cols[i + 1].metric(tipo, int(conteos_tipo.get(tipo, 0)))

st.markdown("---")

# ── Tabla: Técnico × Tipo ──
st.markdown("### OTs por Técnico")

pivot = (
    dff.groupby(["Empresa(proveedor)", "Nombre tecnico", "Tipo"])
    .size()
    .unstack(fill_value=0)
)
for t in TIPOS_VALIDOS:
    if t not in pivot.columns:
        pivot[t] = 0
pivot = pivot[TIPOS_VALIDOS]
pivot["Total"] = pivot.sum(axis=1)
pivot = pivot.reset_index()
pivot = pivot.sort_values(["Empresa(proveedor)", "Total"], ascending=[True, False])

st.dataframe(pivot, use_container_width=True, hide_index=True)

st.markdown("---")

# ── Gráfica: OTs por día ──
st.markdown("### Tendencia de OTs por Día")

ots_dia = (
    dff.groupby(["Fecha", "Tipo"])
    .size()
    .reset_index(name="OTs")
)
ots_dia["Fecha"] = pd.to_datetime(ots_dia["Fecha"])

fig = px.line(
    ots_dia,
    x="Fecha",
    y="OTs",
    color="Tipo",
    markers=True,
    title="OTs cerradas por día y tipo de trabajo",
)
fig.update_layout(hovermode="x unified", legend_title="Tipo")
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ── Detalle por subtipo ──
with st.expander("📋 Ver detalle por Subtipo"):
    sub = (
        dff.groupby(["Tipo", "Subtipo"])
        .size()
        .reset_index(name="OTs")
        .sort_values(["Tipo", "OTs"], ascending=[True, False])
    )
    st.dataframe(sub, use_container_width=True, hide_index=True)