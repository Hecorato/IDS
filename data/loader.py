import pandas as pd

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

def cargar_datos():
    df = pd.read_csv('ids.csv')
    df = df[df['CLUSTER INSTALACION'].isin(CLUSTERS)]
    df['FECHA CREACION'] = pd.to_datetime(df['FECHA CREACION']).dt.date
    df['FECHA'] = pd.to_datetime(df['FECHA CREACION'])
    return df