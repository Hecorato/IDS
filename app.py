import streamlit as st
from data.loader import cargar_datos
from components.auth import check_login
from components.filtros import render_filtros
from components.tickets import render_tickets
from components.fallas import render_fallas
from components.detalle import render_detalle

st.set_page_config(page_title="Dashboard IDS", layout="wide")

if not check_login():
    st.stop()

# ── HEADER ────────────────────────────────────────────
col1, col2 = st.columns([6, 1])
with col1:
    st.title("Dashboard IDS")
with col2:
    st.write(f"👤 {st.session_state['nombre']}")
    if st.button("Cerrar sesión"):
        st.session_state.clear()
        st.rerun()

# ── DASHBOARD ─────────────────────────────────────────
df = cargar_datos()
df_filtrado, filtro, df_agrupado, x_col, hover = render_filtros(df)

col1, col2 = st.columns(2)
with col1:
    evento = render_tickets(df_agrupado, filtro, x_col, hover)
with col2:
    render_fallas(df_filtrado)

render_detalle(df_filtrado, evento)