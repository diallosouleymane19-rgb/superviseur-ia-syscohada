import pandas as pd
from .ai import appel_mistral
from data.plan_comptable_syscohada import get_info_pays

def get_instruction_langue(langue):
    if langue == "pt":
        return "Responde em PORTUGUÊS. Todos os documentos devem ser em português pois é a língua oficial da Guiné-Bissau."
    return "Réponds en FRANÇAIS."

def analyser_balance_syscohada(df, code_pays="SN"):
    try:
        pays = get_info_pays(code_pays)
        devise = pays.get("devise", "FCFA")
        nom_pays = pays.get("nom", "")
        taux_tva = pays.get("taux_tva", 18)
        taux_is = pays.get("taux_is", 30)
        langue = pays.get("langue", "fr")
        instruction = get_instruction_langue(langue)
        apercu = df.head(100).to_string()

        prompt = f"""
Tu es un expert-comptable SYSCOHADA/OHADA.
Pays : {nom_pays} | Devise : {devise}
Taux TVA : {taux_tva}% | Taux IS : {taux_is}%
{instruction}

Analyse cette balance comptable selon les normes SYSCOHADA :
{apercu}

1. STRUCTURE DE LA BALANCE
2. ANALYSE FINANCIÈRE SYSCOHADA (FRNG, BFR, Trésorerie)
3. SOLDES INTERMÉDIAIRES DE GESTION (SIG)
4. ANOMALIES ET RISQUES
5. OBLIGATIONS FISCALES {nom_pays.upper()}
6. RECOMMANDATIONS

Tous les montants en {devise}.
        """
        return appel_mistral(prompt)
    except Exception as e:
        return f"Erreur analyse balance : {e}"


def analyser_liasse_fiscale(df, code_pays="SN", exercice=""):
    try:
        pays = get_info_pays(code_pays)
        devise = pays.get("devise", "FCFA")
        nom_pays = pays.get("nom", "")
        taux_tva = pays.get("taux_tva", 18)
        taux_is = pays.get("taux_is", 30)
        echeances = pays.get("echeances", {})
        langue = pays.get("langue", "fr")
        instruction = get_instruction_langue(langue)
        apercu = df.head(100).to_string()

        prompt = f"""
Tu es un expert fiscaliste spécialisé en droit fiscal {nom_pays}.
Exercice : {exercice} | Devise : {devise}
{instruction}

À partir de cette balance :
{apercu}

Génère la LIASSE FISCALE complète pour {nom_pays} :

1. DÉCLARATION DE RÉSULTAT
   - IS dû ({taux_is}%)

2. DÉCLARATION TVA
   - TVA collectée ({taux_tva}%)
   - TVA déductible
   - TVA à décaisser

3. AUTRES DÉCLARATIONS

4. CALENDRIER FISCAL {nom_pays.upper()}
   - TVA : {echeances.get('TVA', 'N/A')}
   - Acomptes IS : {echeances.get('IS_acompte', 'N/A')}
   - Solde IS : {echeances.get('IS_solde', 'N/A')}

5. RISQUES FISCAUX

Tous les montants en {devise}.
        """
        return appel_mistral(prompt)
    except Exception as e:
        return f"Erreur liasse fiscale : {e}"


def veille_fiscale_uemoa(code_pays="SN"):
    try:
        pays = get_info_pays(code_pays)
        nom_pays = pays.get("nom", "")
        taux_tva = pays.get("taux_tva", 18)
        taux_is = pays.get("taux_is", 30)
        organismes = pays.get("organismes", [])
        langue = pays.get("langue", "fr")
        instruction = get_instruction_langue(langue)

        prompt = f"""
Tu es un expert fiscaliste spécialisé en droit fiscal {nom_pays} et en droit OHADA.
{instruction}

Génère une veille fiscale complète pour {nom_pays} :

1. ACTUALITÉS FISCALES RÉCENTES
2. RAPPEL DU CADRE FISCAL
   - TVA : {taux_tva}%
   - IS : {taux_is}%
   - Organismes : {', '.join(organismes)}
3. ACTUALITÉS DROIT OHADA
4. CALENDRIER FISCAL
5. CONSEILS PRATIQUES

Réponds de façon claire et professionnelle.
        """
        return appel_mistral(prompt)
    except Exception as e:
        return f"Erreur veille fiscale : {e}"