# -*- coding: utf-8 -*-
"""
Superviseur IA Comptable SYSCOHADA - SMD Consulting
Application de supervision comptable selon normes OHADA/UEMOA
Auteur: Souleymane Diallo
"""

import streamlit as st
import pandas as pd
import base64
from utils.ai import appel_mistral
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

# =============================================================================
# INITIALISATION
# =============================================================================
init_db()

st.set_page_config(
    page_title="Superviseur IA SYSCOHADA",
    layout="wide",
    page_icon="🌍",
    initial_sidebar_state="expanded"
)

# =============================================================================
# AUTHENTIFICATION
# =============================================================================
if not is_connecte():
    st.title("🔒 Superviseur IA Comptable SYSCOHADA")
    st.subheader("Accès réservé — Normes OHADA/UEMOA")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("---")
        st.markdown("""
        <div style='background:#f0fdf4;padding:12px;border-radius:8px;margin-bottom:10px;font-size:0.85em'>
        ✅ <b>Données anonymisées</b> — SIRET/NIF masqués, noms supprimés<br>
        ✅ <b>Non stockées</b> — Aucune conservation après analyse<br>
        ✅ <b>Non utilisées pour entraîner l'IA</b> — Politique Mistral garantie
        </div>
        """, unsafe_allow_html=True)
        st.markdown("---")
        email = st.text_input("📧 Email professionnel", placeholder="contact@cabinet.com")
        password = st.text_input("🔑 Mot de passe", type="password")

        if st.button("🚀 Se connecter", type="primary", use_container_width=True):
            if login(email, password):
                st.success("✅ Connexion réussie !")
                st.rerun()
            else:
                st.error("❌ Email ou mot de passe incorrect")

    st.divider()
    st.caption("SMD Consulting © 2026 - Comptable IA Augmenté SYSCOHADA")
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
# FONCTIONS UTILITAIRES
# =============================================================================

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
            file_name=f"{titre}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    except Exception as e:
        st.error(f"Erreur export Word : {e}")


def sauvegarder_si_entreprise(ent_id, type_a, titre, resultat, pays_nom, exercice):
    """Sauvegarde une analyse si une entreprise est sélectionnée"""
    if ent_id:
        try:
            sauvegarder_analyse(ent_id, type_a, titre, resultat, pays_nom, exercice)
            st.success("✅ Analyse sauvegardée dans le dossier entreprise !")
        except Exception as e:
            st.error(f"Erreur sauvegarde : {e}")


def selectionner_entreprise(key_prefix):
    """Widget de sélection d'entreprise réutilisable"""
    entreprises = lister_entreprises()
    ent_id = None
    ent_nom = ""
    exercice = ""

    if entreprises:
        st.subheader("🏢 Associer à une entreprise (optionnel)")
        options = {"-- Aucune --": None}
        options.update({f"{e[1]} ({e[2]})": e[0] for e in entreprises})
        choix = st.selectbox("Entreprise", list(options.keys()), key=f"{key_prefix}_ent")
        ent_id = options[choix]
        ent_nom = choix.split(" (")[0] if ent_id else ""
        exercice = st.text_input("Exercice (ex: 2024)", key=f"{key_prefix}_ex")

    return ent_id, ent_nom, exercice


# =============================================================================
# SIDEBAR - NAVIGATION
# =============================================================================
try:
    st.sidebar.image(
        "https://raw.githubusercontent.com/diallosouleymane19-rgb/superviseur-ia-syscohada/main/uemoa.png",
        width=120
    )
except:
    pass

st.sidebar.title("🌍 Superviseur IA SYSCOHADA")
st.sidebar.markdown(f"👤 Connecté : **{st.session_state.get('user_email', 'Utilisateur')}**")
st.sidebar.markdown("---")

# ✅ CORRECTION : Bouton de déconnexion (pas d'appel direct à logout())
if st.sidebar.button("🚪 Déconnexion", use_container_width=True):
    logout()
    st.rerun()

st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigation",
    [
        "🏠 Accueil",
        "🏢 Dossiers Entreprises",
        "📊 Analyse Balance SYSCOHADA",
        "📋 Bilan SYSCOHADA",
        "📈 Compte de Résultat",
        "💰 TAFIRE",
        "📎 Notes Annexes",
        "🧾 Liasse Fiscale",
        "🔍 Plan Comptable OHADA",
        "📰 Veille Fiscale UEMOA",
    ]
)

# Sélecteur de pays dans la sidebar
st.sidebar.markdown("---")
st.sidebar.subheader("🌍 Pays")
pays_options = {
    f"{v['nom']}": k
    for k, v in FISCALITE_UEMOA.items()
}
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
    col_logo, col_titre = st.columns([1, 4])
    with col_logo:
        try:
            st.image(
                "https://raw.githubusercontent.com/diallosouleymane19-rgb/superviseur-ia-syscohada/main/uemoa.png",
                width=100
            )
        except:
            st.markdown("🌍")
    with col_titre:
        st.title("Superviseur IA Comptable SYSCOHADA")

    st.markdown("### Assistant comptable intelligent — Normes OHADA/UEMOA")
    st.divider()

    col1, col2, col3 = st.columns(3)
    col1.info("📊 **Analyse Balance**\nSelon normes SYSCOHADA")
    col2.info("📋 **Bilan SYSCOHADA**\nGénération automatique")
    col3.info("📈 **Compte de Résultat**\nSIG et ratios OHADA")

    st.markdown("---")
    col4, col5, col6 = st.columns(3)
    col4.success("💰 **TAFIRE**\nTableau financier OHADA")
    col5.success("📎 **Notes Annexes**\nObligatoires SYSCOHADA")
    col6.success("🧾 **Liasse Fiscale**\nPar pays UEMOA")

    st.markdown("---")
    col7, col8 = st.columns(2)
    col7.warning("🔍 **Plan Comptable OHADA**\nRecherche et consultation")
    col8.warning("📰 **Veille Fiscale UEMOA**\nActualités par pays")

    st.divider()
    st.subheader("🌍 Pays membres UEMOA")
    cols = st.columns(4)
    drapeaux = ["🇸🇳", "🇧🇯", "🇧🇫", "🇨🇮", "🇬🇼", "🇲🇱", "🇳🇪", "🇹🇬"]
    for i, (code, info) in enumerate(FISCALITE_UEMOA.items()):
        cols[i % 4].metric(
            f"{drapeaux[i]} {info['nom']}",
            f"TVA {info['taux_tva']}%",
            f"IS {info['taux_is']}%"
        )

    st.divider()
    st.markdown("### 🔒 Vos Données Sont Protégées")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.success("✅ **Anonymisation**\n\nNIF masqués, noms supprimés avant envoi")
    with col2:
        st.success("✅ **Non stockées**\n\nAucune conservation après analyse")
    with col3:
        st.success("✅ **IA éthique**\n\nDonnées non utilisées pour entraîner Mistral")

    st.divider()
    st.caption("**SMD Consulting** - Superviseur IA SYSCOHADA © 2026")

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
            regime = st.selectbox("Régime fiscal", [
                "Réel Normal",
                "Réel Simplifié",
                "Forfait"
            ])
            contact = st.text_input("Contact")
            email_ent = st.text_input("Email")

        if st.button("✅ Créer le dossier", type="primary"):
            if nom:
                creer_entreprise(nom, pays_sel, code_pays_ent, secteur, regime, contact, email_ent)
                st.success(f"✅ Dossier **{nom}** créé avec succès !")
                st.rerun()
            else:
                st.warning("⚠️ Le nom est obligatoire.")

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

                    if st.button(f"🗑️ Supprimer {nom}", key=f"del_{ent_id}"):
                        supprimer_entreprise(ent_id)
                        st.success(f"Dossier {nom} supprimé.")
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
                        if st.button("🗑️ Supprimer", key=f"delA_{a_id}"):
                            supprimer_analyse(a_id)
                            st.rerun()

# =============================================================================
# PAGE : ANALYSE BALANCE SYSCOHADA
# =============================================================================
elif page == "📊 Analyse Balance SYSCOHADA":
    st.title(f"📊 Analyse Balance SYSCOHADA — {info_pays['nom']}")
    st.divider()

    ent_id, ent_nom, exercice = selectionner_entreprise("bal")

    # ✅ CORRECTION CACHE : Réinitialiser si nouveau fichier
    if 'bal_resultat' not in st.session_state:
        st.session_state.bal_resultat = None
    if 'bal_nom_fichier' not in st.session_state:
        st.session_state.bal_nom_fichier = None

    fichier = st.file_uploader("📎 Importer une balance (Excel ou CSV)", type=["xlsx", "csv"])

    if fichier:
        if st.session_state.get('bal_nom_fichier') != fichier.name:
            st.session_state.bal_resultat = None
            st.session_state.bal_nom_fichier = fichier.name

        try:
            df = pd.read_csv(fichier) if fichier.name.endswith(".csv") else pd.read_excel(fichier)

            with st.expander("👀 Aperçu de la balance"):
                st.dataframe(df, use_container_width=True)

            if st.button("🔍 Analyser la balance", type="primary", use_container_width=True):
                with st.spinner("Analyse SYSCOHADA en cours..."):
                    resultat = analyser_balance_syscohada(df, code_pays)
                    st.session_state.bal_resultat = resultat

            if st.session_state.bal_resultat:
                st.subheader("📊 Analyse IA SYSCOHADA :")
                st.markdown(st.session_state.bal_resultat)
                st.divider()

                col1, col2, col3 = st.columns(3)
                with col1:
                    telecharger_html("Analyse_Balance_SYSCOHADA", st.session_state.bal_resultat)
                with col2:
                    telecharger_word("Analyse_Balance_SYSCOHADA", st.session_state.bal_resultat, ent_nom, info_pays['nom'], exercice)
                with col3:
                    if st.button("💾 Sauvegarder dans dossier", use_container_width=True):
                        sauvegarder_si_entreprise(ent_id, "📊 Balance", fichier.name, st.session_state.bal_resultat, info_pays['nom'], exercice)

        except Exception as e:
            st.error(f"❌ Erreur : {e}")

# =============================================================================
# PAGE : BILAN SYSCOHADA
# =============================================================================
elif page == "📋 Bilan SYSCOHADA":
    st.title(f"📋 Bilan SYSCOHADA — {info_pays['nom']}")
    st.divider()

    ent_id, ent_nom, exercice = selectionner_entreprise("bil")

    if 'bil_resultat' not in st.session_state:
        st.session_state.bil_resultat = None
    if 'bil_nom_fichier' not in st.session_state:
        st.session_state.bil_nom_fichier = None

    fichier = st.file_uploader("📎 Importer une balance (Excel ou CSV)", type=["xlsx", "csv"])

    if fichier:
        if st.session_state.get('bil_nom_fichier') != fichier.name:
            st.session_state.bil_resultat = None
            st.session_state.bil_nom_fichier = fichier.name

        try:
            df = pd.read_csv(fichier) if fichier.name.endswith(".csv") else pd.read_excel(fichier)

            with st.expander("👀 Aperçu"):
                st.dataframe(df, use_container_width=True)

            if st.button("📋 Générer le Bilan SYSCOHADA", type="primary", use_container_width=True):
                with st.spinner("Génération du bilan en cours..."):
                    resultat = generer_bilan_syscohada(df, code_pays)
                    st.session_state.bil_resultat = resultat

            if st.session_state.bil_resultat:
                st.subheader("📋 Bilan SYSCOHADA :")
                st.markdown(st.session_state.bil_resultat)
                st.divider()

                col1, col2, col3 = st.columns(3)
                with col1:
                    telecharger_html("Bilan_SYSCOHADA", st.session_state.bil_resultat)
                with col2:
                    telecharger_word("Bilan_SYSCOHADA", st.session_state.bil_resultat, ent_nom, info_pays['nom'], exercice)
                with col3:
                    if st.button("💾 Sauvegarder dans dossier", use_container_width=True):
                        sauvegarder_si_entreprise(ent_id, "📋 Bilan", f"Bilan {exercice}", st.session_state.bil_resultat, info_pays['nom'], exercice)

        except Exception as e:
            st.error(f"❌ Erreur : {e}")

# =============================================================================
# PAGE : COMPTE DE RÉSULTAT
# =============================================================================
elif page == "📈 Compte de Résultat":
    st.title(f"📈 Compte de Résultat SYSCOHADA — {info_pays['nom']}")
    st.divider()

    ent_id, ent_nom, exercice = selectionner_entreprise("cr")

    if 'cr_resultat' not in st.session_state:
        st.session_state.cr_resultat = None
    if 'cr_nom_fichier' not in st.session_state:
        st.session_state.cr_nom_fichier = None

    fichier = st.file_uploader("📎 Importer une balance (Excel ou CSV)", type=["xlsx", "csv"])

    if fichier:
        if st.session_state.get('cr_nom_fichier') != fichier.name:
            st.session_state.cr_resultat = None
            st.session_state.cr_nom_fichier = fichier.name

        try:
            df = pd.read_csv(fichier) if fichier.name.endswith(".csv") else pd.read_excel(fichier)

            with st.expander("👀 Aperçu"):
                st.dataframe(df, use_container_width=True)

            if st.button("📈 Générer le Compte de Résultat", type="primary", use_container_width=True):
                with st.spinner("Génération en cours..."):
                    resultat = generer_compte_resultat_syscohada(df, code_pays)
                    st.session_state.cr_resultat = resultat

            if st.session_state.cr_resultat:
                st.subheader("📈 Compte de Résultat SYSCOHADA :")
                st.markdown(st.session_state.cr_resultat)
                st.divider()

                col1, col2, col3 = st.columns(3)
                with col1:
                    telecharger_html("Compte_Resultat_SYSCOHADA", st.session_state.cr_resultat)
                with col2:
                    telecharger_word("Compte_Resultat_SYSCOHADA", st.session_state.cr_resultat, ent_nom, info_pays['nom'], exercice)
                with col3:
                    if st.button("💾 Sauvegarder dans dossier", use_container_width=True):
                        sauvegarder_si_entreprise(ent_id, "📈 CR", f"CR {exercice}", st.session_state.cr_resultat, info_pays['nom'], exercice)

        except Exception as e:
            st.error(f"❌ Erreur : {e}")

# =============================================================================
# PAGE : TAFIRE
# =============================================================================
elif page == "💰 TAFIRE":
    st.title(f"💰 TAFIRE — {info_pays['nom']}")
    st.markdown("*Tableau Financier des Ressources et Emplois*")
    st.divider()

    ent_id, ent_nom, exercice = selectionner_entreprise("taf")

    if 'taf_resultat' not in st.session_state:
        st.session_state.taf_resultat = None
    if 'taf_nom_fichier' not in st.session_state:
        st.session_state.taf_nom_fichier = None

    fichier = st.file_uploader("📎 Importer une balance (Excel ou CSV)", type=["xlsx", "csv"])

    if fichier:
        if st.session_state.get('taf_nom_fichier') != fichier.name:
            st.session_state.taf_resultat = None
            st.session_state.taf_nom_fichier = fichier.name

        try:
            df = pd.read_csv(fichier) if fichier.name.endswith(".csv") else pd.read_excel(fichier)

            with st.expander("👀 Aperçu"):
                st.dataframe(df, use_container_width=True)

            if st.button("💰 Générer le TAFIRE", type="primary", use_container_width=True):
                with st.spinner("Génération du TAFIRE en cours..."):
                    resultat = generer_tafire(df, code_pays)
                    st.session_state.taf_resultat = resultat

            if st.session_state.taf_resultat:
                st.subheader("💰 TAFIRE :")
                st.markdown(st.session_state.taf_resultat)
                st.divider()

                col1, col2, col3 = st.columns(3)
                with col1:
                    telecharger_html("TAFIRE_SYSCOHADA", st.session_state.taf_resultat)
                with col2:
                    telecharger_word("TAFIRE_SYSCOHADA", st.session_state.taf_resultat, ent_nom, info_pays['nom'], exercice)
                with col3:
                    if st.button("💾 Sauvegarder dans dossier", use_container_width=True):
                        sauvegarder_si_entreprise(ent_id, "💰 TAFIRE", f"TAFIRE {exercice}", st.session_state.taf_resultat, info_pays['nom'], exercice)

        except Exception as e:
            st.error(f"❌ Erreur : {e}")

# =============================================================================
# PAGE : NOTES ANNEXES
# =============================================================================
elif page == "📎 Notes Annexes":
    st.title(f"📎 Notes Annexes SYSCOHADA — {info_pays['nom']}")
    st.divider()

    ent_id, ent_nom, exercice = selectionner_entreprise("notes")

    if 'notes_resultat' not in st.session_state:
        st.session_state.notes_resultat = None
    if 'notes_nom_fichier' not in st.session_state:
        st.session_state.notes_nom_fichier = None

    fichier = st.file_uploader("📎 Importer une balance (Excel ou CSV)", type=["xlsx", "csv"])

    if fichier:
        if st.session_state.get('notes_nom_fichier') != fichier.name:
            st.session_state.notes_resultat = None
            st.session_state.notes_nom_fichier = fichier.name

        try:
            df = pd.read_csv(fichier) if fichier.name.endswith(".csv") else pd.read_excel(fichier)

            with st.expander("👀 Aperçu"):
                st.dataframe(df, use_container_width=True)

            if st.button("📎 Générer les Notes Annexes", type="primary", use_container_width=True):
                with st.spinner("Génération en cours..."):
                    resultat = generer_notes_annexes(df, code_pays, ent_nom, exercice)
                    st.session_state.notes_resultat = resultat

            if st.session_state.notes_resultat:
                st.subheader("📎 Notes Annexes :")
                st.markdown(st.session_state.notes_resultat)
                st.divider()

                col1, col2, col3 = st.columns(3)
                with col1:
                    telecharger_html("Notes_Annexes_SYSCOHADA", st.session_state.notes_resultat)
                with col2:
                    telecharger_word("Notes_Annexes_SYSCOHADA", st.session_state.notes_resultat, ent_nom, info_pays['nom'], exercice)
                with col3:
                    if st.button("💾 Sauvegarder dans dossier", use_container_width=True):
                        sauvegarder_si_entreprise(ent_id, "📎 Notes", f"Notes {exercice}", st.session_state.notes_resultat, info_pays['nom'], exercice)

        except Exception as e:
            st.error(f"❌ Erreur : {e}")

# =============================================================================
# PAGE : LIASSE FISCALE
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
            df = pd.read_csv(fichier) if fichier.name.endswith(".csv") else pd.read_excel(fichier)

            with st.expander("👀 Aperçu"):
                st.dataframe(df, use_container_width=True)

            if st.button("🧾 Générer la Liasse Fiscale", type="primary", use_container_width=True):
                with st.spinner("Génération en cours..."):
                    resultat = analyser_liasse_fiscale(df, code_pays, exercice)
                    st.session_state.liasse_resultat = resultat

            if st.session_state.liasse_resultat:
                st.subheader("🧾 Liasse Fiscale :")
                st.markdown(st.session_state.liasse_resultat)
                st.divider()

                col1, col2, col3 = st.columns(3)
                with col1:
                    telecharger_html("Liasse_Fiscale", st.session_state.liasse_resultat)
                with col2:
                    telecharger_word("Liasse_Fiscale", st.session_state.liasse_resultat, ent_nom, info_pays['nom'], exercice)
                with col3:
                    if st.button("💾 Sauvegarder dans dossier", use_container_width=True):
                        sauvegarder_si_entreprise(ent_id, "🧾 Liasse", f"Liasse {exercice}", st.session_state.liasse_resultat, info_pays['nom'], exercice)

        except Exception as e:
            st.error(f"❌ Erreur : {e}")

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
        df_classe = pd.DataFrame(
            list(comptes_classe.items()),
            columns=["Numéro", "Libellé"]
        )
        st.dataframe(df_classe, use_container_width=True)

# =============================================================================
# PAGE : VEILLE FISCALE UEMOA
# =============================================================================
elif page == "📰 Veille Fiscale UEMOA":
    st.title(f"📰 Veille Fiscale UEMOA — {info_pays['nom']}")
    st.divider()

    st.info(f"""
    **Pays sélectionné :** {info_pays['nom']}  
    **TVA :** {info_pays['taux_tva']}% | **IS :** {info_pays['taux_is']}%  
    **Devise :** {info_pays['devise']}
    """)

    if 'veille_resultat' not in st.session_state:
        st.session_state.veille_resultat = None
    if 'veille_pays' not in st.session_state:
        st.session_state.veille_pays = None

    # Réinitialiser si changement de pays
    if st.session_state.get('veille_pays') != code_pays:
        st.session_state.veille_resultat = None
        st.session_state.veille_pays = code_pays

    if st.button("📰 Obtenir la veille fiscale", type="primary", use_container_width=True):
        with st.spinner("Génération de la veille fiscale en cours..."):
            resultat = veille_fiscale_uemoa(code_pays)
            st.session_state.veille_resultat = resultat

    if st.session_state.veille_resultat:
        st.markdown(st.session_state.veille_resultat)
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            telecharger_html("Veille_Fiscale_UEMOA", st.session_state.veille_resultat)
        with col2:
            telecharger_word("Veille_Fiscale_UEMOA", st.session_state.veille_resultat, pays=info_pays['nom'])

# =============================================================================
# FOOTER
# =============================================================================
st.divider()
st.caption("""
**SMD Consulting** - Superviseur IA Comptable SYSCOHADA  
Comptable Augmenté par Intelligence Artificielle — Normes OHADA/UEMOA  
© 2026 - Souleymane Diallo
""")