# -*- coding: utf-8 -*-
"""
RevisionPro SYSCOHADA - SMD Consulting
Application de supervision comptable selon normes OHADA/UEMOA
Auteur: Souleymane Diallo
Version: 2.3 (Fix formatage FCFA avec espaces)
"""
import streamlit as st
import pandas as pd
import base64
import logging
from datetime import datetime
from utils.ai import appel_mistral
from utils.rendu_financier import afficher_rapport
from utils.permissions import afficher_badge_role, afficher_quota_sidebar, check_quota, log_user_action
from utils.security import sanitize_filename
from utils.etats_financiers import (
    generer_bilan_syscohada,
    generer_compte_resultat_syscohada,
    generer_tafire,
    generer_notes_annexes
)
from utils.analyse_syscohada import (
    analyser_balance_syscohada,
    analyser_liasse_fiscale,
    veille_fiscale_uemoa
)
from utils.export_word import export_analyse_word
from utils.database import (
    init_db, creer_entreprise, lister_entreprises,
    get_entreprise, supprimer_entreprise,
    sauvegarder_analyse, lister_analyses,
    get_analyse, supprimer_analyse
)
from data.plan_comptable_syscohada import (
    PLAN_COMPTABLE, FISCALITE_UEMOA,
    get_pays_uemoa, get_info_pays, rechercher_comptes
)
from auth import login, logout, is_connecte
from utils.database import creer_user
from utils.export_excel import export_etats_financiers_excel
from smd_streamlit import page_dashboard, page_risque_fiscal, page_analyse_facture
from liasse_sn import generer_liasse_sn
from smd_calendar import page_calendrier_fiscal
from smd_aging import page_balance_agee
from smd_reconciliation import page_rapprochement_bancaire
from smd_tresorerie import page_tresorerie_previsionnelle
from smd_plan_financement import page_plan_financement
from smd_tft import page_tft

# =============================================================================
# CONFIGURATION LOGGING
# =============================================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constantes
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB en octets

def fcfa(v, devise="FCFA"):
    """Formate un montant FCFA : séparateur milliers = espace, sans centimes.
    Ex: 27848289276 → '27 848 289 276 FCFA'"""
    try:
        # Formatage avec virgule pour les milliers (style anglais) puis remplacement par espace
        return f"{int(round(float(v))):,}".replace(",", " ") + f" {devise}"
    except Exception:
        return f"{v} {devise}"

# =============================================================================
# INITIALISATION
# =============================================================================
init_db()
st.set_page_config(
    page_title="RevisionPro SYSCOHADA",
    layout="wide",
    page_icon="🌍",
    initial_sidebar_state="expanded"
)

# =============================================================================
# AUTHENTIFICATION
# =============================================================================
if not is_connecte():
    st.title("🔒 RevisionPro SYSCOHADA")
    st.subheader("Contrôle & Conformité SYSCOHADA — Cabinets & PME/TPE")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style='background:#f0fdf4;padding:12px;border-radius:8px;margin-bottom:10px;font-size:0.85em'>
        ✅ <b>Données sécurisées</b> — Hébergées sur Supabase (UE)<br>
        ✅ <b>Analyse confidentielle</b> — Vos données ne quittent pas votre environnement<br>
        ✅ <b>Normes SYSCOHADA</b> — 8 pays UEMOA couverts
        </div>
        """, unsafe_allow_html=True)
        tab_login, tab_signup = st.tabs(["🔑 Se connecter", "📝 Créer un compte"])
        with tab_login:
            st.markdown("")
            email_l    = st.text_input("📧 Email", placeholder="contact@cabinet.com", key="login_email")
            password_l = st.text_input("🔑 Mot de passe", type="password", key="login_pw")
            if st.button("🚀 Se connecter", type="primary", use_container_width=True):
                if login(email_l, password_l):
                    st.success("✅ Connexion réussie !")
                    logger.info(f"Connexion réussie pour l'utilisateur : {email_l}")
                    st.rerun()
                else:
                    st.error("❌ Email ou mot de passe incorrect")
                    logger.warning(f"Tentative de connexion échouée pour : {email_l}")
            st.markdown("---")
            st.markdown("##### 🎯 Tester sans inscription")
            if st.button("👀 Accès Démonstration", use_container_width=True, key="btn_demo"):
                st.session_state["authenticated"] = True
                st.session_state["user_email"]    = "demo@smdconsulting.pro"
                st.session_state["role"]          = "demo"
                st.session_state["nom"]           = "Démonstration"
                st.session_state["cabinet"]       = "Demo"
                st.session_state["login_time"]    = datetime.now().isoformat()
                logger.info("Connexion en mode démonstration")
                st.rerun()
        with tab_signup:
            from utils.page_inscription import page_inscription
            page_inscription(app_name="syscohada")
        st.markdown("---")
        st.caption("📧 Support : contact@smdconsulting.pro")
    st.divider()
    st.caption("SMD Consulting © 2026 — RevisionPro SYSCOHADA")
    st.stop()

# =============================================================================
# STYLE GLOBAL
# =============================================================================
st.markdown("""
<style>
body { font-family: 'Segoe UI', sans-serif; }
table { width: 100%; border-collapse: collapse; }
th, td { border: 1px solid #ddd; padding: 8px; }
th { background-color: #1f77b4; color: white; font-weight: bold; }
tr:nth-child(even) { background-color: #f9f9f9; }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# FONCTIONS UTILITAIRES AMÉLIORÉES
# =============================================================================
def charger_fichier(fichier):
    """
    Charge un fichier CSV ou XLSX avec détection multi-niveaux.
    Gère les en-têtes sur 2 lignes (ex: 'Mouvements' + 'Débit/Crédit').
    v2.2 : conserve les colonnes sans nom (Unnamed) pour permettre
           la détection positionnelle de 'compte' et 'libellé' dans
           les exports Sage/ERP avec cellules fusionnées.
    """
    if fichier.size > MAX_FILE_SIZE:
        size_mb = fichier.size / (1024 * 1024)
        return None, f"⚠ Fichier trop volumineux ({size_mb:.1f} MB). Maximum : 10 MB.", None
    try:
        # Lecture brute sans en-tête (50 lignes)
        if fichier.name.endswith('.xlsx'):
            df_raw = pd.read_excel(fichier, header=None, nrows=50)
        else:
            try:
                df_raw = pd.read_csv(fichier, encoding='utf-8', header=None, nrows=50)
            except Exception:
                fichier.seek(0)
                df_raw = pd.read_csv(fichier, encoding='latin-1', header=None, nrows=50)
        
        mots_cles_ligne_principale = ['compte', 'numero', 'n°', 'mouvement', 'solde', 'cumul']
        mots_cles_sous_ligne = ['débit', 'debit', 'crédit', 'credit', 'libelle', 'libellé', 'intitule']
        
        header_row = 0
        sub_header_row = None
        for idx in range(min(50, len(df_raw))):
            row_values = [str(v).lower().strip() for v in df_raw.iloc[idx].values if pd.notna(v)]
            row_text = ' '.join(row_values)
            if any(mot in row_text for mot in mots_cles_ligne_principale):
                header_row = idx
                logger.info(f"Ligne principale détectée ligne {idx} : {row_values}")
                for sub_idx in range(idx + 1, min(idx + 4, len(df_raw))):
                    sub_values = [str(v).lower().strip() for v in df_raw.iloc[sub_idx].values if pd.notna(v)]
                    sub_text = ' '.join(sub_values)
                    if any(mot in sub_text for mot in mots_cles_sous_ligne):
                        sub_header_row = sub_idx
                        logger.info(f"Sous-ligne détectée ligne {sub_idx} : {sub_values}")
                        break
                break
        
        effective_header = sub_header_row if sub_header_row is not None else header_row
        fichier.seek(0)
        if fichier.name.endswith('.xlsx'):
            df = pd.read_excel(fichier, header=effective_header)
        else:
            try:
                df = pd.read_csv(fichier, encoding='utf-8', header=effective_header)
            except Exception:
                fichier.seek(0)
                df = pd.read_csv(fichier, encoding='latin-1', header=effective_header)

        # FIX v2.2 : suppression des colonnes ENTIÈREMENT vides uniquement
        df = df.dropna(axis=1, how='all')
        df = df.dropna(how='all')

        logger.info(f"Fichier chargé : {fichier.name} ({len(df)} lignes, en-tête effectif ligne {effective_header})")
        return df, None, effective_header
    except Exception as e:
        logger.error(f"Erreur chargement fichier {fichier.name} : {e}")
        return None, f"Erreur de lecture du fichier : {str(e)}", None


def valider_structure_balance(df):
    """
    Valide la structure d'une balance SYSCOHADA.
    v2.4 : fallback positionnel pour exports Sage/ERP avec en-têtes fusionnées.
    """
    if df is None or df.empty:
        return False, "Le fichier est vide ou n'a pas pu être lu.", None

    df_work = df.copy()

    # Nettoyage agressif des noms de colonnes
    col_map = {}
    for col in df_work.columns:
        cleaned = str(col).strip().lower()
        cleaned = cleaned.replace(' ', '_').replace('\n', '_').replace('-', '_')
        cleaned = cleaned.replace('(', '').replace(')', '').replace('/', '_')
        while '__' in cleaned:
            cleaned = cleaned.replace('__', '_')
        cleaned = cleaned.strip('_')
        col_map[col] = cleaned
    df_work = df_work.rename(columns=col_map)
    df_cols = list(df_work.columns)
    logger.info(f"Colonnes après nettoyage : {df_cols}")

    colonnes_acceptees = {
        'compte': [
            'compte', 'numero_compte', 'n°compte', 'n°_compte', 'num_compte',
            'account', 'n_compte', 'num', 'n°', 'numero', 'code_compte',
            'compte_general', 'compte_aux', 'n_compte_gen',
            'numéro_de_compte', 'numero_de_compte'
        ],
        'libelle': [
            'libelle', 'libellé', 'intitule', 'intitulé', 'description',
            'label', 'lib', 'libelle_compte', 'intitule_compte', 'nom_compte',
            'designation', 'libelle_general', 'libelles', 'intitules',
            'comptes', 'detail'
        ],
        'debit': [
            'debit', 'débit', 'debit_montant', 'montant_debit', 'deb', 'debits',
            'montant_deb', 'debit_cumul', 'debit_periode',
            'mouvements_debit', 'mouvement_debit', 'debits_cumules',
            'soldes_debit', 'solde_debit',
            'mouvement_débit', 'mouvements_débit', 'solde_débit', 'soldes_débit',
            'montant_débit', 'débit_période', 'débit_cumulé'
        ],
        'credit': [
            'credit', 'crédit', 'credit_montant', 'montant_credit', 'cred', 'credits',
            'montant_cred', 'credit_cumul', 'credit_periode',
            'mouvements_credit', 'mouvement_credit', 'credits_cumules',
            'soldes_credit', 'solde_credit',
            'mouvement_crédit', 'mouvements_crédit', 'solde_crédit', 'soldes_crédit',
            'montant_crédit', 'crédit_période', 'crédit_cumulé'
        ]
    }

    colonnes_trouvees = {}
    for col_type, variantes in colonnes_acceptees.items():
        found = False
        # Recherche exacte
        for variante in variantes:
            if variante in df_cols:
                colonnes_trouvees[col_type] = variante
                found = True
                break
        if found:
            continue
        # Recherche partielle
        for variante in variantes:
            for col in df_cols:
                if variante in col or col in variante:
                    colonnes_trouvees[col_type] = col
                    found = True
                    break
            if found:
                break

    # ── FALLBACK POSITIONNEL v2.4 ─────────────────────────────────────────────
    if 'compte' not in colonnes_trouvees:
        for col in df_cols:
            vals = df_work[col].dropna().astype(str)
            if len(vals) > 3:
                ratio = vals.str.match(r'^\d{3,8}$').sum() / len(vals)
                if ratio > 0.4:
                    colonnes_trouvees['compte'] = col
                    logger.info(f"Fallback positionnel 'compte' → colonne '{col}' (ratio={ratio:.2f})")
                    break

    if 'libelle' not in colonnes_trouvees:
        compte_col = colonnes_trouvees.get('compte')
        for col in df_cols:
            if col == compte_col:
                continue
            vals = df_work[col].dropna().astype(str)
            if len(vals) > 3:
                ratio_alpha = vals.str.match(r'^[A-Za-zÀ-ÿ0-9\s\-\'\.]{3,}$').sum() / len(vals)
                ratio_num   = vals.str.match(r'^\d+\.?\d*$').sum() / len(vals)
                if ratio_alpha > 0.5 and ratio_num < 0.8:
                    colonnes_trouvees['libelle'] = col
                    logger.info(f"Fallback positionnel 'libelle' → colonne '{col}' (alpha={ratio_alpha:.2f})")
                    break

    # Vérification finale
    for col_type in ['compte', 'libelle', 'debit', 'credit']:
        if col_type not in colonnes_trouvees:
            return False, (
                f"Colonne '{col_type}' manquante.\n"
                f"Colonnes trouvées : {', '.join(df.columns.astype(str).tolist())}\n"
                f"💡 Utilisez les options avancées pour forcer la ligne d'en-tête."
            ), None

    logger.info(f"Mapping détecté : {colonnes_trouvees}")

    # Renommage standardisé
    df_propre = df_work.rename(columns={v: k for k, v in colonnes_trouvees.items()})

    # Vérification critique post-renommage
    for col_requise in ['compte', 'libelle', 'debit', 'credit']:
        if col_requise not in df_propre.columns:
            return False, (
                f"Erreur interne : colonne '{col_requise}' absente après renommage.\n"
                f"Colonnes disponibles : {', '.join(df_propre.columns.tolist())}"
            ), None

    # Conversion numérique
    for col in ['debit', 'credit']:
        df_propre[col] = pd.to_numeric(df_propre[col], errors='coerce').fillna(0).astype(float)

    # Suppression lignes sans compte
    df_propre = df_propre[df_propre['compte'].notna()]
    df_propre = df_propre[df_propre['compte'].astype(str).str.strip() != '']

    # Exclusion des lignes de totaux
    mots_exclusion = ['total', 'solde', 'report', 'totaux', 'cumul', 'net', 'balance']
    pattern = '|'.join(mots_exclusion)
    df_propre = df_propre[~df_propre['compte'].astype(str).str.lower().str.contains(pattern, na=False)]
    df_propre = df_propre.reset_index(drop=True)

    infos_colonnes = {k: colonnes_trouvees[k] for k in ['compte', 'libelle', 'debit', 'credit']}
    logger.info(f"✅ Structure validée : {len(df_propre)} lignes, colonnes finales : {list(df_propre.columns)}")
    return True, infos_colonnes, df_propre


def charger_balance_avec_ui(fichier, prefix):
    """
    UI réutilisable : aperçu brut → sélection manuelle de l'en-tête → chargement validé.
    """
    raw_key    = f"_h_{prefix}_raw"
    loaded_key = f"_h_{prefix}_loaded"
    infos_key  = f"_h_{prefix}_infos"
    fname_key  = f"_h_{prefix}_fname"

    if st.session_state.get(fname_key) != fichier.name:
        for k in [raw_key, loaded_key, infos_key]:
            st.session_state[k] = None
        st.session_state[fname_key] = fichier.name

    if st.session_state.get(raw_key) is None:
        fichier.seek(0)
        if fichier.name.endswith('.xlsx'):
            st.session_state[raw_key] = pd.read_excel(fichier, header=None, nrows=30)
        else:
            try:
                st.session_state[raw_key] = pd.read_csv(fichier, encoding='utf-8', header=None, nrows=30)
            except Exception:
                fichier.seek(0)
                st.session_state[raw_key] = pd.read_csv(fichier, encoding='latin-1', header=None, nrows=30)

    df_brut = st.session_state[raw_key]

    mots_header = ['compte', 'n°', 'numero', 'libelle', 'libellé',
                   'intitule', 'intitulé', 'débit', 'debit', 'crédit', 'credit',
                   'mouvement', 'solde']
    default_header = 0
    for _idx in range(min(20, len(df_brut))):
        _vals = [str(v).lower().strip() for v in df_brut.iloc[_idx].values if pd.notna(v)]
        if sum(1 for mot in mots_header if any(mot in v for v in _vals)) >= 2:
            default_header = _idx
            break

    st.subheader("1⃣ Identifier la ligne d'en-tête")
    st.caption("👇 Repérez la ligne contenant 'Compte', 'Libellé', 'Débit', 'Crédit' et indiquez son numéro.")
    df_aff = df_brut.head(20).copy()
    df_aff.index.name = "N° ligne"
    st.dataframe(df_aff, use_container_width=True)

    header_row = st.number_input(
        "Numéro de la ligne d'en-tête",
        min_value=0, max_value=max(len(df_brut) - 1, 0),
        value=default_header, step=1,
        key=f"_h_{prefix}_hrow",
        help="Détectée automatiquement — ajustez si nécessaire."
    )

    if st.button("✅ Charger avec cette ligne d'en-tête", type="primary", key=f"_h_{prefix}_btn"):
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

        valide, infos_col, df_propre = valider_structure_balance(df)
        if not valide:
            st.error(f"❌ {infos_col}")
            st.session_state[loaded_key] = None
            st.session_state[infos_key]  = None
        elif len(df_propre) == 0:
            st.error("❌ Aucune ligne exploitable trouvée après nettoyage.")
            st.session_state[loaded_key] = None
            st.session_state[infos_key]  = None
        else:
            st.session_state[loaded_key] = df_propre
            st.session_state[infos_key]  = infos_col
            cols_vis = [c for c in df.columns.astype(str).tolist() if not c.startswith('Unnamed')]
            st.success(
                f"✅ Fichier chargé — en-tête ligne {header_row}. "
                f"Colonnes : {', '.join(cols_vis) if cols_vis else '(détection positionnelle active)'}"
            )

    return st.session_state.get(loaded_key), st.session_state.get(infos_key)


def telecharger_html(titre, contenu):
    """Génère un lien de téléchargement HTML"""
    html = f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <title>{titre}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; color: #333; }}
            h1 {{ color: #1f77b4; border-bottom: 2px solid #1f77b4; padding-bottom: 10px; }}
            pre {{ background: #f5f5f5; padding: 20px; border-radius: 8px; white-space: pre-wrap; }}
        </style>
    </head>
    <body>
        <h1>{titre}</h1>
        <pre>{contenu}</pre>
    </body>
    </html>
    """
    b64 = base64.b64encode(html.encode()).decode()
    href = f'<a href="data:text/html;base64,{b64}" download="{titre}.html">📥 Télécharger en HTML</a>'
    st.markdown(href, unsafe_allow_html=True)


def telecharger_word(titre, contenu, nom_entreprise="", pays="", exercice=""):
    """Génère un bouton de téléchargement Word"""
    try:
        buffer = export_analyse_word(titre, contenu, nom_entreprise, pays, exercice)
        st.download_button(
            label="📄 Télécharger en Word (.docx)",
            data=buffer,
            file_name=f"{sanitize_filename(titre)}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    except Exception as e:
        st.error(f"Erreur export Word : {e}")
        logger.error(f"Erreur export Word : {e}")


def sauvegarder_si_entreprise(ent_id, type_a, titre, resultat, pays_nom, exercice):
    """Sauvegarde une analyse si une entreprise est sélectionnée"""
    if ent_id:
        try:
            sauvegarder_analyse(ent_id, type_a, titre, resultat, pays_nom, exercice)
            st.success("✅ Analyse sauvegardée dans le dossier entreprise !")
            logger.info(f"Analyse sauvegardée pour entreprise {ent_id}, type: {type_a}")
        except Exception as e:
            st.error(f"Erreur sauvegarde : {e}")
            logger.error(f"Erreur sauvegarde analyse : {e}")


def selectionner_entreprise(key_prefix):
    """Widget de sélection d'entreprise réutilisable"""
    entreprises = lister_entreprises()
    ent_id = None
    ent_nom = ""
    # Exercice toujours visible, indépendamment des entreprises
    exercice = st.text_input("📅 Exercice fiscal (ex: 2024)", key=f"{key_prefix}_ex")
    if entreprises:
        st.subheader("🏢 Associer à une entreprise (optionnel)")
        options = {"-- Aucune --": None}
        options.update({f"{e[1]} ({e[2]})": e[0] for e in entreprises})
        choix = st.selectbox("Entreprise", list(options.keys()), key=f"{key_prefix}_ent")
        ent_id = options[choix]
        ent_nom = choix.split(" (")[0] if ent_id else ""
    return ent_id, ent_nom, exercice


def is_demo():
    return st.session_state.get("role") == "demo"


def banniere_demo():
    if is_demo():
        st.warning("👀 **Mode Démonstration** — Données fictives uniquement. Sauvegarde désactivée.")


def sauvegarder_si_autorise(ent_id, type_a, titre, resultat, pays_nom, exercice):
    if is_demo():
        st.info("💡 Sauvegarde désactivée en mode démonstration.")
    else:
        sauvegarder_si_entreprise(ent_id, type_a, titre, resultat, pays_nom, exercice)


# =============================================================================
# SIDEBAR - NAVIGATION
# =============================================================================
try:
    st.sidebar.image(
        "https://raw.githubusercontent.com/diallosouleymane19-rgb/superviseur-ia-syscohada/main/uemoa.png",
        width=120
    )
except Exception as e:
    logger.warning(f"Impossible de charger l'image logo : {e}")

st.sidebar.title("🌍 RevisionPro SYSCOHADA")
st.sidebar.markdown(f"👤 Connecté : **{st.session_state.get('user_email', 'Utilisateur')}**")

afficher_badge_role()
afficher_quota_sidebar()

st.sidebar.markdown("---")
if st.sidebar.button("🚪 Déconnexion", use_container_width=True):
    logger.info(f"Déconnexion utilisateur : {st.session_state.get('user_email')}")
    logout()
    st.rerun()
st.sidebar.markdown("---")
if st.session_state.get("role") == "demo":
    st.sidebar.warning("👀 Mode Démonstration")

page = st.sidebar.selectbox(
    "Navigation",
    [
        "🏠 Accueil",
        "🏢 Dossiers Entreprises",
        "─── États Financiers ───",
        "📊 Analyse Balance SYSCOHADA",
        "📋 Bilan SYSCOHADA",
        "📈 Compte de Résultat",
        "💰 TAFIRE",
        "📎 Notes Annexes",
        "📄 Liasse Fiscale Officielle 🇸🇳",
        "─── Fiscal & Réglementaire ───",
        "🧾 Liasse Fiscale",
        "🔍 Plan Comptable OHADA",
        "📰 Veille Fiscale UEMOA",
        "─── Fiscal Quantitatif ───",
        "📅 Calendrier Fiscal UEMOA",
        "📊 Tableau de Bord Fiscal",
        "🚨 Analyse du Risque Fiscal",
        "🧾 Analyse Facture SYSCOHADA",
        "💳 Balance Âgée Tiers",
        "🏦 Rapprochement Bancaire",
        "📊 Tresorerie Previsionnelle",
        "📐 Plan de Financement",
        "💹 TFT SYSCOHADA",
        "─── Connecteurs ───",
        "🔌 Connecteurs ERP",
        "─── Paramètres ───",
        "💳 Tarifs & Abonnement",
    ],
    label_visibility="collapsed"
)

separateurs = [
    "─── États Financiers ───",
    "─── Fiscal & Réglementaire ───",
    "─── Fiscal Quantitatif ───",
    "─── Connecteurs ───",
]
if page in separateurs:
    page = "🏠 Accueil"

st.sidebar.markdown("---")
st.sidebar.subheader("🌍 Pays")
pays_options = {f"{v['nom']}": k for k, v in FISCALITE_UEMOA.items()}
pays_choisi_nom = st.sidebar.selectbox("Sélectionner le pays", list(pays_options.keys()))
code_pays = pays_options[pays_choisi_nom]
info_pays = get_info_pays(code_pays)
st.sidebar.markdown(f"""
**TVA :** {info_pays['taux_tva']}%
**IS :** {info_pays['taux_is']}%
**Devise :** {info_pays['devise']}
""")

# =============================================================================
# PAGE : ACCUEIL
# =============================================================================
if page == "🏠 Accueil":
    _heure = datetime.now().hour
    _salut = "Bonsoir" if _heure >= 18 else ("Bon après-midi" if _heure >= 12 else "Bonjour")
    _nom_user = st.session_state.get("user_nom") or st.session_state.get("user_email", "")
    st.markdown(f"## 🌍 {_salut}{', ' + _nom_user if _nom_user else ''} !")
    st.markdown("### RevisionPro SYSCOHADA — Normes OHADA/UEMOA")
    st.divider()

    try:
        from utils.db_supabase import get_supabase, supabase_disponible
        _sb_ok = supabase_disponible()
        if _sb_ok:
            _sb = get_supabase()
            _nb_users   = len((_sb.table("users").select("id").eq("is_active", True).execute()).data or [])
            _mois_actuel = datetime.now().strftime("%Y-%m")
            _nb_analyses = len((_sb.table("analyses").select("id").execute()).data or [])
            _email_me    = st.session_state.get("user_email", "")
            _quota_used  = 0
            _quota_limit = 10
            if _email_me:
                from utils.auth_rbac import get_quota_used, get_quota_limit, get_user
                _quota_used  = get_quota_used(_email_me)
                _u           = get_user(_email_me)
                _quota_limit = get_quota_limit(_u) if _u else 10
    except Exception:
        _sb_ok = False; _nb_users = 0; _nb_analyses = 0; _quota_used = 0; _quota_limit = 10

    if _sb_ok:
        _kc1, _kc2, _kc3, _kc4 = st.columns(4)
        _kc1.metric("👥 Utilisateurs", _nb_users)
        _kc2.metric("📊 Analyses totales", _nb_analyses)
        _kc3.metric("📈 Quota utilisé", f"{_quota_used}/{_quota_limit if _quota_limit != -1 else '∞'}")
        _kc4.metric("🌍 Pays couverts", "8 UEMOA")
    else:
        st.warning("⚠️ Supabase non connecté — vérifiez SUPABASE_URL et SUPABASE_SERVICE_KEY dans secrets.toml")

    st.divider()
    st.markdown("### ⚡ Accès rapide")
    _ra1, _ra2, _ra3, _ra4 = st.columns(4)
    if _ra1.button("📊 Analyse Balance", use_container_width=True):
        st.session_state["_nav_page"] = "📊 Analyse Balance SYSCOHADA"
        st.rerun()
    if _ra2.button("📋 Bilan SYSCOHADA", use_container_width=True):
        st.session_state["_nav_page"] = "📋 Bilan SYSCOHADA"
        st.rerun()
    if _ra3.button("📈 Compte Résultat", use_container_width=True):
        st.session_state["_nav_page"] = "📈 Compte de Résultat"
        st.rerun()
    if _ra4.button("💰 TAFIRE", use_container_width=True):
        st.session_state["_nav_page"] = "💰 TAFIRE"
        st.rerun()

    st.divider()
    st.markdown("### 🌍 Pays membres UEMOA")
    _cols_pays = st.columns(4)
    _drapeaux = ["🇸🇳", "🇧🇯", "🇧🇫", "🇨🇮", "🇬🇼", "🇲🇱", "🇳🇪", "🇹🇬"]
    for _i, (_code, _info_p) in enumerate(FISCALITE_UEMOA.items()):
        _cols_pays[_i % 4].metric(
            f"{_drapeaux[_i]} {_info_p['nom']}",
            f"TVA {_info_p['taux_tva']}%",
            f"IS {_info_p['taux_is']}%"
        )

    st.divider()
    st.markdown("### ⚙️ Statut Plateforme")
    _sc1, _sc2, _sc3 = st.columns(3)
    with _sc1:
        if _sb_ok:
            st.success("🟢 **Supabase** connecté")
        else:
            st.error("🔴 **Supabase** hors ligne")
    with _sc2:
        _role_label = st.session_state.get("user_role", "—")
        st.info(f"👤 **Rôle** : {_role_label}")
    with _sc3:
        _plan_label = st.session_state.get("user_plan", "—")
        st.info(f"📦 **Plan** : {_plan_label}")

    st.divider()
    st.markdown("### 🔒 Vos Données Sont Protégées")
    _sp1, _sp2, _sp3 = st.columns(3)
    with _sp1:
        st.success("✅ **Anonymisation**\n\nNIF masqués, noms supprimés avant envoi")
    with _sp2:
        st.success("✅ **Non stockées**\n\nAucune conservation après analyse")
    with _sp3:
        st.success("✅ **IA éthique**\n\nDonnées non utilisées pour entraîner Mistral")
    st.divider()
    st.caption("**SMD Consulting** — RevisionPro SYSCOHADA © 2026")

# =============================================================================
# PAGE : DOSSIERS ENTREPRISES
# =============================================================================
elif page == "🏢 Dossiers Entreprises":
    st.title("🏢 Dossiers Entreprises")
    st.divider()
    onglet1, onglet2, onglet3 = st.tabs([
        "➕ Nouvelle Entreprise",
        "📋 Liste des Entreprises",
        "📊 Dossier Entreprise"
    ])
    with onglet1:
        st.subheader("➕ Créer un dossier entreprise")
        nom = st.text_input("Nom de l'entreprise *")
        col1, col2 = st.columns(2)
        with col1:
            pays_list = {v['nom']: k for k, v in FISCALITE_UEMOA.items()}
            pays_sel = st.selectbox("Pays *", list(pays_list.keys()))
            code_pays_ent = pays_list[pays_sel]
            secteur = st.text_input("Secteur d'activité")
        with col2:
            regime = st.selectbox("Régime fiscal", ["Réel Normal", "Réel Simplifié", "Forfait"])
            contact = st.text_input("Contact")
            email_ent = st.text_input("Email")
        if st.button("✅ Créer le dossier", type="primary"):
            if nom:
                creer_entreprise(nom, pays_sel, code_pays_ent, secteur, regime, contact, email_ent)
                st.success(f"✅ Dossier **{nom}** créé avec succès !")
                logger.info(f"Nouvelle entreprise créée : {nom}")
                st.rerun()
            else:
                st.warning("⚠ Le nom est obligatoire.")
    with onglet2:
        st.subheader("📋 Liste des entreprises")
        entreprises = lister_entreprises()
        if not entreprises:
            st.info("Aucune entreprise créée.")
        else:
            for ent in entreprises:
                ent_id, nom, pays, code_p, secteur, regime, contact, email_e, date_c = ent
                analyses = lister_analyses(ent_id)
                with st.expander(f"🏢 {nom} — {pays} — {len(analyses)} analyse(s)"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Pays :** {pays}")
                        st.write(f"**Secteur :** {secteur or 'Non renseigné'}")
                        st.write(f"**Régime :** {regime or 'Non renseigné'}")
                    with col2:
                        st.write(f"**Contact :** {contact or 'Non renseigné'}")
                        st.write(f"**Email :** {email_e or 'Non renseigné'}")
                        st.write(f"**Créé le :** {date_c}")
                    if st.button(f"🗑 Supprimer {nom}", key=f"del_{ent_id}"):
                        supprimer_entreprise(ent_id)
                        st.success(f"Dossier {nom} supprimé.")
                        logger.info(f"Entreprise supprimée : {nom} (ID: {ent_id})")
                        st.rerun()
    with onglet3:
        st.subheader("📊 Dossier Entreprise")
        entreprises = lister_entreprises()
        if not entreprises:
            st.info("Aucune entreprise disponible.")
        else:
            options = {f"{e[1]} ({e[2]})": e[0] for e in entreprises}
            choix = st.selectbox("Sélectionner une entreprise", list(options.keys()))
            ent_id = options[choix]
            ent_nom = choix.split(" (")[0]
            analyses = lister_analyses(ent_id)
            st.markdown(f"### 🏢 {ent_nom} — {len(analyses)} analyse(s)")
            if not analyses:
                st.info("Aucune analyse enregistrée.")
            else:
                for analyse in analyses:
                    a_id, type_a, titre, date_a, pays_a, exercice = analyse
                    with st.expander(f"{type_a} — {titre} ({date_a})"):
                        detail = get_analyse(a_id)
                        if detail:
                            st.markdown(detail[4])
                            telecharger_word(f"{type_a}_{ent_nom}", detail[4], ent_nom, pays_a, exercice)
                        if st.button("🗑 Supprimer", key=f"delA_{a_id}"):
                            supprimer_analyse(a_id)
                            logger.info(f"Analyse supprimée : ID {a_id}")
                            st.rerun()

# =============================================================================
# PAGE : ANALYSE BALANCE SYSCOHADA
# =============================================================================
elif page == "📊 Analyse Balance SYSCOHADA":
    st.title(f"📊 Analyse Balance SYSCOHADA — {info_pays['nom']}")
    st.divider()
    ent_id, ent_nom, exercice = selectionner_entreprise("bal")
    
    for k, v in [('bal_resultat', None), ('bal_nom_fichier', None),
                 ('bal_df_brut', None), ('bal_df_propre', None), ('bal_infos_col', None)]:
        if k not in st.session_state:
            st.session_state[k] = v

    fichier = st.file_uploader("📎 Importer une balance (Excel ou CSV)", type=["xlsx", "csv"])
    if fichier:
        if st.session_state.get('bal_nom_fichier') != fichier.name:
            for k in ['bal_resultat', 'bal_df_brut', 'bal_df_propre', 'bal_infos_col']:
                st.session_state[k] = None
            st.session_state.bal_nom_fichier = fichier.name

        try:
            if st.session_state.bal_df_brut is None:
                if fichier.name.endswith('.xlsx'):
                    st.session_state.bal_df_brut = pd.read_excel(fichier, header=None, nrows=30)
                else:
                    try:
                        st.session_state.bal_df_brut = pd.read_csv(fichier, encoding='utf-8', header=None, nrows=30)
                    except Exception:
                        fichier.seek(0)
                        st.session_state.bal_df_brut = pd.read_csv(fichier, encoding='latin-1', header=None, nrows=30)

            df_brut = st.session_state.bal_df_brut

            st.subheader("1⃣ Identifier la ligne d'en-tête")
            st.caption("👇 Repérez la ligne contenant 'Compte', 'Libellé', 'Débit', 'Crédit' et indiquez son numéro.")

            df_affichage = df_brut.head(20).copy()
            df_affichage.index.name = "N° ligne"
            st.dataframe(df_affichage, use_container_width=True)

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

                cols_visibles = [c for c in df.columns.astype(str).tolist() if not c.startswith('Unnamed')]
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
                    st.session_state.bal_df_propre = df_propre
                    st.session_state.bal_infos_col = infos_col
                    st.session_state.bal_resultat = None

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

            if st.session_state.bal_resultat:
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
                            _m1.metric("📥 Total Débit",   fcfa(_td))
                            _m2.metric("📤 Total Crédit",  fcfa(_tc))
                            _m3.metric("⚖️ Équilibre",
                                       "✅ OK" if _ecart < 1 else f"⚠️ {int(round(_ecart)):,}".replace(",", " "))
                            _m4.metric("🔢 Nb comptes", f"{_nb:,}")
                            
                            if _cpt and _cpt in _df_kpi.columns:
                                _cls = _df_kpi[_cpt].astype(str).str.strip().str[0]
                                _charges  = (_d[_cls == '6'] - _c[_cls == '6']).sum()
                                _produits = (_c[_cls == '7'] - _d[_cls == '7']).sum()
                                if _produits != 0 or _charges != 0:
                                    _res = _produits - _charges
                                    _mr1, _mr2, _mr3 = st.columns(3)
                                    _mr1.metric("📈 Produits cl.7", fcfa(_produits))
                                    _mr2.metric("📉 Charges cl.6",  fcfa(_charges))
                                    _mr3.metric("💹 Résultat",       fcfa(_res),
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

                st.divider()
                st.markdown("### 🤖 Analyse IA Expert-Comptable OHADA")
                st.caption("KPIs calculés depuis votre balance + analyse narrative Mistral AI selon normes SYSCOHADA.")
                if st.button("🤖 Lancer l'analyse IA approfondie", use_container_width=True):
                    try:
                        import pandas as _pd
                        _df = df_propre.copy()
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

                            _result = None
                            if _col_cpt:
                                _cls = _df[_col_cpt].astype(str).str.strip().str[0]
                                _charges = (_d[_cls == '6'] - _c[_cls == '6']).sum()
                                _produits = (_c[_cls == '7'] - _d[_cls == '7']).sum()
                                if _produits != 0:
                                    _result = _produits - _charges

                            st.markdown("#### 📊 KPIs de la Balance")
                            _k1, _k2, _k3, _k4 = st.columns(4)
                            _k1.metric("📥 Total Débit", fcfa(_total_d))
                            _k2.metric("📤 Total Crédit", fcfa(_total_c))
                            _k3.metric(
                                "⚖️ Équilibre",
                                "✅ Équilibré" if _ecart < 1 else f"⚠️ Écart {int(round(_ecart)):,}".replace(",", " "),
                                delta=None
                            )
                            _k4.metric("🔢 Nb comptes", _nb_cpts)

                            if _result is not None:
                                _kr1, _kr2, _kr3 = st.columns(3)
                                _kr1.metric("📈 Produits (cl.7)", fcfa(_produits))
                                _kr2.metric("📉 Charges (cl.6)", fcfa(_charges))
                                _kr3.metric(
                                    "💹 Résultat estimé",
                                    fcfa(_result),
                                    delta=f"{'Bénéfice' if _result >= 0 else 'Déficit'}"
                                )
                        else:
                            st.info("ℹ️ Colonnes Débit/Crédit non détectées — KPIs non disponibles.")
                    except Exception as _ke:
                        st.warning(f"KPIs non calculés : {_ke}")

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
elif page == "📋 Bilan SYSCOHADA":
    st.title(f"📋 Bilan SYSCOHADA — {info_pays['nom']}")
    st.divider()
    ent_id, ent_nom, exercice = selectionner_entreprise("bil")
    if 'bil_resultat' not in st.session_state or not isinstance(st.session_state.bil_resultat, (dict, type(None))):
        st.session_state.bil_resultat = None
    if 'bil_nom_fichier' not in st.session_state:
        st.session_state.bil_nom_fichier = None
    fichier = st.file_uploader("📎 Importer une balance (Excel ou CSV)", type=["xlsx", "csv"])
    if fichier:
        if st.session_state.get('bil_nom_fichier') != fichier.name:
            st.session_state.bil_resultat = None
            st.session_state.bil_nom_fichier = fichier.name
        try:
            df_propre, infos_col = charger_balance_avec_ui(fichier, "bil")
            if df_propre is not None:
                with st.expander("👀 Aperçu"):
                    st.dataframe(df_propre.head(20), use_container_width=True)
                st.success(f"✅ {len(df_propre)} lignes exploitables détectées.")
                if st.button("📋 Générer le Bilan SYSCOHADA", type="primary", use_container_width=True):
                    with st.spinner("Génération du bilan en cours..."):
                        logger.info(f"Génération Bilan pour {ent_nom or 'entreprise non sélectionnée'}")
                        st.session_state.bil_resultat = generer_liasse_sn(df_propre, ent_nom, exercice)
                if isinstance(st.session_state.bil_resultat, dict):
                    liasse = st.session_state.bil_resultat
                    t = liasse['totaux']
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Total Actif",  fcfa(t['total_actif']))
                    c2.metric("Total Passif", fcfa(t['total_passif']))
                    c3.metric("Résultat Net", fcfa(t['resultat_net']))
                    eq = abs(t['total_actif'] - t['total_passif'])
                    if t['total_actif'] > 0 and eq / max(t['total_actif'], 1) < 0.01:
                        st.success("✅ Bilan équilibré")
                    elif t['total_actif'] > 0:
                        st.warning(f"⚠ Écart Actif/Passif : {fcfa(eq)}")
                    st.subheader("Bilan — Actif")
                    st.dataframe(liasse['bilan_actif'].style.apply(
                        lambda r: ['background-color:#D6E4F0;font-weight:bold'
                                   if r['REF'] in ['AZ','BZ','CZ','DZ'] else '' for _ in r], axis=1),
                        use_container_width=True, hide_index=True)
                    st.subheader("Bilan — Passif")
                    st.dataframe(liasse['bilan_passif'].style.apply(
                        lambda r: ['background-color:#D6E4F0;font-weight:bold'
                                   if r['REF'] in ['CZ','DZ','EZ','FZ','GZ','HZ'] else '' for _ in r], axis=1),
                        use_container_width=True, hide_index=True)
                    st.divider()
                    col1, col2 = st.columns(2)
                    with col1:
                        st.download_button(
                            "📊 Télécharger États Financiers (7 onglets)",
                            liasse['excel_bytes'],
                            f"Etats_Financiers_{ent_nom or 'Entreprise'}_{exercice or '2024'}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True, type="primary")
                    with col2:
                        if st.button("💾 Sauvegarder dans dossier", key="sav_bil", use_container_width=True):
                            sauvegarder_si_entreprise(ent_id, "📋 Bilan", f"Bilan {exercice}",
                                                      f"Actif:{fcfa(t['total_actif'])} | Passif:{fcfa(t['total_passif'])}",
                                                      info_pays['nom'], exercice)
        except Exception as e:
            st.error(f"❌ Erreur : {e}")
            logger.error(f"Erreur génération bilan : {e}")

# =============================================================================
# PAGE : COMPTE DE RÉSULTAT
# =============================================================================
elif page == "📈 Compte de Résultat":
    st.title(f"📈 Compte de Résultat SYSCOHADA — {info_pays['nom']}")
    st.divider()
    ent_id, ent_nom, exercice = selectionner_entreprise("cr")
    if 'cr_resultat' not in st.session_state or not isinstance(st.session_state.cr_resultat, (dict, type(None))):
        st.session_state.cr_resultat = None
    if 'cr_nom_fichier' not in st.session_state:
        st.session_state.cr_nom_fichier = None
    fichier = st.file_uploader("📎 Importer une balance (Excel ou CSV)", type=["xlsx", "csv"])
    if fichier:
        if st.session_state.get('cr_nom_fichier') != fichier.name:
            st.session_state.cr_resultat = None
            st.session_state.cr_nom_fichier = fichier.name
        try:
            df_propre, infos_col = charger_balance_avec_ui(fichier, "cr")
            if df_propre is not None:
                with st.expander("👀 Aperçu"):
                    st.dataframe(df_propre.head(20), use_container_width=True)
                st.success(f"✅ {len(df_propre)} lignes exploitables détectées.")
                if st.button("📈 Générer le Compte de Résultat", type="primary", use_container_width=True):
                    with st.spinner("Génération en cours..."):
                        logger.info(f"Génération CR pour {ent_nom or 'entreprise non sélectionnée'}")
                        st.session_state.cr_resultat = generer_liasse_sn(df_propre, ent_nom, exercice)
                if isinstance(st.session_state.cr_resultat, dict):
                    liasse = st.session_state.cr_resultat
                    t = liasse['totaux']
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Chiffre d'affaires", fcfa(t['ca']))
                    c2.metric("Résultat Net",        fcfa(t['resultat_net']))
                    c3.metric("CAF",                 fcfa(t.get('caf', 0)))
                    sig_refs = ['XA','XB','XC','XD','XE','XF','XG','XH','XI']
                    st.subheader("Compte de Résultat — SIG SYSCOHADA")
                    st.dataframe(liasse['compte_resultat'].style.apply(
                        lambda r: ['background-color:#E8F5E9;font-weight:bold'
                                   if r['REF'] in sig_refs else '' for _ in r], axis=1),
                        use_container_width=True, hide_index=True)
                    st.divider()
                    col1, col2 = st.columns(2)
                    with col1:
                        st.download_button(
                            "📊 Télécharger États Financiers (7 onglets)",
                            liasse['excel_bytes'],
                            f"Etats_Financiers_{ent_nom or 'Entreprise'}_{exercice or '2024'}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True, type="primary")
                    with col2:
                        if st.button("💾 Sauvegarder dans dossier", key="sav_cr", use_container_width=True):
                            sauvegarder_si_entreprise(ent_id, "📈 CR", f"CR {exercice}",
                                                      f"CA:{fcfa(t['ca'])} | RN:{fcfa(t['resultat_net'])}",
                                                      info_pays['nom'], exercice)
        except Exception as e:
            st.error(f"❌ Erreur : {e}")
            logger.error(f"Erreur génération CR : {e}")

# =============================================================================
# PAGE : TAFIRE
# =============================================================================
elif page == "💰 TAFIRE":
    st.title(f"💰 TAFIRE — {info_pays['nom']}")
    st.markdown("*Tableau Financier des Ressources et Emplois*")
    st.divider()
    ent_id, ent_nom, exercice = selectionner_entreprise("taf")
    if 'taf_resultat' not in st.session_state or not isinstance(st.session_state.taf_resultat, (dict, type(None))):
        st.session_state.taf_resultat = None
    if 'taf_nom_fichier' not in st.session_state:
        st.session_state.taf_nom_fichier = None
    fichier = st.file_uploader("📎 Importer une balance (Excel ou CSV)", type=["xlsx", "csv"])
    if fichier:
        if st.session_state.get('taf_nom_fichier') != fichier.name:
            st.session_state.taf_resultat = None
            st.session_state.taf_nom_fichier = fichier.name
        try:
            df_propre, infos_col = charger_balance_avec_ui(fichier, "taf")
            if df_propre is not None:
                with st.expander("👀 Aperçu"):
                    st.dataframe(df_propre.head(20), use_container_width=True)
                st.success(f"✅ {len(df_propre)} lignes exploitables détectées.")
                if st.button("💰 Générer le TAFIRE", type="primary", use_container_width=True):
                    with st.spinner("Génération du TAFIRE en cours..."):
                        logger.info(f"Génération TAFIRE pour {ent_nom or 'entreprise non sélectionnée'}")
                        st.session_state.taf_resultat = generer_liasse_sn(df_propre, ent_nom, exercice)
                if isinstance(st.session_state.taf_resultat, dict):
                    liasse = st.session_state.taf_resultat
                    t = liasse['totaux']
                    c1, c2, c3 = st.columns(3)
                    c1.metric("CAF",              fcfa(t.get('caf', 0)))
                    c2.metric("BFR",              fcfa(t.get('bfr', 0)))
                    c3.metric("Trésorerie Nette", fcfa(t.get('treso_nette', 0)))
                    tafire_refs = ["ZC","ZR","ZE","FRG","M4","M8","BFR","TN","EQ","C5"]
                    st.subheader("TAFIRE — Tableau de Financement")
                    st.dataframe(liasse['tafire'].style.apply(
                        lambda r: ['background-color:#D6E4F0;font-weight:bold'
                                   if r['REF'] in tafire_refs else '' for _ in r], axis=1),
                        use_container_width=True, hide_index=True)
                    st.divider()
                    col1, col2 = st.columns(2)
                    with col1:
                        st.download_button(
                            "📊 Télécharger États Financiers (7 onglets)",
                            liasse['excel_bytes'],
                            f"Etats_Financiers_{ent_nom or 'Entreprise'}_{exercice or '2024'}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True, type="primary")
                    with col2:
                        if st.button("💾 Sauvegarder dans dossier", key="sav_taf", use_container_width=True):
                            sauvegarder_si_entreprise(ent_id, "💰 TAFIRE", f"TAFIRE {exercice}",
                                                      f"CAF:{fcfa(t.get('caf',0))} | Tréso:{fcfa(t.get('treso_nette',0))}",
                                                      info_pays['nom'], exercice)
        except Exception as e:
            st.error(f"❌ Erreur : {e}")
            logger.error(f"Erreur génération TAFIRE : {e}")

# =============================================================================
# PAGE : NOTES ANNEXES
# =============================================================================
elif page == "📎 Notes Annexes":
    st.title(f"📎 Notes Annexes SYSCOHADA — {info_pays['nom']}")
    st.divider()
    ent_id, ent_nom, exercice = selectionner_entreprise("notes")
    if 'notes_resultat' not in st.session_state or not isinstance(st.session_state.notes_resultat, (dict, type(None))):
        st.session_state.notes_resultat = None
    if 'notes_nom_fichier' not in st.session_state:
        st.session_state.notes_nom_fichier = None
    fichier = st.file_uploader("📎 Importer une balance (Excel ou CSV)", type=["xlsx", "csv"])
    if fichier:
        if st.session_state.get('notes_nom_fichier') != fichier.name:
            st.session_state.notes_resultat = None
            st.session_state.notes_nom_fichier = fichier.name
        try:
            df_propre, infos_col = charger_balance_avec_ui(fichier, "notes")
            if df_propre is not None:
                with st.expander("👀 Aperçu"):
                    st.dataframe(df_propre.head(20), use_container_width=True)
                st.success(f"✅ {len(df_propre)} lignes exploitables détectées.")
                if st.button("📎 Générer les Notes Annexes", type="primary", use_container_width=True):
                    with st.spinner("Génération en cours..."):
                        logger.info(f"Génération Notes Annexes pour {ent_nom or 'entreprise non sélectionnée'}")
                        st.session_state.notes_resultat = generer_liasse_sn(df_propre, ent_nom, exercice)
                if isinstance(st.session_state.notes_resultat, dict):
                    liasse = st.session_state.notes_resultat
                    notes = liasse.get('notes_annexes', {})
                    if notes:
                        tab_a, tab_b, tab_c, tab_d, tab_e = st.tabs([
                            "A — Immobilisations", "B — Amortissements",
                            "C — Provisions", "D — Créances", "E — Dettes"])
                        with tab_a:
                            st.dataframe(notes['immo'].style.apply(
                                lambda r: ['background-color:#D6E4F0;font-weight:bold'
                                           if r['REF']=='AZ' else '' for _ in r], axis=1),
                                use_container_width=True, hide_index=True)
                        with tab_b:
                            st.dataframe(notes['amort'].style.apply(
                                lambda r: ['background-color:#D6E4F0;font-weight:bold'
                                           if r['COMPTE']=='TOT' else '' for _ in r], axis=1),
                                use_container_width=True, hide_index=True)
                        with tab_c:
                            st.dataframe(notes['provisions'].style.apply(
                                lambda r: ['background-color:#D6E4F0;font-weight:bold'
                                           if r['COMPTE']=='TOT' else '' for _ in r], axis=1),
                                use_container_width=True, hide_index=True)
                        with tab_d:
                            st.dataframe(notes['creances'].style.apply(
                                lambda r: ['background-color:#D6E4F0;font-weight:bold'
                                           if r['COMPTE']=='TOT' else '' for _ in r], axis=1),
                                use_container_width=True, hide_index=True)
                        with tab_e:
                            st.dataframe(notes['dettes'].style.apply(
                                lambda r: ['background-color:#D6E4F0;font-weight:bold'
                                           if r['COMPTE']=='TOT' else '' for _ in r], axis=1),
                                use_container_width=True, hide_index=True)
                    st.divider()
                    col1, col2 = st.columns(2)
                    with col1:
                        st.download_button(
                            "📊 Télécharger États Financiers (7 onglets)",
                            liasse['excel_bytes'],
                            f"Etats_Financiers_{ent_nom or 'Entreprise'}_{exercice or '2024'}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True, type="primary")
                    with col2:
                        if st.button("💾 Sauvegarder dans dossier", key="sav_notes", use_container_width=True):
                            sauvegarder_si_entreprise(ent_id, "📎 Notes", f"Notes {exercice}",
                                                      "Notes annexes générées", info_pays['nom'], exercice)
        except Exception as e:
            st.error(f"❌ Erreur : {e}")
            logger.error(f"Erreur génération Notes Annexes : {e}")

# =============================================================================
# PAGE : LIASSE FISCALE OFFICIELLE DGID SÉNÉGAL
# =============================================================================
elif page == "📄 Liasse Fiscale Officielle 🇸🇳":
    st.title("📄 Liasse Fiscale Officielle — DGID Sénégal")
    st.markdown("*États Financiers Annuels (SAES) — Format SYSCOHADA révisé 2017*")
    st.divider()

    if code_pays != 'SN':
        st.warning("⚠ Ce module est actuellement disponible pour le **Sénégal** uniquement. "
                   "Sélectionnez 🇸🇳 Sénégal dans la barre latérale.")
        st.stop()

    ent_id, ent_nom, exercice = selectionner_entreprise("lfo")

    for k, v in [('lfo_resultat', None), ('lfo_nom_fichier', None)]:
        if k not in st.session_state:
            st.session_state[k] = v

    st.info("""
    📌 **Ce module génère les 3 états officiels SAES reconnus par la DGID Sénégal :**
    - **Tableau 1** — Bilan Actif (REF AA → DZ)
    - **Tableau 2** — Bilan Passif (REF CA → HZ)
    - **Tableau 3** — Compte de Résultat avec SIG (REF TA/RA → XI)

    ✅ Mapping direct depuis la balance SYSCOHADA — aucune saisie manuelle.
    """)

    fichier = st.file_uploader("📎 Importer la balance SYSCOHADA (Excel ou CSV)",
                               type=["xlsx", "csv"], key="lfo_uploader")
    if fichier:
        if st.session_state.get('lfo_nom_fichier') != fichier.name:
            st.session_state.lfo_resultat = None
            st.session_state.lfo_nom_fichier = fichier.name

        try:
            df_propre, infos_col = charger_balance_avec_ui(fichier, "lfo")

            if df_propre is not None:
                with st.expander("👀 Aperçu de la balance chargée"):
                    st.dataframe(df_propre.head(20), use_container_width=True)
                st.success(f"✅ {len(df_propre)} lignes exploitables — balance prête.")

                if st.button("📄 Générer la Liasse Fiscale Officielle DGID",
                             type="primary", use_container_width=True):
                    with st.spinner("Génération des états financiers SAES en cours..."):
                        logger.info(f"Génération Liasse DGID SN pour {ent_nom or 'N/A'}")
                        liasse = generer_liasse_sn(df_propre, ent_nom, exercice)
                        st.session_state.lfo_resultat = liasse

                if isinstance(st.session_state.lfo_resultat, dict):
                    liasse = st.session_state.lfo_resultat
                    totaux = liasse['totaux']

                    st.divider()
                    st.subheader("📊 Indicateurs Clés")
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Total Actif",    fcfa(totaux['total_actif']))
                    col2.metric("Total Passif",   fcfa(totaux['total_passif']))
                    col3.metric("Chiffre d'affaires", fcfa(totaux['ca']))
                    col4.metric("Résultat Net",   fcfa(totaux['resultat_net']))
                    col5, col6, col7, _ = st.columns(4)
                    col5.metric("CAF",            fcfa(totaux.get('caf', 0)))
                    col6.metric("BFR",            fcfa(totaux.get('bfr', 0)))
                    col7.metric("Trésorerie Nette", fcfa(totaux.get('treso_nette', 0)))

                    equilibre = abs(totaux['total_actif'] - totaux['total_passif'])
                    if totaux['total_actif'] > 0 and equilibre / max(totaux['total_actif'], 1) < 0.01:
                        st.success("✅ Bilan équilibré — Actif = Passif")
                    elif totaux['total_actif'] > 0:
                        st.warning(f"⚠ Écart Actif/Passif : {fcfa(equilibre)} — Vérifiez la balance.")

                    st.divider()
                    st.subheader("📋 Tableau 1 — Bilan Actif")
                    st.dataframe(
                        liasse['bilan_actif'].style.apply(
                            lambda row: ['background-color: #D6E4F0; font-weight: bold'
                                         if row['REF'] in ['AZ','BZ','CZ','DZ'] else ''
                                         for _ in row], axis=1
                        ),
                        use_container_width=True, hide_index=True
                    )

                    st.divider()
                    st.subheader("📋 Tableau 2 — Bilan Passif")
                    st.dataframe(
                        liasse['bilan_passif'].style.apply(
                            lambda row: ['background-color: #D6E4F0; font-weight: bold'
                                         if row['REF'] in ['CZ','DZ','EZ','FZ','GZ','HZ'] else ''
                                         for _ in row], axis=1
                        ),
                        use_container_width=True, hide_index=True
                    )

                    st.divider()
                    st.subheader("📋 Tableau 3 — Compte de Résultat")
                    sig_refs = ['XA','XB','XC','XD','XE','XF','XG','XH','XI']
                    st.dataframe(
                        liasse['compte_resultat'].style.apply(
                            lambda row: ['background-color: #E8F5E9; font-weight: bold'
                                         if row['REF'] in sig_refs else ''
                                         for _ in row], axis=1
                        ),
                        use_container_width=True, hide_index=True
                    )

                    st.divider()
                    st.subheader("📋 Tableau 4 — TAFIRE (Financement des Ressources et Emplois)")
                    st.caption("ℹ Les variations BFR (lignes M1→M8) montrent les positions de l'exercice N. "
                               "Pour les variations N/N-1, importez également la balance N-1.")
                    tafire_refs = ["ZC","ZR","ZE","FRG","M4","M8","BFR","TN","EQ","C5"]
                    st.dataframe(
                        liasse['tafire'].style.apply(
                            lambda row: ['background-color: #D6E4F0; font-weight: bold'
                                         if row['REF'] in tafire_refs else ''
                                         for _ in row], axis=1
                        ),
                        use_container_width=True, hide_index=True
                    )

                    st.divider()
                    st.subheader("📎 Notes Annexes — Tableaux Obligatoires SYSCOHADA")
                    notes = liasse.get('notes_annexes', {})
                    if notes:
                        tab_a, tab_b, tab_c, tab_d, tab_e = st.tabs([
                            "A — Immobilisations",
                            "B — Amortissements",
                            "C — Provisions",
                            "D — Créances",
                            "E — Dettes"
                        ])
                        with tab_a:
                            st.caption("État des immobilisations au bilan (Valeur Brute / Amortissements / Valeur Nette)")
                            st.dataframe(
                                notes['immo'].style.apply(
                                    lambda row: ['background-color: #D6E4F0; font-weight: bold'
                                                 if row['REF'] == 'AZ' else '' for _ in row], axis=1
                                ), use_container_width=True, hide_index=True)
                        with tab_b:
                            st.caption("Dotations aux amortissements de l'exercice N (comptes 681-688, 851, 861)")
                            st.dataframe(
                                notes['amort'].style.apply(
                                    lambda row: ['background-color: #D6E4F0; font-weight: bold'
                                                 if row['COMPTE'] == 'TOT' else '' for _ in row], axis=1
                                ), use_container_width=True, hide_index=True)
                        with tab_c:
                            st.caption("État des provisions et dépréciations (comptes 15, 19, 39x, 49x, 59x, 29x)")
                            st.dataframe(
                                notes['provisions'].style.apply(
                                    lambda row: ['background-color: #D6E4F0; font-weight: bold'
                                                 if row['COMPTE'] == 'TOT' else '' for _ in row], axis=1
                                ), use_container_width=True, hide_index=True)
                        with tab_d:
                            st.caption("État des créances par nature (Brut / Dépréciations / Net)")
                            st.dataframe(
                                notes['creances'].style.apply(
                                    lambda row: ['background-color: #D6E4F0; font-weight: bold'
                                                 if row['COMPTE'] == 'TOT' else '' for _ in row], axis=1
                                ), use_container_width=True, hide_index=True)
                        with tab_e:
                            st.caption("État des dettes par nature (emprunts, fournisseurs, fiscal, social…)")
                            st.dataframe(
                                notes['dettes'].style.apply(
                                    lambda row: ['background-color: #D6E4F0; font-weight: bold'
                                                 if row['COMPTE'] == 'TOT' else '' for _ in row], axis=1
                                ), use_container_width=True, hide_index=True)

                    st.divider()
                    st.subheader("📥 Télécharger la Liasse Officielle")
                    col1, col2 = st.columns(2)
                    with col1:
                        nom_fichier = f"Liasse_DGID_SN_{ent_nom or 'Entreprise'}_{exercice or '2024'}.xlsx"
                        st.download_button(
                            label="📊 Télécharger Excel DGID (Bilan + CR + TAFIRE + Notes)",
                            data=liasse['excel_bytes'],
                            file_name=nom_fichier,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True,
                            type="primary"
                        )
                    with col2:
                        if st.button("💾 Sauvegarder dans dossier entreprise", use_container_width=True):
                            sauvegarder_si_autorise(
                                ent_id, "📄 Liasse DGID", f"Liasse DGID {exercice}",
                                f"Liasse DGID générée — CA: {fcfa(totaux['ca'])} | RN: {fcfa(totaux['resultat_net'])}",
                                info_pays['nom'], exercice
                            )

        except Exception as e:
            st.error(f"❌ Erreur : {e}")
            logger.error(f"Erreur Liasse DGID SN : {e}")

# =============================================================================
# PAGE : LIASSE FISCALE IA
# =============================================================================
elif page == "🧾 Liasse Fiscale":
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
elif page == "🔍 Plan Comptable OHADA":
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

# =============================================================================
# HANDLERS FISCAL QUANTITATIF & AUTRES PAGES
# =============================================================================

elif page == "📰 Veille Fiscale UEMOA":
    st.title(f"📰 Veille Fiscale UEMOA — {info_pays['nom']}")
    st.divider()
    if st.button("🔄 Lancer la veille fiscale", type="primary", use_container_width=True):
        with st.spinner("Analyse des actualités fiscales en cours..."):
            try:
                resultat = veille_fiscale_uemoa(code_pays)
                afficher_rapport(resultat, afficher_kpis_auto=True, afficher_alertes_auto=True, afficher_tables_auto=True)
                sauvegarder_si_entreprise(None, "📰 Veille Fiscale", f"veille_{code_pays}", resultat, info_pays['nom'], "")
            except Exception as e:
                st.error(f"Erreur : {e}")
    else:
        st.info(f"Cliquez sur le bouton pour obtenir la veille fiscale UEMOA pour **{info_pays['nom']}** (TVA {info_pays['taux_tva']}%, IS {info_pays['taux_is']}%).")

elif page == "📅 Calendrier Fiscal UEMOA":
    try:
        from smd_calendar import page_calendrier_fiscal
        page_calendrier_fiscal()
    except Exception as e:
        st.error(f"Module calendrier indisponible : {e}")

elif page == "📊 Tableau de Bord Fiscal":
    try:
        from smd_streamlit import page_dashboard
        page_dashboard()
    except Exception as e:
        st.error(f"Module tableau de bord indisponible : {e}")

elif page == "🚨 Analyse du Risque Fiscal":
    try:
        from smd_streamlit import page_risque_fiscal
        page_risque_fiscal()
    except Exception as e:
        st.error(f"Module risque fiscal indisponible : {e}")

elif page == "🧾 Analyse Facture SYSCOHADA":
    try:
        from smd_streamlit import page_analyse_facture
        page_analyse_facture()
    except Exception as e:
        st.error(f"Module analyse facture indisponible : {e}")

elif page == "💳 Balance Âgée Tiers":
    st.title(f"💳 Balance Âgée des Tiers — {info_pays['nom']}")
    st.markdown("Analyse des créances et dettes par ancienneté (0-30j, 30-60j, 60-90j, +90j)")
    st.divider()
    ent_id, ent_nom, exercice = selectionner_entreprise("baget")
    fichier = st.file_uploader("📎 Importer une balance tiers (CSV, XLSX)", type=["csv", "xlsx"])
    if fichier:
        try:
            df_propre, infos_col = charger_balance_avec_ui(fichier, "baget")
            if df_propre is not None:
                col_tiers = infos_col.get('compte')
                col_lib   = infos_col.get('libelle')
                col_d     = infos_col.get('debit')
                col_c     = infos_col.get('credit')
                if col_tiers and col_d and col_c:
                    df_t = df_propre.copy()
                    df_t['_d'] = pd.to_numeric(df_t[col_d].astype(str).str.replace(',','.'), errors='coerce').fillna(0)
                    df_t['_c'] = pd.to_numeric(df_t[col_c].astype(str).str.replace(',','.'), errors='coerce').fillna(0)
                    df_t['Solde'] = df_t['_d'] - df_t['_c']
                    df_clients = df_t[df_t[col_tiers].astype(str).str.startswith('4')]
                    total_creances = df_clients[df_clients['Solde'] > 0]['Solde'].sum()
                    total_dettes   = df_clients[df_clients['Solde'] < 0]['Solde'].abs().sum()
                    m1, m2, m3 = st.columns(3)
                    m1.metric("📈 Total Créances", fcfa(total_creances, info_pays['devise']))
                    m2.metric("📉 Total Dettes",   fcfa(total_dettes, info_pays['devise']))
                    m3.metric("🔢 Nb tiers",       len(df_clients))
                    st.divider()
                    st.markdown("#### 📋 Détail des soldes tiers (Classe 4)")
                    df_affich = df_clients[[col_tiers] + ([col_lib] if col_lib else []) + ['Solde']].sort_values('Solde')
                    st.dataframe(df_affich, use_container_width=True)
                else:
                    st.warning("Colonnes insuffisantes. Vérifiez compte, débit et crédit.")
        except Exception as e:
            st.error(f"Erreur : {e}")

elif page == "🏦 Rapprochement Bancaire":
    st.title(f"🏦 Rapprochement Bancaire — {info_pays['nom']}")
    st.divider()
    ent_id, ent_nom, exercice = selectionner_entreprise("rap")
    col1, col2 = st.columns(2)
    with col1:
        releve = st.file_uploader("📄 Relevé bancaire (CSV/XLSX)", type=["csv", "xlsx"], key="rap_releve")
    with col2:
        ecritures = st.file_uploader("📒 Écritures comptables (CSV/XLSX)", type=["csv", "xlsx"], key="rap_ecrit")
    if releve and ecritures:
        try:
            df_releve, _ = charger_balance_avec_ui(releve, "rap_r")
            df_ecritures, _ = charger_balance_avec_ui(ecritures, "rap_e")
            if df_releve is not None and df_ecritures is not None:
                prompt = f"""
Tu es expert-comptable OHADA. Compare ce relevé bancaire ({len(df_releve)} lignes)
et ces écritures comptables ({len(df_ecritures)} lignes).
Identifie les écarts, opérations non rapprochées, et propose les régularisations.
Balance devise : {info_pays['devise']}, pays : {info_pays['nom']}.
"""
                if st.button("🔍 Lancer le rapprochement IA", type="primary", use_container_width=True):
                    with st.spinner("Analyse IA en cours..."):
                        analyse = appel_mistral(prompt)
                        st.markdown("### Résultat du Rapprochement")
                        st.markdown(analyse)
                        sauvegarder_si_entreprise(ent_id, "🏦 Rapprochement", "rapprochement", analyse, info_pays['nom'], exercice)
        except Exception as e:
            st.error(f"Erreur : {e}")

elif page == "📊 Tresorerie Previsionnelle":
    st.title(f"📊 Trésorerie Prévisionnelle — {info_pays['nom']}")
    st.divider()
    ent_id, ent_nom, exercice = selectionner_entreprise("trep")
    st.markdown("### Saisie des flux prévisionnels")
    nb_mois = st.slider("Horizon (mois)", 3, 12, 6)
    col1, col2 = st.columns(2)
    with col1:
        encaissements = st.number_input(f"Encaissements mensuels estimés ({info_pays['devise']})", min_value=0.0, step=100000.0)
        autres_entrees = st.number_input("Autres entrées (subventions, emprunts...)", min_value=0.0, step=100000.0)
    with col2:
        decaissements = st.number_input(f"Décaissements mensuels estimés ({info_pays['devise']})", min_value=0.0, step=100000.0)
        tresorerie_initiale = st.number_input("Trésorerie initiale", min_value=0.0, step=100000.0)
    if st.button("📊 Générer le prévisionnel", type="primary", use_container_width=True):
        mois = []
        treso = tresorerie_initiale
        rows = []
        for i in range(1, nb_mois + 1):
            entrees = encaissements + autres_entrees
            solde = treso + entrees - decaissements
            rows.append({"Mois": f"M+{i}", "Entrées": entrees, "Sorties": decaissements, "Solde cumulé": solde})
            treso = solde
        df_prev = pd.DataFrame(rows)
        k1, k2, k3 = st.columns(3)
        k1.metric("📈 Solde final", fcfa(treso, info_pays['devise']))
        k2.metric("💰 Total entrées", fcfa(df_prev['Entrées'].sum(), info_pays['devise']))
        k3.metric("💸 Total sorties", fcfa(df_prev['Sorties'].sum(), info_pays['devise']))
        st.dataframe(df_prev, use_container_width=True)
        if treso < 0:
            st.error(f"⚠️ Trésorerie négative à M+{nb_mois} — risque de rupture de trésorerie !")
        else:
            st.success(f"✅ Trésorerie positive sur {nb_mois} mois.")

elif page == "📐 Plan de Financement":
    try:
        from utils.page_tarifs import page_tarifs
        st.title(f"📐 Plan de Financement — {info_pays['nom']}")
        st.divider()
        ent_id, ent_nom, exercice = selectionner_entreprise("pf")
        st.markdown("### Saisie Emplois / Ressources")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**📤 Emplois (Investissements)**")
            invest = st.number_input("Investissements", min_value=0.0, step=100000.0, key="pf_inv")
            bfr    = st.number_input("Augmentation BFR", min_value=0.0, step=100000.0, key="pf_bfr")
            rembours = st.number_input("Remboursements dettes", min_value=0.0, step=100000.0, key="pf_rmb")
        with col2:
            st.markdown("**📥 Ressources**")
            caf    = st.number_input("CAF (Capacité AutoFinancement)", min_value=0.0, step=100000.0, key="pf_caf")
            apport = st.number_input("Apports en capital", min_value=0.0, step=100000.0, key="pf_app")
            emprunt = st.number_input("Emprunts nouveaux", min_value=0.0, step=100000.0, key="pf_emp")
        total_emplois   = invest + bfr + rembours
        total_ressources = caf + apport + emprunt
        ecart = total_ressources - total_emplois
        st.divider()
        m1, m2, m3 = st.columns(3)
        m1.metric("📤 Total Emplois",    fcfa(total_emplois, info_pays['devise']))
        m2.metric("📥 Total Ressources", fcfa(total_ressources, info_pays['devise']))
        m3.metric("⚖️ Équilibre",        fcfa(ecart, info_pays['devise']),
                  delta="Excédent" if ecart >= 0 else "Déficit")
        if ecart < 0:
            st.error(f"❌ Déficit de financement : {fcfa(abs(ecart), info_pays['devise'])} à couvrir.")
        else:
            st.success(f"✅ Plan équilibré — excédent : {fcfa(ecart, info_pays['devise'])}.")
    except Exception as e:
        st.error(f"Erreur : {e}")

elif page == "💹 TFT SYSCOHADA":
    st.title(f"💹 Tableau de Flux de Trésorerie SYSCOHADA — {info_pays['nom']}")
    st.divider()
    ent_id, ent_nom, exercice = selectionner_entreprise("tft")
    fichier = st.file_uploader("📎 Importer la balance SYSCOHADA (CSV/XLSX)", type=["csv", "xlsx"])
    if fichier:
        try:
            df_propre, infos_col = charger_balance_avec_ui(fichier, "tft")
            if df_propre is not None:
                if st.button("💹 Générer le TFT SYSCOHADA", type="primary", use_container_width=True):
                    with st.spinner("Calcul des flux de trésorerie..."):
                        prompt = f"""
Tu es expert-comptable OHADA. Construis le Tableau de Flux de Trésorerie (TFT) 
selon le référentiel SYSCOHADA révisé 2017 à partir de cette balance :
{df_propre.head(30).to_string()}

Calcule et présente :
1. Flux nets de trésorerie des activités opérationnelles (CAF)
2. Flux nets des activités d'investissement
3. Flux nets des activités de financement
4. Variation nette de trésorerie
5. Trésorerie à l'ouverture et à la clôture

Devise : {info_pays['devise']}, Pays : {info_pays['nom']}
"""
                        analyse = appel_mistral(prompt)
                        st.markdown("### 💹 TFT SYSCOHADA")
                        st.markdown(analyse)
                        sauvegarder_si_entreprise(ent_id, "💹 TFT", fichier.name, analyse, info_pays['nom'], exercice)
        except Exception as e:
            st.error(f"Erreur : {e}")

elif page == "🔌 Connecteurs ERP":
    try:
        from utils.page_connectors import page_connectors
        page_connectors(app_name="syscohada")
    except Exception as e:
        st.error(f"Module connecteurs indisponible : {e}")

elif page == "💳 Tarifs & Abonnement":
    try:
        from utils.page_tarifs import page_tarifs
        page_tarifs(app_name="syscohada")
    except Exception as e:
        st.error(f"Module tarifs indisponible : {e}")
