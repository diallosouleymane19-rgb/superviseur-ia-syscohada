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

# Initialiser la base de données
init_db()

# ---------------------------------------------------------
# FONCTIONS EXPORT
# ---------------------------------------------------------
def telecharger_html(titre, contenu):
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
    buffer = export_analyse_word(titre, contenu, nom_entreprise, pays, exercice)
    st.download_button(
        label="📄 Télécharger en Word (.docx)",
        data=buffer,
        file_name=f"{titre}.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

# ---------------------------------------------------------
# AUTHENTIFICATION
# ---------------------------------------------------------
if not is_connecte():
    login()
    st.stop()

# ---------------------------------------------------------
# STYLE GLOBAL
# ---------------------------------------------------------
st.markdown("""
<style>
body { font-family: 'Segoe UI', sans-serif; }
table { width: 100%; border-collapse: collapse; }
th, td { border: 1px solid #ddd; padding: 8px; }
th { background-color: #1f77b4; color: white; font-weight: bold; }
tr:nth-child(even) { background-color: #f9f9f9; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# MENU LATÉRAL
# ---------------------------------------------------------
st.sidebar.image("https://raw.githubusercontent.com/diallosouleymane19-rgb/superviseur-ia-syscohada/main/uemoa.png", width=120)
st.sidebar.title("Superviseur IA SYSCOHADA")
st.sidebar.markdown(f"👤 Connecté : **{st.session_state['username']}**")
st.sidebar.markdown("---")
logout()

page = st.sidebar.radio(
    "Navigation",
    [
        "🏠 Accueil",
        "🏢 Dossiers Entreprises",
        "📊 Analyse Balance SYSCOHADA",
        "📋 Bilan SYSCOHADA",
        "📈 Compte de Résultat",
        "💰 TAFIRE",
        "📝 Notes Annexes",
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

# ---------------------------------------------------------
# PAGE : ACCUEIL
# ---------------------------------------------------------
if page == "🏠 Accueil":
    import plotly.express as px

    col_logo, col_titre = st.columns([1, 4])
    with col_logo:
        st.image("https://raw.githubusercontent.com/diallosouleymane19-rgb/superviseur-ia-syscohada/main/uemoa.png", width=100)
    with col_titre:
        st.title("Superviseur IA Comptable SYSCOHADA")

    st.markdown("### Assistant comptable intelligent — Normes OHADA/UEMOA")
    st.markdown("---")

    col1, col2, col3 = st.columns(3)
    col1.info("📊 Analyse Balance\nSelon normes SYSCOHADA")
    col2.info("📋 Bilan SYSCOHADA\nGénération automatique")
    col3.info("📈 Compte de Résultat\nSIG et ratios OHADA")

    st.markdown("---")
    col4, col5, col6 = st.columns(3)
    col4.success("💰 TAFIRE\nTableau financier OHADA")
    col5.success("📝 Notes Annexes\nObligatoires SYSCOHADA")
    col6.success("🧾 Liasse Fiscale\nPar pays UEMOA")

    st.markdown("---")
    col7, col8 = st.columns(2)
    col7.warning("🔍 Plan Comptable OHADA\nRecherche et consultation")
    col8.warning("📰 Veille Fiscale UEMOA\nActualités par pays")

    st.markdown("---")
    st.subheader("🌍 Pays membres UEMOA")
    cols = st.columns(4)
    drapeaux = ["🇸🇳", "🇨🇮", "🇲🇱", "🇧🇫", "🇳🇪", "🇹🇬", "🇧🇯", "🇬🇼"]
    for i, (code, info) in enumerate(FISCALITE_UEMOA.items()):
        cols[i % 4].metric(
            f"{drapeaux[i]} {info['nom']}",
            f"TVA {info['taux_tva']}%",
            f"IS {info['taux_is']}%"
        )

# ---------------------------------------------------------
# PAGE : DOSSIERS ENTREPRISES
# ---------------------------------------------------------
elif page == "🏢 Dossiers Entreprises":
    st.title("🏢 Dossiers Entreprises")
    st.markdown("---")

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
            email = st.text_input("Email")

        if st.button("Créer le dossier"):
            if nom:
                creer_entreprise(nom, pays_sel, code_pays_ent, secteur, regime, contact, email)
                st.success(f"✅ Dossier **{nom}** créé avec succès !")
                st.rerun()
            else:
                st.warning("Le nom est obligatoire.")

    with onglet2:
        st.subheader("📋 Liste des entreprises")
        entreprises = lister_entreprises()

        if not entreprises:
            st.info("Aucune entreprise créée.")
        else:
            for ent in entreprises:
                ent_id, nom, pays, code_p, secteur, regime, contact, email, date_c = ent
                analyses = lister_analyses(ent_id)

                with st.expander(f"🏢 {nom} — {pays} — {len(analyses)} analyse(s)"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Pays :** {pays}")
                        st.write(f"**Secteur :** {secteur or 'Non renseigné'}")
                        st.write(f"**Régime :** {regime or 'Non renseigné'}")
                    with col2:
                        st.write(f"**Contact :** {contact or 'Non renseigné'}")
                        st.write(f"**Email :** {email or 'Non renseigné'}")
                        st.write(f"**Créé le :** {date_c}")

                    if st.button(f"🗑️ Supprimer", key=f"del_{ent_id}"):
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

# ---------------------------------------------------------
# PAGE : ANALYSE BALANCE SYSCOHADA
# ---------------------------------------------------------
elif page == "📊 Analyse Balance SYSCOHADA":
    st.title(f"📊 Analyse Balance SYSCOHADA — {info_pays['nom']}")

    entreprises = lister_entreprises()
    ent_id = None
    ent_nom = ""
    exercice = ""

    if entreprises:
        st.subheader("🏢 Associer à une entreprise (optionnel)")
        options = {"-- Aucune --": None}
        options.update({f"{e[1]} ({e[2]})": e[0] for e in entreprises})
        choix = st.selectbox("Entreprise", list(options.keys()), key="bal_ent")
        ent_id = options[choix]
        ent_nom = choix.split(" (")[0] if ent_id else ""
        exercice = st.text_input("Exercice (ex: 2024)", key="bal_ex")

    fichier = st.file_uploader("Importer une balance (Excel ou CSV)", type=["xlsx", "csv"])
    if fichier:
        try:
            df = pd.read_csv(fichier) if fichier.name.endswith(".csv") else pd.read_excel(fichier)
            st.subheader("Aperçu de la balance :")
            st.dataframe(df)

            if st.button("Analyser la balance"):
                st.info("Analyse SYSCOHADA en cours…")
                resultat = analyser_balance_syscohada(df, code_pays)
                st.subheader("Analyse IA SYSCOHADA :")
                st.markdown(resultat)
                telecharger_html("Analyse_Balance_SYSCOHADA", resultat)
                telecharger_word("Analyse_Balance_SYSCOHADA", resultat, ent_nom, info_pays['nom'], exercice)

                if ent_id:
                    if st.button("💾 Sauvegarder"):
                        sauvegarder_analyse(ent_id, "📊 Balance", fichier.name, resultat, info_pays['nom'], exercice)
                        st.success("✅ Sauvegardé !")
        except Exception as e:
            st.error(f"Erreur : {e}")

# ---------------------------------------------------------
# PAGE : BILAN SYSCOHADA
# ---------------------------------------------------------
elif page == "📋 Bilan SYSCOHADA":
    st.title(f"📋 Bilan SYSCOHADA — {info_pays['nom']}")

    entreprises = lister_entreprises()
    ent_id = None
    ent_nom = ""
    exercice = ""

    if entreprises:
        options = {"-- Aucune --": None}
        options.update({f"{e[1]} ({e[2]})": e[0] for e in entreprises})
        choix = st.selectbox("Entreprise", list(options.keys()), key="bil_ent")
        ent_id = options[choix]
        ent_nom = choix.split(" (")[0] if ent_id else ""
        exercice = st.text_input("Exercice (ex: 2024)", key="bil_ex")

    fichier = st.file_uploader("Importer une balance (Excel ou CSV)", type=["xlsx", "csv"])
    if fichier:
        try:
            df = pd.read_csv(fichier) if fichier.name.endswith(".csv") else pd.read_excel(fichier)
            st.dataframe(df)

            if st.button("Générer le Bilan SYSCOHADA"):
                st.info("Génération en cours…")
                resultat = generer_bilan_syscohada(df, code_pays)
                st.subheader("Bilan SYSCOHADA :")
                st.markdown(resultat)
                telecharger_html("Bilan_SYSCOHADA", resultat)
                telecharger_word("Bilan_SYSCOHADA", resultat, ent_nom, info_pays['nom'], exercice)

                if ent_id:
                    if st.button("💾 Sauvegarder"):
                        sauvegarder_analyse(ent_id, "📋 Bilan", f"Bilan {exercice}", resultat, info_pays['nom'], exercice)
                        st.success("✅ Sauvegardé !")
        except Exception as e:
            st.error(f"Erreur : {e}")

# ---------------------------------------------------------
# PAGE : COMPTE DE RÉSULTAT
# ---------------------------------------------------------
elif page == "📈 Compte de Résultat":
    st.title(f"📈 Compte de Résultat SYSCOHADA — {info_pays['nom']}")

    entreprises = lister_entreprises()
    ent_id = None
    ent_nom = ""
    exercice = ""

    if entreprises:
        options = {"-- Aucune --": None}
        options.update({f"{e[1]} ({e[2]})": e[0] for e in entreprises})
        choix = st.selectbox("Entreprise", list(options.keys()), key="cr_ent")
        ent_id = options[choix]
        ent_nom = choix.split(" (")[0] if ent_id else ""
        exercice = st.text_input("Exercice (ex: 2024)", key="cr_ex")

    fichier = st.file_uploader("Importer une balance (Excel ou CSV)", type=["xlsx", "csv"])
    if fichier:
        try:
            df = pd.read_csv(fichier) if fichier.name.endswith(".csv") else pd.read_excel(fichier)
            st.dataframe(df)

            if st.button("Générer le Compte de Résultat"):
                st.info("Génération en cours…")
                resultat = generer_compte_resultat_syscohada(df, code_pays)
                st.subheader("Compte de Résultat SYSCOHADA :")
                st.markdown(resultat)
                telecharger_html("Compte_Resultat_SYSCOHADA", resultat)
                telecharger_word("Compte_Resultat_SYSCOHADA", resultat, ent_nom, info_pays['nom'], exercice)

                if ent_id:
                    if st.button("💾 Sauvegarder"):
                        sauvegarder_analyse(ent_id, "📈 CR", f"CR {exercice}", resultat, info_pays['nom'], exercice)
                        st.success("✅ Sauvegardé !")
        except Exception as e:
            st.error(f"Erreur : {e}")

# ---------------------------------------------------------
# PAGE : TAFIRE
# ---------------------------------------------------------
elif page == "💰 TAFIRE":
    st.title(f"💰 TAFIRE — {info_pays['nom']}")
    st.markdown("*Tableau Financier des Ressources et Emplois*")

    entreprises = lister_entreprises()
    ent_id = None
    ent_nom = ""
    exercice = ""

    if entreprises:
        options = {"-- Aucune --": None}
        options.update({f"{e[1]} ({e[2]})": e[0] for e in entreprises})
        choix = st.selectbox("Entreprise", list(options.keys()), key="taf_ent")
        ent_id = options[choix]
        ent_nom = choix.split(" (")[0] if ent_id else ""
        exercice = st.text_input("Exercice (ex: 2024)", key="taf_ex")

    fichier = st.file_uploader("Importer une balance (Excel ou CSV)", type=["xlsx", "csv"])
    if fichier:
        try:
            df = pd.read_csv(fichier) if fichier.name.endswith(".csv") else pd.read_excel(fichier)
            st.dataframe(df)

            if st.button("Générer le TAFIRE"):
                st.info("Génération en cours…")
                resultat = generer_tafire(df, code_pays)
                st.subheader("TAFIRE :")
                st.markdown(resultat)
                telecharger_html("TAFIRE_SYSCOHADA", resultat)
                telecharger_word("TAFIRE_SYSCOHADA", resultat, ent_nom, info_pays['nom'], exercice)

                if ent_id:
                    if st.button("💾 Sauvegarder"):
                        sauvegarder_analyse(ent_id, "💰 TAFIRE", f"TAFIRE {exercice}", resultat, info_pays['nom'], exercice)
                        st.success("✅ Sauvegardé !")
        except Exception as e:
            st.error(f"Erreur : {e}")

# ---------------------------------------------------------
# PAGE : NOTES ANNEXES
# ---------------------------------------------------------
elif page == "📝 Notes Annexes":
    st.title(f"📝 Notes Annexes SYSCOHADA — {info_pays['nom']}")

    entreprises = lister_entreprises()
    ent_id = None
    ent_nom = ""
    exercice = ""

    if entreprises:
        options = {"-- Aucune --": None}
        options.update({f"{e[1]} ({e[2]})": e[0] for e in entreprises})
        choix = st.selectbox("Entreprise", list(options.keys()), key="notes_ent")
        ent_id = options[choix]
        ent_nom = choix.split(" (")[0] if ent_id else ""
        exercice = st.text_input("Exercice (ex: 2024)", key="notes_ex")

    fichier = st.file_uploader("Importer une balance (Excel ou CSV)", type=["xlsx", "csv"])
    if fichier:
        try:
            df = pd.read_csv(fichier) if fichier.name.endswith(".csv") else pd.read_excel(fichier)
            st.dataframe(df)

            if st.button("Générer les Notes Annexes"):
                st.info("Génération en cours…")
                resultat = generer_notes_annexes(df, code_pays, ent_nom, exercice)
                st.subheader("Notes Annexes :")
                st.markdown(resultat)
                telecharger_html("Notes_Annexes_SYSCOHADA", resultat)
                telecharger_word("Notes_Annexes_SYSCOHADA", resultat, ent_nom, info_pays['nom'], exercice)

                if ent_id:
                    if st.button("💾 Sauvegarder"):
                        sauvegarder_analyse(ent_id, "📝 Notes", f"Notes {exercice}", resultat, info_pays['nom'], exercice)
                        st.success("✅ Sauvegardé !")
        except Exception as e:
            st.error(f"Erreur : {e}")

# ---------------------------------------------------------
# PAGE : LIASSE FISCALE
# ---------------------------------------------------------
elif page == "🧾 Liasse Fiscale":
    st.title(f"🧾 Liasse Fiscale — {info_pays['nom']}")

    entreprises = lister_entreprises()
    ent_id = None
    ent_nom = ""
    exercice = ""

    if entreprises:
        options = {"-- Aucune --": None}
        options.update({f"{e[1]} ({e[2]})": e[0] for e in entreprises})
        choix = st.selectbox("Entreprise", list(options.keys()), key="liasse_ent")
        ent_id = options[choix]
        ent_nom = choix.split(" (")[0] if ent_id else ""
        exercice = st.text_input("Exercice (ex: 2024)", key="liasse_ex")

    fichier = st.file_uploader("Importer une balance (Excel ou CSV)", type=["xlsx", "csv"])
    if fichier:
        try:
            df = pd.read_csv(fichier) if fichier.name.endswith(".csv") else pd.read_excel(fichier)
            st.dataframe(df)

            if st.button("Générer la Liasse Fiscale"):
                st.info("Génération en cours…")
                resultat = analyser_liasse_fiscale(df, code_pays, exercice)
                st.subheader("Liasse Fiscale :")
                st.markdown(resultat)
                telecharger_html("Liasse_Fiscale", resultat)
                telecharger_word("Liasse_Fiscale", resultat, ent_nom, info_pays['nom'], exercice)

                if ent_id:
                    if st.button("💾 Sauvegarder"):
                        sauvegarder_analyse(ent_id, "🧾 Liasse", f"Liasse {exercice}", resultat, info_pays['nom'], exercice)
                        st.success("✅ Sauvegardé !")
        except Exception as e:
            st.error(f"Erreur : {e}")

# ---------------------------------------------------------
# PAGE : PLAN COMPTABLE OHADA
# ---------------------------------------------------------
elif page == "🔍 Plan Comptable OHADA":
    st.title("🔍 Plan Comptable OHADA")

    onglet1, onglet2 = st.tabs(["🔎 Recherche", "📚 Plan Complet"])

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
                st.dataframe(df_res)
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

# ---------------------------------------------------------
# PAGE : VEILLE FISCALE UEMOA
# ---------------------------------------------------------
elif page == "📰 Veille Fiscale UEMOA":
    st.title(f"📰 Veille Fiscale UEMOA — {info_pays['nom']}")

    st.info(f"""
    **Pays sélectionné :** {info_pays['nom']}  
    **TVA :** {info_pays['taux_tva']}% | **IS :** {info_pays['taux_is']}%  
    **Devise :** {info_pays['devise']}
    """)

    if st.button("Obtenir la veille fiscale"):
        st.info("Génération en cours…")
        resultat = veille_fiscale_uemoa(code_pays)
        st.markdown(resultat)
        telecharger_html("Veille_Fiscale_UEMOA", resultat)
        telecharger_word("Veille_Fiscale_UEMOA", resultat, pays=info_pays['nom'])