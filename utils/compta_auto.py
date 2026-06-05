from .ai import appel_mistral
from datetime import datetime

def analyse_balance_ai(df, exercice=None):
    """Analyse IA de la balance comptable."""
    annee = str(exercice).strip()[:4] if exercice and str(exercice).strip() else str(datetime.now().year)
    balance_txt = df.head(50).to_string()

    lignes = [
        f"Tu es un expert-comptable SYSCOHADA/OHADA.",
        f"Analyse la balance suivante pour l'exercice fiscal {annee}.",
        "",
        f"IMPORTANT : Toutes tes references fiscales (taux IS, TVA, obligations)",
        f"doivent etre basees sur l'exercice {annee}, pas sur la date actuelle.",
        f"Ne genere pas de header ou titre de rapport.",
        "",
        f"Balance comptable - Exercice {annee} :",
        balance_txt,
        "",
        "Donne une analyse structuree comprenant :",
        "- points forts",
        "- anomalies",
        "- comptes a surveiller",
        "- suggestions de regularisation",
        f"- risques fiscaux pour l'exercice {annee}",
        "- coherence des soldes",
        "- remarques professionnelles",
        "",
        "Reponds en texte clair, structure et professionnel.",
    ]
    prompt = "\n".join(lignes)
    return appel_mistral(prompt)
