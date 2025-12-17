# pages/analytics.py
import streamlit as st
import pandas as pd
import altair as alt
import json
from datetime import datetime
from utils import (load_user_sports, calculate_stats, get_weekly_progress,
                   update_sport_entries, delete_entry)

st.title("Analyse détaillée de vos performances")
st.divider()

data = load_user_sports()

if not data:
    st.info("Aucune donnée à analyser pour le moment.")
else:
    # Sélection du mode
    view_mode = st.radio(
        "Mode d'affichage",
        ["Sport individuel", "Comparaison globale", "Gestion des données"],
        horizontal=True
    )

    if view_mode == "Sport individuel":
        sport_graph = st.selectbox("Choisissez un sport à analyser", list(data.keys()))
        entries = data[sport_graph]["entries"]

        if entries:
            df = pd.DataFrame(entries)
            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values("date")

            # Graphique principal
            chart = (
                alt.Chart(df)
                .mark_line(point=True, size=3)
                .encode(
                    x=alt.X("date:T", title="Date", axis=alt.Axis(format="%d/%m")),
                    y=alt.Y("value:Q", title=f"Performance ({data[sport_graph]['unit']})"),
                    tooltip=[
                        alt.Tooltip("date:T", title="Date", format="%d/%m/%Y"),
                        alt.Tooltip("value:Q", title="Performance")
                    ],
                )
                .properties(
                    title=f"Évolution de {sport_graph}",
                    height=400
                )
            )

            st.altair_chart(chart, use_container_width=True)

            # Statistiques avancées
            stats = calculate_stats(entries)

            st.subheader("Statistiques détaillées")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Progression totale", f"{stats['progression']:.1f}%")
            with col2:
                st.metric("Écart-type", f"{pd.Series([e['value'] for e in entries]).std():.2f}")
            with col3:
                st.metric("Médiane", f"{stats['median']:.1f} {data[sport_graph]['unit']}")
            with col4:
                improvement = stats['last'] - entries[0]['value']
                st.metric("Amélioration", f"{improvement:+.1f} {data[sport_graph]['unit']}")

            # Tableau des performances
            st.subheader("Historique complet")
            df_display = df.copy()
            df_display['date'] = df_display['date'].dt.strftime('%d/%m/%Y')
            df_display['value'] = df_display['value'].apply(lambda x: f"{x} {data[sport_graph]['unit']}")
            st.dataframe(df_display[['date', 'value']], use_container_width=True, hide_index=True)

        else:
            st.info("Aucune donnée disponible pour ce sport.")

    elif view_mode == "Comparaison globale":
        all_data = []
        for sport_name, sport_data in data.items():
            for entry in sport_data["entries"]:
                all_data.append({
                    "sport": sport_name,
                    "date": entry["date"],
                    "value": entry["value"],
                    "unit": sport_data["unit"]
                })

        if all_data:
            df_all = pd.DataFrame(all_data)
            df_all["date"] = pd.to_datetime(df_all["date"])

            # Normalisation
            df_all["value_normalized"] = df_all.groupby("sport")["value"].transform(
                lambda x: (x - x.min()) / (x.max() - x.min()) if x.max() != x.min() else 0
            )

            chart_all = (
                alt.Chart(df_all)
                .mark_line(point=True, size=3)
                .encode(
                    x=alt.X("date:T", title="Date"),
                    y=alt.Y("value_normalized:Q", title="Performance normalisée (0-1)"),
                    color=alt.Color("sport:N", title="Sport"),
                    tooltip=["sport:N", "date:T", "value:Q", "unit:N"],
                )
                .properties(
                    title="Comparaison de tous les sports (valeurs normalisées)",
                    height=400
                )
            )

            st.altair_chart(chart_all, use_container_width=True)
            st.caption(
                "Les valeurs sont normalisées entre 0 et 1 pour permettre la comparaison entre différentes unités.")

            # Statistiques par sport
            st.subheader("Résumé par sport")
            summary_data = []
            for sport_name, sport_data in data.items():
                if sport_data["entries"]:
                    stats = calculate_stats(sport_data["entries"])
                    summary_data.append({
                        "Sport": sport_name,
                        "Séances": stats['total'],
                        "Meilleure": f"{stats['best']} {sport_data['unit']}",
                        "Moyenne": f"{stats['avg']:.1f} {sport_data['unit']}",
                        "Progression": f"{stats['progression']:.1f}%"
                    })

            if summary_data:
                st.dataframe(pd.DataFrame(summary_data), use_container_width=True, hide_index=True)

    else:  # Gestion des données
        st.subheader("Gestion et export des données")

        tab1, tab2 = st.tabs(["Modifier les données", "Exporter les données"])

        with tab1:
            sport_edit = st.selectbox("Sélectionner un sport", list(data.keys()), key="edit_sport")
            entries_edit = data[sport_edit]["entries"]

            if entries_edit:
                st.write(f"**{len(entries_edit)} performance(s) enregistrée(s)**")

                # Tableau avec édition
                df_edit = pd.DataFrame(entries_edit)
                df_edit["date"] = pd.to_datetime(df_edit["date"])
                df_edit = df_edit.sort_values("date", ascending=False)

                st.write("Modifier ou supprimer des performances :")

                for idx, row in df_edit.iterrows():
                    col1, col2, col3, col4 = st.columns([2, 2, 1, 1])

                    with col1:
                        st.text(row["date"].strftime("%d/%m/%Y"))
                    with col2:
                        new_value = st.number_input(
                            "Valeur",
                            value=float(row["value"]),
                            min_value=0.0,
                            step=1.0,
                            key=f"edit_{sport_edit}_{row['date'].isoformat()}",
                            label_visibility="collapsed"
                        )
                    with col3:
                        if st.button("Modifier", key=f"mod_{sport_edit}_{row['date'].isoformat()}"):
                            # Trouver et modifier l'entrée
                            date_str = row["date"].isoformat()
                            for entry in entries_edit:
                                if entry["date"] == date_str:
                                    entry["value"] = new_value
                                    break

                            if update_sport_entries(sport_edit, entries_edit):
                                st.success("Modifié !")
                                st.rerun()
                    with col4:
                        if st.button("🗑️", key=f"del_{sport_edit}_{row['date'].isoformat()}"):
                            if delete_entry(sport_edit, row["date"].isoformat()):
                                st.success("Supprimé !")
                                st.rerun()
            else:
                st.info("Aucune donnée à modifier pour ce sport.")

        with tab2:
            st.write("Exportez vos données dans différents formats")

            export_format = st.radio("Format d'export", ["JSON", "CSV"], horizontal=True)
            sport_export = st.selectbox("Sport à exporter", ["Tous les sports"] + list(data.keys()), key="export_sport")

            if sport_export == "Tous les sports":
                export_data = data
                filename = "keepgoing_all_sports"
            else:
                export_data = {sport_export: data[sport_export]}
                filename = f"keepgoing_{sport_export.lower().replace(' ', '_')}"

            if export_format == "JSON":
                json_str = json.dumps(export_data, indent=2, ensure_ascii=False)
                st.download_button(
                    label="Télécharger JSON",
                    data=json_str,
                    file_name=f"{filename}.json",
                    mime="application/json",
                    use_container_width=True
                )

                with st.expander("Aperçu des données JSON"):
                    st.code(json_str, language="json")

            else:  # CSV
                # Convertir en format plat pour CSV
                csv_data = []
                for sport_name, sport_data in export_data.items():
                    for entry in sport_data["entries"]:
                        csv_data.append({
                            "Sport": sport_name,
                            "Date": entry["date"],
                            "Performance": entry["value"],
                            "Unité": sport_data["unit"]
                        })

                if csv_data:
                    df_csv = pd.DataFrame(csv_data)
                    csv_str = df_csv.to_csv(index=False)

                    st.download_button(
                        label="📥 Télécharger CSV",
                        data=csv_str,
                        file_name=f"{filename}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )

                    with st.expander("Aperçu des données CSV"):
                        st.dataframe(df_csv, use_container_width=True)
                else:
                    st.info("Aucune donnée à exporter")

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