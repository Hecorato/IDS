import streamlit as st
import pandas as pd
import plotly.express as px
from data.loader import cargar_cierre

# ── Configuración de negocio ──
TIPOS_VALIDOS = ["Cierre", "Detenciones", "Gasa", "Mantenimiento Mayor", "Poste", "Ruta"]

EMPRESAS_PE = ["DISARO", "DISACONNECT"]
EMPRESAS_MANTENIMIENTO = ["RCE 3", "SOLVO COMUNICACIONES 3", "CCQ 3"]
EMPRESAS = EMPRESAS_PE + EMPRESAS_MANTENIMIENTO


def _limpiar(df: pd.DataFrame) -> pd.DataFrame:
    """Limpieza específica de esta vista sobre el df ya cargado por cargar_cierre()."""
    df = df.copy()
    df.columns = df.columns.str.strip()

    # Nombre tecnico puede traer saltos de línea/tabs internos
    if "Nombre tecnico" in df.columns:
        df["Nombre tecnico"] = (
            df["Nombre tecnico"].astype(str).str.replace(r"[\n\r\t]+", " ", regex=True).str.strip()
        )

    # Empresa(proveedor) también puede traer espacios
    if "Empresa(proveedor)" in df.columns:
        df["Empresa(proveedor)"] = df["Empresa(proveedor)"].astype(str).str.strip()

    # Tipo
    if "Tipo" in df.columns:
        df["Tipo"] = df["Tipo"].astype(str).str.strip()

    # Fecha trabajo -> datetime (puede traer tabs embebidos)
    if "Fecha trabajo" in df.columns:
        df["Fecha trabajo"] = df["Fecha trabajo"].astype(str).str.replace(r"[\n\r\t]+", "", regex=True)
        df["Fecha trabajo"] = pd.to_datetime(df["Fecha trabajo"], dayfirst=True, errors="coerce")

    df = df.dropna(subset=["Fecha trabajo"])
    df["Dia"] = df["Fecha trabajo"].dt.date
    df["Semana"] = df["Fecha trabajo"].dt.isocalendar().week

    return df


def show():
    st.title("📊 Productividad de Cuadrillas")

    df_raw = cargar_cierre()
    if df_raw is None or df_raw.empty:
        st.warning("No hay datos de cierre cargados. Ve a Admin para subir el archivo.")
        return

    df = _limpiar(df_raw)

    # Solo tipos de trabajo relevantes para productividad
    df = df[df["Tipo"].isin(TIPOS_VALIDOS)]

    if df.empty:
        st.info("No hay registros con los tipos de trabajo de productividad (Cierre, Detenciones, Gasa, Mantenimiento Mayor, Poste, Ruta).")
        return

    # ── Filtros ──
    col1, col2, col3 = st.columns(3)

    with col1:
        empresa_sel = st.selectbox("Empresa", ["Todas"] + sorted(df["Empresa(proveedor)"].dropna().unique().tolist()))

    df_emp = df if empresa_sel == "Todas" else df[df["Empresa(proveedor)"] == empresa_sel]

    with col2:
        semanas_disp = sorted(df_emp["Semana"].dropna().unique().tolist())
        semana_sel = st.selectbox("Semana", ["Todas"] + [f"SEM {int(s)}" for s in semanas_disp])

    if semana_sel != "Todas":
        sem_num = int(semana_sel.replace("SEM ", ""))
        df_sem = df_emp[df_emp["Semana"] == sem_num]
    else:
        df_sem = df_emp

    with col3:
        dias_disp = sorted(df_sem["Dia"].dropna().unique().tolist())
        dia_sel = st.selectbox("Día", ["Todos"] + [d.strftime("%d/%m/%Y") for d in dias_disp])

    if dia_sel != "Todos":
        dia_num = pd.to_datetime(dia_sel, dayfirst=True).date()
        df_filtrado = df_sem[df_sem["Dia"] == dia_num]
    else:
        df_filtrado = df_sem

    if df_filtrado.empty:
        st.info("No hay registros para los filtros seleccionados.")
        return

    st.divider()

    # ── KPIs ──
    st.subheader("KPIs")
    total_ots = len(df_filtrado)

    kpi_cols = st.columns(len(TIPOS_VALIDOS) + 1)
    kpi_cols[0].metric("Total OTs", total_ots)
    for i, tipo in enumerate(TIPOS_VALIDOS, start=1):
        cantidad = int((df_filtrado["Tipo"] == tipo).sum())
        kpi_cols[i].metric(tipo, cantidad)

    st.divider()

    # ── Tabla Técnico x Tipo ──
    st.subheader("Productividad por Técnico")

    tabla = pd.pivot_table(
        df_filtrado,
        index="Nombre tecnico",
        columns="Tipo",
        values="OT",
        aggfunc="count",
        fill_value=0,
    )

    # Asegurar todas las columnas de tipos, en orden fijo
    for tipo in TIPOS_VALIDOS:
        if tipo not in tabla.columns:
            tabla[tipo] = 0
    tabla = tabla[TIPOS_VALIDOS]
    tabla["Total"] = tabla.sum(axis=1)
    tabla = tabla.sort_values("Total", ascending=False)

    st.dataframe(tabla, use_container_width=True)

    st.divider()

    # ── Gráfica: OTs por día ──
    st.subheader("Tendencia de OTs por Día")

    serie_dia = (
        df_filtrado.groupby("Dia")
        .size()
        .reset_index(name="OTs")
        .sort_values("Dia")
    )

    fig = px.line(
        serie_dia,
        x="Dia",
        y="OTs",
        markers=True,
        title="OTs por día",
    )
    fig.update_traces(line_shape="spline")
    fig.update_layout(xaxis_title="Día", yaxis_title="Cantidad de OTs")

    st.plotly_chart(fig, use_container_width=True)