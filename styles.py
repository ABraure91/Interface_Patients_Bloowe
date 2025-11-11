# styles.py
# Design System (tokens) + CSS d'interface

import streamlit as st

def inject():
    st.markdown(
        """
<style>
:root{
  --primary:#26C6DA;        /* Couleur principale (turquoise) */
  --bg:#F7FAFC;             /* Fond */
  --surface:#FFFFFF;        /* Cartes */
  --text:#1A202C;           /* Texte principal */
  --muted:#718096;          /* Texte atténué */
  --ok:#2F855A;             /* États */
  --warn:#D69E2E;
  --danger:#E53E3E;
  --radius:14px;            /* Rayon cartes */
  --shadow:0 4px 16px rgba(0,0,0,.06);
}

html, body, .stApp { background: var(--bg); color: var(--text); }

.card{
  background:var(--surface); border-radius:var(--radius); padding:1rem 1.2rem; 
  box-shadow:var(--shadow); margin:0.6rem 0;
}

.muted { color: var(--muted); font-size:.9rem; }

.badge, .badge-ok, .badge-warn, .badge-danger, .badge-muted{
  display:inline-block; padding:.25rem .6rem; border-radius:999px; font-size:.85rem;
  background:#EEF2F6; color:#334;
}
.badge-ok{ background: rgba(47,133,90,.12); color: var(--ok); }
.badge-warn{ background: rgba(214,158,46,.15); color: var(--warn); }
.badge-danger{ background: rgba(229,62,62,.15); color: var(--danger); }
.badge-muted{ background:#EDF2F7; color: var(--muted); }

/* Alert cards */
.alert-ok{ border-left:5px solid var(--ok); }
.alert-warn{ border-left:5px solid var(--warn); }
.alert-danger{ border-left:5px solid var(--danger); }

/* Chat */
.chat { display:flex; flex-direction:column; gap:.4rem; }
.msg { max-width: 85%; }
.msg.me { align-self:flex-end; }
.msg.other { align-self:flex-start; }
.msg .bubble{
  padding:.6rem .8rem; border-radius:14px; box-shadow:var(--shadow);
  background: var(--surface);
}
.msg.me .bubble{ background: rgba(38,198,218,.13); }
.msg .meta { font-size:.75rem; color:var(--muted); margin:.2rem .3rem; }

/* Streamlit tweaks */
section.main > div { padding-top: .5rem; }
.stTabs [role="tab"]{ padding: .65rem 1rem; font-weight:600; }
</style>
        """,
        unsafe_allow_html=True,
    )

# ⬆️ Pour personnaliser la charte : modifiez les variables CSS dans :root
#    (--primary, --bg, --surface, --text, --muted, --ok, --warn, --danger, --radius, --shadow)

