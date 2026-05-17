import os
import sqlite3
from datetime import datetime

# Sur Streamlit Cloud le filesystem est éphémère — /tmp persiste pendant la session
_IS_CLOUD = os.getenv("STREAMLIT_SHARING_MODE") or os.getenv("HOME") == "/home/appuser"
DB_PATH = "/tmp/smd_syscohada.db" if _IS_CLOUD else "smd_syscohada.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Table entreprises
    c.execute("""
        CREATE TABLE IF NOT EXISTS entreprises (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            pays TEXT,
            code_pays TEXT,
            secteur TEXT,
            regime_fiscal TEXT,
            contact TEXT,
            email TEXT,
            date_creation TEXT
        )
    """)

    # Table analyses
    c.execute("""
        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entreprise_id INTEGER,
            type_analyse TEXT,
            titre TEXT,
            contenu TEXT,
            pays TEXT,
            exercice TEXT,
            date_analyse TEXT,
            FOREIGN KEY (entreprise_id) REFERENCES entreprises(id)
        )
    """)

    conn.commit()
    conn.close()

# ---------------------------------------------------------
# ENTREPRISES
# ---------------------------------------------------------
def creer_entreprise(nom, pays, code_pays, secteur, regime_fiscal, contact, email):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO entreprises (nom, pays, code_pays, secteur, regime_fiscal, contact, email, date_creation)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (nom, pays, code_pays, secteur, regime_fiscal, contact, email,
          datetime.now().strftime("%d/%m/%Y %H:%M")))
    conn.commit()
    conn.close()

def lister_entreprises():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM entreprises ORDER BY nom")
    entreprises = c.fetchall()
    conn.close()
    return entreprises

def get_entreprise(entreprise_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM entreprises WHERE id = ?", (entreprise_id,))
    entreprise = c.fetchone()
    conn.close()
    return entreprise

def supprimer_entreprise(entreprise_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM analyses WHERE entreprise_id = ?", (entreprise_id,))
    c.execute("DELETE FROM entreprises WHERE id = ?", (entreprise_id,))
    conn.commit()
    conn.close()

# ---------------------------------------------------------
# ANALYSES
# ---------------------------------------------------------
def sauvegarder_analyse(entreprise_id, type_analyse, titre, contenu, pays, exercice):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO analyses (entreprise_id, type_analyse, titre, contenu, pays, exercice, date_analyse)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (entreprise_id, type_analyse, titre, contenu, pays, exercice,
          datetime.now().strftime("%d/%m/%Y %H:%M")))
    conn.commit()
    conn.close()

def lister_analyses(entreprise_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT id, type_analyse, titre, date_analyse, pays, exercice
        FROM analyses
        WHERE entreprise_id = ?
        ORDER BY date_analyse DESC
    """, (entreprise_id,))
    analyses = c.fetchall()
    conn.close()
    return analyses

def get_analyse(analyse_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM analyses WHERE id = ?", (analyse_id,))
    analyse = c.fetchone()
    conn.close()
    return analyse

def supprimer_analyse(analyse_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM analyses WHERE id = ?", (analyse_id,))
    conn.commit()
    conn.close()