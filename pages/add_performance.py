# pages/add_performance.py
import streamlit as st
from datetime import date
from utils import load_user_sports, update_sport_entries, get_weekly_progress

st.title("Enregistrer une nouvelle performance")
st.divider()

data = load_user_sports()

if not data:
    st.warning("Vous devez d'abord créer un sport.")
    if st.button("Créer un sport", type="primary"):
        st.switch_page("pages/add_sport.py")
else:
    # Sélection du sport en dehors du formulaire pour mise à jour dynamique
    selected_sport = st.session_state.get("selected_sport", list(data.keys())[0])
    sport = st.selectbox(
        "Sport",
        list(data.keys()),
        index=list(data.keys()).index(selected_sport) if selected_sport in data else 0,
        help="Sélectionnez le sport pour lequel enregistrer une performance",
        key="sport_selector"
    )

    # Sauvegarder la sélection
    st.session_state["selected_sport"] = sport

    with st.form("add_performance_form"):
        col_a, col_b = st.columns(2)
        with col_a:
            performance = st.number_input(
                f"Performance ({data[sport]['unit']})",
                min_value=0.0,
                step=1.0,
                help="Entrez votre performance"
            )
        with col_b:
            selected_date = st.date_input(
                "Date",
                value=date.today(),
                max_value=date.today(),
                help="Date de la performance"
            )

        submit_perf = st.form_submit_button("Enregistrer la performance", use_container_width=True,
                                            type="primary")

        if submit_perf:
            if performance > 0:
                date_str = selected_date.isoformat()
                entries = data[sport]["entries"]

                existing_entry = next((e for e in entries if e["date"] == date_str), None)

                if existing_entry:
                    if st.session_state.get("confirm_overwrite"):
                        existing_entry["value"] = performance
                        if update_sport_entries(sport, entries):
                            st.success("Performance mise à jour avec succès !")
                            st.session_state["confirm_overwrite"] = False
                            st.rerun()
                    else:
                        st.warning(
                            f"Une performance existe déjà pour le {date_str}. Cliquez à nouveau pour remplacer.")
                        st.session_state["confirm_overwrite"] = True
                else:
                    new_entry = {"date": date_str, "value": performance}
                    entries.append(new_entry)
                    if update_sport_entries(sport, entries):
                        st.success("Performance enregistrée avec succès !")
                        st.balloons()
                        st.session_state["confirm_overwrite"] = False
                        st.rerun()
            else:
                st.error("La performance doit être supérieure à 0")

# Sidebar avec stats et déconnexion
with st.sidebar:
    st.subheader("📊 Vue d'ensemble")

    total_sports = len(data)
    total_entries = sum(len(s["entries"]) for s in data.values())
    active_week = sum(1 for s in data.values() if get_weekly_progress(s["entries"]) > 0)

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Sports", total_sports)
    with col2:
        st.metric("Séances totales", total_entries)

    st.metric("Actifs cette semaine", f"{active_week}/{total_sports}" if total_sports > 0 else "0")

    st.divider()
    if st.button("Se déconnecter", use_container_width=True):
        st.logout()