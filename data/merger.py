import pandas as pd

def hacer_merge(df_tickets, df_soluciones):
    # Seleccionar solo columnas relevantes de soluciones
    cols_soluciones = ['OS', 'Falla', 'Causa', 'Solucion', 'Estatus', 'Cluster']
    df_sol = df_soluciones[cols_soluciones].copy()

    # Merge por OS
    df_merge = pd.merge(df_tickets, df_sol, on='OS', how='left')

    return df_merge

def cargar_soluciones():
    df = pd.read_csv('soluciones.csv')
    return df