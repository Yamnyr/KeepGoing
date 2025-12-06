# utils.py
import streamlit as st
import json
from datetime import date, datetime, timedelta
from supabase import create_client, Client


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


def calculate_streak(entries):
    """Calcule la série de jours consécutifs."""
    if not entries:
        return 0

    dates = sorted([datetime.fromisoformat(e["date"]).date() for e in entries], reverse=True)
    streak = 1

    for i in range(len(dates) - 1):
        diff = (dates[i] - dates[i + 1]).days
        if diff == 1:
            streak += 1
        else:
            break

    return streak if dates[0] >= date.today() - timedelta(days=1) else 0


def get_weekly_progress(entries):
    """Calcule le nombre de sessions cette semaine."""
    if not entries:
        return 0

    week_ago = date.today() - timedelta(days=7)
    return sum(1 for e in entries if datetime.fromisoformat(e["date"]).date() >= week_ago)


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