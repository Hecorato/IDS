import pandas as pd

def cargar_datos():
    df = pd.read_csv('IDS ABRIL-MAYO - Hoja 1.csv')
    df['FECHA CREACION'] = pd.to_datetime(df['FECHA CREACION']).dt.date
    df['FECHA'] = pd.to_datetime(df['FECHA CREACION'])
    return df