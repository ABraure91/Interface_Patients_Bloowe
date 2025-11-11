# logic.py
# Logique de session, filtres, seuils, actions simulées

from __future__ import annotations
import pandas as pd
import streamlit as st

import data

# ----------------------- État & Sélection -----------------------------------

def init_state(db: dict) -> None:
    if "selected_patient_id" not in st.session_state:
        st.session_state.selected_patient_id = db["patients"][0]["id"]
    if "selected_doctor_id" not in st.session_state:
        st.session_state.selected_doctor_id = None
    if "date_to" not in st.session_state:
        st.session_state.date_to = pd.Timestamp.today().date()
    if "date_from" not in st.session_state:
        st.session_state.date_from = (pd.Timestamp.today() - pd.Timedelta(days=29)).date()
    if "last_export" not in st.session_state:
        st.session_state.last_export = None

def select_patient(pid: str) -> None:
    st.session_state.selected_patient_id = pid

def select_doctor(did: str) -> None:
    st.session_state.selected_doctor_id = did

# ----------------------- Métriques / Aides ----------------------------------

def trend_vs_days(df: pd.DataFrame, days: int, col: str) -> float:
    if len(df) < days + 1:
        return 0.0
    latest = float(df[col].iloc[-1])
    past = float(df[col].iloc[-days-1])
    if past == 0:
        return 0.0
    return (latest - past) / abs(past) * 100.0

def risk_status(value: float, threshold: float = 70.0) -> str:
    if value >= threshold:
        return "danger"
    if value >= max(threshold - 15, 0):
        return "warn"
    return "ok"

# ----------------------- Actions simulées -----------------------------------

def can_export_patient(pid: str) -> tuple[bool, str]:
    """Dans ce POC l'export est toujours autorisé (explication fournie)."""
    return True, "Autorisation simulée : export disponible pour téléchargement."

def simulate_delete_account(db: dict, pid: str) -> None:
    p = data.get_patient(db, pid)
    p["active"] = False  # masque le patient de la sélection (POC)

