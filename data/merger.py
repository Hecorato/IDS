import pandas as pd

def hacer_merge(df_tickets, df_soluciones):
    cols_soluciones = ['OS', 'Falla', 'Causa', 'Solucion', 'Estatus', 'Cluster']
    # Solo tomar columnas que existan
    cols_existentes = [c for c in cols_soluciones if c in df_soluciones.columns]
    df_sol = df_soluciones[cols_existentes].copy()
    df_merge = pd.merge(df_tickets, df_sol, on='OS', how='left')
    return df_merge

def cargar_soluciones():
    df = pd.read_csv(
        'soluciones.csv',
        encoding='utf-8-sig',
        on_bad_lines='skip'
    )
    return df