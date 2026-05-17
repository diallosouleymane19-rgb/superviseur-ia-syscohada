# -*- coding: utf-8 -*-
"""
Base de données — SMD Consulting
Supabase (PostgreSQL) en production, SQLite en local si Supabase non configuré
"""
import os
import sqlite3
from datetime import datetime

# ─── Client Supabase ────────────────────────────────────────────────────────

def _get_supabase():
    """Retourne un client Supabase ou None si non configuré."""
    try:
        from supabase import create_client
        import streamlit as st
        url  = st.secrets.get("SUPABASE_URL", "")
        key  = st.secrets.get("SUPABASE_KEY", "")
        if url and key:
            return create_client(url, key)
    except Exception:
        pass
    # Fallback : pas de Supabase configuré
    try:
        url  = os.getenv("SUPABASE_URL", "")
        key  = os.getenv("SUPABASE_KEY", "")
        if url and key:
            from supabase import create_client
            return create_client(url, key)
    except Exception:
        pass
    return None

def _user_email():
    """Récupère l'email de l'utilisateur connecté."""
    try:
        import streamlit as st
        return st.session_state.get("user_email", "anonymous")
    except Exception:
        return "anonymous"

# ─── SQLite fallback ────────────────────────────────────────────────────────

_IS_CLOUD = os.getenv("STREAMLIT_SHARING_MODE") or os.getenv("HOME") == "/home/appuser"
DB_PATH   = "/tmp/smd_syscohada.db" if _IS_CLOUD else "smd_syscohada.db"

def _sqlite():
    return sqlite3.connect(DB_PATH)

# ─── init_db ────────────────────────────────────────────────────────────────

def init_db():
    """Initialise la DB locale SQLite (fallback uniquement)."""
    conn = _sqlite()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS entreprises (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT DEFAULT 'local',
            nom TEXT NOT NULL, pays TEXT, code_pays TEXT,
            secteur TEXT, regime_fiscal TEXT, contact TEXT,
            email TEXT, date_creation TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entreprise_id INTEGER,
            user_email TEXT DEFAULT 'local',
            type_analyse TEXT, titre TEXT, contenu TEXT,
            pays TEXT, exercice TEXT, date_analyse TEXT,
            FOREIGN KEY (entreprise_id) REFERENCES entreprises(id)
        )
    """)
    conn.commit()
    conn.close()

# ════════════════════════════════════════════════════════════════════════════
# ENTREPRISES
# ════════════════════════════════════════════════════════════════════════════

def creer_entreprise(nom, pays, code_pays, secteur, regime_fiscal, contact, email):
    sb = _get_supabase()
    date_c = datetime.now().strftime("%d/%m/%Y %H:%M")
    if sb:
        sb.table("entreprises").insert({
            "user_email": _user_email(),
            "nom": nom, "pays": pays, "code_pays": code_pays,
            "secteur": secteur, "regime_fiscal": regime_fiscal,
            "contact": contact, "email": email, "date_creation": date_c
        }).execute()
    else:
        conn = _sqlite()
        conn.execute("""
            INSERT INTO entreprises
            (user_email, nom, pays, code_pays, secteur, regime_fiscal, contact, email, date_creation)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (_user_email(), nom, pays, code_pays, secteur, regime_fiscal, contact, email, date_c))
        conn.commit(); conn.close()


def lister_entreprises():
    sb = _get_supabase()
    if sb:
        res = sb.table("entreprises")\
                .select("*")\
                .eq("user_email", _user_email())\
                .order("nom")\
                .execute()
        return [(r["id"], r["nom"], r["pays"], r["code_pays"],
                 r.get("secteur",""), r.get("regime_fiscal",""),
                 r.get("contact",""), r.get("email",""), r.get("date_creation",""))
                for r in res.data]
    else:
        conn = _sqlite()
        rows = conn.execute("SELECT * FROM entreprises ORDER BY nom").fetchall()
        conn.close(); return rows


def get_entreprise(entreprise_id):
    sb = _get_supabase()
    if sb:
        res = sb.table("entreprises").select("*").eq("id", entreprise_id).execute()
        if res.data:
            r = res.data[0]
            return (r["id"], r["nom"], r["pays"], r["code_pays"],
                    r.get("secteur",""), r.get("regime_fiscal",""),
                    r.get("contact",""), r.get("email",""), r.get("date_creation",""))
    else:
        conn = _sqlite()
        row = conn.execute("SELECT * FROM entreprises WHERE id=?", (entreprise_id,)).fetchone()
        conn.close(); return row


def supprimer_entreprise(entreprise_id):
    sb = _get_supabase()
    if sb:
        sb.table("analyses").delete().eq("entreprise_id", entreprise_id).execute()
        sb.table("entreprises").delete().eq("id", entreprise_id).execute()
    else:
        conn = _sqlite()
        conn.execute("DELETE FROM analyses WHERE entreprise_id=?", (entreprise_id,))
        conn.execute("DELETE FROM entreprises WHERE id=?", (entreprise_id,))
        conn.commit(); conn.close()

# ════════════════════════════════════════════════════════════════════════════
# ANALYSES
# ════════════════════════════════════════════════════════════════════════════

def sauvegarder_analyse(entreprise_id, type_analyse, titre, contenu, pays, exercice):
    sb = _get_supabase()
    date_a = datetime.now().strftime("%d/%m/%Y %H:%M")
    if sb:
        sb.table("analyses").insert({
            "entreprise_id": entreprise_id,
            "user_email": _user_email(),
            "type_analyse": type_analyse, "titre": titre,
            "contenu": contenu, "pays": pays,
            "exercice": exercice, "date_analyse": date_a
        }).execute()
    else:
        conn = _sqlite()
        conn.execute("""
            INSERT INTO analyses
            (entreprise_id, user_email, type_analyse, titre, contenu, pays, exercice, date_analyse)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (entreprise_id, _user_email(), type_analyse, titre, contenu, pays, exercice, date_a))
        conn.commit(); conn.close()


def lister_analyses(entreprise_id):
    sb = _get_supabase()
    if sb:
        res = sb.table("analyses")\
                .select("id, type_analyse, titre, date_analyse, pays, exercice")\
                .eq("entreprise_id", entreprise_id)\
                .order("date_analyse", desc=True)\
                .execute()
        return [(r["id"], r["type_analyse"], r["titre"],
                 r["date_analyse"], r.get("pays",""), r.get("exercice",""))
                for r in res.data]
    else:
        conn = _sqlite()
        rows = conn.execute("""
            SELECT id, type_analyse, titre, date_analyse, pays, exercice
            FROM analyses WHERE entreprise_id=? ORDER BY date_analyse DESC
        """, (entreprise_id,)).fetchall()
        conn.close(); return rows


def get_analyse(analyse_id):
    sb = _get_supabase()
    if sb:
        res = sb.table("analyses").select("*").eq("id", analyse_id).execute()
        if res.data:
            r = res.data[0]
            return (r["id"], r.get("entreprise_id"), r.get("type_analyse"),
                    r.get("titre"), r.get("contenu"), r.get("pays"),
                    r.get("exercice"), r.get("date_analyse"))
    else:
        conn = _sqlite()
        row = conn.execute("SELECT * FROM analyses WHERE id=?", (analyse_id,)).fetchone()
        conn.close(); return row


def supprimer_analyse(analyse_id):
    sb = _get_supabase()
    if sb:
        sb.table("analyses").delete().eq("id", analyse_id).execute()
    else:
        conn = _sqlite()
        conn.execute("DELETE FROM analyses WHERE id=?", (analyse_id,))
        conn.commit(); conn.close()
