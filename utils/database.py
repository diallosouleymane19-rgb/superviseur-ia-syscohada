# -*- coding: utf-8 -*-
"""
Base de données — SMD Consulting
Supabase REST API (production) / SQLite (local fallback)
"""
import os
import sqlite3
import requests
from datetime import datetime

# ─── Config Supabase ────────────────────────────────────────────────────────

def _get_config():
    """Récupère URL et clé Supabase depuis st.secrets ou env."""
    try:
        import streamlit as st
        url = st.secrets.get("SUPABASE_URL", "")
        key = st.secrets.get("SUPABASE_KEY", "")
        if url and key:
            return url.rstrip("/"), key
    except Exception:
        pass
    url = os.getenv("SUPABASE_URL", "")
    key = os.getenv("SUPABASE_KEY", "")
    if url and key:
        return url.rstrip("/"), key
    return None, None


def _headers():
    _, key = _get_config()
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


def _use_supabase():
    url, key = _get_config()
    return bool(url and key)


def _sb_url(table):
    url, _ = _get_config()
    return f"{url}/rest/v1/{table}"


def _user_email():
    try:
        import streamlit as st
        return st.session_state.get("user_email", "anonymous")
    except Exception:
        return "anonymous"


# ─── SQLite fallback ────────────────────────────────────────────────────────

_IS_CLOUD = os.getenv("STREAMLIT_SHARING_MODE") or os.getenv("HOME") == "/home/appuser"
DB_PATH   = "/tmp/smd_syscohada.db" if _IS_CLOUD else "smd_syscohada.db"


def init_db():
    """Initialise SQLite (fallback local uniquement)."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS entreprises (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT DEFAULT 'local',
            nom TEXT NOT NULL, pays TEXT, code_pays TEXT,
            secteur TEXT, regime_fiscal TEXT,
            contact TEXT, email TEXT, date_creation TEXT
        )
    """)
    # Migration : ajouter user_email si absent (ancienne DB)
    try:
        c.execute("ALTER TABLE entreprises ADD COLUMN user_email TEXT DEFAULT 'local'")
    except Exception:
        pass
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
    try:
        c.execute("ALTER TABLE analyses ADD COLUMN user_email TEXT DEFAULT 'local'")
    except Exception:
        pass
    conn.commit()
    conn.close()


# ════════════════════════════════════════════════════════════════════════════
# ENTREPRISES
# ════════════════════════════════════════════════════════════════════════════

def creer_entreprise(nom, pays, code_pays, secteur, regime_fiscal, contact, email):
    date_c = datetime.now().strftime("%d/%m/%Y %H:%M")
    user   = _user_email()

    if _use_supabase():
        payload = {
            "user_email": user, "nom": nom, "pays": pays,
            "code_pays": code_pays, "secteur": secteur,
            "regime_fiscal": regime_fiscal, "contact": contact,
            "email": email, "date_creation": date_c
        }
        r = requests.post(_sb_url("entreprises"), json=payload, headers=_headers())
        if r.status_code not in (200, 201):
            raise Exception(f"Supabase error {r.status_code}: {r.text}")
    else:
        init_db()
        conn = sqlite3.connect(DB_PATH)
        conn.execute("""
            INSERT INTO entreprises
            (user_email, nom, pays, code_pays, secteur, regime_fiscal, contact, email, date_creation)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (user, nom, pays, code_pays, secteur, regime_fiscal, contact, email, date_c))
        conn.commit(); conn.close()


def lister_entreprises():
    user = _user_email()
    if _use_supabase():
        r = requests.get(
            _sb_url("entreprises"),
            headers=_headers(),
            params={"user_email": f"eq.{user}", "order": "nom.asc"}
        )
        if r.status_code == 200:
            return [(e["id"], e["nom"], e.get("pays",""), e.get("code_pays",""),
                     e.get("secteur",""), e.get("regime_fiscal",""),
                     e.get("contact",""), e.get("email",""), e.get("date_creation",""))
                    for e in r.json()]
        return []
    else:
        init_db()
        conn = sqlite3.connect(DB_PATH)
        rows = conn.execute("""
            SELECT id, nom, pays, code_pays, secteur, regime_fiscal,
                   contact, email, date_creation
            FROM entreprises ORDER BY nom
        """).fetchall()
        conn.close(); return rows


def get_entreprise(entreprise_id):
    if _use_supabase():
        r = requests.get(
            _sb_url("entreprises"),
            headers=_headers(),
            params={"id": f"eq.{entreprise_id}"}
        )
        if r.status_code == 200 and r.json():
            e = r.json()[0]
            return (e["id"], e["nom"], e.get("pays",""), e.get("code_pays",""),
                    e.get("secteur",""), e.get("regime_fiscal",""),
                    e.get("contact",""), e.get("email",""), e.get("date_creation",""))
        return None
    else:
        init_db()
        conn = sqlite3.connect(DB_PATH)
        row = conn.execute("""
            SELECT id, nom, pays, code_pays, secteur, regime_fiscal,
                   contact, email, date_creation
            FROM entreprises WHERE id=?
        """, (entreprise_id,)).fetchone()
        conn.close(); return row


def supprimer_entreprise(entreprise_id):
    if _use_supabase():
        requests.delete(_sb_url("analyses"),    headers=_headers(), params={"entreprise_id": f"eq.{entreprise_id}"})
        requests.delete(_sb_url("entreprises"), headers=_headers(), params={"id": f"eq.{entreprise_id}"})
    else:
        init_db()
        conn = sqlite3.connect(DB_PATH)
        conn.execute("DELETE FROM analyses WHERE entreprise_id=?",  (entreprise_id,))
        conn.execute("DELETE FROM entreprises WHERE id=?", (entreprise_id,))
        conn.commit(); conn.close()


# ════════════════════════════════════════════════════════════════════════════
# ANALYSES
# ════════════════════════════════════════════════════════════════════════════

def sauvegarder_analyse(entreprise_id, type_analyse, titre, contenu, pays, exercice):
    date_a = datetime.now().strftime("%d/%m/%Y %H:%M")
    user   = _user_email()
    if _use_supabase():
        payload = {
            "entreprise_id": entreprise_id, "user_email": user,
            "type_analyse": type_analyse, "titre": titre,
            "contenu": contenu, "pays": pays,
            "exercice": exercice, "date_analyse": date_a
        }
        r = requests.post(_sb_url("analyses"), json=payload, headers=_headers())
        if r.status_code not in (200, 201):
            raise Exception(f"Supabase error {r.status_code}: {r.text}")
    else:
        init_db()
        conn = sqlite3.connect(DB_PATH)
        conn.execute("""
            INSERT INTO analyses
            (entreprise_id, user_email, type_analyse, titre, contenu, pays, exercice, date_analyse)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (entreprise_id, user, type_analyse, titre, contenu, pays, exercice, date_a))
        conn.commit(); conn.close()


def lister_analyses(entreprise_id):
    if _use_supabase():
        r = requests.get(
            _sb_url("analyses"),
            headers=_headers(),
            params={
                "select": "id,type_analyse,titre,date_analyse,pays,exercice",
                "entreprise_id": f"eq.{entreprise_id}",
                "order": "date_analyse.desc"
            }
        )
        if r.status_code == 200:
            return [(a["id"], a["type_analyse"], a["titre"],
                     a["date_analyse"], a.get("pays",""), a.get("exercice",""))
                    for a in r.json()]
        return []
    else:
        init_db()
        conn = sqlite3.connect(DB_PATH)
        rows = conn.execute("""
            SELECT id, type_analyse, titre, date_analyse, pays, exercice
            FROM analyses WHERE entreprise_id=? ORDER BY date_analyse DESC
        """, (entreprise_id,)).fetchall()
        conn.close(); return rows


def get_analyse(analyse_id):
    if _use_supabase():
        r = requests.get(_sb_url("analyses"), headers=_headers(), params={"id": f"eq.{analyse_id}"})
        if r.status_code == 200 and r.json():
            a = r.json()[0]
            return (a["id"], a.get("entreprise_id"), a.get("type_analyse"),
                    a.get("titre"), a.get("contenu"), a.get("pays"),
                    a.get("exercice"), a.get("date_analyse"))
        return None
    else:
        init_db()
        conn = sqlite3.connect(DB_PATH)
        row = conn.execute("SELECT * FROM analyses WHERE id=?", (analyse_id,)).fetchone()
        conn.close(); return row


def supprimer_analyse(analyse_id):
    if _use_supabase():
        requests.delete(_sb_url("analyses"), headers=_headers(), params={"id": f"eq.{analyse_id}"})
    else:
        init_db()
        conn = sqlite3.connect(DB_PATH)
        conn.execute("DELETE FROM analyses WHERE id=?", (analyse_id,))
        conn.commit(); conn.close()


# ════════════════════════════════════════════════════════════════════════════
# GESTION DES UTILISATEURS
# ════════════════════════════════════════════════════════════════════════════

def creer_user(email: str, password: str, nom: str = "", cabinet: str = "", pays: str = "") -> dict:
    """Crée un nouvel utilisateur avec mot de passe hashé. Retourne {"ok": True} ou {"error": "..."}"""
    import bcrypt
    # Vérifier si l'email existe déjà
    existant = get_user_by_email(email)
    if existant:
        return {"error": "Cet email est déjà enregistré."}

    pw_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    date_i  = datetime.now().strftime("%d/%m/%Y %H:%M")

    if _use_supabase():
        payload = {
            "email": email.lower().strip(),
            "password_hash": pw_hash,
            "nom": nom, "cabinet": cabinet, "pays": pays,
            "role": "client", "is_active": True,
            "date_inscription": date_i
        }
        r = requests.post(_sb_url("users"), json=payload, headers=_headers())
        if r.status_code in (200, 201):
            return {"ok": True}
        return {"error": f"Erreur serveur ({r.status_code}). Réessayez."}
    else:
        init_db()
        conn = sqlite3.connect(DB_PATH)
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    nom TEXT, cabinet TEXT, pays TEXT,
                    role TEXT DEFAULT 'client',
                    is_active INTEGER DEFAULT 1,
                    date_inscription TEXT
                )
            """)
            conn.execute("""
                INSERT INTO users (email, password_hash, nom, cabinet, pays, role, is_active, date_inscription)
                VALUES (?, ?, ?, ?, ?, 'client', 1, ?)
            """, (email.lower().strip(), pw_hash, nom, cabinet, pays, date_i))
            conn.commit()
            return {"ok": True}
        except sqlite3.IntegrityError:
            return {"error": "Cet email est déjà enregistré."}
        finally:
            conn.close()


def get_user_by_email(email: str):
    """Retourne les infos d'un utilisateur par email, ou None."""
    email = email.lower().strip()
    if _use_supabase():
        r = requests.get(
            _sb_url("users"),
            headers=_headers(),
            params={"email": f"eq.{email}", "is_active": "eq.true"}
        )
        if r.status_code == 200 and r.json():
            return r.json()[0]
        return None
    else:
        init_db()
        conn = sqlite3.connect(DB_PATH)
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    nom TEXT, cabinet TEXT, pays TEXT,
                    role TEXT DEFAULT 'client',
                    is_active INTEGER DEFAULT 1,
                    date_inscription TEXT
                )
            """)
            row = conn.execute(
                "SELECT * FROM users WHERE email=? AND is_active=1", (email,)
            ).fetchone()
            if row:
                cols = ["id","email","password_hash","nom","cabinet","pays","role","is_active","date_inscription"]
                return dict(zip(cols, row))
            return None
        finally:
            conn.close()


def verifier_mot_de_passe(email: str, password: str):
    """Vérifie email + mot de passe. Retourne le user dict si OK, None sinon."""
    import bcrypt
    user = get_user_by_email(email)
    if not user:
        return None
    try:
        if bcrypt.checkpw(password.encode("utf-8"), user["password_hash"].encode("utf-8")):
            return user
    except Exception:
        pass
    return None
