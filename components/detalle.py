import pandas as pd
import plotly.express as px
import streamlit as st

def render_detalle(df_filtrado, evento):
    if evento and evento.selection and evento.selection.points:
        punto = evento.selection.points[0]
        fecha_click = pd.to_datetime(punto['x']).date()
        df_dia = df_filtrado[df_filtrado['FECHA CREACION'] == fecha_click]

        st.markdown("---")
        st.subheader(f"📅 Detalle del {fecha_click}")

        col1, col2 = st.columns(2)

        with col1:
            with st.container(border=True):
                st.subheader("⚠️ Causas")
                df_causas = df_dia.groupby('NIVEL2').size().reset_index(name='TOTAL')
                df_causas = df_causas.sort_values('TOTAL', ascending=False)
                fig1 = px.bar(df_causas, x='TOTAL', y='NIVEL2',
                              orientation='h', color='NIVEL2', text='TOTAL')
                fig1.update_layout(showlegend=False, height=400)
                fig1.update_traces(showlegend=False, textposition='outside')
                st.plotly_chart(fig1, use_container_width=True)

        with col2:
            with st.container(border=True):
                st.subheader("🏘️ Por Cluster")
                df_cluster = df_dia.groupby('CLUSTER INSTALACION').size().reset_index(name='TOTAL')
                df_cluster = df_cluster.sort_values('TOTAL', ascending=False)
                fig2 = px.bar(df_cluster, x='TOTAL', y='CLUSTER INSTALACION',
                              orientation='h', color='CLUSTER INSTALACION', text='TOTAL')
                fig2.update_layout(showlegend=False, height=400)
                fig2.update_traces(showlegend=False, textposition='outside')
                st.plotly_chart(fig2, use_container_width=True)

        with st.container(border=True):
            st.subheader("📋 Tickets del día")
            cols_mostrar = ['OT', 'CUENTA', 'CLUSTER INSTALACION', 'NIVEL2', 'ESTATUS']
            cols_existentes = [c for c in cols_mostrar if c in df_dia.columns]
            st.dataframe(df_dia[cols_existentes], use_container_width=True)