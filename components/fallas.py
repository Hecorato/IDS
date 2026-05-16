import plotly.express as px
import streamlit as st

def render_fallas(df_filtrado):
    with st.container(border=True):
        st.subheader("⚠️ Fallas")
        df_fallas = df_filtrado.groupby('NIVEL2').size().reset_index(name='TOTAL')
        df_fallas = df_fallas.sort_values('TOTAL', ascending=False)
        total_fallas = df_fallas['TOTAL'].sum()
        st.metric("Total fallas en el período", f"{total_fallas:,}")
        fig = px.bar(df_fallas, x='TOTAL', y='NIVEL2', orientation='h',
                     color='NIVEL2', text='TOTAL')
        fig.update_traces(
            hovertemplate='%{y}<br>Fallas: %{x}<extra></extra>',
            textposition='outside',
            showlegend=False
        )
        fig.update_layout(
            yaxis_title='', xaxis_title='Total Fallas',
            yaxis=dict(autorange='reversed'),
            showlegend=False, height=500
        )
        st.plotly_chart(fig, use_container_width=True)