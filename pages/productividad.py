import streamlit as st
import pandas as pd
import plotly.express as px
from components.auth import check_login

# ── Configuración de negocio — Planta Externa: DISARO + DISACONNECT ──
EMPRESAS_PE = ["DISARO", "DISACONNECT"]
TIPOS_VALIDOS = ["Cierre", "Detenciones", "Gasa", "Mantenimiento Mayor", "Poste", "Ruta"]

# Meta diaria de OTs por técnico. Las cuadrillas generales tienen meta de 20/día;
# las especializadas en Detenciones (splitters) tienen meta de 5/día.
METAS_DIARIAS = {
    "Antonio Chavez Guzman": 20,
    "Gerardo Arellano Chavez": 20,
    "Manuel Cortez Rubio": 20,
    "Jose Antonio Granados Cruz": 5,
    "Pedro Francisco Cruz Rodriguez": 5,
}
META_DEFAULT = 20  # para técnicos que no estén en el diccionario de arriba


def _cargar_archivo(archivo_subido) -> pd.DataFrame:
    """
    Lee el .xlsx de Cierre Diario. Los encabezados reales están en la fila 2
    de Excel (header=1) — la fila 1 y la columna A vienen vacías.
    """
    if archivo_subido.name.endswith((".xls", ".xlsx")):
        df = pd.read_excel(archivo_subido, sheet_name="Reporte Cierre Diario", header=1)
    else:
        df = pd.read_csv(archivo_subido, header=1)
    df = df.loc[:, ~df.columns.astype(str).str.contains("^Unnamed")]
    df = df.dropna(how="all")
    df.columns = df.columns.str.strip()
    return df


def _limpiar(df: pd.DataFrame) -> pd.DataFrame:
    """Limpia texto con \\n\\r\\t embebidos y arma columnas Dia/Semana."""
    df = df.copy()

    for col in ["Nombre tecnico", "Nombre despacho/AA", "Nombre supervisor"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(r"[\n\r\t]+", " ", regex=True).str.strip()

    if "Empresa(proveedor)" in df.columns:
        df["Empresa(proveedor)"] = df["Empresa(proveedor)"].astype(str).str.strip()
    if "Tipo" in df.columns:
        df["Tipo"] = df["Tipo"].astype(str).str.strip()
    if "Subtipo" in df.columns:
        df["Subtipo"] = df["Subtipo"].astype(str).str.strip()

    # Fecha termino es la más confiable para PE: Fecha trabajo viene vacía al 100%
    if "Fecha termino" in df.columns:
        df["Fecha termino"] = df["Fecha termino"].astype(str).str.replace(r"[\n\r\t]+", "", regex=True)
        df["Fecha termino"] = pd.to_datetime(df["Fecha termino"], dayfirst=True, errors="coerce")

    df = df.dropna(subset=["Fecha termino"])
    df["Dia"] = df["Fecha termino"].dt.date
    df["Semana"] = df["Fecha termino"].dt.isocalendar().week

    return df


# ── PÁGINA ────────────────────────────────────────────
st.set_page_config(page_title="Productividad PE - Dashboard IDS", layout="wide")

if not check_login():
    st.stop()

st.title("📊 Productividad PE (DISARO / DISACONNECT)")
st.markdown("---")

archivo = st.file_uploader(
    "Sube el reporte de Cierre Diario (.xlsx)",
    type=["xlsx", "xls", "csv"],
    key="productividad_pe_uploader",
)

if archivo is None:
    st.info("Sube un archivo para generar la vista.")
    st.stop()

df_raw = _cargar_archivo(archivo)
df = _limpiar(df_raw)

# Solo empresas de Planta Externa
df = df[df["Empresa(proveedor)"].isin(EMPRESAS_PE)]

# Solo tipos de trabajo relevantes para productividad
df = df[df["Tipo"].isin(TIPOS_VALIDOS)]

if df.empty:
    st.warning("No hay registros PE (DISARO/DISACONNECT) con tipos de trabajo válidos en este archivo.")
    st.stop()

st.markdown("---")

# ── Filtros ──
col1, col2, col3 = st.columns(3)

with col1:
    empresa_sel = st.selectbox("Empresa", ["Todas"] + sorted(df["Empresa(proveedor)"].unique().tolist()))
df_emp = df if empresa_sel == "Todas" else df[df["Empresa(proveedor)"] == empresa_sel]

with col2:
    semanas_disp = sorted(df_emp["Semana"].dropna().unique().tolist())
    semana_sel = st.selectbox("Semana", ["Todas"] + [f"SEM {int(s)}" for s in semanas_disp])
df_sem = df_emp if semana_sel == "Todas" else df_emp[df_emp["Semana"] == int(semana_sel.replace("SEM ", ""))]

with col3:
    dias_disp = sorted(df_sem["Dia"].dropna().unique().tolist())
    dia_sel = st.selectbox("Día", ["Todos"] + [d.strftime("%d/%m/%Y") for d in dias_disp])
df_filtrado = df_sem if dia_sel == "Todos" else df_sem[df_sem["Dia"] == pd.to_datetime(dia_sel, dayfirst=True).date()]

if df_filtrado.empty:
    st.info("No hay registros para los filtros seleccionados.")
    st.stop()

st.markdown("---")

# ── KPIs ──
st.subheader("KPIs")
kpi_cols = st.columns(len(TIPOS_VALIDOS) + 1)
kpi_cols[0].metric("Total OTs", len(df_filtrado))
for i, tipo in enumerate(TIPOS_VALIDOS, start=1):
    kpi_cols[i].metric(tipo, int((df_filtrado["Tipo"] == tipo).sum()))

st.markdown("---")

# ── Detalle por Técnico: Tipo > Subtipo por día + cumplimiento de meta ──
st.subheader("Detalle por Técnico")

dias_ordenados = sorted(df_filtrado["Dia"].unique())
columnas_dia = [d.strftime("%d-%b") for d in dias_ordenados]

for tecnico, grupo_tec in df_filtrado.groupby("Nombre tecnico"):
    total_tec = len(grupo_tec)
    meta = METAS_DIARIAS.get(tecnico, META_DEFAULT)

    with st.expander(f"{tecnico} — {total_tec} OTs (meta {meta}/día)"):
        # Tabla Tipo > Subtipo x Día
        filas = []
        for tipo, grupo_tipo in grupo_tec.groupby("Tipo"):
            fila_tipo = {"Tipo / Subtipo": f"**{tipo}**"}
            for d, col_name in zip(dias_ordenados, columnas_dia):
                fila_tipo[col_name] = int((grupo_tipo["Dia"] == d).sum())
            fila_tipo["Total"] = len(grupo_tipo)
            filas.append(fila_tipo)

            for subtipo, grupo_sub in grupo_tipo.groupby("Subtipo"):
                fila_sub = {"Tipo / Subtipo": f"　{subtipo}"}
                for d, col_name in zip(dias_ordenados, columnas_dia):
                    fila_sub[col_name] = int((grupo_sub["Dia"] == d).sum())
                fila_sub["Total"] = len(grupo_sub)
                filas.append(fila_sub)

        tabla_tec = pd.DataFrame(filas).set_index("Tipo / Subtipo")
        st.dataframe(tabla_tec, use_container_width=True)

        # Cumplimiento diario vs meta
        st.markdown(f"**Cumplimiento diario (meta: {meta} OT/día)**")
        cumplimiento = []
        for d, col_name in zip(dias_ordenados, columnas_dia):
            real = int((grupo_tec["Dia"] == d).sum())
            if real == 0:
                continue
            cumplimiento.append({
                "Día": col_name,
                "OTs": real,
                "Meta": meta,
                "Brecha": real - meta,
                "Cumplimiento %": round(real / meta * 100, 0),
            })
        st.dataframe(pd.DataFrame(cumplimiento), use_container_width=True, hide_index=True)

st.markdown("---")

# ── Gráfica: OTs por día ──
st.subheader("Tendencia de OTs por Día")

serie_dia = (
    df_filtrado.groupby("Dia")
    .size()
    .reset_index(name="OTs")
    .sort_values("Dia")
)

fig = px.line(serie_dia, x="Dia", y="OTs", markers=True, title="OTs por día (PE)")
fig.update_traces(line_shape="spline")
fig.update_layout(xaxis_title="Día", yaxis_title="Cantidad de OTs")
st.plotly_chart(fig, use_container_width=True)