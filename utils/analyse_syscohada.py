# -*- coding: utf-8 -*-
"""
Module Analyse SYSCOHADA - SMD Global Consulting LLC
Analyses comptables et fiscales selon normes OHADA/UEMOA
Version 2025 — Données fiscales actualisées + Veille RSS
v2.3 : Fix formatage FCFA (espaces pour milliers, pas de centimes)
"""
import pandas as pd
from datetime import datetime
from .ai import appel_mistral, MODEL_FAST, MODEL_MEDIUM
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
# UTILITAIRES LOCAUX
# =============================================================================

def _fmt_fcfa(v):
    """Formate un nombre en FCFA avec espace pour les milliers et sans décimales."""
    try:
        # Format anglais avec virgule -> remplacement par espace
        return f"{int(round(float(v))):,}".replace(",", " ")
    except Exception:
        return str(v)

def get_instruction_langue(langue):
    if langue == "pt":
        return (
            "IMPORTANTE: Responde EXCLUSIVAMENTE em PORTUGUÊS. "
            "Todos os documentos, análises e relatórios devem ser redigidos em português, "
            "pois é a língua oficial da Guiné-Bissau."
        )
    return "Réponds exclusivement en FRANÇAIS avec un style professionnel de cabinet d'expertise comptable."


def preparer_contexte_date(exercice=None):
    ctx = get_date_contexte()
    if exercice and str(exercice).strip():
        annee = str(exercice).strip()[:4]
        trimestre = ctx['trimestre'].split()[0]  # ex: "T2"
        return f"Date d'analyse : {ctx['date_jour']} | Période : {trimestre} {annee} | Année fiscale : {annee}"
    return f"Date d'analyse : {ctx['date_jour']} | Période : {ctx['trimestre']} | Année fiscale : {ctx['annee']}"


def preparer_apercu_balance(df, max_lignes=50):
    """Aperçu brut limité — utilisé uniquement pour liasse et états financiers."""
    try:
        apercu = df.head(max_lignes).to_string()
        stats = (
            f"\nSTATISTIQUES BALANCE :\n"
            f"- Nombre de lignes : {len(df):,}\n"
            f"- Colonnes : {', '.join(df.columns.tolist())}\n"
            f"- Lignes affichées : {min(max_lignes, len(df))}\n"
        )
        return stats + "\n" + apercu
    except Exception:
        return df.head(max_lignes).to_string()


def preparer_balance_agregee(df):
    """
    Agrège la balance par classe de comptes SYSCOHADA (8 classes).
    Réduit ~150 lignes → 8 lignes + top 10 comptes significatifs.
    Utilisé pour analyser_balance_syscohada → prompt léger et rapide.
    """
    try:
        col_compte = 'compte'
        col_debit  = 'debit'
        col_credit = 'credit'

        df_w = df[[col_compte, col_debit, col_credit]].copy()
        df_w[col_compte] = df_w[col_compte].astype(str).str.strip()

        # Classe = premier chiffre du numéro de compte
        df_w['classe'] = df_w[col_compte].str[0]

        noms_classes = {
            '1': 'Classe 1 — Ressources durables (Capitaux)',
            '2': 'Classe 2 — Actif immobilisé',
            '3': 'Classe 3 — Stocks',
            '4': 'Classe 4 — Tiers (Créances/Dettes)',
            '5': 'Classe 5 — Trésorerie',
            '6': 'Classe 6 — Charges',
            '7': 'Classe 7 — Produits',
            '8': 'Classe 8 — Autres charges et produits',
        }

        # Agrégation par classe
        agg = (
            df_w.groupby('classe')[[col_debit, col_credit]]
            .sum()
            .reset_index()
        )
        agg['libelle']  = agg['classe'].map(noms_classes).fillna('Autre')
        agg['solde_net'] = agg[col_debit] - agg[col_credit]

        # Totaux généraux
        total_debit  = df_w[col_debit].sum()
        total_credit = df_w[col_credit].sum()
        equilibre    = abs(total_debit - total_credit) < 1

        # Top 10 comptes par montant absolu
        df_w['montant_abs'] = (df_w[col_debit] + df_w[col_credit]).abs()
        top10 = df_w.nlargest(10, 'montant_abs')[[col_compte, col_debit, col_credit]]

        # Libellés si disponibles
        if 'libelle' in df.columns:
            top10 = top10.merge(
                df[['compte', 'libelle']].rename(columns={'compte': col_compte}),
                on=col_compte, how='left'
            )

        # Formatage texte avec _fmt_fcfa
        lignes = ["BALANCE AGRÉGÉE PAR CLASSE SYSCOHADA :", ""]
        for _, row in agg.iterrows():
            lignes.append(
                f"  {row['libelle']:<45} "
                f"Débit: {_fmt_fcfa(row[col_debit]):>15}  "
                f"Crédit: {_fmt_fcfa(row[col_credit]):>15}  "
                f"Solde net: {_fmt_fcfa(row['solde_net']):>+15}"
            )
        lignes += [
            "",
            f"  {'TOTAL BALANCE':<45} "
            f"Débit: {_fmt_fcfa(total_debit):>15}  "
            f"Crédit: {_fmt_fcfa(total_credit):>15}",
            f"  Équilibre débit/crédit : {'✅ OUI' if equilibre else '❌ NON — écart : ' + _fmt_fcfa(abs(total_debit-total_credit))}",
            "",
            f"Nombre total de comptes : {len(df)}",
            "",
            "TOP 10 COMPTES LES PLUS SIGNIFICATIFS :",
        ]
        for _, row in top10.iterrows():
            lib = row.get('libelle', '')
            lignes.append(
                f"  Compte {row[col_compte]} {str(lib)[:30]:<30} "
                f"D: {_fmt_fcfa(row[col_debit]):>12}  C: {_fmt_fcfa(row[col_credit]):>12}"
            )

        return "\n".join(lignes)

    except Exception as e:
        # Fallback : aperçu brut limité
        return preparer_apercu_balance(df, max_lignes=30)


# =============================================================================
# ANALYSE BALANCE SYSCOHADA
# =============================================================================
def analyser_balance_syscohada(df, code_pays="SN", exercice=None):
    """
    Analyse une balance comptable selon les normes SYSCOHADA.
    v2.3 : utilise mistral-small-latest + agrégation par classe (prompt ~10x plus léger).
    """
    try:
        pays_base       = get_info_pays(code_pays)
        pays_2025       = get_info_pays_2025(code_pays)
        devise          = pays_base.get("devise", "FCFA (XOF)")
        nom_pays        = pays_base.get("nom", pays_2025.get("nom", ""))
        langue          = pays_base.get("langue", "fr")
        instruction     = get_instruction_langue(langue)
        contexte_date   = preparer_contexte_date(exercice=exercice)
        contexte_fiscal = get_contexte_fiscal_complet(code_pays)

        # Agrégation : ~150 lignes → 8 classes + top 10
        apercu = preparer_balance_agregee(df)

        # Actualités RSS (3 max)
        actualites_txt = ""
        if RSS_DISPONIBLE:
            try:
                articles = get_actualites_pays(code_pays, max_articles=3)
                actualites_txt = formater_actualites_pour_prompt(articles, nom_pays)
            except Exception:
                actualites_txt = ""

        annee_exercice = str(exercice).strip()[:4] if exercice and str(exercice).strip() else str(get_date_contexte()['annee'])

        prompt = f"""
Tu es un expert-comptable SYSCOHADA/OHADA senior dans un cabinet d'expertise comptable.
{instruction}
{contexte_date}
{contexte_fiscal}
{actualites_txt}

IMPORTANT : La balance analysée concerne l'exercice fiscal {annee_exercice}.
Ne génère PAS de header ou titre de rapport. Commence directement par l'analyse.
Toutes les références temporelles (obligations fiscales, délais, SIG) doivent être
basées sur l'exercice {annee_exercice}, pas sur la date d'aujourd'hui.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DONNÉES DE LA BALANCE — EXERCICE {annee_exercice} :
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{apercu}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ANALYSE REQUISE — EXERCICE {annee_exercice} :
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. STRUCTURE DE LA BALANCE SYSCOHADA
   - Équilibre débit/crédit et anomalies de classification
2. ANALYSE FINANCIÈRE SYSCOHADA
   - FRNG, BFR, Trésorerie Nette, Autonomie financière
3. SOLDES INTERMÉDIAIRES DE GESTION (SIG) — OHADA
   - MBM, VA, EBE, Résultat d'exploitation, RAO, Résultat net
4. OBLIGATIONS FISCALES {nom_pays.upper()} — EXERCICE {annee_exercice}
   - TVA estimée, IS provisionnel, risques de redressement
5. ANOMALIES ET RISQUES DÉTECTÉS
   - Comptes sensibles, non-conformités SYSCOHADA
6. RECOMMANDATIONS
   - Actions correctives et optimisations fiscales légales

Tous les montants en {devise}. Style rapport professionnel de cabinet. Sois concis et précis.
"""
        # mistral-small-latest : rapide (5-15s), suffisant pour l'analyse de balance agrégée
        return appel_mistral(prompt, model=MODEL_FAST)

    except Exception as e:
        return f"❌ Erreur analyse balance SYSCOHADA : {e}"


# =============================================================================
# LIASSE FISCALE
# =============================================================================
def analyser_liasse_fiscale(df, code_pays="SN", exercice="2025"):
    """
    Génère une liasse fiscale complète avec données 2025/2026 actualisées.
    Utilise mistral-large-latest (analyse fiscale complexe).
    """
    try:
        pays_base       = get_info_pays(code_pays)
        pays_2025       = get_info_pays_2025(code_pays)
        devise          = pays_base.get("devise", "FCFA (XOF)")
        nom_pays        = pays_base.get("nom", pays_2025.get("nom", ""))
        langue          = pays_base.get("langue", "fr")
        instruction     = get_instruction_langue(langue)
        contexte_date   = preparer_contexte_date()
        contexte_fiscal = get_contexte_fiscal_complet(code_pays)
        apercu          = preparer_apercu_balance(df, max_lignes=50)

        taux        = pays_2025.get("taux", {})
        echeances   = pays_2025.get("echeances_2025", pays_base.get("echeances", {}))
        reformes    = pays_2025.get("reformes_2025", [])
        penalites   = pays_2025.get("penalites", {})
        organisme   = pays_2025.get("organisme_fiscal", "Administration fiscale")
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
        return appel_mistral(prompt, model=MODEL_MEDIUM)

    except Exception as e:
        return f"❌ Erreur liasse fiscale : {e}"


# =============================================================================
# VEILLE FISCALE UEMOA
# =============================================================================
def veille_fiscale_uemoa(code_pays="SN"):
    """
    Génère une veille fiscale complète et actualisée 2025/2026
    avec RSS en temps réel + données officielles.
    Utilise mistral-large-latest (analyse riche sans données balance).
    """
    try:
        pays_base       = get_info_pays(code_pays)
        pays_2025       = get_info_pays_2025(code_pays)
        nom_pays        = pays_base.get("nom", pays_2025.get("nom", ""))
        langue          = pays_base.get("langue", "fr")
        instruction     = get_instruction_langue(langue)
        contexte_date   = preparer_contexte_date()
        contexte_fiscal = get_contexte_fiscal_complet(code_pays)

        digitalisation_ohada = "\n".join([f"  • {d}" for d in REFORMES_OHADA_2025.get("digitalisation", [])])
        jurisprudence_ohada  = "\n".join([f"  • {j}" for j in REFORMES_OHADA_2025.get("jurisprudence_2024_2025", [])])

        actualites_txt = ""
        if RSS_DISPONIBLE:
            try:
                articles = get_actualites_pays(code_pays, max_articles=5)
                actualites_txt = formater_actualites_pour_prompt(articles, nom_pays)
            except Exception:
                actualites_txt = "[Flux RSS non disponible — données officielles utilisées]"
        else:
            actualites_txt = "[Module RSS non installé — données officielles utilisées]"

        taux        = pays_2025.get("taux", {})
        echeances   = pays_2025.get("echeances_2025", {})
        reformes    = pays_2025.get("reformes_2025", [])
        penalites   = pays_2025.get("penalites", {})
        organisme   = pays_2025.get("organisme_fiscal", "")
        seuils      = pays_2025.get("seuils", {})
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
1. SYNTHÈSE EXÉCUTIVE (5 lignes max)
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
   - 5 actions prioritaires ce trimestre
   - Points de vigilance pour l'exercice en cours
   - Opportunités d'optimisation fiscale légale
8. SOURCES ET RÉFÉRENCES
   - Textes officiels applicables
   - Liens utiles : {pays_2025.get('site_officiel', '')}
Style : Note de veille fiscale d'un grand cabinet. Ton : Professionnel, précis, actionnable.
"""
        return appel_mistral(prompt, model=MODEL_MEDIUM)

    except Exception as e:
        return f"❌ Erreur veille fiscale : {e}"


def page_analyse_balance():
    import streamlit as st
    import pandas as pd
    from datetime import datetime
    from utils.syscohada_helpers import (
        selectionner_entreprise, charger_balance_avec_ui, valider_structure_balance,
        sauvegarder_si_entreprise, telecharger_html, telecharger_word,
        get_info_pays, get_code_pays,
    )
    from data.plan_comptable_syscohada import PLAN_COMPTABLE, FISCALITE_UEMOA, rechercher_comptes
    from utils.ai import appel_mistral
    from utils.rendu_financier import afficher_rapport
    info_pays = get_info_pays()
    code_pays = get_code_pays()
    st.title(f"📊 Analyse Balance SYSCOHADA — {info_pays['nom']}")
    st.divider()
    ent_id, ent_nom, exercice = selectionner_entreprise("bal")
    # ── STATE INIT ────────────────────────────────────────────────────────────
    for k, v in [('bal_resultat', None), ('bal_nom_fichier', None),
                 ('bal_df_brut', None), ('bal_df_propre', None), ('bal_infos_col', None)]:
        if k not in st.session_state:
            st.session_state[k] = v

    fichier = st.file_uploader("📎 Importer une balance (Excel ou CSV)", type=["xlsx", "csv"])
    if fichier:
        if st.session_state.get('bal_nom_fichier') != fichier.name:
            # Nouveau fichier → reset complet
            for k in ['bal_resultat', 'bal_df_brut', 'bal_df_propre', 'bal_infos_col']:
                st.session_state[k] = None
            st.session_state.bal_nom_fichier = fichier.name

        try:
            # ── ÉTAPE 1 : lecture brute pour affichage ─────────────────
            if st.session_state.bal_df_brut is None:
                if fichier.name.endswith('.xlsx'):
                    st.session_state.bal_df_brut = pd.read_excel(fichier, header=None, nrows=30)
                else:
                    try:
                        st.session_state.bal_df_brut = pd.read_csv(
                            fichier, encoding='utf-8', header=None, nrows=30)
                    except Exception:
                        fichier.seek(0)
                        st.session_state.bal_df_brut = pd.read_csv(
                            fichier, encoding='latin-1', header=None, nrows=30)

            df_brut = st.session_state.bal_df_brut

            # ── ÉTAPE 2 : sélection de la ligne d'en-tête ─────────────
            st.subheader("1⃣ Identifier la ligne d'en-tête")
            st.caption("👇 Repérez la ligne contenant 'Compte', 'Libellé', 'Débit', 'Crédit' et indiquez son numéro.")

            df_affichage = df_brut.head(20).copy()
            df_affichage.index.name = "N° ligne"
            st.dataframe(df_affichage, use_container_width=True)

            # Détection automatique du meilleur header
            mots_header = ['compte', 'n°', 'numero', 'libelle', 'libellé',
                           'intitule', 'intitulé', 'débit', 'debit', 'crédit', 'credit',
                           'mouvement', 'solde']
            default_header = 0
            for _idx in range(min(20, len(df_brut))):
                _vals = [str(v).lower().strip() for v in df_brut.iloc[_idx].values if pd.notna(v)]
                if sum(1 for mot in mots_header if any(mot in v for v in _vals)) >= 2:
                    default_header = _idx
                    break

            header_row = st.number_input(
                "Numéro de la ligne d'en-tête",
                min_value=0, max_value=len(df_brut) - 1,
                value=default_header, step=1,
                help="Ligne contenant les noms de colonnes. Détectée automatiquement — ajustez si nécessaire."
            )

            # ── ÉTAPE 3 : bouton Charger ───────────────────────────────
            if st.button("✅ Charger avec cette ligne d'en-tête", type="primary"):
                fichier.seek(0)
                if fichier.name.endswith('.xlsx'):
                    df = pd.read_excel(fichier, header=int(header_row))
                else:
                    try:
                        df = pd.read_csv(fichier, encoding='utf-8', header=int(header_row))
                    except Exception:
                        fichier.seek(0)
                        df = pd.read_csv(fichier, encoding='latin-1', header=int(header_row))

                df = df.dropna(axis=1, how='all')
                df = df.dropna(how='all')

                cols_visibles = [c for c in df.columns.astype(str).tolist()
                                 if not c.startswith('Unnamed')]
                st.success(
                    f"✅ Fichier chargé — en-tête ligne {header_row}. "
                    f"Colonnes : {', '.join(cols_visibles) if cols_visibles else '(détection positionnelle active)'}"
                )

                valide, infos_col, df_propre = valider_structure_balance(df)
                if not valide:
                    st.error(f"❌ {infos_col}")
                    st.session_state.bal_df_propre = None
                elif len(df_propre) == 0:
                    st.error("❌ Aucune ligne exploitable trouvée après nettoyage.")
                    st.session_state.bal_df_propre = None
                else:
                    # Stocker df_propre dans session_state pour survivre au rerun
                    st.session_state.bal_df_propre = df_propre
                    st.session_state.bal_infos_col = infos_col
                    st.session_state.bal_resultat = None  # reset analyse précédente

            # ── ÉTAPE 4 : aperçu + bouton Analyser (hors du bloc Charger) ──
            if st.session_state.bal_df_propre is not None:
                df_propre  = st.session_state.bal_df_propre
                infos_col  = st.session_state.bal_infos_col

                with st.expander("👀 Aperçu des données nettoyées"):
                    st.dataframe(df_propre.head(20), use_container_width=True)
                st.success(f"✅ {len(df_propre)} lignes exploitables. Prêt pour l'analyse !")
                st.caption(
                    f"Mapping : compte={infos_col.get('compte')}, "
                    f"libellé={infos_col.get('libelle')}, "
                    f"débit={infos_col.get('debit')}, crédit={infos_col.get('credit')}"
                )

                if st.button("🔍 Analyser la balance", type="primary", use_container_width=True):
                    with st.spinner("Analyse SYSCOHADA en cours..."):
                        logger.info(f"Analyse balance pour {ent_nom or 'N/A'} - Exercice {exercice}")
                        # Correction : On passe l'exercice ici
                        resultat = analyser_balance_syscohada(df_propre, code_pays, exercice=exercice)
                        st.session_state.bal_resultat = resultat

            # ── ÉTAPE 5 : affichage du résultat ───────────────────────
            if st.session_state.bal_resultat:
                # ── KPIs visuels directs (avant le rapport narratif) ──────
                _df_kpi = st.session_state.get("bal_df_propre")
                _infos_kpi = st.session_state.get("bal_infos_col") or {}
                if _df_kpi is not None:
                    try:
                        def _num(s):
                            return pd.to_numeric(
                                s.astype(str).str.replace(',', '.').str.replace(' ', ''),
                                errors='coerce'
                            ).fillna(0)
                        _cd = _infos_kpi.get('debit')
                        _cc = _infos_kpi.get('credit')
                        _cpt = _infos_kpi.get('compte')
                        if _cd and _cc and _cd in _df_kpi.columns and _cc in _df_kpi.columns:
                            _d = _num(_df_kpi[_cd])
                            _c = _num(_df_kpi[_cc])
                            _td = _d.sum(); _tc = _c.sum()
                            _ecart = abs(_td - _tc)
                            _nb = _df_kpi[_cpt].nunique() if _cpt and _cpt in _df_kpi.columns else len(_df_kpi)
                            st.markdown("#### 📊 KPIs Balance")
                            _m1, _m2, _m3, _m4 = st.columns(4)
                            _m1.metric("📥 Total Débit",   _fmt(_td))
                            _m2.metric("📤 Total Crédit",  _fmt(_tc))
                            _m3.metric("⚖️ Équilibre",
                                       "✅ OK" if _ecart < 1 else f"⚠️ {int(round(_ecart)):,}".replace(",", " "))
                            _m4.metric("🔢 Nb comptes", f"{_nb:,}")
                            # Résultat par classe
                            if _cpt and _cpt in _df_kpi.columns:
                                _cls = _df_kpi[_cpt].astype(str).str.strip().str[0]
                                _charges  = (_d[_cls == '6'] - _c[_cls == '6']).sum()
                                _produits = (_c[_cls == '7'] - _d[_cls == '7']).sum()
                                if _produits != 0 or _charges != 0:
                                    _res = _produits - _charges
                                    _mr1, _mr2, _mr3 = st.columns(3)
                                    _mr1.metric("📈 Produits cl.7", _fmt(_produits))
                                    _mr2.metric("📉 Charges cl.6",  _fmt(_charges))
                                    _mr3.metric("💹 Résultat",       _fmt(_res),
                                                delta="Bénéfice" if _res >= 0 else "Déficit")
                    except Exception:
                        pass
                    st.divider()

                st.subheader("📊 Analyse IA SYSCOHADA :")
                afficher_rapport(st.session_state.bal_resultat, afficher_kpis_auto=True, afficher_alertes_auto=True, afficher_tables_auto=True)
                st.divider()
                col1, col2, col3 = st.columns(3)
                with col1:
                    telecharger_html("Analyse_Balance_SYSCOHADA", st.session_state.bal_resultat)
                with col2:
                    telecharger_word("Analyse_Balance_SYSCOHADA", st.session_state.bal_resultat,
                                     ent_nom, info_pays['nom'], exercice)
                with col3:
                    if st.button("💾 Sauvegarder dans dossier", use_container_width=True):
                        sauvegarder_si_entreprise(ent_id, "📊 Balance", fichier.name,
                                                  st.session_state.bal_resultat,
                                                  info_pays['nom'], exercice)

                # ── Analyse IA Approfondie ────────────────────────────────
                st.divider()
                st.markdown("### 🤖 Analyse IA Expert-Comptable OHADA")
                st.caption("KPIs calculés depuis votre balance + analyse narrative Mistral AI selon normes SYSCOHADA.")
                if st.button("🤖 Lancer l'analyse IA approfondie", use_container_width=True):
                    # ── 1. KPIs visuels calculés depuis df_propre ──────────
                    try:
                        import pandas as _pd
                        _df = df_propre.copy()
                        # Détecter colonnes numériques Débit / Crédit
                        def _to_num(series):
                            return _pd.to_numeric(
                                series.astype(str).str.replace(',', '.').str.replace(' ', ''),
                                errors='coerce'
                            ).fillna(0)

                        _col_d = next((c for c in _df.columns if 'debit' in str(c).lower() or 'débit' in str(c).lower()), None)
                        _col_c = next((c for c in _df.columns if 'credit' in str(c).lower() or 'crédit' in str(c).lower()), None)
                        _col_cpt = next((c for c in _df.columns if 'compte' in str(c).lower() or 'comptenum' in str(c).lower()), None)

                        if _col_d and _col_c:
                            _d = _to_num(_df[_col_d])
                            _c = _to_num(_df[_col_c])
                            _total_d  = _d.sum()
                            _total_c  = _c.sum()
                            _ecart    = abs(_total_d - _total_c)
                            _nb_cpts  = _df[_col_cpt].nunique() if _col_cpt else len(_df)

                            # Résultat estimé (classe 7 - classe 6)
                            _result = None
                            if _col_cpt:
                                _cls = _df[_col_cpt].astype(str).str.strip().str[0]
                                _charges = (_d[_cls == '6'] - _c[_cls == '6']).sum()
                                _produits = (_c[_cls == '7'] - _d[_cls == '7']).sum()
                                if _produits != 0:
                                    _result = _produits - _charges

                            st.markdown("#### 📊 KPIs de la Balance")
                            _k1, _k2, _k3, _k4 = st.columns(4)
                            _k1.metric("📥 Total Débit", _fmt(_total_d))
                            _k2.metric("📤 Total Crédit", _fmt(_total_c))
                            _k3.metric(
                                "⚖️ Équilibre",
                                "✅ Équilibré" if _ecart < 1 else f"⚠️ Écart {int(round(_ecart)):,}".replace(",", " "),
                                delta=None
                            )
                            _k4.metric("🔢 Nb comptes", _nb_cpts)

                            if _result is not None:
                                _kr1, _kr2, _kr3 = st.columns(3)
                                _kr1.metric("📈 Produits (cl.7)", _fmt(_produits))
                                _kr2.metric("📉 Charges (cl.6)", _fmt(_charges))
                                _kr3.metric(
                                    "💹 Résultat estimé",
                                    _fmt(_result),
                                    delta=f"{'Bénéfice' if _result >= 0 else 'Déficit'}"
                                )
                        else:
                            st.info("ℹ️ Colonnes Débit/Crédit non détectées — KPIs non disponibles.")
                    except Exception as _ke:
                        st.warning(f"KPIs non calculés : {_ke}")

                    # ── 2. Analyse narrative Mistral AI ────────────────────
                    st.divider()
                    st.markdown("#### 🤖 Analyse narrative Mistral AI")
                    with st.spinner("🤖 Mistral AI analyse votre balance SYSCOHADA..."):
                        try:
                            from utils.compta_auto import analyse_balance_ai
                            analyse_ia = analyse_balance_ai(df_propre, exercice=exercice)
                            st.markdown(analyse_ia)
                            sauvegarder_si_entreprise(ent_id, "🤖 Analyse IA", "ia_balance",
                                                      analyse_ia, info_pays['nom'], exercice)
                        except ImportError as _e:
                            st.error(f"Module compta_auto indisponible : {_e}")
                        except Exception as _e:
                            st.error(f"Erreur analyse IA : {_e}")

        except Exception as e:
            st.error(f"❌ Erreur : {e}")
            logger.error(f"Erreur analyse balance : {e}")

    # =============================================================================
    # PAGE : BILAN SYSCOHADA
    # =============================================================================


def page_liasse_fiscale():
    import streamlit as st
    import pandas as pd
    from datetime import datetime
    from utils.syscohada_helpers import (
        selectionner_entreprise, charger_balance_avec_ui, valider_structure_balance,
        sauvegarder_si_entreprise, telecharger_html, telecharger_word,
        get_info_pays, get_code_pays,
    )
    from data.plan_comptable_syscohada import PLAN_COMPTABLE, FISCALITE_UEMOA, rechercher_comptes
    from utils.ai import appel_mistral
    from utils.rendu_financier import afficher_rapport
    info_pays = get_info_pays()
    code_pays = get_code_pays()
    st.title(f"🧾 Liasse Fiscale — {info_pays['nom']}")
    st.divider()
    ent_id, ent_nom, exercice = selectionner_entreprise("liasse")
    if 'liasse_resultat' not in st.session_state:
        st.session_state.liasse_resultat = None
    if 'liasse_nom_fichier' not in st.session_state:
        st.session_state.liasse_nom_fichier = None
    fichier = st.file_uploader("📎 Importer une balance (Excel ou CSV)", type=["xlsx", "csv"])
    if fichier:
        if st.session_state.get('liasse_nom_fichier') != fichier.name:
            st.session_state.liasse_resultat = None
            st.session_state.liasse_nom_fichier = fichier.name
        try:
            df_propre, infos_col = charger_balance_avec_ui(fichier, "liasse")
            if df_propre is not None:
                with st.expander("👀 Aperçu"):
                    st.dataframe(df_propre.head(20), use_container_width=True)
                st.success(f"✅ {len(df_propre)} lignes exploitables détectées.")
                if st.button("🧾 Générer la Liasse Fiscale", type="primary", use_container_width=True):
                    with st.spinner("Génération en cours..."):
                        logger.info(f"Génération Liasse Fiscale pour {ent_nom or 'entreprise non sélectionnée'}")
                        resultat = analyser_liasse_fiscale(df_propre, code_pays, exercice)
                        st.session_state.liasse_resultat = resultat
                if st.session_state.liasse_resultat:
                    st.subheader("🧾 Liasse Fiscale :")
                    afficher_rapport(st.session_state.liasse_resultat, afficher_kpis_auto=True, afficher_alertes_auto=True, afficher_tables_auto=True)
                    st.divider()
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        telecharger_html("Liasse_Fiscale", st.session_state.liasse_resultat)
                    with col2:
                        telecharger_word("Liasse_Fiscale", st.session_state.liasse_resultat,
                                         ent_nom, info_pays['nom'], exercice)
                    with col3:
                        if st.button("💾 Sauvegarder dans dossier", use_container_width=True):
                            sauvegarder_si_entreprise(ent_id, "🧾 Liasse", f"Liasse {exercice}",
                                                      st.session_state.liasse_resultat,
                                                      info_pays['nom'], exercice)
        except Exception as e:
            st.error(f"❌ Erreur : {e}")
            logger.error(f"Erreur génération Liasse Fiscale : {e}")

    # =============================================================================
    # PAGE : PLAN COMPTABLE OHADA
    # =============================================================================


def page_plan_comptable():
    import streamlit as st
    import pandas as pd
    from datetime import datetime
    from utils.syscohada_helpers import (
        selectionner_entreprise, charger_balance_avec_ui, valider_structure_balance,
        sauvegarder_si_entreprise, telecharger_html, telecharger_word,
        get_info_pays, get_code_pays,
    )
    from data.plan_comptable_syscohada import PLAN_COMPTABLE, FISCALITE_UEMOA, rechercher_comptes
    from utils.rendu_financier import afficher_rapport
    info_pays = get_info_pays()
    code_pays = get_code_pays()
    st.title("🔍 Plan Comptable OHADA")
    st.divider()
    onglet1, onglet2 = st.tabs(["🔎 Recherche", "📜 Plan Complet"])
    with onglet1:
        st.subheader("Rechercher un compte")
        mot_cle = st.text_input("Numéro ou libellé du compte")
        if mot_cle:
            resultats = rechercher_comptes(mot_cle)
            if resultats:
                df_res = pd.DataFrame(
                    list(resultats.items()),
                    columns=["Numéro", "Libellé"]
                )
                st.dataframe(df_res, use_container_width=True)
                logger.info(f"Recherche compte : '{mot_cle}' - {len(resultats)} résultat(s)")
            else:
                st.warning("Aucun compte trouvé.")
    with onglet2:
        st.subheader("Plan Comptable SYSCOHADA Complet")
        classe = st.selectbox("Classe de comptes", [
            "Classe 1 — Ressources durables",
            "Classe 2 — Actif immobilisé",
            "Classe 3 — Stocks",
            "Classe 4 — Tiers",
            "Classe 5 — Trésorerie",
            "Classe 6 — Charges",
            "Classe 7 — Produits",
            "Classe 8 — Autres charges et produits"
        ])
        num_classe = classe[6]
        comptes_classe = {
            k: v for k, v in PLAN_COMPTABLE.items()
            if k.startswith(num_classe)
        }
        if comptes_classe:
            df_classe = pd.DataFrame(
                list(comptes_classe.items()),
                columns=["Numéro", "Libellé"]
            )
            st.dataframe(df_classe, use_container_width=True)
            st.caption(f"{len(comptes_classe)} comptes dans la {num_classe}")
        else:
            st.info("Aucun compte pour cette classe.")

