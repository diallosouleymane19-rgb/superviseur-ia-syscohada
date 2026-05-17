# -*- coding: utf-8 -*-
"""
Module d'authentification — SMD Consulting
Supporte : st.secrets (Streamlit Cloud) ET fallback local
"""
import streamlit as st

# Identifiants de fallback (développement local uniquement)
# Sur Streamlit Cloud, définir dans Settings → Secrets :
#   [users]
#   "smdconsulting" = "votre_mot_de_passe"
_FALLBACK_USERS = {
    "smdconsulting": "compta2026",
}

def _get_users() -> dict:
    """Récupère les utilisateurs depuis st.secrets ou le fallback local."""
    try:
        users = st.secrets.get("users", {})
        if users:
            return dict(users)
    except Exception:
        pass
    return _FALLBACK_USERS


def login(email: str, password: str) -> bool:
    """Authentifie un utilisateur."""
    users = _get_users()
    email = email.strip()
    if email in users and users[email] == password.strip():
        st.session_state["authenticated"] = True
        st.session_state["user_email"] = email
        st.session_state["role"] = "admin"
        st.session_state["nom"] = email.split("@")[0]
        return True
    return False


def logout():
    """Déconnexion complète."""
    for key in ["authenticated", "user_email", "role", "nom", "login_time"]:
        st.session_state.pop(key, None)


def is_connecte() -> bool:
    """Vérifie si l'utilisateur est authentifié."""
    return st.session_state.get("authenticated", False)
