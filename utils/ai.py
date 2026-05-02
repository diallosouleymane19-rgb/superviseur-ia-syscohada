# utils/ai.py
import os
from dotenv import load_dotenv
from mistralai import Mistral
from data.plan_comptable_syscohada import PLAN_COMPTABLE_SYSCOHADA, get_account_class

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

class ComptableSupervisorAgent:
    def __init__(self):
        api_key = os.getenv("MISTRAL_API_KEY")
        if not api_key:
            raise ValueError("La clé API MISTRAL_API_KEY n'est pas définie dans le fichier .env")
        self.client = Mistral(api_key=api_key)
        self.model = "mistral-large-latest"

    def validate_account_number(self, account_number: str) -> dict:
        """Valide si un numéro de compte existe dans le plan SYSCOHADA."""
        if not account_number or not account_number.isdigit():
            return {
                "valid": False,
                "message": "Numéro de compte invalide (doit contenir uniquement des chiffres).",
                "suggestion": "Exemple de compte valide : 6011, 4011, 5121"
            }
        
        class_info = get_account_class(account_number)
        
        if not class_info:
            return {
                "valid": False,
                "message": f"Le compte {account_number} n'appartient à aucune classe SYSCOHADA valide.",
                "suggestion": "Le premier chiffre doit être entre 1 et 8."
            }
        
        return {
            "valid": True,
            "class_name": class_info.get("nom"),
            "message": f"✅ Compte valide. Classe : {class_info.get('nom')}"
        }

    def suggest_account(self, transaction_description: str) -> str:
        """Utilise Mistral AI pour suggérer un compte SYSCOHADA."""
        context = "Tu es un expert comptable OHADA. Voici les classes du SYSCOHADA révisé :\n"
        for key, value in PLAN_COMPTABLE_SYSCOHADA.items():
            context += f"- Classe {key}: {value['nom']}\n"
        
        prompt = f"""
{context}

Tâche : Pour la transaction suivante, suggère le numéro de compte SYSCOHADA le plus approprié.
Transaction : "{transaction_description}"

Réponds UNIQUEMENT avec ce format :
Compte: [NUMÉRO] - Justification: [TEXTE COURT]
"""
        try:
            response = self.client.chat.complete(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Tu es un assistant comptable expert SYSCOHADA."},
                    {"role": "user", "content": prompt},
                ],
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"⚠️ Erreur IA : {str(e)}"