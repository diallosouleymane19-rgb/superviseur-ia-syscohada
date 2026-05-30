# -*- coding: utf-8 -*-
"""
utils/database.py - SMD Consulting
Gestion clients + analyses (RGPD).
Backend : Supabase PostgreSQL — remplace SQLite.
API identique a l'ancienne version — drop-in replacement.
"""

import logging
from datetime import datetime, timedelta

from utils.db_supabase import get_supabase

logger = logging.getLogger(__name__)

RETENTION_JOURS = 30  # duree conservation RGPD


# =============================================================================
# Compatibilite — init_db() no-op (schema gere par migrations Supabase)
# =============================================================================
def init_db():
    pass


# =============================================================================
# CLIENTS
# =============================================================================

def creer_client(nom: str, siret: str = "", secteur: str = "",
                 contact: str = "", email: str = "") -> bool:
    try:
        user_email = _get_current_user_email()
        get_supabase().table("clients").insert({
            "nom":        nom,
            "siret":      siret,
            "secteur":    secteur,
            "contact":    contact,
            "email":      email,
            "user_email": user_email,
        }).execute()
        _log_action("CREATION_CLIENT", user_email, f"Client : {nom}")
        return True
    except Exception as e:
        logger.error("creer_client : " + str(e))
        return False


def lister_clients() -> list:
    try:
        user_email = _get_current_user_email()
        res = (
            get_supabase()
            .table("clients")
            .select("id, nom, siret, secteur, contact, email, user_email, created_at")
            .eq("user_email", user_email)
            .order("nom")
            .execute()
        )
        # Convertit en tuples pour compatibilite ascendante
        rows = []
        for r in (res.data or []):
            rows.append((
                r["id"], r["nom"], r.get("siret", ""),
                r.get("secteur", ""), r.get("contact", ""),
                r.get("email", ""),
                r.get("created_at", "")[:16] if r.get("created_at") else "",
            ))
        return rows
    except Exception as e:
        logger.error("lister_clients : " + str(e))
        return []


def get_client(client_id) -> tuple | None:
    try:
        res = (
            get_supabase()
            .table("clients")
            .select("*")
            .eq("id", int(client_id))
            .limit(1)
            .execute()
        )
        if res.data:
            r = res.data[0]
            return (
                r["id"], r["nom"], r.get("siret", ""),
                r.get("secteur", ""), r.get("contact", ""),
                r.get("email", ""),
                r.get("created_at", ""),
            )
        return None
    except Exception as e:
        logger.error("get_client : " + str(e))
        return None


def supprimer_client(client_id) -> bool:
    try:
        sb = get_supabase()
        sb.table("analyses").update({"client_id": None}).eq("client_id", int(client_id)).execute()
        sb.table("clients").delete().eq("id", int(client_id)).execute()
        _log_action("SUPPRESSION_CLIENT", _get_current_user_email(), f"ID : {client_id}")
        return True
    except Exception as e:
        logger.error("supprimer_client : " + str(e))
        return False


# =============================================================================
# ANALYSES
# =============================================================================

def sauvegarder_analyse(type_analyse=None, resultat=None, client_id=0,
                         titre=None, contenu=None, exercice="", **kwargs) -> bool:
    if contenu is None and resultat is not None:
        contenu = str(resultat)
    elif contenu is None:
        contenu = ""
    if titre is None:
        titre = type_analyse or "Analyse"
    if client_id is None:
        client_id = 0

    expires_at = (datetime.utcnow() + timedelta(days=RETENTION_JOURS)).isoformat()
    user_email = _get_current_user_email()

    try:
        get_supabase().table("analyses").insert({
            "client_id":    int(client_id) if client_id else None,
            "type_analyse": type_analyse,
            "titre":        titre,
            "contenu":      str(contenu),
            "exercice":     exercice,
            "user_email":   user_email,
            "expires_at":   expires_at,
        }).execute()
        _log_action("SAUVEGARDE_ANALYSE", user_email, f"Type : {type_analyse}")
        return True
    except Exception as e:
        logger.error("sauvegarder_analyse : " + str(e))
        return False


def lister_analyses(client_id=None) -> list:
    try:
        user_email = _get_current_user_email()
        sb = get_supabase()
        q = (
            sb.table("analyses")
            .select("id, type_analyse, titre, created_at, exercice")
            .eq("user_email", user_email)
        )
        if client_id is not None:
            q = q.eq("client_id", int(client_id))
        res = q.order("created_at", desc=True).execute()
        rows = []
        for r in (res.data or []):
            rows.append((
                r["id"],
                r.get("type_analyse", ""),
                r.get("titre", ""),
                r.get("created_at", "")[:16] if r.get("created_at") else "",
                r.get("exercice", ""),
            ))
        return rows
    except Exception as e:
        logger.error("lister_analyses : " + str(e))
        return []


def get_analyse(analyse_id) -> tuple | None:
    try:
        res = (
            get_supabase()
            .table("analyses")
            .select("*")
            .eq("id", int(analyse_id))
            .limit(1)
            .execute()
        )
        if res.data:
            r = res.data[0]
            return (
                r["id"],
                r.get("client_id"),
                r.get("type_analyse", ""),
                r.get("titre", ""),
                r.get("contenu", ""),
                r.get("created_at", ""),
                r.get("expires_at", ""),
                r.get("exercice", ""),
                r.get("user_email", ""),
            )
        return None
    except Exception as e:
        logger.error("get_analyse : " + str(e))
        return None


def supprimer_analyse(analyse_id) -> bool:
    try:
        get_supabase().table("analyses").delete().eq("id", int(analyse_id)).execute()
        _log_action("SUPPRESSION_ANALYSE", _get_current_user_email(), f"ID : {analyse_id}")
        return True
    except Exception as e:
        logger.error("supprimer_analyse : " + str(e))
        return False


def purger_donnees_expirees():
    """Supprime les analyses dont expires_at est depasse (RGPD)."""
    try:
        now = datetime.utcnow().isoformat()
        res = (
            get_supabase()
            .table("analyses")
            .delete()
            .lt("expires_at", now)
            .execute()
        )
        nb = len(res.data or [])
        if nb > 0:
            logger.info(f"RGPD : {nb} analyse(s) expiree(s) supprimee(s)")
    except Exception as e:
        logger.error("purger_donnees_expirees : " + str(e))


# =============================================================================
# Helpers
# =============================================================================

def _get_current_user_email() -> str:
    try:
        import streamlit as st
        return st.session_state.get("user_email", "system")
    except Exception:
        return "system"


def _log_action(action: str, user_email: str = "", detail: str = ""):
    try:
        get_supabase().table("audit_logs").insert({
            "action":  action,
            "module":  "database",
            "details": {"user_email": user_email, "detail": detail},
        }).execute()
    except Exception:
        pass


# =============================================================================
# Aliases SYSCOHADA (l'app utilise "entreprise" au lieu de "client")
# =============================================================================

def creer_entreprise(nom, siret="", secteur="", contact="", email=""):
    return creer_client(nom, siret, secteur, contact, email)

def lister_entreprises():
    return lister_clients()

def get_entreprise(entreprise_id):
    return get_client(entreprise_id)

def supprimer_entreprise(entreprise_id):
    return supprimer_client(entreprise_id)

def creer_user(email, password, nom="", cabinet="", pays="FR",
               role="client", plan="free"):
    from utils.auth_rbac import creer_user_rbac
    return creer_user_rbac(email, password, nom, cabinet, pays, role, plan)


def page_dossiers_entreprises():
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
