import pandas as pd
import streamlit as st
import requests
import base64
from components.auth import check_login

# ── LISTA DE CLUSTERS ─────────────────────────────────
CLUSTERS = [
    "AMPLIACION COACALCO",
    "AMPLIACION CUAUTITLAN 2",
    "AMPLIACION MELCHOR OCAMPO 1",
    "AMPLIACION MELCHOR OCAMPO 2",
    "AMPLIACION PASEOS DEL VALLE 1",
    "AMPLIACION SAN PABLO DE LAS SALINAS 2",
    "COACALCO",
    "MELCHOR OCAMPO",
    "PASEOS DEL VALLE",
    "SAN PABLO DE LAS SALINAS I",
    "SAN PABLO DE LAS SALINAS II",
    "TEOLOYUCAN_A",
    "MELCHOR OCAMPO_A",
    "TEOLOYUCAN",
    "TULTEPEC",
    "VILLA DE LAS FLORES",
    "TEOLOYUCAN_2_A"
]

# ── FUNCIÓN: SUBIR A GITHUB ───────────────────────────
def subir_a_github(df):
    token = st.secrets["github"]["token"]
    repo = st.secrets["github"]["repo"]
    url = f"https://api.github.com/repos/{repo}/contents/ids.csv"
    headers = {"Authorization": f"token {token}"}

    r = requests.get(url, headers=headers)
    sha = r.json().get("sha", None)

    contenido = df.to_csv(index=False).encode()
    contenido_b64 = base64.b64encode(contenido).decode()

    payload = {
        "message": "Actualización automática ids.csv",
        "content": contenido_b64,
        "sha": sha
    }

    r = requests.put(url, headers=headers, json=payload)
    return r.status_code in [200, 201]

# ── FUNCIÓN: LEER Y LIMPIAR XLSX ──────────────────────
def procesar_archivo(archivo):
    df = pd.read_excel(archivo,
        sheet_name='Reporte ingresos soportes',
        header=1
    )
    # Eliminar columnas vacías
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    # Eliminar filas vacías
    df = df.dropna(how='all')
    # Filtrar solo tus clusters
    df = df[df['CLUSTER INSTALACION'].isin(CLUSTERS)]
    # Agregar columna fecha limpia y semana
    df['FECHA CREACION'] = pd.to_datetime(df['FECHA CREACION'], dayfirst=True, errors='coerce').dt.date
    df['SEMANA'] = pd.to_datetime(df['FECHA CREACION']).dt.isocalendar().week
    return df

# ── PÁGINA ────────────────────────────────────────────
st.set_page_config(page_title="Admin - Dashboard IDS", layout="wide")

if not check_login():
    st.stop()

st.title("⚙️ Administración")
st.markdown("---")

with st.container(border=True):
    st.subheader("📤 Cargar reporte del día")
    st.caption("Sube el archivo xlsx tal como lo descargas, sin modificarlo")

    archivo = st.file_uploader("Selecciona el archivo", type=["xlsx", "xls"])

    if archivo:
        with st.spinner("Procesando archivo..."):
            df_nuevo = procesar_archivo(archivo)

        st.success(f"✅ {len(df_nuevo)} registros de tus clusters encontrados")
        st.dataframe(df_nuevo.head(10), use_container_width=True)

        st.markdown("---")
        if st.button("⬆️ Actualizar dashboard", use_container_width=True):
            with st.spinner("Fusionando y subiendo a GitHub..."):
                try:
                    df_base = pd.read_csv('ids.csv')
                    df_base['FECHA CREACION'] = pd.to_datetime(
                        df_base['FECHA CREACION']
                    ).dt.date
                    df_total = pd.concat(
                        [df_base, df_nuevo], ignore_index=True
                    )
                    df_total = df_total.drop_duplicates(
                        subset=['OS'], keep='last'
                    )
                except:
                    df_total = df_nuevo

                if subir_a_github(df_total):
                    st.success(
                        f"🎉 Dashboard actualizado con {len(df_total)} registros totales"
                    )
                    st.balloons()
                else:
                    st.error("❌ Error al subir a GitHub, intenta de nuevo")