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

def page_bilan_syscohada():
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
                    c1.metric("Total Actif",  f"{t['total_actif']:,.0f} FCFA")
                    c2.metric("Total Passif", f"{t['total_passif']:,.0f} FCFA")
                    c3.metric("Résultat Net", f"{t['resultat_net']:,.0f} FCFA")
                    eq = abs(t['total_actif'] - t['total_passif'])
                    if t['total_actif'] > 0 and eq / max(t['total_actif'], 1) < 0.01:
                        st.success("✅ Bilan équilibré")
                    elif t['total_actif'] > 0:
                        st.warning(f"⚠ Écart Actif/Passif : {eq:,.0f} FCFA")
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
                                                      f"Actif:{t['total_actif']:,.0f} | Passif:{t['total_passif']:,.0f}",
                                                      info_pays['nom'], exercice)
        except Exception as e:
            st.error(f"❌ Erreur : {e}")
            logger.error(f"Erreur génération bilan : {e}")


    # =============================================================================
    # PAGE : COMPTE DE RÉSULTAT
    # =============================================================================


def page_compte_resultat_syscohada():
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
                    c1.metric("Chiffre d'affaires", f"{t['ca']:,.0f} FCFA")
                    c2.metric("Résultat Net",        f"{t['resultat_net']:,.0f} FCFA")
                    c3.metric("CAF",                 f"{t.get('caf', 0):,.0f} FCFA")
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
                                                      f"CA:{t['ca']:,.0f} | RN:{t['resultat_net']:,.0f}",
                                                      info_pays['nom'], exercice)
        except Exception as e:
            st.error(f"❌ Erreur : {e}")
            logger.error(f"Erreur génération CR : {e}")


    # =============================================================================
    # PAGE : TAFIRE
    # =============================================================================


def page_tafire():
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
                    c1.metric("CAF",              f"{t.get('caf', 0):,.0f} FCFA")
                    c2.metric("BFR",              f"{t.get('bfr', 0):,.0f} FCFA")
                    c3.metric("Trésorerie Nette", f"{t.get('treso_nette', 0):,.0f} FCFA")
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
                                                      f"CAF:{t.get('caf',0):,.0f} | Tréso:{t.get('treso_nette',0):,.0f}",
                                                      info_pays['nom'], exercice)
        except Exception as e:
            st.error(f"❌ Erreur : {e}")
            logger.error(f"Erreur génération TAFIRE : {e}")

    # =============================================================================
    # PAGE : NOTES ANNEXES
    # =============================================================================


def page_notes_annexes():
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
    # ── Helpers SYSCOHADA ──────────────────────────────────────────────────
    from utils.syscohada_helpers import (
        selectionner_entreprise, charger_balance_avec_ui, valider_structure_balance,
        sauvegarder_si_entreprise, telecharger_html, telecharger_word,
        get_info_pays, get_code_pays,
    )
    from data.plan_comptable_syscohada import PLAN_COMPTABLE, FISCALITE_UEMOA, rechercher_comptes
    from utils.ai import appel_mistral
    from utils.rendu_financier import afficher_rapport
    info_pays  = get_info_pays()
    code_pays  = get_code_pays()
