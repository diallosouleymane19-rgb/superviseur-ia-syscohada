# -*- coding: utf-8 -*-
"""
Appel API Mistral — SMD Global Consulting LLC
Supporte : .env (local) ET st.secrets (Streamlit Cloud)
v2.1 : timeout 120s, retry x2, paramètre model, max_tokens
"""
import os
import time
import requests
from pathlib import Path

# --- Chargement local via .env (si présent) ---
try:
    from dotenv import load_dotenv
    ROOT_DIR = Path(__file__).resolve().parent.parent
    load_dotenv(dotenv_path=ROOT_DIR / ".env")
except ImportError:
    pass

# Modèles disponibles (du plus rapide au plus puissant)
MODEL_FAST   = "mistral-small-latest"   # ~5-10s  — analyses légères
MODEL_MEDIUM = "mistral-large-latest"   # ~30-90s — analyses complexes (défaut)

# Paramètres globaux
DEFAULT_TIMEOUT    = 120   # secondes
DEFAULT_MAX_TOKENS = 4096  # limite la longueur de reponse -> plus rapide
MAX_RETRIES        = 2     # tentatives supplementaires en cas d'echec

# =============================================================================
# RATE LIMITING PAR SESSION (protection couts API)
# =============================================================================
RATE_LIMITS = {
    "free":       10,
    "starter":    50,
    "pro":       200,
    "enterprise": -1,
    "demo":        5,
    "admin":      -1,
}


def _get_rate_key() -> str:
    from datetime import date
    try:
        import streamlit as st
        email = st.session_state.get("user_email", "anonymous")
    except Exception:
        email = "anonymous"
    return "_rl_" + email + "_" + date.today().isoformat()


def check_rate_limit() -> tuple:
    """Retourne (autorise, message, calls_today, limit)"""
    try:
        import streamlit as st
        plan  = st.session_state.get("plan", "free")
        limit = RATE_LIMITS.get(plan, RATE_LIMITS["free"])
        key   = _get_rate_key()
        if limit == -1:
            return True, "", 0, -1
        calls = st.session_state.get(key, 0)
        if calls >= limit:
            msg = (
                "Limite d'analyses atteinte (" + str(calls) + "/" + str(limit)
                + " aujourd'hui). Plan " + plan.capitalize()
                + " limite a " + str(limit) + " appels/jour."
            )
            return False, msg, calls, limit
        return True, "", calls, limit
    except Exception:
        return True, "", 0, -1


def increment_rate_counter():
    try:
        import streamlit as st
        key = _get_rate_key()
        st.session_state[key] = st.session_state.get(key, 0) + 1
    except Exception:
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


def appel_mistral(
    prompt: str,
    model: str = MODEL_MEDIUM,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    timeout: int = DEFAULT_TIMEOUT,
) -> str:
    """
    Envoie un prompt à Mistral et retourne la réponse.

    Paramètres
    ----------
    prompt     : texte du prompt
    model      : modèle Mistral (défaut : mistral-large-latest)
    max_tokens : limite de tokens en sortie (défaut : 4096)
    timeout    : délai max en secondes (défaut : 120)
    """
    # --- Rate limiting par session ---
    allowed, rl_msg, _, _ = check_rate_limit()
    if not allowed:
        return "❌ " + rl_msg

    api_key = _get_api_key()
    if not api_key:
        return (
            "❌ Cle API Mistral introuvable.\n"
            "• En local : fichier `.env` avec MISTRAL_API_KEY=votre_cle\n"
            "• Sur Streamlit Cloud : Settings -> Secrets"
        )

    # Troncature préventive : si le prompt dépasse ~12 000 caractères,
    # on garde le début et la fin pour ne pas surcharger le contexte
    MAX_PROMPT_CHARS = 12_000
    if len(prompt) > MAX_PROMPT_CHARS:
        moitie = MAX_PROMPT_CHARS // 2
        prompt = (
            prompt[:moitie]
            + "\n\n[... données tronquées pour optimisation ...]\n\n"
            + prompt[-moitie:]
        )

    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {
        "Authorization": "Bearer " + api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "model":      model,
        "messages":   [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
    }

    last_error = ""
    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
            if resp.status_code == 429:
                return "❌ Rate limit Mistral atteint. Patientez quelques minutes."
            if resp.status_code == 401:
                return "❌ Cle API Mistral invalide."
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            increment_rate_counter()
            return content
        except requests.exceptions.Timeout:
            last_error = "Timeout (" + str(timeout) + "s)"
            if attempt < MAX_RETRIES:
                time.sleep(2 ** attempt)
        except requests.exceptions.ConnectionError as e:
            last_error = "Erreur connexion : " + str(e)[:80]
            if attempt < MAX_RETRIES:
                time.sleep(2 ** attempt)
        except Exception as e:
            last_error = str(e)[:120]
            break

    return (
        "❌ Echec apres " + str(MAX_RETRIES + 1) + " tentatives.\n"
        "Derniere erreur : " + last_error + "\n"
        "Verifiez votre connexion ou reessayez dans 1-2 minutes."
    )
