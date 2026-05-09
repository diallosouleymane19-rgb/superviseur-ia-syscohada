# -*- coding: utf-8 -*-
"""
Données fiscales UEMOA 2025/2026 - SMD Consulting
Source : Lois de Finances 2025, Actes OHADA, DGI par pays
Mise à jour : Mai 2026
"""

from datetime import datetime

DATE_MISE_A_JOUR = "Mai 2026"
ANNEE_FISCALE = 2025

# =============================================================================
# DONNÉES FISCALES COMPLÈTES PAR PAYS — 2025/2026
# =============================================================================

FISCALITE_2025 = {

    # ─────────────────────────────────────────────────────────────────────────
    "SN": {
        "nom": "Sénégal",
        "devise": "FCFA (XOF)",
        "langue": "fr",
        "organisme_fiscal": "Direction Générale des Impôts et Domaines (DGID)",
        "site_officiel": "https://www.impotsetdomaines.gouv.sn",

        "taux": {
            "tva": 18,
            "is": 30,
            "ircm": 10,
            "irvm": 10,
            "retenue_source_salaires": "Barème progressif (0% à 40%)",
            "contribution_economique_locale": "Variable selon CA",
            "taxe_patronale_apprentissage": 3,
            "minimum_fiscal": "1% du CA HT (min 500 000 FCFA)",
        },

        "seuils": {
            "regime_reel_normal": 100_000_000,
            "regime_reel_simplifie": 50_000_000,
            "regime_forfaitaire": "< 50 000 000 FCFA",
        },

        "echeances_2025": {
            "TVA": "15 du mois suivant",
            "IS_acompte_1": "15 mars 2025",
            "IS_acompte_2": "15 juin 2025",
            "IS_acompte_3": "15 septembre 2025",
            "IS_solde": "15 avril 2026",
            "liasse_fiscale": "30 avril 2026",
            "IPRES_CSS": "15 du mois suivant",
        },

        "reformes_2025": [
            "Loi de Finances 2025 : Renforcement du contrôle fiscal numérique",
            "Obligation de facturation électronique pour les grandes entreprises",
            "Extension du régime de l'auto-liquidation TVA aux services numériques étrangers",
            "Révision des taux de la contribution foncière des propriétés bâties (CFPB)",
            "Renforcement des obligations déclaratives pour les groupes multinationaux",
            "Mise en place du numéro d'identification fiscal unique (NIF biométrique)",
        ],

        "organismes": ["DGID", "IPRES", "CSS", "NINEA"],
        "penalites": {
            "retard_declaration": "25% des droits + 10% par mois",
            "retard_paiement": "10% + 2% par mois supplémentaire",
            "manquement_grave": "Jusqu'à 100% des droits éludés",
        },
    },

    # ─────────────────────────────────────────────────────────────────────────
    "CI": {
        "nom": "Côte d'Ivoire",
        "devise": "FCFA (XOF)",
        "langue": "fr",
        "organisme_fiscal": "Direction Générale des Impôts (DGI)",
        "site_officiel": "https://www.dgi.gouv.ci",

        "taux": {
            "tva": 18,
            "is": 25,
            "ircm": 15,
            "irvm": 15,
            "retenue_source_salaires": "Barème progressif (0% à 36%)",
            "impot_minimum_forfaitaire": "0.5% du CA HT",
            "taxe_patronale_apprentissage": 1.2,
        },

        "seuils": {
            "regime_reel_normal": 150_000_000,
            "regime_reel_simplifie": 50_000_000,
            "regime_forfaitaire": "< 50 000 000 FCFA",
        },

        "echeances_2025": {
            "TVA": "15 du mois suivant",
            "IS_acompte_1": "15 mars 2025",
            "IS_acompte_2": "15 juin 2025",
            "IS_acompte_3": "15 septembre 2025",
            "IS_solde": "30 avril 2026",
            "liasse_fiscale": "30 avril 2026",
            "CNPS": "15 du mois suivant",
        },

        "reformes_2025": [
            "Loi de Finances 2025 : Maintien du taux IS à 25% (avantage concurrentiel UEMOA)",
            "Renforcement du dispositif de retenue à la source sur les prestations de services",
            "Obligation de dépôt électronique des déclarations fiscales pour CA > 500M FCFA",
            "Nouveau régime fiscal des zones économiques spéciales (ZES)",
            "Extension de la TVA aux services numériques fournis par des non-résidents",
            "Révision des conditions d'exonération pour les entreprises du secteur agricole",
            "Mise en place d'un identifiant fiscal unique pour les contribuables",
        ],

        "organismes": ["DGI", "CNPS", "DGT", "DGDDI"],
        "penalites": {
            "retard_declaration": "25% des droits + 5% par mois (max 50%)",
            "retard_paiement": "10% + 3% par mois",
            "manquement_grave": "Jusqu'à 150% des droits éludés",
        },
    },

    # ─────────────────────────────────────────────────────────────────────────
    "ML": {
        "nom": "Mali",
        "devise": "FCFA (XOF)",
        "langue": "fr",
        "organisme_fiscal": "Direction Générale des Impôts (DGI)",
        "site_officiel": "https://www.dgi.gouv.ml",

        "taux": {
            "tva": 18,
            "is": 30,
            "ircm": 10,
            "irvm": 10,
            "retenue_source_salaires": "Barème progressif (0% à 40%)",
            "impot_minimum_forfaitaire": "1% du CA HT (min 600 000 FCFA)",
            "contribution_des_patentes": "Variable selon activité",
        },

        "seuils": {
            "regime_reel_normal": 100_000_000,
            "regime_reel_simplifie": 50_000_000,
            "regime_forfaitaire": "< 50 000 000 FCFA",
        },

        "echeances_2025": {
            "TVA": "20 du mois suivant",
            "IS_acompte_1": "20 mars 2025",
            "IS_acompte_2": "20 juin 2025",
            "IS_acompte_3": "20 septembre 2025",
            "IS_solde": "30 avril 2026",
            "liasse_fiscale": "30 avril 2026",
            "INPS": "20 du mois suivant",
        },

        "reformes_2025": [
            "Budget rectificatif 2025 : Renforcement des recettes fiscales intérieures",
            "Digitalisation de la DGI : extension de la plateforme Mali Impôts en ligne",
            "Renforcement des contrôles fiscaux secteur mines et télécommunications",
            "Révision du régime fiscal des associations et ONG",
            "Nouvelles obligations déclaratives pour les professions libérales",
            "Révision de la contribution des patentes et licences",
        ],

        "organismes": ["DGI", "INPS", "DGDDI", "DNT"],
        "penalites": {
            "retard_declaration": "25% des droits + 10% par mois",
            "retard_paiement": "10% + 2% par mois",
            "manquement_grave": "100% des droits éludés + sanctions pénales",
        },
    },

    # ─────────────────────────────────────────────────────────────────────────
    "BF": {
        "nom": "Burkina Faso",
        "devise": "FCFA (XOF)",
        "langue": "fr",
        "organisme_fiscal": "Direction Générale des Impôts (DGI)",
        "site_officiel": "https://www.dgi.bf.gov",

        "taux": {
            "tva": 18,
            "is": 27.5,
            "ircm": 12.5,
            "irvm": 12.5,
            "retenue_source_salaires": "Barème progressif (0% à 35%)",
            "taxe_patronale_apprentissage": 3,
            "contribution_secteur_informel": "Variable",
        },

        "seuils": {
            "regime_reel_normal": 100_000_000,
            "regime_reel_simplifie": 50_000_000,
            "regime_forfaitaire": "< 50 000 000 FCFA",
        },

        "echeances_2025": {
            "TVA": "20 du mois suivant",
            "IS_acompte_1": "20 mars 2025",
            "IS_acompte_2": "20 juin 2025",
            "IS_acompte_3": "20 septembre 2025",
            "IS_solde": "30 avril 2026",
            "liasse_fiscale": "30 avril 2026",
            "CNSS": "20 du mois suivant",
        },

        "reformes_2025": [
            "Loi de Finances 2025 : Maintien IS à 27.5% (plus bas de la zone UEMOA)",
            "Mesures fiscales d'urgence dans le contexte sécuritaire",
            "Renforcement de la taxe sur les transactions financières mobiles (MoMo, Orange Money)",
            "Révision des exonérations fiscales dans les zones de développement prioritaire",
            "Nouvelles obligations de retenue à la source pour les marchés publics",
            "Extension de la facturation électronique obligatoire",
        ],

        "organismes": ["DGI", "CNSS", "DGTCP", "DGADM"],
        "penalites": {
            "retard_declaration": "25% des droits + 5% par mois",
            "retard_paiement": "10% + 2% par mois",
            "manquement_grave": "100% des droits + poursuites pénales",
        },
    },

    # ─────────────────────────────────────────────────────────────────────────
    "NE": {
        "nom": "Niger",
        "devise": "FCFA (XOF)",
        "langue": "fr",
        "organisme_fiscal": "Direction Générale des Impôts (DGI)",
        "site_officiel": "https://www.dgi.gouv.ne",

        "taux": {
            "tva": 19,
            "is": 30,
            "ircm": 10,
            "irvm": 10,
            "retenue_source_salaires": "Barème progressif (0% à 35%)",
            "impot_minimum_forfaitaire": "1% du CA HT",
            "taxe_statistique": "1% à l'importation",
        },

        "seuils": {
            "regime_reel_normal": 100_000_000,
            "regime_reel_simplifie": 50_000_000,
            "regime_forfaitaire": "< 50 000 000 FCFA",
        },

        "echeances_2025": {
            "TVA": "15 du mois suivant",
            "IS_acompte_1": "15 mars 2025",
            "IS_acompte_2": "15 juin 2025",
            "IS_acompte_3": "15 septembre 2025",
            "IS_solde": "30 avril 2026",
            "liasse_fiscale": "30 avril 2026",
            "CNSS": "15 du mois suivant",
        },

        "reformes_2025": [
            "TVA à 19% : taux le plus élevé de la zone UEMOA — maintenu en 2025",
            "Budget rectificatif 2025 dans le contexte post-transition politique",
            "Renforcement des recettes pétrolières et minières",
            "Révision du régime fiscal du secteur de l'uranium",
            "Nouvelles mesures anti-fraude et anti-blanchiment",
            "Extension de la TVA aux services de télécommunications et numériques",
        ],

        "organismes": ["DGI", "CNSS", "DGDDI", "DGEEF"],
        "penalites": {
            "retard_declaration": "25% des droits + 5% par mois (max 50%)",
            "retard_paiement": "10% + 3% par mois",
            "manquement_grave": "100% à 200% des droits éludés",
        },
    },

    # ─────────────────────────────────────────────────────────────────────────
    "TG": {
        "nom": "Togo",
        "devise": "FCFA (XOF)",
        "langue": "fr",
        "organisme_fiscal": "Office Togolais des Recettes (OTR)",
        "site_officiel": "https://www.otr.tg",

        "taux": {
            "tva": 18,
            "is": 27,
            "ircm": 10,
            "irvm": 10,
            "retenue_source_salaires": "Barème progressif (0% à 35%)",
            "contribution_des_patentes": "Variable",
            "taxe_professionnelle": "2% du CA pour certains secteurs",
        },

        "seuils": {
            "regime_reel_normal": 60_000_000,
            "regime_reel_simplifie": 30_000_000,
            "regime_forfaitaire": "< 30 000 000 FCFA",
        },

        "echeances_2025": {
            "TVA": "15 du mois suivant",
            "IS_acompte_1": "31 mars 2025",
            "IS_acompte_2": "30 juin 2025",
            "IS_acompte_3": "30 septembre 2025",
            "IS_solde": "30 avril 2026",
            "liasse_fiscale": "30 avril 2026",
            "CNSS": "15 du mois suivant",
        },

        "reformes_2025": [
            "Loi de Finances 2025 : IS réduit à 27% (effort compétitivité fiscale)",
            "OTR : Extension du guichet unique fiscal numérique e-Tax",
            "Nouveau régime d'incitation fiscale pour les zones franches industrielles",
            "Révision du régime de la contribution des patentes",
            "Obligation TVA pour toutes les entreprises CA > 30M FCFA",
            "Renforcement des conventions fiscales bilatérales (France, UEMOA)",
            "Mesures d'amnistie fiscale pour régularisation 2019-2024",
        ],

        "organismes": ["OTR", "CNSS", "ITRA", "ANPE"],
        "penalites": {
            "retard_declaration": "25% des droits + 5% par mois",
            "retard_paiement": "15% + 2% par mois",
            "manquement_grave": "100% des droits + sanctions administratives",
        },
    },

    # ─────────────────────────────────────────────────────────────────────────
    "BJ": {
        "nom": "Bénin",
        "devise": "FCFA (XOF)",
        "langue": "fr",
        "organisme_fiscal": "Direction Générale des Impôts (DGI)",
        "site_officiel": "https://www.impots.finances.bj",

        "taux": {
            "tva": 18,
            "is": 30,
            "ircm": 10,
            "irvm": 10,
            "retenue_source_salaires": "Barème progressif (0% à 35%)",
            "impot_minimum_forfaitaire": "1% du CA HT",
            "taxe_affaires_sociales": "1% masse salariale",
        },

        "seuils": {
            "regime_reel_normal": 100_000_000,
            "regime_reel_simplifie": 50_000_000,
            "regime_forfaitaire": "< 50 000 000 FCFA",
        },

        "echeances_2025": {
            "TVA": "20 du mois suivant",
            "IS_acompte_1": "31 mars 2025",
            "IS_acompte_2": "30 juin 2025",
            "IS_acompte_3": "30 septembre 2025",
            "IS_solde": "30 avril 2026",
            "liasse_fiscale": "30 avril 2026",
            "CNSS": "20 du mois suivant",
        },

        "reformes_2025": [
            "Loi de Finances 2025 : Réforme de la fiscalité du secteur portuaire (Port de Cotonou)",
            "Extension de la TVA aux prestations de services numériques étrangers",
            "Nouveau code des investissements : réduction IS à 25% pour secteurs prioritaires",
            "Digitalisation complète des déclarations TVA et IS",
            "Renforcement du dispositif de prix de transfert pour les multinationales",
            "Exonérations fiscales révisées pour le secteur agricole et agroalimentaire",
            "Contribution spéciale de solidarité : révision du taux",
        ],

        "organismes": ["DGI", "CNSS", "DGTCP", "DDP"],
        "penalites": {
            "retard_declaration": "25% des droits + 10% par mois",
            "retard_paiement": "10% + 2% par mois",
            "manquement_grave": "100% des droits + poursuites judiciaires",
        },
    },

    # ─────────────────────────────────────────────────────────────────────────
    "GW": {
        "nom": "Guinée-Bissau",
        "nom_local": "Guiné-Bissau",
        "devise": "FCFA (XOF)",
        "langue": "pt",
        "organisme_fiscal": "Direcção Geral das Contribuições e Impostos (DGCI)",
        "site_officiel": "https://www.minfin.gw",

        "taux": {
            "tva": 15,
            "is": 25,
            "ircm": 10,
            "irvm": 10,
            "retenue_source_salaires": "Barème progressif (0% à 30%)",
            "impot_minimum_forfaitaire": "0.5% du CA HT",
        },

        "seuils": {
            "regime_reel_normal": 25_000_000,
            "regime_reel_simplifie": 10_000_000,
            "regime_forfaitaire": "< 10 000 000 FCFA",
        },

        "echeances_2025": {
            "TVA": "15 do mês seguinte",
            "IS_acompte_1": "15 março 2025",
            "IS_acompte_2": "15 junho 2025",
            "IS_acompte_3": "15 setembro 2025",
            "IS_solde": "30 abril 2026",
            "liasse_fiscale": "30 abril 2026",
            "INSS": "15 do mês seguinte",
        },

        "reformes_2025": [
            "Orçamento 2025 : Renforcement des capacités de la DGCI",
            "TVA maintenue à 15% : taux le plus compétitif de la zone UEMOA",
            "Harmonisation progressive avec les normes fiscales UEMOA",
            "Nouvelles mesures pour formaliser l'économie informelle",
            "Révision des accords fiscaux avec le Portugal et les pays CEDEAO",
            "Extension du système de facturation électronique aux grandes entreprises",
        ],

        "organismes": ["DGCI", "INSS", "DGTF", "BDU"],
        "penalites": {
            "retard_declaration": "25% dos direitos + 5% por mês",
            "retard_paiement": "10% + 2% por mês",
            "manquement_grave": "100% dos direitos eludidos",
        },
    },
}


# =============================================================================
# DONNÉES OHADA 2025 — DROIT COMPTABLE
# =============================================================================

REFORMES_OHADA_2025 = {
    "acte_uniforme_comptable": {
        "version": "SYSCOHADA Révisé 2017 — en vigueur",
        "prochaine_revision": "Révision prévue 2025-2026 en discussion",
        "points_revision": [
            "Intégration des normes IFRS pour les grandes entreprises",
            "Adaptation aux instruments financiers complexes",
            "Nouvelles règles sur les actifs biologiques (agriculture)",
            "Traitement des cryptomonnaies et actifs numériques",
        ]
    },
    "acte_uniforme_societes": {
        "derniere_revision": "2014",
        "actualites_2025": [
            "Réflexions sur la SAS (Société par Actions Simplifiée) en droit OHADA",
            "Renforcement des droits des minoritaires",
            "Encadrement des pactes d'actionnaires",
        ]
    },
    "digitalisation": [
        "Projet OHADA Digital : dématérialisation des actes de commerce",
        "Signature électronique reconnue dans l'espace OHADA",
        "Registre du Commerce Électronique (RCCM digital) en déploiement",
        "Archivage électronique des documents comptables reconnu légalement",
    ],
    "jurisprudence_2024_2025": [
        "CCJA : Précisions sur le traitement des sûretés mobilières",
        "CCJA : Consolidation jurisprudence sur les procédures collectives",
        "Harmonisation des pratiques d'audit dans l'espace OHADA",
    ]
}


# =============================================================================
# FLUX RSS OFFICIELS PAR PAYS
# =============================================================================

RSS_SOURCES = {
    "SN": [
        "https://www.impotsetdomaines.gouv.sn/rss",
        "https://www.sec.gouv.sn/rss.xml",
        "https://www.financessenegal.gouv.sn/feed",
    ],
    "CI": [
        "https://www.dgi.gouv.ci/rss",
        "https://www.finances.gouv.ci/feed",
        "https://www.tresor.gouv.ci/rss",
    ],
    "ML": [
        "https://www.dgi.gouv.ml/rss",
        "https://www.finances.gouv.ml/feed",
    ],
    "BF": [
        "https://www.dgi.bf/rss",
        "https://www.finances.gov.bf/feed",
    ],
    "NE": [
        "https://www.dgi.ne/rss",
        "https://www.finances.gov.ne/feed",
    ],
    "TG": [
        "https://www.otr.tg/rss",
        "https://www.finances.gouv.tg/feed",
    ],
    "BJ": [
        "https://www.impots.finances.bj/rss",
        "https://www.finances.bj/feed",
    ],
    "GW": [
        "https://www.minfin.gw/rss",
    ],
    "UEMOA": [
        "https://www.uemoa.int/fr/rss.xml",
        "https://www.bceao.int/fr/rss.xml",
    ],
    "OHADA": [
        "https://www.ohada.com/rss",
        "https://www.juriscope.org/rss",
    ],
}


# =============================================================================
# FONCTIONS UTILITAIRES
# =============================================================================

def get_info_pays_2025(code_pays):
    """Retourne les données fiscales 2025/2026 pour un pays"""
    return FISCALITE_2025.get(code_pays, {})


def get_reformes_pays(code_pays):
    """Retourne les réformes fiscales 2025 pour un pays"""
    pays = FISCALITE_2025.get(code_pays, {})
    return pays.get("reformes_2025", [])


def get_echeances_pays(code_pays):
    """Retourne les échéances fiscales 2025 pour un pays"""
    pays = FISCALITE_2025.get(code_pays, {})
    return pays.get("echeances_2025", {})


def get_penalites_pays(code_pays):
    """Retourne les pénalités fiscales pour un pays"""
    pays = FISCALITE_2025.get(code_pays, {})
    return pays.get("penalites", {})


def get_contexte_fiscal_complet(code_pays):
    """Retourne un contexte fiscal complet formaté pour les prompts IA"""
    pays = FISCALITE_2025.get(code_pays, {})
    if not pays:
        return ""

    reformes = "\n".join([f"  • {r}" for r in pays.get("reformes_2025", [])])
    echeances = pays.get("echeances_2025", {})
    taux = pays.get("taux", {})
    penalites = pays.get("penalites", {})

    return f"""
═══════════════════════════════════════════════════════════
DONNÉES FISCALES OFFICIELLES — {pays.get('nom', '').upper()} — 2025/2026
Source : {pays.get('organisme_fiscal', '')} | MAJ : {DATE_MISE_A_JOUR}
═══════════════════════════════════════════════════════════

📊 TAUX FISCAUX EN VIGUEUR :
  • TVA : {taux.get('tva', 'N/A')}%
  • IS (Impôt sur les Sociétés) : {taux.get('is', 'N/A')}%
  • IRCM : {taux.get('ircm', 'N/A')}%
  • Retenue sur salaires : {taux.get('retenue_source_salaires', 'N/A')}
  • Minimum fiscal : {taux.get('impot_minimum_forfaitaire', 'N/A')}

📅 CALENDRIER FISCAL 2025/2026 :
  • TVA : {echeances.get('TVA', 'N/A')}
  • Acompte IS 1er : {echeances.get('IS_acompte_1', 'N/A')}
  • Acompte IS 2e : {echeances.get('IS_acompte_2', 'N/A')}
  • Acompte IS 3e : {echeances.get('IS_acompte_3', 'N/A')}
  • Solde IS : {echeances.get('IS_solde', 'N/A')}
  • Liasse fiscale : {echeances.get('liasse_fiscale', 'N/A')}

🔄 RÉFORMES FISCALES 2025 :
{reformes}

⚠️ PÉNALITÉS :
  • Retard déclaration : {penalites.get('retard_declaration', 'N/A')}
  • Retard paiement : {penalites.get('retard_paiement', 'N/A')}
  • Manquement grave : {penalites.get('manquement_grave', 'N/A')}

🏛️ ORGANISMES : {', '.join(pays.get('organismes', []))}
═══════════════════════════════════════════════════════════
"""
