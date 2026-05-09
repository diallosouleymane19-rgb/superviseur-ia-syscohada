# -*- coding: utf-8 -*-
"""Module d'authentification - SMD Consulting SYSCOHADA"""
import streamlit as st

# Identifiants SYSCOHADA
VALID_USERNAME = "smdconsulting"
VALID_PASSWORD = "compta2026"

def login(email, password):
    """Authentifie un utilisateur"""
    if email.strip() == VALID_USERNAME and password.strip() == VALID_PASSWORD:
        st.session_state["authenticated"] = True
        st.session_state["user_email"] = email
        return True
    return False

def logout():
    """Déconnexion"""
    st.session_state["authenticated"] = False
    st.session_state["user_email"] = None

def is_connecte():
    """Vérifie si l'utilisateur est authentifié"""
    return st.session_state.get("authenticated", False)