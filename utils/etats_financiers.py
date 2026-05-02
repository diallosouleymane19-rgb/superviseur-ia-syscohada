import pandas as pd
from .ai import appel_mistral
from data.plan_comptable_syscohada import get_info_pays, PLAN_COMPTABLE

def get_instruction_langue(langue):
    if langue == "pt":
        return "Responde em PORTUGUÊS. Todos os documentos devem ser em português pois é a língua oficial da Guiné-Bissau."
    return "Réponds en FRANÇAIS."

def generer_bilan_syscohada(df_balance, code_pays="SN"):
    try:
        pays = get_info_pays(code_pays)
        devise = pays.get("devise", "FCFA")
        nom_pays = pays.get("nom", "")
        langue = pays.get("langue", "fr")
        instruction = get_instruction_langue(langue)
        apercu = df_balance.head(100).to_string()

        prompt = f"""
Tu es un expert-comptable SYSCOHADA spécialisé en droit OHADA.
Pays : {nom_pays} | Devise : {devise}
{instruction}

À partir de cette balance comptable :
{apercu}

Génère le BILAN SYSCOHADA complet selon le modèle officiel OHADA :

ACTIF :
1. ACTIF IMMOBILISÉ
   - Immobilisations incorporelles (Comptes 21x)
   - Immobilisations corporelles (Comptes 22x, 23x, 24x)
   - Immobilisations financières (Comptes 25x, 26x)
   TOTAL ACTIF IMMOBILISÉ

2. ACTIF CIRCULANT
   - Stocks (Comptes 3xx)
   - Créances clients (Comptes 41x)
   - Autres créances (Comptes 4xx)
   TOTAL ACTIF CIRCULANT

3. TRÉSORERIE ACTIF
   - Banques et caisses (Comptes 5xx)
   TOTAL TRÉSORERIE ACTIF

TOTAL ACTIF

PASSIF :
1. CAPITAUX PROPRES ET RESSOURCES ASSIMILÉES
   - Capital social (Compte 101)
   - Réserves (Compte 107)
   - Résultat net (Compte 109)
   TOTAL CAPITAUX PROPRES

2. DETTES FINANCIÈRES ET RESSOURCES ASSIMILÉES
   - Emprunts (Comptes 14x)
   TOTAL DETTES FINANCIÈRES

3. PASSIF CIRCULANT
   - Fournisseurs (Comptes 40x)
   - Dettes fiscales et sociales (Comptes 43x, 44x)
   TOTAL PASSIF CIRCULANT

4. TRÉSORERIE PASSIF
   - Découverts bancaires (Comptes 55x)
   TOTAL TRÉSORERIE PASSIF

TOTAL PASSIF

Indique tous les montants en {devise}.
Vérifie que TOTAL ACTIF = TOTAL PASSIF.
Donne des recommandations professionnelles à la fin.
        """
        return appel_mistral(prompt)
    except Exception as e:
        return f"Erreur génération bilan : {e}"


def generer_compte_resultat_syscohada(df_balance, code_pays="SN"):
    try:
        pays = get_info_pays(code_pays)
        devise = pays.get("devise", "FCFA")
        nom_pays = pays.get("nom", "")
        taux_is = pays.get("taux_is", 30)
        langue = pays.get("langue", "fr")
        instruction = get_instruction_langue(langue)
        apercu = df_balance.head(100).to_string()

        prompt = f"""
Tu es un expert-comptable SYSCOHADA.
Pays : {nom_pays} | Devise : {devise} | Taux IS : {taux_is}%
{instruction}

À partir de cette balance :
{apercu}

Génère le COMPTE DE RÉSULTAT SYSCOHADA complet :

I. ACTIVITÉ D'EXPLOITATION
   + Ventes de marchandises (701)
   - Achats de marchandises (601)
   = MARGE COMMERCIALE
   + Production vendue (702 à 706)
   = CHIFFRE D'AFFAIRES TOTAL
   - Achats de matières (602, 604)
   - Services extérieurs (62x)
   - Impôts et taxes (64x)
   = VALEUR AJOUTÉE (VA)
   - Charges de personnel (66x)
   = EXCÉDENT BRUT D'EXPLOITATION (EBE)
   - Dotations aux amortissements (671)
   = RÉSULTAT D'EXPLOITATION
   + Produits financiers (75x)
   - Charges financières (63x)
   = RÉSULTAT FINANCIER
   = RÉSULTAT DES ACTIVITÉS ORDINAIRES (RAO)

II. HORS ACTIVITÉS ORDINAIRES (HAO)
   = RÉSULTAT HAO

III. RÉSULTAT NET
   - Impôt sur les bénéfices ({taux_is}%)
   = RÉSULTAT NET DE L'EXERCICE

Indique tous les montants en {devise}.
        """
        return appel_mistral(prompt)
    except Exception as e:
        return f"Erreur génération compte de résultat : {e}"


def generer_tafire(df_balance, code_pays="SN"):
    try:
        pays = get_info_pays(code_pays)
        devise = pays.get("devise", "FCFA")
        nom_pays = pays.get("nom", "")
        langue = pays.get("langue", "fr")
        instruction = get_instruction_langue(langue)
        apercu = df_balance.head(100).to_string()

        prompt = f"""
Tu es un expert-comptable SYSCOHADA.
Pays : {nom_pays} | Devise : {devise}
{instruction}

À partir de cette balance :
{apercu}

Génère le TAFIRE (Tableau Financier des Ressources et Emplois) SYSCOHADA :

I. RESSOURCES
   A. Capacité d'Autofinancement Globale (CAFG)
   B. Cessions et réductions d'actifs
   C. Augmentation de capital
   D. Emprunts nouveaux
   TOTAL RESSOURCES

II. EMPLOIS
   A. Dividendes distribués
   B. Acquisitions d'immobilisations
   C. Remboursements d'emprunts
   D. Augmentation du BFR
   TOTAL EMPLOIS

III. VARIATION DE TRÉSORERIE
   = TOTAL RESSOURCES - TOTAL EMPLOIS

Indique tous les montants en {devise}.
        """
        return appel_mistral(prompt)
    except Exception as e:
        return f"Erreur génération TAFIRE : {e}"


def generer_notes_annexes(df_balance, code_pays="SN", nom_entreprise="", exercice=""):
    try:
        pays = get_info_pays(code_pays)
        devise = pays.get("devise", "FCFA")
        nom_pays = pays.get("nom", "")
        langue = pays.get("langue", "fr")
        instruction = get_instruction_langue(langue)
        apercu = df_balance.head(50).to_string()

        prompt = f"""
Tu es un expert-comptable SYSCOHADA.
Entreprise : {nom_entreprise}
Pays : {nom_pays} | Devise : {devise}
Exercice : {exercice}
{instruction}

À partir de cette balance :
{apercu}

Génère les NOTES ANNEXES SYSCOHADA obligatoires :

1. FAITS CARACTÉRISTIQUES DE L'EXERCICE
2. PRINCIPES ET MÉTHODES COMPTABLES
3. IMMOBILISATIONS
4. CRÉANCES ET DETTES
5. INFORMATIONS SUR LE PERSONNEL
6. INFORMATIONS FISCALES
   - TVA : {pays.get('taux_tva', 18)}%
   - IS : {pays.get('taux_is', 30)}%
7. ÉVÉNEMENTS POSTÉRIEURS À LA CLÔTURE

Rédige de façon professionnelle et conforme aux normes OHADA.
        """
        return appel_mistral(prompt)
    except Exception as e:
        return f"Erreur génération notes annexes : {e}"