# app.py
# POC Streamlit – Interface Patient (Bloowe) – 100% autonome / données factices
# Langue: FR

import datetime as dt
from dateutil.relativedelta import relativedelta
import pandas as pd
import streamlit as st

import data
import logic
import styles
import ui_components as ui
import exporter

st.set_page_config(page_title="Bloowe – App Patient (POC)", page_icon="🩺", layout="wide")

# 1) Styles / Design System
styles.inject()

# 2) Initialisation des données (en session)
if "db" not in st.session_state:
    st.session_state.db = data.init_fake_data(seed=42, n_patients=12, n_days=60)

# 3) Initialisation de l'état applicatif
logic.init_state(st.session_state.db)

db = st.session_state.db
pid = st.session_state.selected_patient_id

# --- SIDEBAR (navigation + réglages POC) ------------------------------------
with st.sidebar:
    st.markdown("### 🩺 Bloowe – POC App Patient")
    # Sélection patient (démo)
    p_options = {f"{p['prenom']} {p['nom']} ({p['id']})": p["id"] for p in data.list_patients(db) if p.get("active", True)}
    sel_label = st.selectbox("Changer de patient (démo)", list(p_options.keys()),
                             index=list(p_options.values()).index(pid) if pid in p_options.values() else 0)
    logic.select_patient(p_options[sel_label])

    # Fenêtre temporelle globale
    col_a, col_b = st.columns(2)
    with col_a:
        st.session_state.date_from = st.date_input(
            "Début",
            st.session_state.date_from,
            max_value=dt.date.today()
        )
    with col_b:
        st.session_state.date_to = st.date_input(
            "Fin",
            st.session_state.date_to,
            min_value=st.session_state.date_from,
            max_value=dt.date.today()
        )

    # Export (simulation d’autorisation)
    st.markdown("---")
    if st.button("📤 Exporter les données (.xlsx)"):
        ok, msg = logic.can_export_patient(pid)
        if ok:
            xls = exporter.export_patient_to_excel(db, pid)
            st.session_state.last_export = xls
            st.success("Export prêt. Utilisez le bouton ci-dessous pour télécharger (simulation d’autorisation).")
        else:
            st.warning(msg)

    if st.session_state.get("last_export"):
        st.download_button(
            "⬇️ Télécharger l'export",
            data=st.session_state["last_export"],
            file_name=f"export_{pid}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    st.markdown("---")
    st.caption("**POC** – Aucune donnée réelle. Pas d'API. Tout fonctionne en local.")

# --- HEADER patient ----------------------------------------------------------
patient = data.get_patient(db, pid)
st.markdown(
    f"""
<div class="card" style="margin-top:0;">
  <div style="display:flex;justify-content:space-between;align-items:center;gap:1rem;flex-wrap:wrap;">
    <div>
      <div class="muted">Patient</div>
      <div style="font-weight:600;font-size:1.1rem;">{patient['prenom']} {patient['nom']}</div>
      <div class="muted">{patient['sexe']} • {patient['age']} ans • {patient['profile']}</div>
    </div>
    <div style="min-width:240px;">
      {ui.badge('ID '+patient['id'], 'neutral')}
    </div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

# --- TABS (tab bar type mobile) ---------------------------------------------
tabs = st.tabs(["🏠 Accueil", "💬 Conversations", "📈 Graphs", "🧠 Conseils", "☰ Menu"])

# ---------------------- TAB 1: ACCUEIL --------------------------------------
with tabs[0]:
    s_df = data.get_series(db, pid)
    s_df = s_df[(s_df["date"].dt.date >= st.session_state.date_from) & (s_df["date"].dt.date <= st.session_state.date_to)]

    last = s_df.iloc[-1]
    risk = float(last["risque"])
    trend_pct = logic.trend_vs_days(s_df, days=7, col="risque")
    status = logic.risk_status(risk, threshold=patient["thresholds"]["risk_alert"])

    # Score & tendance
    col1, col2 = st.columns([1, 2], vertical_alignment="center")
    with col1:
        ui.alert_block(
            title="Score de risque",
            content=f"{risk:.0f} %",
            level=status,
            right=ui.badge(("🡅 " if trend_pct > 0 else "🡇 " if trend_pct < 0 else "→ ") + f"{abs(trend_pct):.1f}% / 7j", "muted")
        )
    with col2:
        ui.sparkline(s_df, y="risque", title="Évolution du risque")

    # Alerte si dépassement du seuil
    if risk >= patient["thresholds"]["risk_alert"] and patient["notification_prefs"].get("risk_alerts", True):
        ui.alert_block("Alerte", "Votre score est supérieur au seuil défini. Pensez à consulter vos conseils et, si besoin, à contacter votre praticien.", level="danger")

    # Formulaire de saisie quotidienne
    with st.expander("📝 Formulaire quotidien (saisie simulée)", expanded=False):
        with st.form("form_daily"):
            c1, c2 = st.columns(2)
            with c1:
                hemoglobine = st.number_input("Taux d’hémoglobine (g/dL)", min_value=5.0, max_value=15.0, value=float(last["hemoglobine_g_dl"]), step=0.1)
                hematocrite = st.number_input("Taux d’hématocrite (L/L)", min_value=0.2, max_value=0.6, value=float(last["hematocrite_l_l"]), step=0.005)
                hydratation = st.slider("Hydratation (verres 25 cL)", 0, 15, int(last["hydratation_verres"]))
                kcal_total = st.number_input("Activité – Kcal quotidiennes", min_value=0, max_value=8000, value=int(last["kcal_total"]), step=10)
                kcal_sport = st.number_input("Activité – Kcal sport", min_value=0, max_value=3000, value=int(last["kcal_sport"]), step=10)
            with c2:
                sommeil_min = st.slider("Sommeil – durée (min)", 0, 720, int(last["sommeil_minutes"]))
                sommeil_q = st.slider("Sommeil – qualité (1 à 5)", 1, 5, int(last["sommeil_qualite"]))
                stress = st.slider("Niveau de stress (1 à 5)", 1, 5, int(last["stress_niveau"]))
                douleur = st.slider("Niveau de douleur (0 à 10)", 0, 10, int(last["douleur_niveau"]))

            submitted = st.form_submit_button("Enregistrer (POC)")
            if submitted:
                data.add_daily_entry(
                    db, pid,
                    hemoglobine_g_dl=hemoglobine,
                    hematocrite_l_l=hematocrite,
                    hydratation_verres=hydratation,
                    kcal_total=kcal_total, kcal_sport=kcal_sport,
                    sommeil_minutes=sommeil_min, sommeil_qualite=sommeil_q,
                    stress_niveau=stress, douleur_niveau=douleur
                )
                st.success("Données enregistrées (simulation, en mémoire uniquement).")

    # Conversations – aperçu
    st.markdown("### 💬 Conversations (aperçu)")
    convs = data.get_conversations(db, pid)
    if not convs:
        st.info("Aucune conversation.")
    else:
        for conv in convs[:2]:
            d = conv["doctor"]
            unread = conv["unread"]
            last_msg = conv["last"]["text"]
            ui.conversation_row(d, last_msg, unread)

    # Conseils – top 3 personnalisés
    st.markdown("### 🧠 Conseils personnalisés")
    for res in data.get_personalized_resources(db, pid, top_n=3):
        ui.resource_card(res)

# ---------------------- TAB 2: CONVERSATIONS --------------------------------
with tabs[1]:
    st.markdown("#### Mes conversations")
    convs = data.get_conversations(db, pid)
    if not convs:
        st.info("Aucune conversation.")
    else:
        # Sélecteur de conversation
        opts = {f"{c['doctor']['prenom']} {c['doctor']['nom']} – {c['doctor']['specialite']}": c['doctor']['id'] for c in convs}
        sel = st.selectbox("Choisir un praticien", list(opts.keys()))
        did = opts[sel]
        logic.select_doctor(did)

        # Liste des messages (et marquage lus)
        messages = data.get_messages(db, pid, did)
        data.mark_conversation_read_by_patient(db, pid, did)
        ui.message_list(messages, current="patient")

        # Saisie d'un nouveau message
        st.markdown("---")
        msg = st.text_input("Votre message")
        col_a, col_b = st.columns([1,1])
        with col_a:
            if st.button("Envoyer"):
                if msg.strip():
                    data.add_message(db, pid, did, sender="patient", text=msg.strip())
                    st.success("Message envoyé (simulation).")
                else:
                    st.warning("Veuillez saisir un message.")
        with col_b:
            st.caption("Les messages sont stockés uniquement en mémoire (POC).")

# ---------------------- TAB 3: GRAPHS ---------------------------------------
with tabs[2]:
    st.markdown("#### Visualisations")
    s_df = data.get_series(db, pid)
    s_df = s_df[(s_df["date"].dt.date >= st.session_state.date_from) & (s_df["date"].dt.date <= st.session_state.date_to)]

    # 1) Risque de crise
    ui.chart_line(s_df, y="risque", title="Risque de crise (%)")

    # 2) Taux sanguins (2 courbes)
    ui.chart_multi_line(
        s_df,
        y_columns=[("hemoglobine_g_dl", "Hémoglobine (g/dL)"), ("hematocrite_l_l", "Hématocrite (L/L)")],
        title="Taux sanguins"
    )

    # 3) Hydratation (histogramme)
    ui.chart_bar(s_df, y="hydratation_verres", title="Hydratation (verres/jour)")

    # 4) Activité physique
    ui.chart_multi_line(
        s_df,
        y_columns=[("kcal_total", "Kcal quotidiennes"), ("kcal_sport", "Kcal sport")],
        title="Activité"
    )

    # 5) Sommeil
    ui.chart_line(s_df, y="sommeil_minutes", title="Sommeil – durée (min)")
    ui.chart_bar(s_df, y="sommeil_qualite", title="Sommeil – qualité (1 à 5)")

    # 6) Stress & douleur (histogrammes)
    ui.chart_bar(s_df, y="stress_niveau", title="Stress (1 à 5)")
    ui.chart_bar(s_df, y="douleur_niveau", title="Douleur (0 à 10)")

# ---------------------- TAB 4: CONSEILS -------------------------------------
with tabs[3]:
    st.markdown("#### Conseils")
    sub = st.radio("Type de ressources", ["Personnalisés", "Globaux"], horizontal=True)
    if sub == "Personnalisés":
        resources = data.get_personalized_resources(db, pid, top_n=10)
    else:
        resources = data.get_resources_global(db)

    if not resources:
        st.info("Aucune ressource à afficher.")
    else:
        for res in resources:
            ui.resource_card(res, show_meta=True)

# ---------------------- TAB 5: MENU -----------------------------------------
with tabs[4]:
    menu = st.radio("Menu", ["Profil", "Paramètres", "Partage des données", "Infos légales", "Contact & bug", "Suppression de compte"], horizontal=True)

    if menu == "Profil":
        st.markdown("#### Mon profil")
        data.edit_profile(db, pid)  # rendu inline via widgets

    elif menu == "Paramètres":
        st.markdown("#### Paramètres")
        # Notifications
        st.subheader("Notifications")
        prefs = patient["notification_prefs"]
        c1, c2, c3 = st.columns(3)
        with c1:
            prefs["risk_alerts"] = st.toggle("Alerte risque élevé", value=prefs.get("risk_alerts", True))
        with c2:
            prefs["daily_reminder"] = st.toggle("Rappel de saisie quotidienne", value=prefs.get("daily_reminder", True))
        with c3:
            prefs["tips"] = st.toggle("Conseils contextuels", value=prefs.get("tips", True))
        # Seuils
        st.subheader("Seuils d’alerte")
        thr = st.slider("Seuil de risque élevé (%)", min_value=20, max_value=95, value=int(patient["thresholds"]["risk_alert"]))
        patient["thresholds"]["risk_alert"] = thr
        st.success("Préférences enregistrées (mémoire uniquement).")

    elif menu == "Partage des données":
        st.markdown("#### Mes partages (simulation)")
        data.manage_shares(db, pid)

    elif menu == "Infos légales":
        st.markdown("#### Infos légales (POC)")
        st.info("CGU / Mentions légales / Politique de confidentialité – placeholders (dans l’app finale : webview).")

    elif menu == "Contact & bug":
        st.markdown("#### Contact")
        with st.form("contact_form"):
            sujet = st.text_input("Sujet")
            message = st.text_area("Message")
            sent = st.form_submit_button("Envoyer")
            if sent:
                st.success("Message transmis (simulation).")

    elif menu == "Suppression de compte":
        st.markdown("#### Suppression de compte (simulation)")
        st.write("Pour supprimer votre compte, tapez **supprimer** puis validez. (POC : l’utilisateur est masqué)")
        confirm = st.text_input("Confirmation")
        if st.button("Supprimer mon compte"):
            if confirm.strip().lower() == "supprimer":
                logic.simulate_delete_account(db, pid)
                st.warning("Compte masqué (simulation). Sélectionnez un autre patient dans la sidebar.")
            else:
                st.error("Veuillez taper exactement « supprimer ».")


