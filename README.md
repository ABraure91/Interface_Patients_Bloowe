# Bloowe – App Patient (POC Streamlit)

Prototype **100 % autonome** de l’interface **patient** décrite dans la proposition commerciale.
Il illustre l’accueil (score de risque + saisie quotidienne), la **messagerie**, les **visualisations**, les **conseils**, les **paramètres** (notifications & seuils), la **gestion du partage** et l’**export**.

> ⚠️ **Avertissement**  
> Ce projet est une **démo / POC**.  
> Il **n’utilise aucune donnée de santé réelle** et **ne doit pas être utilisé en production**.  
> Aucune API ni base distante : tout est en mémoire locale.

---

## Installation & exécution

```bash
python -m venv .venv && source .venv/bin/activate  # macOS / Linux
# ou
.\.venv\Scripts\activate  # Windows

pip install -r requirements.txt
streamlit run app.py

