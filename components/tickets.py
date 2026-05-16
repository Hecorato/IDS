import plotly.express as px
import streamlit as st

def render_tickets(df_agrupado, filtro, x_col, hover):
    with st.container(border=True):
        st.subheader("📋 Ingreso de tickets")
        fig = px.line(df_agrupado, x=x_col, y='TOTAL_TICKETS', markers=True)
        fig.update_traces(
            line=dict(color='#1f77b4', shape='spline', smoothing=1.3),
            marker=dict(size=8, color='#1f77b4'),
            hovertemplate=hover
        )
        if filtro == 'Semana':
            fig.update_traces(customdata=df_agrupado['NUM_SEMANA'])
        fig.update_layout(xaxis_title='Fecha', yaxis_title='Total Tickets', height=500)
        evento = st.plotly_chart(fig, use_container_width=True, on_select='rerun', key='fig_tickets')
    return evento