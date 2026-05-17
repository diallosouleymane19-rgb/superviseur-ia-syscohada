# -*- coding: utf-8 -*-
"""
Superviseur IA Comptable SYSCOHADA - SMD Consulting
Application de supervision comptable selon normes OHADA/UEMOA
Auteur: Souleymane Diallo
"""

import streamlit as st
import pandas as pd
import base64
from datetime import datetime
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
from utils.database import creer_user
from utils.export_excel import export_etats_financiers_excel
from smd_streamlit import page_dashboard, page_risque_fiscal, page_analyse_facture
from smd_calendar import page_calendrier_fiscal
from smd_aging import page_balance_agee
from smd_reconciliation import page_rapprochement_bancaire
from smd_tresorerie import page_tresorerie_previsionnelle
from smd_plan_financement import page_plan_financement
from smd_tft import page_tft

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
    st.subheader("Normes OHADA/UEMOA — Cabinets & PME/TPE")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style='background:#f0fdf4;padding:12px;border-radius:8px;margin-bottom:10px;font-size:0.85em'>
        ✅ <b>Données sécurisées</b> — Hébergées sur Supabase (UE)<br>
        ✅ <b>IA Mistral</b> — Données non utilisées pour l'entraînement<br>
        ✅ <b>Normes SYSCOHADA</b> — 8 pays UEMOA couverts
        </div>
        """, unsafe_allow_html=True)

        # ── Onglets Connexion / Inscription ───────────────────────────────
        tab_login, tab_signup = st.tabs(["🔑 Se connecter", "📝 Créer un compte"])

        # ── CONNEXION ─────────────────────────────────────────────────────
        with tab_login:
            st.markdown("")
            email_l    = st.text_input("📧 Email", placeholder="contact@cabinet.com", key="login_email")
            password_l = st.text_input("🔑 Mot de passe", type="password", key="login_pw")
            if st.button("🚀 Se connecter", type="primary", use_container_width=True):
                if login(email_l, password_l):
                    st.success("✅ Connexion réussie !")
                    st.rerun()
                else:
                    st.error("❌ Email ou mot de passe incorrect")
            st.markdown("---")
            st.markdown("##### 🎯 Tester sans inscription")
            if st.button("👀 Accès Démonstration", use_container_width=True, key="btn_demo"):
                st.session_state["authenticated"] = True
                st.session_state["user_email"]    = "demo@smdconsulting.pro"
                st.session_state["role"]          = "demo"
                st.session_state["nom"]           = "Démonstration"
                st.session_state["cabinet"]       = "Demo"
                st.session_state["login_time"]    = datetime.now().isoformat()
                st.rerun()

        # ── INSCRIPTION ───────────────────────────────────────────────────
        with tab_signup:
            st.markdown("")
            from data.plan_comptable_syscohada import FISCALITE_UEMOA
            pays_opts = {v["nom"]: k for k, v in FISCALITE_UEMOA.items()}

            with st.form("form_inscription"):
                s_email    = st.text_input("📧 Email professionnel *", placeholder="contact@cabinet.com")
                s_nom      = st.text_input("👤 Nom complet *",          placeholder="Souleymane Diallo")
                s_cabinet  = st.text_input("🏢 Cabinet / Entreprise *", placeholder="Cabinet SMD")
                s_pays     = st.selectbox("🌍 Pays", list(pays_opts.keys()))
                s_pw       = st.text_input("🔑 Mot de passe *",  type="password",
                                           help="8 caractères minimum")
                s_pw2      = st.text_input("🔑 Confirmer le mot de passe *", type="password")
                submitted  = st.form_submit_button("✅ Créer mon compte", use_container_width=True,
                                                   type="primary")

            if submitted:
                # Validations
                if not all([s_email, s_nom, s_cabinet, s_pw, s_pw2]):
                    st.error("⚠️ Tous les champs obligatoires (*) doivent être remplis.")
                elif len(s_pw) < 8:
                    st.error("⚠️ Le mot de passe doit faire au moins 8 caractères.")
                elif s_pw != s_pw2:
                    st.error("⚠️ Les mots de passe ne correspondent pas.")
                elif "@" not in s_email or "." not in s_email:
                    st.error("⚠️ Adresse email invalide.")
                else:
                    result = creer_user(
                        email   = s_email,
                        password= s_pw,
                        nom     = s_nom,
                        cabinet = s_cabinet,
                        pays    = s_pays
                    )
                    if result.get("ok"):
                        st.success(f"🎉 Compte créé ! Connectez-vous avec **{s_email}**")
                        st.balloons()
                    else:
                        st.error(f"❌ {result.get('error', 'Erreur inconnue')}")

        st.markdown("---")
        st.caption("📧 Support : contact@smdconsulting.pro")

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
def is_demo():
    """Vérifie si l'utilisateur est en mode démonstration"""
    return st.session_state.get("role") == "demo"

def banniere_demo():
    """Affiche une bannière demo si applicable"""
    if is_demo():
        st.warning("👀 **Mode Démonstration** — Données fictives uniquement. Sauvegarde désactivée.")

def sauvegarder_si_autorise(ent_id, type_a, titre, resultat, pays_nom, exercice):
    """Sauvegarde uniquement si pas en mode démo"""
    if is_demo():
        st.info("💡 Sauvegarde désactivée en mode démonstration.")
    else:
        sauvegarder_si_entreprise(ent_id, type_a, titre, resultat, pays_nom, exercice)
def charger_fichier(fichier):
    """Charge un fichier CSV ou XLSX en DataFrame avec gestion d'erreurs"""
    try:
        if fichier.name.endswith('.xlsx'):
            return pd.read_excel(fichier), None
        else:
            try:
                return pd.read_csv(fichier, encoding='utf-8'), None
            except:
                fichier.seek(0)
                return pd.read_csv(fichier, encoding='latin-1'), None
    except Exception as e:
        return None, str(e)


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
# Indicateur mode démo
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
    ],
    label_visibility="collapsed"
)

# Neutraliser les séparateurs
separateurs = [
    "─── États Financiers ───",
    "─── Fiscal & Réglementaire ───",
    "─── Fiscal Quantitatif ───",
]
if page in separateurs:
    page = "🏠 Accueil"

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
            df, erreur = charger_fichier(fichier)

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
            df, erreur = charger_fichier(fichier)

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
                with st.container():
                    st.markdown("#### 📥 Export Excel Professionnel")
                    try:
                        excel_buf = export_etats_financiers_excel(
                            df, code_pays, ent_nom, exercice
                        )
                        st.download_button(
                            "📊 Télécharger États Financiers Excel (Bilan + CR + TAFIRE + Ratios)",
                            excel_buf,
                            f"Etats_Financiers_{ent_nom}_{exercice}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                    except Exception as e:
                        st.error(f"Erreur export Excel : {e}")
   
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
            df, erreur = charger_fichier(fichier)

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
                with st.container():
                    st.markdown("#### 📥 Export Excel Professionnel")
                    try:
                        excel_buf = export_etats_financiers_excel(
                            df, code_pays, ent_nom, exercice
                        )
                        st.download_button(
                            "📊 Télécharger États Financiers Excel (Bilan + CR + TAFIRE + Ratios)",
                            excel_buf,
                            f"Etats_Financiers_{ent_nom}_{exercice}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                    except Exception as e:
                        st.error(f"Erreur export Excel : {e}")

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
            df, erreur = charger_fichier(fichier)

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
                with st.container():
                    st.markdown("#### 📥 Export Excel Professionnel")
                    try:
                        excel_buf = export_etats_financiers_excel(
                            df, code_pays, ent_nom, exercice
                        )
                        st.download_button(
                            "📊 Télécharger États Financiers Excel (Bilan + CR + TAFIRE + Ratios)",
                            excel_buf,
                            f"Etats_Financiers_{ent_nom}_{exercice}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                    except Exception as e:
                        st.error(f"Erreur export Excel : {e}")

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
            df, erreur = charger_fichier(fichier)

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
            df, erreur = charger_fichier(fichier)

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
# PAGE : CALENDRIER FISCAL / TABLEAU DE BORD
# =============================================================================
elif page == "📅 Calendrier Fiscal UEMOA":
    page_calendrier_fiscal()

elif page == "📊 Tableau de Bord Fiscal":
    page_dashboard()

# =============================================================================
# PAGE : ANALYSE DU RISQUE FISCAL
# =============================================================================
elif page == "🚨 Analyse du Risque Fiscal":
    page_risque_fiscal()

# =============================================================================
# PAGE : ANALYSE FACTURE SYSCOHADA
# =============================================================================
elif page == "🧾 Analyse Facture SYSCOHADA":
    page_analyse_facture()

# =============================================================================
# PAGE : BALANCE AGEE TIERS
# =============================================================================
elif page == "💳 Balance Âgée Tiers":
    page_balance_agee()

# =============================================================================
# PAGE : RAPPROCHEMENT BANCAIRE
# =============================================================================
elif page == "🏦 Rapprochement Bancaire":
    page_rapprochement_bancaire()

# =============================================================================
# PAGE : TRESORERIE PREVISIONNELLE
# =============================================================================
elif page == "📊 Tresorerie Previsionnelle":
    page_tresorerie_previsionnelle()

# =============================================================================
# PAGE : PLAN DE FINANCEMENT
# =============================================================================
elif page == "📐 Plan de Financement":
    page_plan_financement()

# =============================================================================
# PAGE : TFT SYSCOHADA
# =============================================================================
elif page == "💹 TFT SYSCOHADA":
    page_tft()

st.divider()
st.caption(
    "**SMD Consulting** - Superviseur IA Comptable SYSCOHADA\n"
    "Comptable Augmenté par Intelligence Artificielle — Normes OHADA/UEMOA\n"
    "© 2026 - Souleymane Diallo"
)
