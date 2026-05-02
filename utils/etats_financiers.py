import pandas as pd
from .ai import appel_mistral
from data.plan_comptable_syscohada import get_info_pays, PLAN_COMPTABLE

def generer_bilan_syscohada(df_balance, code_pays="SN"):
    """
    Génère le Bilan SYSCOHADA à partir d'une balance.
    """
    try:
        pays = get_info_pays(code_pays)
        devise = pays.get("devise", "FCFA")
        nom_pays = pays.get("nom", "")

        apercu = df_balance.head(100).to_string()

        prompt = f"""
Tu es un expert-comptable SYSCOHADA spécialisé en droit OHADA.
Pays : {nom_pays} | Devise : {devise}

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
   - Dettes financières diverses (Comptes 16x)
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
    """
    Génère le Compte de Résultat SYSCOHADA.
    """
    try:
        pays = get_info_pays(code_pays)
        devise = pays.get("devise", "FCFA")
        nom_pays = pays.get("nom", "")
        taux_is = pays.get("taux_is", 30)

        apercu = df_balance.head(100).to_string()

        prompt = f"""
Tu es un expert-comptable SYSCOHADA.
Pays : {nom_pays} | Devise : {devise} | Taux IS : {taux_is}%

À partir de cette balance :
{apercu}

Génère le COMPTE DE RÉSULTAT SYSCOHADA complet :

I. ACTIVITÉ D'EXPLOITATION
   + Ventes de marchandises (701)
   - Achats de marchandises (601)
   - Variation de stocks marchandises (603)
   = MARGE COMMERCIALE

   + Production vendue (702 à 706)
   + Production stockée (71x)
   + Production immobilisée (72x)
   = CHIFFRE D'AFFAIRES TOTAL

   - Achats de matières (602, 604)
   - Transports (61x)
   - Services extérieurs (62x)
   - Impôts et taxes (64x)
   = VALEUR AJOUTÉE (VA)

   - Charges de personnel (66x)
   = EXCÉDENT BRUT D'EXPLOITATION (EBE)

   - Dotations aux amortissements (671)
   - Dotations aux provisions (672, 673)
   + Reprises (771, 772)
   = RÉSULTAT D'EXPLOITATION

   + Produits financiers (75x)
   - Charges financières (63x)
   = RÉSULTAT FINANCIER

   = RÉSULTAT DES ACTIVITÉS ORDINAIRES (RAO)

II. HORS ACTIVITÉS ORDINAIRES (HAO)
   + Produits HAO (78x, 82x)
   - Charges HAO (68x, 81x)
   = RÉSULTAT HAO

III. RÉSULTAT NET
   = RAO + HAO
   - Impôt sur les bénéfices ({taux_is}%)
   - Participation des travailleurs (691)
   = RÉSULTAT NET DE L'EXERCICE

Indique tous les montants en {devise}.
Calcule tous les SIG et ratios de rentabilité.
Donne des recommandations professionnelles.
        """
        return appel_mistral(prompt)
    except Exception as e:
        return f"Erreur génération compte de résultat : {e}"


def generer_tafire(df_balance, code_pays="SN"):
    """
    Génère le TAFIRE - Tableau Financier des Ressources et Emplois.
    """
    try:
        pays = get_info_pays(code_pays)
        devise = pays.get("devise", "FCFA")
        nom_pays = pays.get("nom", "")

        apercu = df_balance.head(100).to_string()

        prompt = f"""
Tu es un expert-comptable SYSCOHADA.
Pays : {nom_pays} | Devise : {devise}

À partir de cette balance :
{apercu}

Génère le TAFIRE (Tableau Financier des Ressources et Emplois) SYSCOHADA :

I. RESSOURCES
   A. Capacité d'Autofinancement Globale (CAFG)
      + Résultat net
      + Dotations aux amortissements
      + Dotations aux provisions
      - Reprises sur provisions
      - Plus-values de cession
      = CAFG

   B. Cessions et réductions d'actifs immobilisés
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

Analyse la situation de trésorerie et donne des recommandations.
Indique tous les montants en {devise}.
        """
        return appel_mistral(prompt)
    except Exception as e:
        return f"Erreur génération TAFIRE : {e}"


def generer_notes_annexes(df_balance, code_pays="SN", nom_entreprise="", exercice=""):
    """
    Génère les Notes Annexes SYSCOHADA.
    """
    try:
        pays = get_info_pays(code_pays)
        devise = pays.get("devise", "FCFA")
        nom_pays = pays.get("nom", "")

        apercu = df_balance.head(50).to_string()

        prompt = f"""
Tu es un expert-comptable SYSCOHADA.
Entreprise : {nom_entreprise}
Pays : {nom_pays} | Devise : {devise}
Exercice : {exercice}

À partir de cette balance :
{apercu}

Génère les NOTES ANNEXES SYSCOHADA obligatoires :

1. FAITS CARACTÉRISTIQUES DE L'EXERCICE
   - Événements importants de l'exercice
   - Changements de méthodes comptables

2. PRINCIPES ET MÉTHODES COMPTABLES
   - Méthodes d'évaluation des immobilisations
   - Méthodes d'amortissement utilisées
   - Méthodes d'évaluation des stocks

3. IMMOBILISATIONS
   - Tableau des immobilisations
   - Tableau des amortissements
   - Tableau des provisions

4. CRÉANCES ET DETTES
   - Analyse des créances clients
   - Analyse des dettes fournisseurs
   - Créances et dettes en monnaie étrangère

5. INFORMATIONS SUR LE PERSONNEL
   - Effectif moyen
   - Charges de personnel

6. INFORMATIONS FISCALES
   - Régime fiscal applicable
   - Taux TVA : {pays.get('taux_tva', 18)}%
   - Taux IS : {pays.get('taux_is', 30)}%

7. ÉVÉNEMENTS POSTÉRIEURS À LA CLÔTURE

Rédige de façon professionnelle et conforme aux normes OHADA.
        """
        return appel_mistral(prompt)
    except Exception as e:
        return f"Erreur génération notes annexes : {e}"