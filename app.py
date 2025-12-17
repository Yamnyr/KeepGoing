import streamlit as st

st.set_page_config(
    page_title="KeepGoing",
    page_icon="🏋️",
    layout="wide"
)

# Vérification de l'authentification
if not st.user.is_logged_in:
    st.title("KeepGoing - Suivi Sportif")
    st.write("Application de suivi de performances sportives personnalisée")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.info("Connectez-vous pour accéder à votre espace personnel")
        st.button("Se connecter avec Google", on_click=st.login, use_container_width=True)
    st.stop()

# Utilisateur connecté
st.sidebar.success(f"Connecté en tant que {st.user.email}")

# Bouton de déconnexion dans la sidebar
if st.sidebar.button("🚪 Se déconnecter"):
    st.logout()

pages = [
    st.Page("pages/dashboard.py", title="📊 Tableau de bord"),
    st.Page("pages/add_sport.py", title="➕ Ajouter un sport"),
    st.Page("pages/add_performance.py", title="🎯 Nouvelle performance"),
    st.Page("pages/analytics.py", title="📈 Analyse détaillée"),
]

pg = st.navigation(pages, position="top")
pg.run()