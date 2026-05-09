import os
import json
import requests
from dotenv import load_dotenv
from pathlib import Path

# ---------------------------------------------------------
# Charger le fichier .env depuis la RACINE du projet
# ---------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH)

# ---------------------------------------------------------
# Récupérer la clé API Mistral
# ---------------------------------------------------------
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

# ---------------------------------------------------------
# Fonction d'appel à l'API Mistral
# ---------------------------------------------------------
def appel_mistral(prompt: str):
    """
    Envoie un prompt texte au modèle Mistral et retourne la réponse.
    """

    if not MISTRAL_API_KEY:
        return "Erreur : MISTRAL_API_KEY introuvable (None). Vérifie ton fichier .env."

    url = "https://api.mistral.ai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "mistral-large-latest",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code != 200:
        return f"Erreur IA : HTTP {response.status_code} - {response.text}"

    data = response.json()
    return data["choices"][0]["message"]["content"]
