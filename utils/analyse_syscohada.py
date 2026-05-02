import pandas as pd
from .ai import appel_mistral
from data.plan_comptable_syscohada import get_info_pays

def generer_bilan_syscohada(df_balance, code_pays="SN"):
    try:
        pays = get_info_pays(code_pays)
        devise = pays.get("devise", "FCFA")
        nom_pays = pays.get("nom", "")
        langue = pays.get("langue", "fr")

        apercu = df_balance.head(100).to_string()

        if langue == "pt":
            instruction_langue = "Responde em PORTUGUÊS. Todos os documentos devem ser em português pois é a língua oficial da Guiné-Bissau."
        else:
            instruction_langue = "Réponds en FRANÇAIS."

        prompt = f"""
Tu es un expert-comptable SYSCOHADA/OHADA.
Pays : {nom_pays} | Devise : {devise}
Taux TVA : {taux_tva}% | Taux IS : {taux_is}%

Analyse cette balance comptable selon les normes SYSCOHADA :

{apercu}

Donne une analyse complète :

1. STRUCTURE DE LA BALANCE
   - Vérification de l'équilibre débit/crédit
   - Analyse des soldes par classe de comptes
   - Cohérence avec le plan comptable OHADA

2. ANALYSE FINANCIÈRE SYSCOHADA
   - Fonds de Roulement Net Global (FRNG)
   - Besoin en Fonds de Roulement (BFR)
   - Trésorerie Nette
   - Ratios de liquidité et solvabilité

3. SOLDES INTERMÉDIAIRES DE GESTION (SIG)
   - Marge commerciale
   - Valeur Ajoutée (VA)
   - Excédent Brut d'Exploitation (EBE)
   - Résultat d'Exploitation
   - Résultat des Activités Ordinaires (RAO)

4. ANOMALIES ET RISQUES
   - Comptes avec soldes anormaux
   - Risques fiscaux selon législation {nom_pays}
   - Points de contrôle prioritaires

5. OBLIGATIONS FISCALES {nom_pays.upper()}
   - TVA à déclarer ({taux_tva}%)
   - Acomptes IS ({taux_is}%)
   - Autres obligations fiscales

6. RECOMMANDATIONS
   - Actions correctives prioritaires
   - Optimisations fiscales légales
   - Points d'attention pour la clôture

Tous les montants en {devise}.
        """
        return appel_mistral(prompt)
    except Exception as e:
        return f"Erreur analyse balance : {e}"


def generer_bilan_syscohada(df_balance, code_pays="SN"):
    try:
        pays = get_info_pays(code_pays)
        devise = pays.get("devise", "FCFA")
        nom_pays = pays.get("nom", "")
        langue = pays.get("langue", "fr")

        apercu = df_balance.head(100).to_string()

        if langue == "pt":
            instruction_langue = "Responde em PORTUGUÊS. Todos os documentos devem ser em português pois é a língua oficial da Guiné-Bissau."
        else:
            instruction_langue = "Réponds en FRANÇAIS."

        prompt = f"""
Tu es un expert fiscaliste spécialisé en droit fiscal {nom_pays}.
Exercice : {exercice} | Devise : {devise}

À partir de cette balance :
{apercu}

Génère la LIASSE FISCALE complète pour {nom_pays} :

1. DÉCLARATION DE RÉSULTAT
   - Détermination du résultat fiscal
   - Réintégrations extra-comptables
   - Déductions extra-comptables
   - Base imposable à l'IS
   - IS dû ({taux_is}%)
   - Acomptes versés
   - IS à payer ou crédit d'impôt

2. DÉCLARATION TVA
   - CA taxable ({taux_tva}%)
   - TVA collectée
   - TVA déductible
   - TVA à décaisser ou crédit de TVA

3. AUTRES DÉCLARATIONS
   - Patente / Taxe professionnelle
   - Contribution foncière
   - Autres taxes locales

4. CALENDRIER FISCAL {nom_pays.upper()}
   - TVA : {echeances.get('TVA', 'N/A')}
   - Acomptes IS : {echeances.get('IS_acompte', 'N/A')}
   - Solde IS : {echeances.get('IS_solde', 'N/A')}
   - Déclarations sociales : {echeances.get('DSS', 'N/A')}

5. RISQUES FISCAUX
   - Points de contrôle prioritaires
   - Risques de redressement
   - Recommandations

Tous les montants en {devise}.
        """
        return appel_mistral(prompt)
    except Exception as e:
        return f"Erreur liasse fiscale : {e}"


def generer_bilan_syscohada(df_balance, code_pays="SN"):
    try:
        pays = get_info_pays(code_pays)
        devise = pays.get("devise", "FCFA")
        nom_pays = pays.get("nom", "")
        langue = pays.get("langue", "fr")

        apercu = df_balance.head(100).to_string()

        if langue == "pt":
            instruction_langue = "Responde em PORTUGUÊS. Todos os documentos devem ser em português pois é a língua oficial da Guiné-Bissau."
        else:
            instruction_langue = "Réponds en FRANÇAIS."

        prompt = f"""
Tu es un expert fiscaliste spécialisé en droit fiscal {nom_pays} et en droit OHADA.

Génère une veille fiscale complète pour {nom_pays} :

1. ACTUALITÉS FISCALES RÉCENTES {nom_pays.upper()}
   - Dernières modifications du Code Général des Impôts
   - Nouvelles directives UEMOA
   - Jurisprudences fiscales importantes

2. RAPPEL DU CADRE FISCAL {nom_pays.upper()}
   - TVA : {taux_tva}%
   - IS : {taux_is}%
   - Organismes fiscaux : {', '.join(organismes)}

3. ACTUALITÉS DROIT OHADA
   - Modifications récentes du droit comptable OHADA
   - Nouvelles dispositions SYSCOHADA
   - Harmonisation fiscale UEMOA

4. CALENDRIER FISCAL DU MOMENT
   - Échéances fiscales importantes
   - Déclarations à venir
   - Pénalités en cas de retard

5. CONSEILS PRATIQUES
   - Optimisations fiscales légales
   - Bonnes pratiques comptables SYSCOHADA
   - Points de vigilance

Réponds de façon claire et professionnelle.
        """
        return appel_mistral(prompt)
    except Exception as e:
        return f"Erreur veille fiscale : {e}"