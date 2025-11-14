# data.py
# Génération et accès aux données factices (patients, séries, messages, ressources)

from __future__ import annotations
import random
import io
import numpy as np
import pandas as pd
from faker import Faker

# Facultatif : si ton modèle attend d’autres noms de colonnes, mappe-les ici.
FEATURE_RENAME = {
    # "hemoglobine_g_dl": "hemoglobin",
    # "hematocrite_l_l": "hematocrit",
    # "hydratation_verres": "hydration_glasses",
    # "kcal_total": "effort_kcal",
    # "kcal_sport": "sport_kcal",
    # "sommeil_minutes": "sleep_min",
    # "sommeil_qualite": "sleep_quality",
    # "stress_niveau": "stress",
    # "douleur_niveau": "pain",
}

def _infer_genotype(profile: str) -> str:
    """Extrait le génotype à partir de la chaîne profil."""
    s = (profile or "").upper()
    if " SC" in s or s.endswith(" SC"):
        return "SC"
    if " AS" in s or "PORTEUR" in s:
        return "AS"
    return "SS"  # par défaut

# ----------------------- Génération -----------------------------------------

def init_fake_data(seed: int = 42, n_patients: int = 12, n_days: int = 60) -> dict:
    """Génère un jeu complet de données factices."""
    rng = np.random.RandomState(seed)
    Faker.seed(seed)
    random.seed(seed)
    fake = Faker("fr_FR")

    # Médecins fictifs
    doctors = []
    specs = ["Hématologue", "Généraliste", "Interniste"]
    for i in range(3):
        doctors.append({
            "id": f"D{i+1:03d}",
            "prenom": fake.first_name(),
            "nom": fake.last_name().upper(),
            "specialite": random.choice(specs),
            "email": fake.email(),
        })

    # Ressources / Conseils
    res_types = ["Hydratation", "Activité", "Sommeil", "Douleur", "Prévention"]
    resources = []
    for i in range(12):
        rtype = random.choice(res_types)
        resources.append({
            "id": f"R{i+1:03d}",
            "title": f"{rtype} – {fake.sentence(nb_words=4).rstrip('.')}",
            "type": rtype,
            "content": "\n\n".join(fake.paragraphs(nb=3)),
            "personalized_keys": random.sample(["risk_high", "hydration_low", "sleep_low", "pain_high", "stress_high"], k=2),
            "date": pd.Timestamp.today() - pd.Timedelta(days=random.randint(0, 120)),
            "visibility": "Publié",
        })

    patients, series, messages = [], {}, []
    start_id = 1000

    for i in range(n_patients):
        sexe = random.choice(["F", "M"])
        pid = f"P{start_id+i}"
        patient = {
            "id": pid,
            "prenom": fake.first_name_female() if sexe == "F" else fake.first_name_male(),
            "nom": fake.last_name().upper(),
            "email": fake.email(),
            "sexe": sexe,
            "age": random.randint(16, 65),
            "taille_cm": random.randint(150, 195),
            "poids_kg": random.randint(50, 95),
            "ville": fake.city(),
            "profile": random.choice(["Drépanocytose SS", "Drépanocytose SC", "Porteur AS"]),
            "thresholds": {"risk_alert": 70},
            "notification_prefs": {"risk_alerts": True, "daily_reminder": True, "tips": True},
            "active": True,
            "sharing": [],  # liste par médecin
        }
        # Partages initiaux (1–2 médecins)
        dsel = random.sample(doctors, k=random.randint(1, 2))
        for d in dsel:
            patient["sharing"].append({
                "doctor_id": d["id"],
                "data_access": {
                    "risque": True, "sanguins": True, "hydratation": True, "activite": True,
                    "sommeil": random.choice([True, False]), "stress": random.choice([True, False]), "douleur": True
                }
            })
        patients.append(patient)

        # Séries 30–60 jours
        geno = _infer_genotype(patient["profile"])
        series[pid] = _generate_series(n_days=n_days, seed=seed+i, genotype_code=geno)

        # Messages (≥40 au total)
        nb = random.randint(2, 6)
        base_time = pd.Timestamp.today() - pd.Timedelta(days=10)
        did = dsel[0]["id"]
        for k in range(nb):
            sender = "doctor" if k % 2 == 0 else "patient"
            messages.append({
                "id": f"M{pid}{k+1:03d}",
                "patient_id": pid,
                "doctor_id": did,
                "sender": sender,
                "text": fake.sentence(nb_words=12),
                "timestamp": base_time + pd.Timedelta(days=k) + pd.Timedelta(minutes=random.randint(0, 11*60)),
                "read_by_patient": sender == "patient",
                "read_by_doctor": sender == "doctor",
            })

    return {"patients": patients, "series": series, "messages": messages, "doctors": doctors, "resources": resources}

def _generate_series(n_days: int = 60, seed: int = 0, genotype_code: str = "SS") -> pd.DataFrame:
    rng = np.random.RandomState(seed)
    end = pd.Timestamp.today().normalize()
    dates = pd.date_range(end=end, periods=n_days, freq="D")

    # --- Risque simulé (fallback) : on le calcule d'abord, et on le remplacera par le modèle si dispo
    risk_sim = [rng.uniform(20, 60)]
    for _ in range(1, n_days):
        risk_sim.append(np.clip(risk_sim[-1] + rng.normal(0, 4), 0, 100))

    # --- Autres mesures factices
    df = pd.DataFrame({
        "date": dates,
        "risque": np.round(risk_sim, 1),
        "hemoglobine_g_dl": np.clip(rng.normal(9.5, 1.1, size=n_days), 6.5, 12.5).round(1),
        "hematocrite_l_l": np.clip(rng.normal(0.32, 0.05, size=n_days), 0.2, 0.45).round(3),
        "hydratation_verres": np.clip(rng.poisson(6, size=n_days), 0, 12),
        "kcal_total": np.clip(rng.normal(2100, 300, size=n_days), 1200, 4000).round(0),
        "kcal_sport": np.clip(rng.normal(180, 120, size=n_days), 0, 800).round(0),
        "sommeil_minutes": np.clip(rng.normal(420, 60, size=n_days), 240, 600).round(0),
        "sommeil_qualite": rng.randint(1, 6, size=n_days),
        "stress_niveau": rng.randint(1, 6, size=n_days),
        "douleur_niveau": rng.randint(0, 11, size=n_days),
    })

    # --- Colonnes nécessaires au modèle
    df["Genotype"] = genotype_code

    # Si nécessaire, renommer pour coller aux noms attendus par le .pkl
    df_for_model = df.rename(columns=FEATURE_RENAME, errors="ignore").copy()

    # --- ⚙️ Remplacer 'risque' par la prédiction du modèle (si possible)
    try:
        keras_path = str(KERAS_PATH) if KERAS_PATH.exists() else None
        pred = predict_patient_timeseries(df_for_model, str(PKL_PATH), keras_path, alpha=0.6)
        # 'pred' est en 0..100 – on le met dans la colonne 'risque'
        df["risque"] = pred.astype(float).round(1)
    except Exception as e:
        # Fallback silencieux : on conserve le risque simulé si le modèle ne charge pas
        # (tu peux aussi logguer/afficher un avertissement côté UI)
        pass

    return df

# ----------------------- Accès / utilitaires --------------------------------

def list_patients(db: dict) -> list[dict]:
    return db["patients"]

def get_patient(db: dict, pid: str) -> dict:
    return next(p for p in db["patients"] if p["id"] == pid)

def get_series(db: dict, pid: str) -> pd.DataFrame:
    return db["series"][pid].copy()

def add_daily_entry(db: dict, pid: str, **kwargs) -> dict:
    """Ajoute/écrase la ligne du jour avec les valeurs fournies (ou aléatoires)."""
    df = db["series"][pid].copy()
    today = pd.Timestamp.today().normalize()
    df = df[df["date"] != today]

    # Entrées (fallback aléatoire raisonnable)
    pain = int(kwargs.get("douleur_niveau", np.random.randint(0, 10)))
    stress = int(kwargs.get("stress_niveau", np.random.randint(1, 5)))
    sleep = int(kwargs.get("sommeil_minutes", np.random.randint(300, 540)))
    water = int(kwargs.get("hydratation_verres", np.random.randint(2, 12)))

    # Petit modèle synthétique de risque (POC)
    prev = float(df.iloc[-1]["risque"])
    risk = prev + (pain - 5) * 2 + (stress - 3) * 2 + (-1 if water > 6 else 1) * 2 + (-1 if sleep >= 420 else 2)
    risk = float(np.clip(risk + np.random.randn() * 2, 0, 100))

    row = {
        "date": today,
        "risque": round(risk, 1),
        "hemoglobine_g_dl": float(kwargs.get("hemoglobine_g_dl", np.random.uniform(7.5, 11.5))),
        "hematocrite_l_l": float(kwargs.get("hematocrite_l_l", np.random.uniform(0.25, 0.40))),
        "hydratation_verres": water,
        "kcal_total": int(kwargs.get("kcal_total", np.random.uniform(1700, 2800))),
        "kcal_sport": int(kwargs.get("kcal_sport", np.random.uniform(0, 500))),
        "sommeil_minutes": sleep,
        "sommeil_qualite": int(kwargs.get("sommeil_qualite", np.random.randint(1, 6))),
        "stress_niveau": stress,
        "douleur_niveau": pain,
    }
    new_df = pd.concat([df, pd.DataFrame([row])], ignore_index=True).sort_values("date")
    # --- Tentative de recalcul via modèle pour la dernière ligne
    try:
        geno = _infer_genotype(get_patient(db, pid)["profile"])
        tmp = new_df.copy()
        tmp["Genotype"] = geno
        tmp_for_model = tmp.rename(columns=FEATURE_RENAME, errors="ignore")
        keras_path = str(KERAS_PATH) if KERAS_PATH.exists() else None
        pred = predict_patient_timeseries(tmp_for_model, str(PKL_PATH), keras_path, alpha=0.6)
        # Remplace le risque de la dernière ligne par la prédiction du modèle
        new_df.loc[new_df.index[-1], "risque"] = float(pred.iloc[-1])
        row["risque"] = float(pred.iloc[-1])
    except Exception:
        # si le modèle échoue, on garde la valeur heuristique déjà dans 'row' / 'new_df'
        pass
    db["series"][pid] = new_df
    return row

# --- Messages / conversations ---

def get_doctor(db: dict, did: str) -> dict | None:
    for d in db["doctors"]:
        if d["id"] == did:
            return d
    return None

def get_conversations(db: dict, pid: str) -> list[dict]:
    convs = {}
    for m in db["messages"]:
        if m["patient_id"] != pid:
            continue
        did = m["doctor_id"]
        convs.setdefault(did, {"doctor": get_doctor(db, did), "last": None, "unread": 0})
        if (convs[did]["last"] is None) or (m["timestamp"] > convs[did]["last"]["timestamp"]):
            convs[did]["last"] = m
        if m["sender"] == "doctor" and not m.get("read_by_patient", False):
            convs[did]["unread"] += 1
    return list(convs.values())

def get_messages(db: dict, pid: str, did: str) -> list[dict]:
    return sorted([m for m in db["messages"] if m["patient_id"] == pid and m["doctor_id"] == did],
                  key=lambda x: x["timestamp"])

def add_message(db: dict, pid: str, did: str, sender: str, text: str) -> dict:
    mid = f"M{pid}{len([m for m in db['messages'] if m['patient_id']==pid])+1:03d}"
    msg = {
        "id": mid, "patient_id": pid, "doctor_id": did, "sender": sender, "text": text,
        "timestamp": pd.Timestamp.now(), "read_by_patient": sender == "patient", "read_by_doctor": sender == "doctor"
    }
    db["messages"].append(msg)
    return msg

def mark_conversation_read_by_patient(db: dict, pid: str, did: str) -> None:
    for m in db["messages"]:
        if m["patient_id"] == pid and m["doctor_id"] == did:
            m["read_by_patient"] = True

# --- Ressources / Conseils ---

def get_personalized_resources(db: dict, pid: str, top_n: int = 3) -> list[dict]:
    df = get_series(db, pid)
    last = df.iloc[-1]
    keys = []
    if last["risque"] >= 70: keys.append("risk_high")
    if last["hydratation_verres"] <= 4: keys.append("hydration_low")
    if last["sommeil_minutes"] < 360: keys.append("sleep_low")
    if last["douleur_niveau"] >= 6: keys.append("pain_high")
    if last["stress_niveau"] >= 4: keys.append("stress_high")

    scored = []
    for r in db["resources"]:
        overlap = len(set(keys).intersection(r["personalized_keys"]))
        scored.append((overlap, r["date"], r))
    scored.sort(key=lambda t: (t[0], t[1]), reverse=True)
    return [r for _, __, r in scored[:top_n]]

def get_resources_global(db: dict) -> list[dict]:
    return sorted([r for r in db["resources"] if r["visibility"] == "Publié"], key=lambda r: r["date"], reverse=True)

# --- Profil & Partages (widgets de rendu simple) ---

import streamlit as st  # utilisé pour quelques formulaires inline dans le POC

def edit_profile(db: dict, pid: str) -> None:
    p = get_patient(db, pid)
    c1, c2, c3 = st.columns(3)
    with c1:
        p["prenom"] = st.text_input("Prénom", value=p["prenom"])
        p["sexe"] = st.selectbox("Sexe", ["F", "M"], index=0 if p["sexe"] == "F" else 1)
        p["taille_cm"] = st.number_input("Taille (cm)", 100, 220, p["taille_cm"])
    with c2:
        p["nom"] = st.text_input("Nom", value=p["nom"])
        p["age"] = st.number_input("Âge", 10, 100, p["age"])
        p["poids_kg"] = st.number_input("Poids (kg)", 30, 200, p["poids_kg"])
    with c3:
        p["email"] = st.text_input("E-mail", value=p["email"])
        p["ville"] = st.text_input("Ville", value=p["ville"])
        p["profile"] = st.selectbox("Profil", ["Drépanocytose SS", "Drépanocytose SC", "Porteur AS"],
                                    index=["Drépanocytose SS", "Drépanocytose SC", "Porteur AS"].index(p["profile"]))
    st.success("Profil mis à jour (mémoire uniquement).")

def manage_shares(db: dict, pid: str) -> None:
    p = get_patient(db, pid)
    # Affichage par médecin
    for share in p["sharing"]:
        did = share["doctor_id"]
        d = get_doctor(db, did)
        st.markdown(f"**{d['prenom']} {d['nom']}** – {d['specialite']}  \n*{d['email']}*")
        cols = st.columns(7)
        keys = ["risque", "sanguins", "hydratation", "activite", "sommeil", "stress", "douleur"]
        labels = ["Risque", "Sanguins", "Hydratation", "Activité", "Sommeil", "Stress", "Douleur"]
        for c, k, label in zip(cols, keys, labels):
            with c:
                share["data_access"][k] = st.checkbox(label, value=share["data_access"][k], key=f"{pid}-{did}-{k}")
        st.divider()

    with st.expander("➕ Ajouter un praticien (simulation)"):
        new_email = st.text_input("E-mail du praticien")
        spec = st.selectbox("Spécialité", ["Hématologue", "Généraliste", "Interniste"])
        if st.button("Inviter"):
            if new_email:
                # création d'un médecin factice et partage par défaut
                did = f"D{len(db['doctors'])+1:03d}"
                db["doctors"].append({"id": did, "prenom": "Nouveau", "nom": "PRATICIEN", "specialite": spec, "email": new_email})
                p["sharing"].append({"doctor_id": did, "data_access": {k: True for k in ["risque","sanguins","hydratation","activite","sommeil","stress","douleur"]}})
                st.success("Invitation envoyée (simulation).")
            else:
                st.warning("Saisissez une adresse e-mail.")

