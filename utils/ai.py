# -*- coding: utf-8 -*-
"""
Appel API Mistral — SMD Consulting
Supporte : .env (local) ET st.secrets (Streamlit Cloud)
"""
import os
import requests
from pathlib import Path

# --- Chargement local via .env (si présent) ---
try:
    from dotenv import load_dotenv
    ROOT_DIR = Path(__file__).resolve().parent.parent
    load_dotenv(dotenv_path=ROOT_DIR / ".env")
except ImportError:
    pass

def _get_api_key() -> str:
    """Récupère la clé API : st.secrets en priorité, puis .env"""
    try:
        import streamlit as st
        key = st.secrets.get("MISTRAL_API_KEY", "")
        if key:
            return key
    except Exception:
        pass
    return os.getenv("MISTRAL_API_KEY", "")


def appel_mistral(prompt: str) -> str:
    """Envoie un prompt à Mistral et retourne la réponse."""
    api_key = _get_api_key()

    if not api_key:
        return (
            "❌ Clé API Mistral introuvable.\n"
            "• En local : fichier `.env` avec MISTRAL_API_KEY=votre_clé\n"
            "• Sur Streamlit Cloud : Settings → Secrets"
        )

    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "mistral-large-latest",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        if response.status_code != 200:
            return f"❌ Erreur API Mistral : HTTP {response.status_code} — {response.text[:300]}"
        return response.json()["choices"][0]["message"]["content"]
    except requests.exceptions.Timeout:
        return "❌ Timeout : l'API Mistral ne répond pas (> 60s). Réessayez."
    except Exception as e:
        return f"❌ Erreur inattendue : {e}"
