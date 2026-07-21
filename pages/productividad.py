import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import io
from components.auth import check_login

# ── Configuración de negocio — Planta Externa: DISARO + DISACONNECT ──
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


def _leer_de_github(nombre_archivo, dtype=None):
    """Trae el csv más reciente directo de GitHub (mismo patrón que admin.py)."""
    repo = st.secrets["github"]["repo"]
    token = st.secrets["github"]["token"]
    url = f"https://raw.githubusercontent.com/{repo}/main/{nombre_archivo}"
    headers = {"Authorization": f"token {token}"}

    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        return None

    try:
        return pd.read_csv(io.StringIO(r.text), dtype=dtype)
    except Exception:
        return None


def _limpiar(df: pd.DataFrame) -> pd.DataFrame:
    """Arma columnas Dia/Semana a partir de Fecha termino ya limpia (viene de admin.py)."""
    df = df.copy()

    if "Nombre tecnico" in df.columns:
        df["Nombre tecnico"] = df["Nombre tecnico"].astype(str).str.strip()
    if "Tipo" in df.columns:
        df["Tipo"] = df["Tipo"].astype(str).str.strip()
    if "Subtipo" in df.columns:
        df["Subtipo"] = df["Subtipo"].astype(str).str.strip()

    df["Fecha termino"] = pd.to_datetime(df["Fecha termino"], errors="coerce")
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

df_raw = _leer_de_github("cierrePE.csv", dtype={"Cuenta": str})

if df_raw is None or df_raw.empty:
    st.info("Todavía no hay datos de Cierre Diario PE cargados. Ve a Admin para subir el archivo.")
    st.stop()

df = _limpiar(df_raw)

# Solo tipos de trabajo relevantes para productividad
df = df[df["Tipo"].isin(TIPOS_VALIDOS)]

if df.empty:
    st.warning("No hay registros PE con tipos de trabajo válidos.")
    st.stop()

# ── Filtros ──
col1, col2, col3 = st.columns(3)

with col1:
    empresa_sel = st.selectbox("Empresa", ["Todas"] + sorted(df["Empresa(proveedor)"].dropna().unique().tolist()))
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