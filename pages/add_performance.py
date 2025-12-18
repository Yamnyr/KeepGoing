# pages/add_performance.py
import streamlit as st
import pandas as pd
from datetime import date
from utils import (load_user_sports, update_sport_entries, get_weekly_progress,
                   calculate_stats, get_monthly_progress, render_sidebar)

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

    # Afficher les statistiques du sport sélectionné
    entries = data[sport]["entries"]

    if entries:
        st.subheader(f"Statistiques - {sport}")
        stats = calculate_stats(entries)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Dernière performance", f"{stats['last']} {data[sport]['unit']}")
        with col2:
            st.metric("Meilleure performance", f"{stats['best']} {data[sport]['unit']}")
        with col3:
            st.metric("Moyenne", f"{stats['avg']:.1f} {data[sport]['unit']}")
        with col4:
            st.metric("Total séances", stats['total'])

        st.divider()

    # Formulaire d'ajout
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

    # Historique des performances
    if entries:
        st.divider()
        st.subheader("Historique des performances")

        # Trier par date décroissante
        sorted_entries = sorted(entries, key=lambda x: x["date"], reverse=True)

        # Créer un DataFrame pour l'affichage
        df_history = pd.DataFrame(sorted_entries)
        df_history["date"] = pd.to_datetime(df_history["date"]).dt.strftime('%d/%m/%Y')
        df_history["value"] = df_history["value"].apply(lambda x: f"{x} {data[sport]['unit']}")
        df_history.columns = ["Date", "Performance"]

        # Afficher les 10 dernières performances
        display_count = min(10, len(df_history))
        st.dataframe(
            df_history.head(display_count),
            use_container_width=True,
            hide_index=True
        )

        if len(df_history) > 10:
            st.caption(
                f"Affichage des 10 dernières sur {len(df_history)} performances. Voir toutes les performances dans la section Analyse.")

# Sidebar avec stats et déconnexion

render_sidebar(data)