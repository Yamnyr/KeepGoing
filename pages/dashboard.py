# pages/dashboard.py
import streamlit as st
import pandas as pd
import altair as alt
from utils import (load_user_sports, calculate_stats, calculate_streak,
                   get_weekly_progress, get_monthly_progress, get_user_level,
                   get_activity_by_period, render_sidebar)

st.title("KeepGoing - Tableau de bord")
st.write("Suivez vos performances et progressez dans vos activités sportives")
st.divider()

data = load_user_sports()

if not data:
    st.info("Bienvenue sur KeepGoing ! Commencez par ajouter votre premier sport.")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Ajouter mon premier sport", use_container_width=True, type="primary"):
            st.switch_page("pages/add_sport.py")
else:
    # Statistiques globales
    st.subheader("Statistiques globales")

    total_sessions = sum(len(s["entries"]) for s in data.values())
    week_total = sum(get_weekly_progress(s["entries"]) for s in data.values())
    month_total = sum(get_monthly_progress(s["entries"]) for s in data.values())
    max_streak = max([calculate_streak(s["entries"]) for s in data.values()], default=0)

    # Niveau utilisateur
    level_info = get_user_level(total_sessions)

    cols = st.columns(5)
    with cols[0]:
        st.metric("Sports actifs", len(data))
    with cols[1]:
        st.metric("Total séances", total_sessions)
    with cols[2]:
        st.metric("Ce mois", f"{month_total} séances")
    with cols[3]:
        st.metric("Cette semaine", f"{week_total} séances")
    with cols[4]:
        st.metric("Meilleure série", f"{max_streak} jours")

    # Système de niveau
    st.subheader(f"{level_info['emoji']} Niveau : {level_info['name']}")
    if level_info['next_threshold']:
        st.progress(level_info['progress'] / 100)
        st.caption(f"{level_info['current']} / {level_info['next_threshold']} séances pour le niveau suivant")
    else:
        st.success("🎉 Niveau maximum atteint !")

    st.divider()

    # Cartes de sports avec bouton d'ajout de performance
    st.subheader("Vos sports")

    cols = st.columns(3)
    for idx, (sport_name, sport_data) in enumerate(data.items()):
        with cols[idx % 3]:

            with st.container(border=True):
                st.subheader(sport_name)

                entries = sport_data["entries"]

                if entries:
                    stats = calculate_stats(entries)
                    streak = calculate_streak(entries)
                    week_progress = get_weekly_progress(entries)

                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Dernière", f"{stats['last']} {sport_data['unit']}")
                        st.metric("Meilleure", f"{stats['best']} {sport_data['unit']}")
                    with col2:
                        st.metric("Moyenne", f"{stats['avg']:.1f} {sport_data['unit']}")
                        st.metric("Série actuelle", f"{streak} jours")

                    # Barre de progression hebdomadaire
                    if week_progress > 0:
                        st.progress(min(week_progress / 7, 1.0))
                        st.caption(f"{week_progress} séance(s) cette semaine")
                    else:
                        st.caption("Aucune séance cette semaine")

                    # Objectif
                    if sport_data.get("goal"):
                        goal_progress = (stats['last'] / sport_data['goal']) * 100
                        st.progress(min(goal_progress / 100, 1.0))
                        st.caption(f"Objectif : {sport_data['goal']} {sport_data['unit']} ({goal_progress:.0f}%)")
                else:
                    st.info("Aucune performance enregistrée")

                # Bouton pour ajouter une performance
                if st.button(f"Nouvelle performance", key=f"add_{sport_name}", use_container_width=True):
                    st.session_state["selected_sport"] = sport_name
                    st.switch_page("pages/add_performance.py")

    # Graphique d'activité
    st.subheader("Activité sur la période")

    period_choice = st.radio("Période", ["Semaine", "Mois", "Année"], horizontal=True)
    period_map = {"Semaine": "week", "Mois": "month", "Année": "year"}

    activity_data = get_activity_by_period(data, period_map[period_choice])

    if activity_data:
        df_activity = pd.DataFrame(list(activity_data.items()), columns=["Période", "Séances"])

        chart = alt.Chart(df_activity).mark_bar(color="#1f77b4").encode(
            x=alt.X("Période:N", title=""),
            y=alt.Y("Séances:Q", title="Nombre de séances"),
            tooltip=["Période", "Séances"]
        ).properties(height=300)

        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("Aucune donnée d'activité disponible")

    st.divider()
# Sidebar enrichie avec statistiques complètes
render_sidebar(data)