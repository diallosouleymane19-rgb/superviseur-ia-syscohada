# -*- coding: utf-8 -*-
"""
Module d'authentification — SMD Consulting
Priorité : table Supabase users → st.secrets [users] → fallback admin local
"""
import streamlit as st


# ─── Comptes hardcodés (admin SMD uniquement, fallback si Supabase KO) ───────
_ADMIN_USERS = {
    "smdconsulting": "compta2026",
}


def _get_secrets_users() -> dict:
    """Lit les users depuis st.secrets [users]."""
    try:
        users = st.secrets.get("users", {})
        if users:
            return dict(users)
    except Exception:
        pass
    return _ADMIN_USERS


def login(email: str, password: str) -> bool:
    """
    Authentifie un utilisateur.
    Ordre de vérification :
    1. Table Supabase `users` (bcrypt)
    2. st.secrets [users] (mot de passe en clair — admin uniquement)
    """
    email = email.strip()

    # ── 1. Supabase users ──────────────────────────────────────────────────
    try:
        from utils.database import verifier_mot_de_passe
        user = verifier_mot_de_passe(email, password)
        if user:
            st.session_state["authenticated"] = True
            st.session_state["user_email"]    = user["email"]
            st.session_state["role"]          = user.get("role", "client")
            st.session_state["nom"]           = user.get("nom") or user["email"].split("@")[0]
            st.session_state["cabinet"]       = user.get("cabinet", "")
            st.session_state["pays_user"]     = user.get("pays", "")
            return True
    except Exception:
        pass

    # ── 2. st.secrets [users] (admin / fallback) ───────────────────────────
    secrets_users = _get_secrets_users()
    if email in secrets_users and secrets_users[email] == password.strip():
        st.session_state["authenticated"] = True
        st.session_state["user_email"]    = email
        st.session_state["role"]          = "admin"
        st.session_state["nom"]           = email.split("@")[0]
        st.session_state["cabinet"]       = "SMD Consulting"
        st.session_state["pays_user"]     = ""
        return True

    return False


def logout():
    """Déconnexion complète."""
    for key in ["authenticated", "user_email", "role", "nom",
                "cabinet", "pays_user", "login_time"]:
        st.session_state.pop(key, None)


def is_connecte() -> bool:
    """Vérifie si l'utilisateur est authentifié."""
    return st.session_state.get("authenticated", False)


def is_admin() -> bool:
    """Vérifie si l'utilisateur est admin."""
    return st.session_state.get("role") == "admin"
