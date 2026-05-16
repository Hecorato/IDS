import streamlit as st

def check_login():
    def login():
        usuario = st.session_state["usuario"]
        password = st.session_state["password"]
        usuarios = st.secrets["users"]

        if usuario in usuarios and usuarios[usuario] == password:
            st.session_state["logged_in"] = True
            st.session_state["nombre"] = usuario
        else:
            st.session_state["logged_in"] = False
            st.session_state["error"] = True

    if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image("https://img.icons8.com/color/96/dashboard-layout.png")
            st.title("Dashboard IDS")
            st.text_input("Usuario", key="usuario")
            st.text_input("Contraseña", type="password", key="password")
            st.button("Entrar", on_click=login, use_container_width=True)
            if st.session_state.get("error"):
                st.error("Usuario o contraseña incorrectos ❌")
        return False
    return True