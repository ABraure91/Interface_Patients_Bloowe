# ui_components.py
# Composants UI réutilisables (cartes, badges, graphes, messages)

import altair as alt
import pandas as pd
import streamlit as st
from typing import Optional

# ----------------------- Badges, alertes, cartes ----------------------------

def badge(text: str, level: str = "neutral") -> str:
    """Retourne un badge HTML."""
    cls = {"ok":"badge-ok","warn":"badge-warn","danger":"badge-danger","muted":"badge-muted","neutral":"badge"}\
        .get(level, "badge")
    return f'<span class="{cls}">{text}</span>'

def alert_block(title: str, content: str, level: str = "ok", right: Optional[str] = None):
    right_html = f'<div>{right}</div>' if right else ""
    html = f"""
<div class="card alert-{level}">
  <div style="display:flex;justify-content:space-between;align-items:center;">
    <div><div class="muted">{title}</div><div style="font-weight:700;font-size:1.6rem;">{content}</div></div>
    {right_html}
  </div>
</div>
"""
    st.markdown(html, unsafe_allow_html=True)

def resource_card(res: dict, show_meta: bool = False):
    meta = f'<div class="muted">{res["type"]} • {pd.to_datetime(res["date"]).date()}</div>' if show_meta else ""
    with st.expander(f"🧠 {res['title']}", expanded=False):
        st.markdown(meta, unsafe_allow_html=True)
        st.markdown(res["content"])

def conversation_row(doc: dict, last_text: str, unread: int):
    cols = st.columns([3, 6, 1])
    cols[0].markdown(f"**{doc['prenom']} {doc['nom']}**  \n{doc['specialite']}")
    cols[1].markdown(f'<div class="muted">{last_text}</div>', unsafe_allow_html=True)
    cols[2].markdown(badge(f"{unread} non lus", "warn") if unread else badge("0", "muted"), unsafe_allow_html=True)

# ----------------------- Graphiques -----------------------------------------

def sparkline(df: pd.DataFrame, y: str, title: str = ""):
    if df.empty: return
    ch = alt.Chart(df).mark_line().encode(
        x=alt.X("date:T", axis=None), y=alt.Y(f"{y}:Q", axis=None)
    ).properties(height=60)
    st.altair_chart(ch, use_container_width=True)
    if title:
        st.caption(title)

def chart_line(df: pd.DataFrame, y: str, title: str):
    if df.empty: return
    ch = alt.Chart(df).mark_line().encode(
        x=alt.X("date:T", title="Date"),
        y=alt.Y(f"{y}:Q", title=None),
        tooltip=["date:T", alt.Tooltip(f"{y}:Q", format=".2f")]
    ).properties(height=220, title=title)
    st.altair_chart(ch, use_container_width=True)

def chart_bar(df: pd.DataFrame, y: str, title: str):
    if df.empty: return
    ch = alt.Chart(df).mark_bar().encode(
        x=alt.X("date:T", title="Date"),
        y=alt.Y(f"{y}:Q", title=None),
        tooltip=["date:T", alt.Tooltip(f"{y}:Q", format=".2f")]
    ).properties(height=220, title=title)
    st.altair_chart(ch, use_container_width=True)

def chart_multi_line(df: pd.DataFrame, y_columns: list[tuple[str, str]], title: str):
    if df.empty: return
    melt = df.melt(id_vars=["date"], value_vars=[c for c, _ in y_columns], var_name="mesure", value_name="valeur")
    mapping = {c: label for c, label in y_columns}
    melt["mesure"] = melt["mesure"].map(mapping)
    ch = alt.Chart(melt).mark_line().encode(
        x=alt.X("date:T"),
        y=alt.Y("valeur:Q"),
        color=alt.Color("mesure:N", legend=alt.Legend(title=None)),
        tooltip=["date:T", "mesure:N", alt.Tooltip("valeur:Q", format=".2f")]
    ).properties(height=260, title=title)
    st.altair_chart(ch, use_container_width=True)

# ----------------------- Chat (liste de messages) ---------------------------

def message_list(msgs: list[dict], current: str = "patient"):
    """Affichage type bulles (patient / docteur)."""
    st.markdown('<div class="chat">', unsafe_allow_html=True)
    for m in msgs:
        side = "me" if m["sender"] == current else "other"
        who = "Moi" if side == "me" else "Praticien"
        time = pd.to_datetime(m["timestamp"]).strftime("%d/%m %H:%M")
        st.markdown(
            f"""
<div class="msg {side}">
  <div class="bubble">{m['text']}</div>
  <div class="meta">{who} • {time}</div>
</div>
""",
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)

