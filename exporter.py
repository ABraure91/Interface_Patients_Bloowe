# exporter.py
# Exports .xlsx via pandas + openpyxl

import io
import pandas as pd
from openpyxl.utils import get_column_letter

import data

def export_patient_to_excel(db: dict, pid: str) -> bytes:
    patient = data.get_patient(db, pid)
    series = data.get_series(db, pid)
    messages = [m for m in db["messages"] if m["patient_id"] == pid]

    # Partages -> DataFrame
    shares = []
    for s in patient.get("sharing", []):
        row = {"doctor_id": s["doctor_id"], **s.get("data_access", {})}
        shares.append(row)
    df_shares = pd.DataFrame(shares) if shares else pd.DataFrame(columns=["doctor_id"])

    bio = io.BytesIO()
    with pd.ExcelWriter(bio, engine="openpyxl") as writer:
        pd.DataFrame([patient]).to_excel(writer, index=False, sheet_name="Profil")
        series.to_excel(writer, index=False, sheet_name="Series")
        pd.DataFrame(messages).to_excel(writer, index=False, sheet_name="Messages")
        df_shares.to_excel(writer, index=False, sheet_name="Partages")
    bio.seek(0)
    return bio.getvalue()

