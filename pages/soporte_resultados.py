st.markdown("---")

with st.container(border=True):
    st.subheader("Resumen del dia: causas vs soluciones")
    st.caption(f"Dia: {dia_sel}")

    col_izq, col_der = st.columns(2)

    with col_izq:
        st.markdown("**Causas del soporte ingresado**")
        df_causas_dia = (
            df_dia.groupby('NIVEL2')
            .size()
            .reset_index(name='Tickets')
            .sort_values('Tickets', ascending=True)
            .tail(10)
        )
        if df_causas_dia.empty:
            st.info("Sin tickets ingresados este dia.")
        else:
            colores_causa = {
                c: '#e63946' if i == len(df_causas_dia) - 1 else '#1f77b4'
                for i, c in enumerate(df_causas_dia['NIVEL2'])
            }
            fig_causas = px.bar(
                df_causas_dia, x='Tickets', y='NIVEL2', orientation='h',
                text='Tickets', color='NIVEL2', color_discrete_map=colores_causa
            )
            fig_causas.update_traces(textposition='outside')
            fig_causas.update_layout(
                height=400, xaxis_title='Tickets', yaxis_title='',
                showlegend=False, margin=dict(l=10, r=40, t=10, b=10)
            )
            st.plotly_chart(fig_causas, use_container_width=True)

    with col_der:
        st.markdown("**Soluciones aplicadas**")
        df_cierre_dia = df_cierre[df_cierre['DIA'] == dia_sel]
        df_sol_dia = (
            df_cierre_dia.dropna(subset=['Solucion'])
            .groupby('Solucion')
            .size()
            .reset_index(name='Cierres')
            .sort_values('Cierres', ascending=True)
            .tail(10)
        )
        if df_sol_dia.empty:
            st.info("Sin soluciones registradas este dia.")
        else:
            colores_sol = {
                s: '#e63946' if i == len(df_sol_dia) - 1 else '#1f77b4'
                for i, s in enumerate(df_sol_dia['Solucion'])
            }
            fig_sol = px.bar(
                df_sol_dia, x='Cierres', y='Solucion', orientation='h',
                text='Cierres', color='Solucion', color_discrete_map=colores_sol
            )
            fig_sol.update_traces(textposition='outside')
            fig_sol.update_layout(
                height=400, xaxis_title='Cierres', yaxis_title='',
                showlegend=False, margin=dict(l=10, r=40, t=10, b=10)
            )
            st.plotly_chart(fig_sol, use_container_width=True)

    st.markdown("---")

    if not df_causas_dia.empty or not df_sol_dia.empty:
        buffer_c = io.StringIO()
        buffer_s = io.StringIO()
        if not df_causas_dia.empty:
            fig_causas.write_html(buffer_c)
        if not df_sol_dia.empty:
            fig_sol.write_html(buffer_s)

        resumen_html = f"""<!DOCTYPE html>
<html>
<head><meta charset='utf-8'><title>Resumen {dia_sel}</title></head>
<body style='font-family:Arial;padding:20px'>
<h2>Resumen de soporte — {dia_sel}</h2>
<h3>Causas del soporte ingresado</h3>
{buffer_c.getvalue()}
<h3>Soluciones aplicadas</h3>
{buffer_s.getvalue()}
</body>
</html>"""

        st.download_button(
            label="📥 Descargar resumen (causas + soluciones)",
            data=resumen_html,
            file_name=f"resumen_causas_soluciones_{dia_sel}.html",
            mime="text/html",
            key="download_resumen_causas_sol"
        )