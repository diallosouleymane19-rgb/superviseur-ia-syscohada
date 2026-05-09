# -*- coding: utf-8 -*-
"""
Module Analyse SYSCOHADA - SMD Consulting
Analyses comptables et fiscales selon normes OHADA/UEMOA
Version 2025 — Données fiscales actualisées + Veille RSS
"""

import pandas as pd
from datetime import datetime
from .ai import appel_mistral
from data.plan_comptable_syscohada import get_info_pays
from data.fiscalite_uemoa_2025 import (
    get_info_pays_2025,
    get_contexte_fiscal_complet,
    REFORMES_OHADA_2025
)

# Import RSS avec fallback si non disponible
try:
    from utils.veille_rss import get_actualites_pays, formater_actualites_pour_prompt, get_date_contexte
    RSS_DISPONIBLE = True
except Exception:
    RSS_DISPONIBLE = False
    def get_date_contexte():
        now = datetime.now()
        return {"date_jour": now.strftime("%d %B %Y"), "annee": now.year,
                "mois": now.strftime("%B %Y"), "trimestre": f"T{((now.month-1)//3)+1} {now.year}"}


# =============================================================================
# UTILITAIRES
# =============================================================================

def get_instruction_langue(langue):
    """Retourne l'instruction de langue pour le prompt"""
    if langue == "pt":
        return (
            "IMPORTANTE: Responde EXCLUSIVAMENTE em PORTUGUÊS. "
            "Todos os documentos, análises e relatórios devem ser redigidos em português, "
            "pois é a língua oficial da Guiné-Bissau."
        )
    return "Réponds exclusivement en FRANÇAIS avec un style professionnel de cabinet d'expertise comptable."


def preparer_contexte_date():
    """Prépare le contexte temporel pour le prompt"""
    ctx = get_date_contexte()
    return f"Date d'analyse : {ctx['date_jour']} | Période : {ctx['trimestre']} | Année fiscale : {ctx['annee']}"


def preparer_apercu_balance(df, max_lignes=150):
    """Prépare un aperçu structuré de la balance"""
    try:
        apercu = df.head(max_lignes).to_string()
        stats = f"""
STATISTIQUES BALANCE :
- Nombre de lignes : {len(df):,}
- Colonnes : {', '.join(df.columns.tolist())}
- Lignes analysées : {min(max_lignes, len(df))}
"""
        return stats + "\n" + apercu
    except Exception:
        return df.head(max_lignes).to_string()


# =============================================================================
# ANALYSE BALANCE SYSCOHADA
# =============================================================================

def analyser_balance_syscohada(df, code_pays="SN"):
    """
    Analyse une balance comptable selon les normes SYSCOHADA
    avec données fiscales 2025/2026 actualisées
    """
    try:
        # Données de base (compatibilité ancienne structure)
        pays_base = get_info_pays(code_pays)
        # Données enrichies 2025
        pays_2025 = get_info_pays_2025(code_pays)

        devise = pays_base.get("devise", "FCFA (XOF)")
        nom_pays = pays_base.get("nom", pays_2025.get("nom", ""))
        langue = pays_base.get("langue", "fr")
        instruction = get_instruction_langue(langue)
        contexte_date = preparer_contexte_date()
        contexte_fiscal = get_contexte_fiscal_complet(code_pays)
        apercu = preparer_apercu_balance(df)

        # Récupération actualités RSS
        actualites_txt = ""
        if RSS_DISPONIBLE:
            try:
                articles = get_actualites_pays(code_pays, max_articles=3)
                actualites_txt = formater_actualites_pour_prompt(articles, nom_pays)
            except Exception:
                actualites_txt = ""

        prompt = f"""
Tu es un expert-comptable et fiscaliste senior, spécialisé en normes SYSCOHADA/OHADA,
exerçant dans un grand cabinet d'expertise comptable international.

{instruction}
{contexte_date}

{contexte_fiscal}

{actualites_txt}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BALANCE COMPTABLE À ANALYSER :
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{apercu}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ANALYSE REQUISE — NIVEAU GRAND CABINET :
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. STRUCTURE DE LA BALANCE SYSCOHADA
   - Vérification de l'équilibre débit/crédit
   - Identification des classes de comptes (1 à 8)
   - Anomalies de classification SYSCOHADA

2. ANALYSE FINANCIÈRE SYSCOHADA
   - Fonds de Roulement Net Global (FRNG)
   - Besoin en Fonds de Roulement (BFR)
   - Trésorerie Nette (TN)
   - Ratio d'autonomie financière

3. SOLDES INTERMÉDIAIRES DE GESTION (SIG) — OHADA
   - Marge Brute sur Marchandises (MBM)
   - Valeur Ajoutée (VA)
   - Excédent Brut d'Exploitation (EBE)
   - Résultat d'Exploitation
   - Résultat des Activités Ordinaires (RAO)
   - Résultat Net

4. OBLIGATIONS FISCALES {nom_pays.upper()} 2025/2026
   - TVA collectée et déductible estimées
   - IS provisionnel calculé
   - Risques de redressement identifiés
   - Points de vigilance fiscale

5. ANOMALIES ET RISQUES DÉTECTÉS
   - Comptes sensibles ou inhabituels
   - Écritures suspectes ou doublons potentiels
   - Non-conformités SYSCOHADA

6. RECOMMANDATIONS CABINET
   - Actions correctives prioritaires
   - Optimisations fiscales légales
   - Points à documenter pour le commissaire aux comptes

Tous les montants en {devise}. Style : rapport professionnel de cabinet.
"""
        return appel_mistral(prompt)

    except Exception as e:
        return f"❌ Erreur analyse balance SYSCOHADA : {e}"


# =============================================================================
# LIASSE FISCALE
# =============================================================================

def analyser_liasse_fiscale(df, code_pays="SN", exercice="2025"):
    """
    Génère une liasse fiscale complète avec données 2025/2026 actualisées
    """
    try:
        pays_base = get_info_pays(code_pays)
        pays_2025 = get_info_pays_2025(code_pays)

        devise = pays_base.get("devise", "FCFA (XOF)")
        nom_pays = pays_base.get("nom", pays_2025.get("nom", ""))
        langue = pays_base.get("langue", "fr")
        instruction = get_instruction_langue(langue)
        contexte_date = preparer_contexte_date()
        contexte_fiscal = get_contexte_fiscal_complet(code_pays)
        apercu = preparer_apercu_balance(df)

        taux = pays_2025.get("taux", {})
        echeances = pays_2025.get("echeances_2025", pays_base.get("echeances", {}))
        reformes = pays_2025.get("reformes_2025", [])
        penalites = pays_2025.get("penalites", {})
        organisme = pays_2025.get("organisme_fiscal", "Administration fiscale")

        reformes_txt = "\n".join([f"  • {r}" for r in reformes[:5]])

        prompt = f"""
Tu es un fiscaliste expert en droit fiscal {nom_pays}, spécialisé en liasses fiscales SYSCOHADA,
travaillant pour un grand cabinet d'expertise comptable.

{instruction}
{contexte_date}
Exercice fiscal : {exercice}

{contexte_fiscal}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BALANCE COMPTABLE :
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{apercu}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LIASSE FISCALE COMPLÈTE {nom_pays.upper()} — EXERCICE {exercice}
Organisme compétent : {organisme}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. DÉCLARATION DE RÉSULTAT (IS)
   - Résultat comptable avant impôt
   - Réintégrations fiscales (charges non déductibles)
   - Déductions fiscales
   - Résultat fiscal imposable
   - IS dû au taux de {taux.get('is', 30)}%
   - Minimum fiscal : {taux.get('impot_minimum_forfaitaire', 'N/A')}
   - Acomptes déjà versés
   - Solde IS à payer

2. DÉCLARATION TVA — TAUX {taux.get('tva', 18)}%
   - CA HT imposable à la TVA
   - TVA collectée sur ventes ({taux.get('tva', 18)}%)
   - TVA déductible sur achats
   - TVA déductible sur immobilisations
   - Crédit de TVA reportable
   - TVA nette à décaisser

3. RETENUES À LA SOURCE
   - IRCM ({taux.get('ircm', 10)}%) sur revenus mobiliers
   - Retenues sur salaires (barème progressif)
   - Retenues sur prestations de services

4. AUTRES TAXES ET CONTRIBUTIONS
   - Contribution des patentes/licences
   - Taxes foncières
   - Contributions sociales ({', '.join(pays_2025.get('organismes', []))})

5. CALENDRIER FISCAL {nom_pays.upper()} {exercice}
   - TVA : {echeances.get('TVA', 'N/A')}
   - 1er acompte IS : {echeances.get('IS_acompte_1', 'N/A')}
   - 2e acompte IS : {echeances.get('IS_acompte_2', 'N/A')}
   - 3e acompte IS : {echeances.get('IS_acompte_3', 'N/A')}
   - Solde IS : {echeances.get('IS_solde', 'N/A')}
   - Dépôt liasse fiscale : {echeances.get('liasse_fiscale', 'N/A')}

6. RÉFORMES FISCALES 2025 APPLICABLES
{reformes_txt}

7. RISQUES FISCAUX ET POINTS DE VIGILANCE
   - Risques de redressement identifiés
   - Pénalités applicables en cas de retard :
     • Retard déclaration : {penalites.get('retard_declaration', 'N/A')}
     • Retard paiement : {penalites.get('retard_paiement', 'N/A')}

8. TABLEAU RÉCAPITULATIF DES OBLIGATIONS
   (Tableau avec montants, dates et organismes)

Tous les montants en {devise}. Style rapport fiscal professionnel.
"""
        return appel_mistral(prompt)

    except Exception as e:
        return f"❌ Erreur liasse fiscale : {e}"


# =============================================================================
# VEILLE FISCALE UEMOA
# =============================================================================

def veille_fiscale_uemoa(code_pays="SN"):
    """
    Génère une veille fiscale complète et actualisée 2025/2026
    avec RSS en temps réel + données officielles
    """
    try:
        pays_base = get_info_pays(code_pays)
        pays_2025 = get_info_pays_2025(code_pays)

        nom_pays = pays_base.get("nom", pays_2025.get("nom", ""))
        langue = pays_base.get("langue", "fr")
        instruction = get_instruction_langue(langue)
        contexte_date = preparer_contexte_date()
        contexte_fiscal = get_contexte_fiscal_complet(code_pays)

        # Réformes OHADA
        digitalisation_ohada = "\n".join([f"  • {d}" for d in REFORMES_OHADA_2025.get("digitalisation", [])])
        jurisprudence_ohada = "\n".join([f"  • {j}" for j in REFORMES_OHADA_2025.get("jurisprudence_2024_2025", [])])

        # Actualités RSS en temps réel
        actualites_txt = ""
        if RSS_DISPONIBLE:
            try:
                articles = get_actualites_pays(code_pays, max_articles=5)
                actualites_txt = formater_actualites_pour_prompt(articles, nom_pays)
            except Exception:
                actualites_txt = "[Flux RSS non disponible — données officielles utilisées]"
        else:
            actualites_txt = "[Module RSS non installé — données officielles utilisées]"

        taux = pays_2025.get("taux", {})
        echeances = pays_2025.get("echeances_2025", {})
        reformes = pays_2025.get("reformes_2025", [])
        penalites = pays_2025.get("penalites", {})
        organisme = pays_2025.get("organisme_fiscal", "")
        seuils = pays_2025.get("seuils", {})

        reformes_txt = "\n".join([f"  • {r}" for r in reformes])

        prompt = f"""
Tu es un expert fiscaliste senior, spécialisé en droit fiscal UEMOA et droit OHADA,
associé dans un grand cabinet d'expertise comptable international (type Big Four).

{instruction}
{contexte_date}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ACTUALITÉS EN TEMPS RÉEL :
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{actualites_txt}

{contexte_fiscal}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DONNÉES OHADA 2025 :
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Digitalisation OHADA :
{digitalisation_ohada}

Jurisprudence CCJA 2024-2025 :
{jurisprudence_ohada}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
VEILLE FISCALE COMPLÈTE — {nom_pays.upper()} — {contexte_date}
Organisme : {organisme}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Génère une veille fiscale professionnelle complète structurée ainsi :

1. SYNTHÈSE EXÉCUTIVE
   (Résumé des points essentiels en 5 lignes)

2. RÉFORMES FISCALES 2025 — {nom_pays.upper()}
{reformes_txt}
   → Analyse l'impact pratique de chaque réforme pour les entreprises

3. CADRE FISCAL EN VIGUEUR 2025/2026
   - TVA : {taux.get('tva', 'N/A')}% | IS : {taux.get('is', 'N/A')}% | IRCM : {taux.get('ircm', 'N/A')}%
   - Minimum fiscal : {taux.get('impot_minimum_forfaitaire', 'N/A')}
   - Seuils de régimes : {seuils}
   - Organisme compétent : {organisme}

4. CALENDRIER FISCAL 2025/2026
   - TVA : {echeances.get('TVA', 'N/A')}
   - Acomptes IS : {echeances.get('IS_acompte_1', 'N/A')}, {echeances.get('IS_acompte_2', 'N/A')}, {echeances.get('IS_acompte_3', 'N/A')}
   - Solde IS + Liasse : {echeances.get('IS_solde', 'N/A')}

5. ACTUALITÉS DROIT OHADA
   - SYSCOHADA Révisé : points de vigilance
   - Jurisprudence CCJA récente applicable
   - Digitalisation et dématérialisation

6. OBLIGATIONS DÉCLARATIVES ET SANCTIONS
   - Retard déclaration : {penalites.get('retard_declaration', 'N/A')}
   - Retard paiement : {penalites.get('retard_paiement', 'N/A')}
   - Manquements graves : {penalites.get('manquement_grave', 'N/A')}

7. CONSEILS PRATIQUES CABINET
   - 5 actions prioritaires à entreprendre ce trimestre
   - Points de vigilance pour l'exercice en cours
   - Opportunités d'optimisation fiscale légale

8. SOURCES ET RÉFÉRENCES
   - Textes officiels applicables
   - Liens utiles : {pays_2025.get('site_officiel', '')}

Style : Note de veille fiscale d'un grand cabinet d'expertise comptable.
Ton : Professionnel, précis, actionnable.
"""
        return appel_mistral(prompt)

    except Exception as e:
        return f"❌ Erreur veille fiscale : {e}"