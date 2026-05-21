import streamlit as st
import requests
from components.auth import check_login

st.set_page_config(page_title="Buscador de Cuenta(En construccion)", layout="wide")

if not check_login():
    st.stop()

BASE = "https://apiservice.sistemastp.com.mx/gsa/lite/v1/port"
headers = {"User-Agent": "DashboardIDS/1.0"}

st.title("🔍 Buscador de Cuenta")
st.markdown("---")

col1, col2 = st.columns([2, 1])
with col1:
    cuenta = st.text_input("Número de cuenta", placeholder="Ej: 0135295039")
with col2:
    qr = st.text_input("QR del splitter", placeholder="Ej: TP794566")

buscar = st.button("🔍 Buscar", use_container_width=True)

if buscar:
    if not cuenta or not qr:
        st.warning("Ingresa la cuenta y el QR para buscar.")
    else:
        with st.spinner("Consultando API..."):
            try:
                response = requests.get(f"{BASE}/qr?qr={qr}", headers=headers)
                
                if response.status_code != 200:
                    st.error(f"Error al consultar la API: {response.status_code}")
                else:
                    data = response.json()
                    resultado = None

                    for splitter in data.get("splitters", []):
                        for puerto in splitter.get("listmodelpuertos", []):
                            if puerto.get("cuenta") == cuenta:
                                resultado = {
                                    "QR": qr,
                                    "Splitter": splitter.get("nombre", "N/A"),
                                    "Puerto": puerto.get("numeroPuerto", "N/A"),
                                    "OT": puerto.get("ot", "N/A"),
                                    "Serie": puerto.get("serie", "N/A"),
                                    "Status": puerto.get("descripcionPuerto", "N/A"),
                                }
                                break
                        if resultado:
                            break

                    if resultado:
                        st.success("✅ Cuenta encontrada")
                        with st.container(border=True):
                            c1, c2, c3 = st.columns(3)
                            c1.metric("📡 QR", resultado["QR"])
                            c1.metric("🔌 Splitter", resultado["Splitter"])
                            c2.metric("🔢 Puerto", resultado["Puerto"])
                            c2.metric("📋 OT", resultado["OT"])
                            c3.metric("🏷️ Serie", resultado["Serie"])
                            c3.metric("📶 Status", resultado["Status"])
                    else:
                        st.error(f"❌ Cuenta `{cuenta}` no encontrada en el QR `{qr}`")

            except Exception as e:
                st.error(f"Error de conexión: {e}")

if st.button("← Regresar al dashboard"):
    st.switch_page("app.py")