import pandas as pd
import streamlit as st
import requests
import base64
import io
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


# ── FUNCIÓN: LEER BASE ACTUAL DIRECTO DE GITHUB (NO LOCAL) ──
def leer_de_github(nombre_archivo, dtype=None):
    """
    Trae siempre la versión más reciente del csv desde GitHub (raw),
    en vez de leer el archivo local del contenedor. Esto evita que
    se pierda histórico si subes varios archivos en la misma sesión,
    ya que el archivo local nunca se entera de lo que se sube a GitHub.
    Devuelve None si el archivo no existe todavía en el repo.
    """
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

# ── FUNCIÓN: LEER Y LIMPIAR CIERRE DIARIO PE (DISARO/DISACONNECT) ──
def procesar_cierre_pe(archivo):
    df = pd.read_excel(archivo,
        sheet_name='Reporte Cierre Diario',
        header=1
    )
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    df = df.dropna(how='all')
    df.columns = df.columns.str.strip()

    # Solo empresas de Planta Externa
    df['Empresa(proveedor)'] = df['Empresa(proveedor)'].astype(str).str.strip()
    df = df[df['Empresa(proveedor)'].isin(['DISARO', 'DISACONNECT'])]

    # Limpiar saltos de linea/tabs embebidos en nombre y fechas
    for col in ['Nombre tecnico', 'Nombre despacho/AA', 'Nombre supervisor']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(r'[\n\r\t]+', ' ', regex=True).str.strip()

    cols_fecha = [
        'Fecha creacion FFM', 'Fecha asignacion', 'Fecha transito',
        'Fecha sitio', 'Fecha trabajo', 'Fecha termino'
    ]
    for col in cols_fecha:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(r'[\n\r\t]+', '', regex=True)
            df[col] = pd.to_datetime(df[col], dayfirst=True, errors='coerce')

    if 'Tipo' in df.columns:
        df['Tipo'] = df['Tipo'].astype(str).str.strip()
    if 'Subtipo' in df.columns:
        df['Subtipo'] = df['Subtipo'].astype(str).str.strip()

    cols_necesarias = [
        'Cuenta', 'OS', 'OT', 'Tipo', 'Subtipo', 'Cluster',
        'Nombre tecnico', 'Usuario instalador', 'Empresa(proveedor)',
        'Fecha creacion FFM', 'Fecha trabajo', 'Fecha termino',
        'Estatus', 'Estado', 'QR asignado'
    ]
    cols_disp = [c for c in cols_necesarias if c in df.columns]
    df = df[cols_disp]

    return df

# ── FUNCIÓN: LEER Y LIMPIAR SEGUIMIENTO DIARIO PE (FOLIOS MASIVOS) ──
def procesar_seguimiento_pe(archivo):
    df = pd.read_excel(archivo,
        sheet_name='Reporte segumiento Diario',
        header=1
    )
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    df = df.dropna(how='all')
    df.columns = df.columns.str.strip()

    # Solo empresas de Planta Externa
    df['Empresa(proveedor)'] = df['Empresa(proveedor)'].astype(str).str.strip()
    df = df[df['Empresa(proveedor)'].isin(['DISARO', 'DISACONNECT'])]

    if 'Nombre tecnico' in df.columns:
        df['Nombre tecnico'] = df['Nombre tecnico'].astype(str).str.replace(r'[\n\r\t]+', ' ', regex=True).str.strip()

    cols_fecha = ['Fecha creacion FFM', 'Fecha ultima agenda', 'Fecha termino', 'Fecha Confirmacion']
    for col in cols_fecha:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(r'[\n\r\t]+', '', regex=True)
            df[col] = pd.to_datetime(df[col], dayfirst=True, errors='coerce')

    cols_necesarias = [
        'Cuenta', 'Ticket', 'OT', 'Tipo', 'Subtipo', 'Empresa(proveedor)',
        'Nombre tecnico', 'Fecha creacion FFM', 'Fecha ultima agenda',
        'Fecha termino', 'Estatus', 'Estado', 'Motivo'
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

    # Filtrar solo cuentas validas (solo numeros, sin guiones ni vacios)
    df = df[df['Cuenta'].astype(str).str.strip().str.match(r'^\d+$')]

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
                df_base = leer_de_github("ids.csv")
                if df_base is not None:
                    df_base['FECHA CREACION'] = pd.to_datetime(df_base['FECHA CREACION'], errors='coerce').dt.date
                    df_total = pd.concat([df_base, df_nuevo], ignore_index=True)
                    df_total = df_total.drop_duplicates(subset=['OS'], keep='last')
                else:
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
                df_cierre_base = leer_de_github("reporteCierreDiario.csv", dtype={'Cuenta': str})
                if df_cierre_base is not None:
                    cols_fecha = ['Fecha creacion FFM', 'Fecha trabajo', 'Fecha termino']
                    for col in cols_fecha:
                        if col in df_cierre_base.columns:
                            df_cierre_base[col] = pd.to_datetime(df_cierre_base[col], errors='coerce')
                    df_cierre_total = pd.concat([df_cierre_base, df_cierre_nuevo], ignore_index=True)
                    df_cierre_total = df_cierre_total.drop_duplicates(subset=['OS'], keep='last')
                else:
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

st.markdown("---")

with st.container(border=True):
    st.subheader("📤 Cargar Cierre Diario PE (DISARO / DISACONNECT)")
    st.caption("Sube el mismo archivo de Cierre Diario — aquí se filtra y guarda solo Planta Externa")

    archivo_cierre_pe = st.file_uploader("Selecciona el archivo", type=["xlsx", "xls"], key="cierre_pe_uploader")

    if archivo_cierre_pe:
        with st.spinner("Procesando archivo..."):
            df_cierre_pe_nuevo = procesar_cierre_pe(archivo_cierre_pe)

        st.success(f"✅ {len(df_cierre_pe_nuevo)} registros de DISARO/DISACONNECT encontrados")
        st.dataframe(df_cierre_pe_nuevo.head(10), use_container_width=True)

        st.markdown("---")
        if st.button("⬆️ Actualizar Cierre Diario PE", use_container_width=True, key="btn_cierre_pe"):
            with st.spinner("Fusionando y subiendo a GitHub..."):
                df_cierre_pe_base = leer_de_github("cierrePE.csv", dtype={'Cuenta': str})
                if df_cierre_pe_base is not None:
                    cols_fecha = ['Fecha creacion FFM', 'Fecha trabajo', 'Fecha termino']
                    for col in cols_fecha:
                        if col in df_cierre_pe_base.columns:
                            df_cierre_pe_base[col] = pd.to_datetime(df_cierre_pe_base[col], errors='coerce')
                    df_cierre_pe_total = pd.concat([df_cierre_pe_base, df_cierre_pe_nuevo], ignore_index=True)
                    # OS casi siempre viene vacío en PE (solo tienen OT) — dedup por OT, no por OS
                    df_cierre_pe_total = df_cierre_pe_total.drop_duplicates(subset=['OT'], keep='last')
                else:
                    df_cierre_pe_total = df_cierre_pe_nuevo

                if subir_a_github(df_cierre_pe_total, "cierrePE.csv", "Actualización automática cierrePE.csv"):
                    st.success(f"🎉 Cierre Diario PE actualizado con {len(df_cierre_pe_total)} registros totales")
                    st.balloons()
                else:
                    st.error("❌ Error al subir a GitHub, intenta de nuevo")

st.markdown("---")

with st.container(border=True):
    st.subheader("📤 Cargar Seguimiento Diario PE (Folios Masivos / MDR)")
    st.caption("Sube el reporte de Seguimiento Diario (Falla Masiva) — se filtra solo Planta Externa")

    archivo_seguimiento = st.file_uploader("Selecciona el archivo", type=["xlsx", "xls"], key="seguimiento_uploader")

    if archivo_seguimiento:
        with st.spinner("Procesando archivo..."):
            df_seguimiento_nuevo = procesar_seguimiento_pe(archivo_seguimiento)

        st.success(f"✅ {len(df_seguimiento_nuevo)} registros de DISARO/DISACONNECT encontrados")
        st.dataframe(df_seguimiento_nuevo.head(10), use_container_width=True)

        st.markdown("---")
        if st.button("⬆️ Actualizar Seguimiento Diario PE", use_container_width=True, key="btn_seguimiento"):
            with st.spinner("Fusionando y subiendo a GitHub..."):
                df_seguimiento_base = leer_de_github("seguimientoPE.csv", dtype={'Cuenta': str})
                if df_seguimiento_base is not None:
                    cols_fecha = ['Fecha creacion FFM', 'Fecha ultima agenda', 'Fecha termino']
                    for col in cols_fecha:
                        if col in df_seguimiento_base.columns:
                            df_seguimiento_base[col] = pd.to_datetime(df_seguimiento_base[col], errors='coerce')
                    df_seguimiento_total = pd.concat([df_seguimiento_base, df_seguimiento_nuevo], ignore_index=True)
                    df_seguimiento_total = df_seguimiento_total.drop_duplicates(subset=['OT'], keep='last')
                else:
                    df_seguimiento_total = df_seguimiento_nuevo

                if subir_a_github(df_seguimiento_total, "seguimientoPE.csv", "Actualización automática seguimientoPE.csv"):
                    st.success(f"🎉 Seguimiento Diario PE actualizado con {len(df_seguimiento_total)} registros totales")
                    st.balloons()
                else:
                    st.error("❌ Error al subir a GitHub, intenta de nuevo")