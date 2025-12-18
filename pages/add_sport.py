# pages/add_sport.py
import streamlit as st
from utils import load_user_sports, save_sport, render_sidebar

st.title("Ajouter un nouveau sport")
st.divider()

data = load_user_sports()

col1, col2 = st.columns([2, 1])

with col1:
    with st.form("add_sport_form"):
        new_sport = st.text_input(
            "Nom du sport",
            placeholder="Ex: Planche, Pompes, Course à pied...",
            help="Donnez un nom descriptif à votre activité sportive"
        )

        col_a, col_b = st.columns(2)
        with col_a:
            unit = st.text_input(
                "Unité de mesure",
                placeholder="Ex: secondes, répétitions, km...",
                help="Comment mesurer vos performances ?"
            )
        with col_b:
            goal = st.number_input(
                "Objectif (optionnel)",
                min_value=0.0,
                step=1.0,
                help="Définissez un objectif à atteindre"
            )

        submit_sport = st.form_submit_button("Créer le sport", use_container_width=True, type="primary")

        if submit_sport:
            if new_sport and unit:
                if new_sport in data:
                    st.warning("Ce sport existe déjà dans votre liste.")
                else:
                    if save_sport(new_sport, unit, goal if goal > 0 else None):
                        st.success(f"Sport '{new_sport}' ajouté avec succès !")
                        st.balloons()
                        st.rerun()
            else:
                st.error("Veuillez remplir tous les champs obligatoires")

with col2:
    st.info("""
    **Conseils pour ajouter un sport :**

    - Choisissez un nom clair et reconnaissable
    - Utilisez une unité cohérente que vous pourrez maintenir
    - Définissez un objectif réaliste et motivant
    """)

# Sidebar avec stats et déconnexion
render_sidebar(data)