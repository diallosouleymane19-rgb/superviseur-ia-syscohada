# -*- coding: utf-8 -*-
"""Module d'authentification multi-clients - SMD Consulting"""
import streamlit as st

# Identifiants clients
UTILISATEURS = {
    "smdconsulting@gmail.com": "SMDConsulting2026!",  # Admin SMD
    # Ajoute ici tes clients :
    # "client1@cabinet.com": "MotDePasse1!",
    # "client2@entreprise.com": "MotDePasse2!",
}

def login(email, password):
    """Authentifie un utilisateur"""
    if email.strip() in UTILISATEURS:
        if UTILISATEURS[email.strip()] == password.strip():
            st.session_state["authenticated"] = True
            st.session_state["user_email"] = email.strip()
            return True
    return False

def logout():
    """Déconnexion"""
    st.session_state["authenticated"] = False
    st.session_state["user_email"] = None

def is_connecte():
    """Vérifie si l'utilisateur est authentifié"""
    return st.session_state.get("authenticated", False)