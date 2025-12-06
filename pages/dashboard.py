# pages/dashboard.py
import streamlit as st
from utils import load_user_sports, calculate_stats, calculate_streak, get_weekly_progress

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

    cols = st.columns(4)
    with cols[0]:
        st.metric("Sports actifs", len(data))
    with cols[1]:
        st.metric("Total séances", sum(len(s["entries"]) for s in data.values()))
    with cols[2]:
        max_streak = max([calculate_streak(s["entries"]) for s in data.values()], default=0)
        st.metric("Meilleure série", f"{max_streak} jours")
    with cols[3]:
        week_total = sum(get_weekly_progress(s["entries"]) for s in data.values())
        st.metric("Cette semaine", f"{week_total} séances")

    st.divider()

    # Cartes de sports
    st.subheader("Vos sports")

    cols = st.columns(3)
    for idx, (sport_name, sport_data) in enumerate(data.items()):
        with cols[idx % 3]:
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

# Sidebar avec stats et déconnexion
with st.sidebar:
    st.subheader("📊 Vue d'ensemble")

    total_sports = len(data)
    total_entries = sum(len(s["entries"]) for s in data.values())
    active_week = sum(get_weekly_progress(s["entries"]) > 0 for s in data.values())

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Sports", total_sports)
    with col2:
        st.metric("Séances totales", total_entries)

    st.metric("Actifs cette semaine", f"{active_week}/{total_sports}" if total_sports > 0 else "0")

    st.divider()
    if st.button("Se déconnecter", use_container_width=True):
        st.logout()