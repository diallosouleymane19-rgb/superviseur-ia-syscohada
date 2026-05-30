# -*- coding: utf-8 -*-
"""
auth.py — RevisionPro SYSCOHADA
Authentification : RBAC (smd_users.db) → ancienne DB (smd_syscohada.db) → secrets admin.
"""

import streamlit as st
from datetime import datetime


# ─── Helpers internes ─────────────────────────────────────────────────────────

def _set_session(email: str, role: str, nom: str, plan: str = "free",
                 cabinet: str = "", pays: str = "") -> None:
    """Hydrate st.session_state après connexion réussie."""
    st.session_state["authenticated"] = True
    st.session_state["user_email"]    = email
    st.session_state["role"]          = role
    st.session_state["nom"]           = nom
    st.session_state["plan"]          = plan
    st.session_state["cabinet"]       = cabinet
    st.session_state["pays_user"]     = pays
    st.session_state["login_time"]    = datetime.now().isoformat()


# ─── LOGIN ────────────────────────────────────────────────────────────────────

def login(email: str, password: str) -> bool:
    """
    Authentification en 3 étapes :
    1. Base RBAC (smd_users.db) — nouveaux utilisateurs
    2. Ancienne DB (smd_syscohada.db / Supabase) — utilisateurs existants
    3. Secrets admin (fallback SMD)
    """
    email = email.strip().lower()

    # ── Étape 1 : base RBAC ──────────────────────────────────────────────────
    try:
        from utils.auth_rbac import verifier_login, log_action
        user = verifier_login(email, password)
        if user:
            _set_session(
                email   = user["email"],
                role    = user.get("role", "client"),
                nom     = user.get("nom") or email.split("@")[0],
                plan    = user.get("plan", "free"),
                cabinet = user.get("cabinet", ""),
                pays    = user.get("pays", ""),
            )
            try:
                log_action(email, "login", app="syscohada")
            except Exception:
                pass
            return True
    except Exception:
        pass

    # ── Étape 2 : ancienne DB SYSCOHADA (utilisateurs existants) ─────────────
    try:
        from utils.database import verifier_mot_de_passe
        user = verifier_mot_de_passe(email, password)
        if user:
            _set_session(
                email   = user["email"],
                role    = user.get("role", "client"),
                nom     = user.get("nom") or email.split("@")[0],
                plan    = "free",        # plan par défaut pour anciens users
                cabinet = user.get("cabinet", ""),
                pays    = user.get("pays", ""),
            )
            return True
    except Exception:
        pass

    # ── Étape 3 : secrets admin (fallback hardcodé) ───────────────────────────
    _ADMIN_USERS = {"smdconsulting": "compta2026"}
    try:
        users = st.secrets.get("users", _ADMIN_USERS)
        if email in users and users[email] == password.strip():
            _set_session(
                email   = email,
                role    = "admin",
                nom     = email.split("@")[0],
                plan    = "enterprise",
                cabinet = "SMD Consulting",
            )
            return True
    except Exception:
        if email in _ADMIN_USERS and _ADMIN_USERS[email] == password.strip():
            _set_session(
                email   = email,
                role    = "admin",
                nom     = "SMD Consulting",
                plan    = "enterprise",
                cabinet = "SMD Consulting",
            )
            return True

    return False


# ─── SESSION ──────────────────────────────────────────────────────────────────

def is_connecte() -> bool:
    """Vérifie si une session valide est active (timeout 8h)."""
    if not st.session_state.get("authenticated", False):
        return False
    login_time = st.session_state.get("login_time")
    if login_time:
        try:
            delta = datetime.now() - datetime.fromisoformat(login_time)
            if delta.total_seconds() > 28800:  # 8 heures
                logout()
                st.warning("⏰ Session expirée. Veuillez vous reconnecter.")
                return False
        except Exception:
            pass
    return True


def logout() -> None:
    """Déconnexion complète."""
    keys = ["authenticated", "user_email", "role", "nom", "plan",
            "cabinet", "pays_user", "login_time"]
    for key in keys:
        st.session_state.pop(key, None)


# ─── Accesseurs session ───────────────────────────────────────────────────────

def get_role() -> str:
    return st.session_state.get("role", "client")


def get_nom() -> str:
    return st.session_state.get("nom", "Utilisateur")


def get_plan() -> str:
    return st.session_state.get("plan", "free")


def is_admin() -> bool:
    return get_role() == "admin"


def is_cabinet() -> bool:
    return get_role() in ("admin", "cabinet")
