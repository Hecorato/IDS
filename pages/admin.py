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

# ── FUNCIÓN: SUBIR ARCHIVO A GITHUB (GENERICA) ────────
def subir_a_github(df, nombre_archivo, mensaje):
    token = st.secrets["github"]["token"]
    repo = st.secrets["github"]["repo"]
    url = f"https://api.github.com/repos/{repo}/contents/{nombre_archivo}"
    headers = {"Authorization": f"token {token}"}

    r = requests.get(url, headers=headers)
    sha = r.json().get("sha", None)

    contenido = df.to_csv(index=False).encode()
    contenido_b64 = base64.b64encode(contenido).decode()

    payload = {
        "message": mensaje,
        "content": contenido_b64,
        "sha": sha
    }

    r = requests.put(url, headers=headers, json=payload)
    return r.status_code in [200, 201]

# ── FUNCIÓN: LEER Y LIMPIAR IDS.XLSX ──────────────────
def procesar_archivo(archivo):
    df = pd.read_excel(archivo,
        sheet_name='Reporte ingresos soportes',
        header=1
    )
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    df = df.dropna(how='all')
    df = df[df['CLUSTER INSTALACION'].isin(CLUSTERS)]
    df['FECHA CREACION'] = pd.to_datetime(df['FECHA CREACION'], dayfirst=True, errors='coerce').dt.date
    df['SEMANA'] = pd.to_datetime(df['FECHA CREACION']).dt.isocalendar().week
    return df

# ── FUNCIÓN: LEER Y LIMPIAR REPORTE CIERRE DIARIO ─────
def procesar_cierre(archivo):
    df = pd.read_excel(archivo,
        sheet_name='Reporte Cierre Diario',
        header=1
    )
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    df = df.dropna(how='all')
    df.columns = df.columns.str.strip()

    df['Cuenta'] = df['Cuenta'].astype(str).str.strip().str.replace('.0', '', regex=False).str.zfill(10)

    cols_fecha = [
        'Fecha creacion FFM', 'Fecha asignacion', 'Fecha transito',
        'Fecha sitio', 'Fecha trabajo', 'Fecha termino'
    ]
    for col in cols_fecha:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], dayfirst=True, errors='coerce')

    cols_necesarias = [
        'Cuenta', 'OS', 'OT', 'Tipo', 'Subtipo', 'Cluster',
        'Nombre tecnico', 'Usuario instalador', 'Empresa(proveedor)',
        'Fecha creacion FFM', 'Fecha trabajo', 'Fecha termino',
        'Estatus', 'Estado', 'Falla', 'Causa', 'Solucion',
        'Potencia inicial', 'Potencia final', 'QR asignado'
    ]
    cols_disp = [c for c in cols_necesarias if c in df.columns]
    df = df[cols_disp]

    return df

# ── FUNCIÓN: LEER Y LIMPIAR NCE (All_GPON_ONU) ────────
def procesar_nce(archivo):
    df = pd.read_excel(archivo, sheet_name='Sheet1', header=0)
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    df = df.dropna(how='all')
    df.columns = df.columns.str.strip()

    cols_necesarias = [
        'Device Name', 'Running Status', 'Frame', 'Slot', 'Port',
        'Alias', 'SN', 'Vendor ID', 'Terminal Type'
    ]
    cols_disp = [c for c in cols_necesarias if c in df.columns]
    df = df[cols_disp]

    return df

# ── FUNCIÓN: LEER Y LIMPIAR SEMANA DETALLE ────────────
def procesar_detalle(archivo):
    df = pd.read_excel(archivo, sheet_name='Sheet1', header=0)
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    df = df.dropna(how='all')
    df.columns = df.columns.str.strip()

    df['Cuenta'] = df['Cuenta'].astype(str).str.strip().str.replace('.0', '', regex=False).str.zfill(10)

    cols_necesarias = [
        'Distrito', 'Cluster', 'OLT', 'F', 'S', 'P',
        'Cuenta', 'Código QR', 'Capacidad',
        'Latitud', 'Longitud', 'NOMBRE_SPLITTER', 'Ubicacion'
    ]
    cols_disp = [c for c in cols_necesarias if c in df.columns]
    df = df[cols_disp]

    return df

# ── PÁGINA ────────────────────────────────────────────
st.set_page_config(page_title="Admin - Dashboard IDS", layout="wide")

if not check_login():
    st.stop()

st.title("⚙️ Administración")
st.markdown("---")

with st.container(border=True):
    st.subheader("📤 Cargar reporte del día (IDS)")
    st.caption("Sube el archivo xlsx tal como lo descargas, sin modificarlo")

    archivo = st.file_uploader("Selecciona el archivo", type=["xlsx", "xls"], key="ids_uploader")

    if archivo:
        with st.spinner("Procesando archivo..."):
            df_nuevo = procesar_archivo(archivo)

        st.success(f"✅ {len(df_nuevo)} registros de tus clusters encontrados")
        st.dataframe(df_nuevo.head(10), use_container_width=True)

        st.markdown("---")
        if st.button("⬆️ Actualizar dashboard", use_container_width=True, key="btn_ids"):
            with st.spinner("Fusionando y subiendo a GitHub..."):
                try:
                    df_base = pd.read_csv('ids.csv')
                    df_base['FECHA CREACION'] = pd.to_datetime(df_base['FECHA CREACION']).dt.date
                    df_total = pd.concat([df_base, df_nuevo], ignore_index=True)
                    df_total = df_total.drop_duplicates(subset=['OS'], keep='last')
                except:
                    df_total = df_nuevo

                if subir_a_github(df_total, "ids.csv", "Actualización automática ids.csv"):
                    st.success(f"🎉 Dashboard actualizado con {len(df_total)} registros totales")
                    st.balloons()
                else:
                    st.error("❌ Error al subir a GitHub, intenta de nuevo")

st.markdown("---")

with st.container(border=True):
    st.subheader("📤 Cargar Reporte Cierre Diario")
    st.caption("Sube el archivo xls tal como lo descargas, sin modificarlo")

    archivo_cierre = st.file_uploader("Selecciona el archivo", type=["xlsx", "xls"], key="cierre_uploader")

    if archivo_cierre:
        with st.spinner("Procesando archivo..."):
            df_cierre_nuevo = procesar_cierre(archivo_cierre)

        st.success(f"✅ {len(df_cierre_nuevo)} registros encontrados")
        st.dataframe(df_cierre_nuevo.head(10), use_container_width=True)

        st.markdown("---")
        if st.button("⬆️ Actualizar Reporte Cierre Diario", use_container_width=True, key="btn_cierre"):
            with st.spinner("Fusionando y subiendo a GitHub..."):
                try:
                    df_cierre_base = pd.read_csv('reporteCierreDiario.csv', dtype={'Cuenta': str})
                    cols_fecha = ['Fecha creacion FFM', 'Fecha trabajo', 'Fecha termino']
                    for col in cols_fecha:
                        if col in df_cierre_base.columns:
                            df_cierre_base[col] = pd.to_datetime(df_cierre_base[col], errors='coerce')
                    df_cierre_total = pd.concat([df_cierre_base, df_cierre_nuevo], ignore_index=True)
                    df_cierre_total = df_cierre_total.drop_duplicates(subset=['OS'], keep='last')
                except Exception:
                    df_cierre_total = df_cierre_nuevo

                if subir_a_github(df_cierre_total, "reporteCierreDiario.csv", "Actualización automática reporteCierreDiario.csv"):
                    st.success(f"🎉 Reporte Cierre Diario actualizado con {len(df_cierre_total)} registros totales")
                    st.balloons()
                else:
                    st.error("❌ Error al subir a GitHub, intenta de nuevo")

st.markdown("---")

with st.container(border=True):
    st.subheader("📤 Cargar base NCE (All_GPON_ONU)")
    st.caption("Sube el archivo xlsx de puertos NCE — reemplaza la base completa")

    archivo_nce = st.file_uploader("Selecciona el archivo", type=["xlsx", "xls"], key="nce_uploader")

    if archivo_nce:
        with st.spinner("Procesando archivo..."):
            df_nce_nuevo = procesar_nce(archivo_nce)

        st.success(f"✅ {len(df_nce_nuevo)} registros encontrados")
        st.dataframe(df_nce_nuevo.head(10), use_container_width=True)

        st.markdown("---")
        if st.button("⬆️ Actualizar NCE", use_container_width=True, key="btn_nce"):
            with st.spinner("Subiendo a GitHub..."):
                if subir_a_github(df_nce_nuevo, "coacalco_nce.csv", "Actualización automática coacalco_nce.csv"):
                    st.success(f"🎉 NCE actualizado con {len(df_nce_nuevo)} registros")
                    st.balloons()
                else:
                    st.error("❌ Error al subir a GitHub, intenta de nuevo")

st.markdown("---")

with st.container(border=True):
    st.subheader("📤 Cargar Semana Detalle Coacalco")
    st.caption("Sube el archivo xlsx de infraestructura — reemplaza la base completa")

    archivo_detalle = st.file_uploader("Selecciona el archivo", type=["xlsx", "xls"], key="detalle_uploader")

    if archivo_detalle:
        with st.spinner("Procesando archivo..."):
            df_detalle_nuevo = procesar_detalle(archivo_detalle)

        st.success(f"✅ {len(df_detalle_nuevo)} registros encontrados")
        st.dataframe(df_detalle_nuevo.head(10), use_container_width=True)

        st.markdown("---")
        if st.button("⬆️ Actualizar Semana Detalle", use_container_width=True, key="btn_detalle"):
            with st.spinner("Subiendo a GitHub..."):
                if subir_a_github(df_detalle_nuevo, "semana_detalle_coacalco.csv", "Actualización automática semana_detalle_coacalco.csv"):
                    st.success(f"🎉 Semana Detalle actualizado con {len(df_detalle_nuevo)} registros")
                    st.balloons()
                else:
                    st.error("❌ Error al subir a GitHub, intenta de nuevo")