import pandas as pd

CLUSTERS = [
    "AMPLIACION COACALCO",
    "AMPLIACION CUAUTITLAN 2",
    "AMPLIACION MELCHOR OCAMPO 1",
    "AMPLIACION MELCHOR OCAMPO 2",
    "AMPLIACION MELCHOR OCAMPO 2_A",
    "AMPLIACION PASEOS DEL VALLE 1",
    "AMPLIACION SAN PABLO DE LAS SALINAS II",
    "COACALCO",
    "MELCHOR OCAMPO",
    "PASEOS DEL VALLE",
    "SAN PABLO DE LAS SALINAS I",
    "SAN PABLO DE LAS SALINAS II",
    "MELCHOR OCAMPO_A",
    "MELCHOR OCAMPO 2_A",
    "TEOLOYUCAN",
    "TULTEPEC",
    "VILLA DE LAS FLORES",
    "TEOLOYUCAN_2_A",
    "TEOLOYUCAN_3_A",
    "TEOLOYUCAN_A"
]

def cargar_datos():
    df = pd.read_csv('ids.csv', dtype={'CUENTA': str})  # ← fuerza lectura como texto
    df = df[df['CLUSTER INSTALACION'].isin(CLUSTERS)]
    df = df[df['ESTATUS'] != 'Cancelado']
    df['CUENTA'] = df['CUENTA'].str.strip().str.zfill(10)
    df['FECHA CREACION'] = pd.to_datetime(df['FECHA CREACION']).dt.date
    df['FECHA'] = pd.to_datetime(df['FECHA CREACION'])
    return df

    st.cache_data.clear()