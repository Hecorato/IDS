import streamlit as st
import cloudinary
import cloudinary.uploader
import cloudinary.api
from components.auth import check_login

st.set_page_config(page_title="Evidencias - Dashboard IDS", layout="wide")

if not check_login():
    st.stop()

cloudinary.config(
    cloud_name=st.secrets["cloudinary"]["cloud_name"],
    api_key=st.secrets["cloudinary"]["api_key"],
    api_secret=st.secrets["cloudinary"]["api_secret"]
)

st.title("📸 Evidencias por Splitter")
st.markdown("---")

# ── BUSCAR QR ─────────────────────────────────────────
qr = st.text_input("Ingresa el QR del splitter:", placeholder="Ej: TP586687").strip().upper()

if not qr:
    st.info("Ingresa un QR para ver o subir evidencias.")
    st.stop()

st.subheader(f"📡 Splitter: {qr}")
st.markdown("---")

tab_antes, tab_durante, tab_despues = st.tabs(["📷 Antes", "🔧 Durante", "✅ Después"])

for tab, etapa in zip([tab_antes, tab_durante, tab_despues], ["antes", "durante", "despues"]):
    with tab:
        folder = f"evidencias/{qr}/{etapa}"

        # ── SUBIR ──
        with st.container(border=True):
            st.markdown(f"**Subir imagen — {etapa}**")
            archivo = st.file_uploader(
                "Selecciona una imagen",
                type=["jpg", "jpeg", "png"],
                key=f"upload_{qr}_{etapa}"
            )
            if archivo:
                with st.spinner("Subiendo..."):
                    try:
                        cloudinary.uploader.upload(
                            archivo,
                            folder=folder,
                            public_id=f"{qr}_{etapa}_{archivo.name}"
                        )
                        st.success("✅ Imagen subida correctamente")
                    except Exception as e:
                        st.error(f"Error al subir: {e}")

        # ── VER ──
        with st.container(border=True):
            st.markdown(f"**Evidencias guardadas — {etapa}**")
            try:
                recursos = cloudinary.api.resources(
                    type="upload",
                    prefix=folder,
                    max_results=10
                )
                imagenes = recursos.get("resources", [])

                if imagenes:
                    cols = st.columns(3)
                    for i, img in enumerate(imagenes):
                        with cols[i % 3]:
                            st.image(img["secure_url"], use_column_width=True)
                            if st.button("🗑️ Eliminar", key=f"del_{img['public_id']}"):
                                cloudinary.uploader.destroy(img["public_id"])
                                st.rerun()
                else:
                    st.info("Sin evidencias aún.")
            except Exception:
                st.info("Sin evidencias aún.")

if st.button("← Regresar al dashboard", key="regresar_evidencias"):
    st.switch_page('app.py')