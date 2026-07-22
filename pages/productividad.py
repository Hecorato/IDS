import streamlit as st
import pandas as pd
import requests
import base64
import io
import datetime
from components.auth import check_login

# ── Configuración de negocio — Planta Externa: DISARO + DISACONNECT ──
TIPOS_VALIDOS = ["Cierre", "Detenciones", "Gasa", "Mantenimiento Mayor", "Poste", "Ruta"]
DIAS_SEMANA = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

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

OT_OPD_ARCHIVO = "otOpdManual.csv"  # técnico + día + cantidad de OT OPD (cargado a mano)


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


def _subir_a_github(df, nombre_archivo, mensaje):
    """Sube/actualiza un csv en GitHub (mismo patrón que admin.py)."""
    token = st.secrets["github"]["token"]
    repo = st.secrets["github"]["repo"]
    url = f"https://api.github.com/repos/{repo}/contents/{nombre_archivo}"
    headers = {"Authorization": f"token {token}"}

    r = requests.get(url, headers=headers)
    sha = r.json().get("sha", None)

    contenido = df.to_csv(index=False).encode()
    contenido_b64 = base64.b64encode(contenido).decode()

    payload = {"message": mensaje, "content": contenido_b64, "sha": sha}
    r = requests.put(url, headers=headers, json=payload)
    return r.status_code in [200, 201]


def _limpiar_cierre(df: pd.DataFrame) -> pd.DataFrame:
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
    df["Anio"] = df["Fecha termino"].dt.isocalendar().year
    df["Semana"] = df["Fecha termino"].dt.isocalendar().week
    return df


def _limpiar_seguimiento(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "Nombre tecnico" in df.columns:
        df["Nombre tecnico"] = df["Nombre tecnico"].astype(str).str.strip()

    df["Fecha termino"] = pd.to_datetime(df["Fecha termino"], errors="coerce")
    df = df.dropna(subset=["Fecha termino"])
    df["Dia"] = df["Fecha termino"].dt.date
    df["Anio"] = df["Fecha termino"].dt.isocalendar().year
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

df = _limpiar_cierre(df_raw)
df = df[df["Tipo"].isin(TIPOS_VALIDOS)]

df_seg_raw = _leer_de_github("seguimientoPE.csv", dtype={"Cuenta": str})
df_seg = _limpiar_seguimiento(df_seg_raw) if df_seg_raw is not None and not df_seg_raw.empty else pd.DataFrame(
    columns=["Nombre tecnico", "Dia", "Anio", "Semana"]
)

df_opd = _leer_de_github(OT_OPD_ARCHIVO)
if df_opd is None or df_opd.empty:
    df_opd = pd.DataFrame(columns=["Nombre tecnico", "Dia", "OT_OPD"])
else:
    df_opd["Dia"] = pd.to_datetime(df_opd["Dia"]).dt.date
opd_dict = {(t, d): c for t, d, c in zip(df_opd["Nombre tecnico"], df_opd["Dia"], df_opd["OT_OPD"])}

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
    opciones_semana = [f"SEM {int(s)}" for s in semanas_disp]
    semana_sel = st.selectbox("Semana", opciones_semana, index=len(opciones_semana) - 1 if opciones_semana else 0)
sem_num = int(semana_sel.replace("SEM ", "")) if semana_sel else None
df_sem = df_emp[df_emp["Semana"] == sem_num] if sem_num else df_emp

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
            fila_tipo = {"Tipo / Subtipo": tipo.upper()}
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

# ── Tabla semanal: Cuadrilla x Día x (OT Preventivo / Folio Masivo / OT OPD) ──
st.subheader(f"Tabla Semanal — {semana_sel}")
st.caption(
    "OT Preventivo = OTs del Cierre Diario. Folio Masivo = tickets del Seguimiento Diario (Corte Masivo). "
    "OT OPD se captura a mano abajo — todavía no viene de ningún archivo."
)

anio_ref = int(df_sem["Anio"].mode()[0]) if not df_sem.empty else datetime.date.today().year
lunes = datetime.date.fromisocalendar(anio_ref, sem_num, 1) if sem_num else None
dias_semana_completa = [lunes + datetime.timedelta(days=i) for i in range(7)] if lunes else []

tecnicos_semana = sorted(df_sem["Nombre tecnico"].dropna().unique().tolist())

filas_semana = []
for tecnico in tecnicos_semana:
    grupo_prev = df_sem[df_sem["Nombre tecnico"] == tecnico]
    grupo_folio = df_seg[
        (df_seg["Nombre tecnico"] == tecnico) & (df_seg.get("Semana") == sem_num)
    ] if not df_seg.empty else pd.DataFrame(columns=["Dia"])

    fila = {"Cuadrilla": tecnico}
    total_sem = 0
    for d, etiqueta in zip(dias_semana_completa, DIAS_SEMANA):
        prev = int((grupo_prev["Dia"] == d).sum())
        folio = int((grupo_folio["Dia"] == d).sum()) if not grupo_folio.empty else 0
        opd = int(opd_dict.get((tecnico, d), 0))

        fila[f"{etiqueta} — OT Prev."] = prev
        fila[f"{etiqueta} — Folio Masivo"] = folio
        fila[f"{etiqueta} — OT OPD"] = opd
        total_sem += prev + folio + opd

    fila["Total Sem"] = total_sem
    filas_semana.append(fila)

tabla_semana = pd.DataFrame(filas_semana).set_index("Cuadrilla")
if not tabla_semana.empty:
    tabla_semana.loc["Total"] = tabla_semana.sum()

st.dataframe(tabla_semana, use_container_width=True)

st.markdown("---")

# ── Captura manual de OT OPD ──
st.subheader("Captura de OT OPD")
st.caption("Todavía no hay archivo para esta columna — captúrala aquí y se guarda en GitHub.")

filas_opd_editor = []
for tecnico in tecnicos_semana:
    for d, etiqueta in zip(dias_semana_completa, DIAS_SEMANA):
        filas_opd_editor.append({
            "Cuadrilla": tecnico,
            "Día": f"{etiqueta} {d.strftime('%d-%b')}",
            "OT OPD": int(opd_dict.get((tecnico, d), 0)),
            "_dia_real": d,
        })

df_opd_editor = pd.DataFrame(filas_opd_editor)

if not df_opd_editor.empty:
    resultado_editor = st.data_editor(
        df_opd_editor.drop(columns=["_dia_real"]),
        use_container_width=True,
        hide_index=True,
        disabled=["Cuadrilla", "Día"],
        key="opd_editor",
    )

    if st.button("💾 Guardar OT OPD", use_container_width=True):
        nuevos = []
        for i, row in resultado_editor.iterrows():
            cantidad = int(row["OT OPD"])
            if cantidad > 0:
                nuevos.append({
                    "Nombre tecnico": df_opd_editor.loc[i, "Cuadrilla"],
                    "Dia": df_opd_editor.loc[i, "_dia_real"],
                    "OT_OPD": cantidad,
                })

        pares_en_vista = set(zip(df_opd_editor["Cuadrilla"], df_opd_editor["_dia_real"]))
        otros = df_opd[~df_opd.apply(lambda r: (r["Nombre tecnico"], r["Dia"]) in pares_en_vista, axis=1)] if not df_opd.empty else pd.DataFrame(columns=["Nombre tecnico", "Dia", "OT_OPD"])

        df_opd_final = pd.concat([otros, pd.DataFrame(nuevos)], ignore_index=True)

        if _subir_a_github(df_opd_final, OT_OPD_ARCHIVO, "Actualización manual de OT OPD"):
            st.success("OT OPD guardado.")
            st.rerun()
        else:
            st.error("❌ Error al guardar OT OPD en GitHub, intenta de nuevo")