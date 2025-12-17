# utils.py
import streamlit as st
import json
from datetime import date, datetime, timedelta
from supabase import create_client, Client

# Unités de mesure disponibles
UNITS = {
    "s": "secondes",
    "min": "minutes",
    "h": "heures",
    "rep": "répétitions",
    "km": "kilomètres",
    "m": "mètres",
    "kg": "kilogrammes",
    "cal": "calories",
    "pts": "points"
}


def get_unit_display(unit_short):
    """Retourne l'abréviation de l'unité pour l'affichage."""
    return unit_short


def get_unit_full_name(unit_short):
    """Retourne le nom complet de l'unité."""
    return UNITS.get(unit_short, unit_short)


@st.cache_resource
def init_supabase() -> Client:
    """Initialise et retourne le client Supabase."""
    try:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"Erreur de connexion à Supabase : {str(e)}")
        st.stop()


def load_user_sports():
    """Charge les sports de l'utilisateur depuis Supabase."""
    supabase = init_supabase()
    try:
        response = supabase.table("sports").select("*").eq("user_email", st.user.email).execute()
        data = {}

        for row in response.data:
            raw_entries = row.get("entries", [])

            # Accepte string JSON OU liste
            if isinstance(raw_entries, str):
                try:
                    raw_entries = json.loads(raw_entries)
                except Exception:
                    raw_entries = []

            data[row["sport_name"]] = {
                "unit": row["unit"],
                "entries": raw_entries,
                "goal": row.get("goal")
            }

        return data

    except Exception as e:
        st.error(f"Erreur lors du chargement : {str(e)}")
        return {}


def save_sport(sport_name, unit, goal=None):
    """Ajoute un nouveau sport dans Supabase."""
    supabase = init_supabase()
    try:
        data = {
            "user_email": st.user.email,
            "sport_name": sport_name,
            "unit": unit,
            "entries": json.dumps([]),
            "goal": goal
        }
        supabase.table("sports").insert(data).execute()
        return True
    except Exception as e:
        st.error(f"Erreur : {str(e)}")
        return False


def update_sport_entries(sport_name, entries):
    """Met à jour les performances d'un sport."""
    supabase = init_supabase()
    try:
        supabase.table("sports").update({
            "entries": json.dumps(entries)
        }).eq("user_email", st.user.email).eq("sport_name", sport_name).execute()
        return True
    except Exception as e:
        st.error(f"Erreur : {str(e)}")
        return False


def delete_entry(sport_name, date_str):
    """Supprime une entrée spécifique d'un sport."""
    supabase = init_supabase()
    try:
        # Charger les données actuelles
        response = supabase.table("sports").select("entries").eq("user_email", st.user.email).eq("sport_name",
                                                                                                 sport_name).execute()

        if response.data:
            entries = response.data[0]["entries"]
            if isinstance(entries, str):
                entries = json.loads(entries)

            # Filtrer l'entrée à supprimer
            entries = [e for e in entries if e["date"] != date_str]

            # Mettre à jour
            supabase.table("sports").update({
                "entries": json.dumps(entries)
            }).eq("user_email", st.user.email).eq("sport_name", sport_name).execute()
            return True
    except Exception as e:
        st.error(f"Erreur : {str(e)}")
        return False


def calculate_streak(entries):
    if not entries:
        return 0

    dates = sorted(
        {datetime.fromisoformat(e["date"]).date() for e in entries}
    )

    best = streak = 1

    for i in range(1, len(dates)):
        if (dates[i] - dates[i - 1]).days == 1:
            streak += 1
            best = max(best, streak)
        else:
            streak = 1

    return best


def get_weekly_progress(entries):
    """Calcule le nombre de sessions cette semaine."""
    if not entries:
        return 0

    week_ago = date.today() - timedelta(days=7)
    return sum(1 for e in entries if datetime.fromisoformat(e["date"]).date() >= week_ago)


def get_monthly_progress(entries):
    """Calcule le nombre de sessions ce mois."""
    if not entries:
        return 0

    month_start = date.today().replace(day=1)
    return sum(1 for e in entries if datetime.fromisoformat(e["date"]).date() >= month_start)


def calculate_stats(entries):
    """Calcule les statistiques d'un sport."""
    if not entries:
        return None

    values = [e["value"] for e in entries]
    return {
        "last": values[-1],
        "best": max(values),
        "worst": min(values),
        "avg": sum(values) / len(values),
        "median": sorted(values)[len(values) // 2],
        "total": len(values),
        "progression": ((values[-1] / values[0] - 1) * 100) if len(values) > 1 else 0
    }


def get_user_level(total_sessions):
    """Calcule le niveau de l'utilisateur basé sur le nombre de séances."""
    levels = [
        (0, "Débutant", "🌱"),
        (10, "Novice", "🌿"),
        (25, "Amateur", "🌳"),
        (50, "Intermédiaire", "🏃"),
        (100, "Confirmé", "💪"),
        (200, "Expert", "🏆"),
        (400, "Maître", "⭐"),
        (800, "Légende", "👑")
    ]

    for i in range(len(levels) - 1, -1, -1):
        threshold, name, emoji = levels[i]
        if total_sessions >= threshold:
            next_threshold = levels[i + 1][0] if i < len(levels) - 1 else None
            return {
                "name": name,
                "emoji": emoji,
                "current": total_sessions,
                "threshold": threshold,
                "next_threshold": next_threshold,
                "progress": ((total_sessions - threshold) / (
                            next_threshold - threshold) * 100) if next_threshold else 100
            }

    return levels[0]


def get_activity_by_period(data, period="week"):
    """Retourne l'activité groupée par période."""
    all_entries = []
    for sport_name, sport_data in data.items():
        for entry in sport_data["entries"]:
            all_entries.append({
                "date": datetime.fromisoformat(entry["date"]),
                "sport": sport_name
            })

    if not all_entries:
        return {}

    activity = {}
    for entry in all_entries:
        if period == "week":
            # Semaine ISO (lundi = début)
            key = entry["date"].strftime("%Y-W%W")
        elif period == "month":
            key = entry["date"].strftime("%Y-%m")
        else:  # year
            key = entry["date"].strftime("%Y")

        activity[key] = activity.get(key, 0) + 1

    return dict(sorted(activity.items()))