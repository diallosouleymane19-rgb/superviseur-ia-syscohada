# -*- coding: utf-8 -*-
"""
utils/syscohada_helpers.py - SMD Global Consulting LLC
Fonctions utilitaires partagées par toutes les pages SYSCOHADA.
"""
import streamlit as st
import pandas as pd
import logging
from datetime import datetime
from utils.export_word import export_analyse_word
from utils.security import sanitize_filename
from utils.database import sauvegarder_analyse

logger = logging.getLogger(__name__)
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


def get_info_pays():
    """Récupère info_pays depuis session_state."""
    from data.plan_comptable_syscohada import get_info_pays as _get_info_pays
    code = st.session_state.get('_code_pays', 'SN')
    return _get_info_pays(code)


def get_code_pays():
    return st.session_state.get('_code_pays', 'SN')


def valider_structure_balance(df):
    """
    Valide la structure d'une balance SYSCOHADA.
    v2.4 : fallback positionnel pour exports Sage/ERP avec en-têtes fusionnées
           (colonnes compte et libellé sans nom d'en-tête explicite).
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
            # Variantes avec accents (exports restructurés Claude/Excel)
            'mouvement_débit', 'mouvements_débit', 'solde_débit', 'soldes_débit',
            'montant_débit', 'débit_période', 'débit_cumulé'
        ],
        'credit': [
            'credit', 'crédit', 'credit_montant', 'montant_credit', 'cred', 'credits',
            'montant_cred', 'credit_cumul', 'credit_periode',
            'mouvements_credit', 'mouvement_credit', 'credits_cumules',
            'soldes_credit', 'solde_credit',
            # Variantes avec accents (exports restructurés Claude/Excel)
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
    # Pour les exports Sage 100 / ERP avec cellules fusionnées où les colonnes
    # 'compte' et 'libellé' n'ont pas d'en-tête explicite (colonnes "Unnamed").
    # Détection par analyse du contenu des colonnes.

    if 'compte' not in colonnes_trouvees:
        for col in df_cols:
            vals = df_work[col].dropna().astype(str)
            if len(vals) > 3:
                # Colonne majoritairement composée de codes numériques 3-8 chiffres
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
                # Colonne avec du texte alphabétique (libellés de comptes)
                ratio_alpha = vals.str.match(r'^[A-Za-zÀ-ÿ0-9\s\-\'\.]{3,}$').sum() / len(vals)
                ratio_num   = vals.str.match(r'^\d+\.?\d*$').sum() / len(vals)
                if ratio_alpha > 0.5 and ratio_num < 0.8:
                    colonnes_trouvees['libelle'] = col
                    logger.info(f"Fallback positionnel 'libelle' → colonne '{col}' (alpha={ratio_alpha:.2f})")
                    break

    # Vérification finale : toutes les colonnes obligatoires trouvées ?
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
    Remplace charger_fichier() + valider_structure_balance() pour tous les modules
    qui utilisent des exports Sage 100 / ERP (en-têtes sur plusieurs lignes).
    Retourne (df_propre, infos_col) si chargé et valide, sinon (None, None).
    """
    raw_key    = f"_h_{prefix}_raw"
    loaded_key = f"_h_{prefix}_loaded"
    infos_key  = f"_h_{prefix}_infos"
    fname_key  = f"_h_{prefix}_fname"

    # Réinitialisation si nouveau fichier
    if st.session_state.get(fname_key) != fichier.name:
        for k in [raw_key, loaded_key, infos_key]:
            st.session_state[k] = None
        st.session_state[fname_key] = fichier.name

    # Lecture brute (une seule fois)
    if st.session_state.get(raw_key) is None:
        fichier.seek(0)
        if fichier.name.endswith('.xlsx'):
            st.session_state[raw_key] = pd.read_excel(fichier, header=None, nrows=30)
        else:
            try:
                st.session_state[raw_key] = pd.read_csv(
                    fichier, encoding='utf-8', header=None, nrows=30)
            except Exception:
                fichier.seek(0)
                st.session_state[raw_key] = pd.read_csv(
                    fichier, encoding='latin-1', header=None, nrows=30)

    df_brut = st.session_state[raw_key]

    # Auto-détection de la ligne d'en-tête
    mots_header = ['compte', 'n°', 'numero', 'libelle', 'libellé',
                   'intitule', 'intitulé', 'débit', 'debit', 'crédit', 'credit',
                   'mouvement', 'solde']
    default_header = 0
    for _idx in range(min(20, len(df_brut))):
        _vals = [str(v).lower().strip() for v in df_brut.iloc[_idx].values if pd.notna(v)]
        if sum(1 for mot in mots_header if any(mot in v for v in _vals)) >= 2:
            default_header = _idx
            break

    # Aperçu + sélecteur
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

    if st.button("✅ Charger avec cette ligne d'en-tête", type="primary",
                 key=f"_h_{prefix}_btn"):
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
            cols_vis = [c for c in df.columns.astype(str).tolist()
                        if not c.startswith('Unnamed')]
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



