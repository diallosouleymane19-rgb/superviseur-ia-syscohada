# -*- coding: utf-8 -*-
"""Refonte page Accueil — version pro epuree"""
import sys, re

app_path = r"C:\Users\blois\superviseur-ia\app.py"

with open(app_path, encoding="utf-8") as f:
    app = f.read()

# Marqueurs uniques
START = 'if page == "\U0001f3e0 Accueil":'
END   = '# ---'   # debut section suivante

idx_start = app.find(START)
if idx_start == -1:
    print("ERREUR : marqueur Accueil introuvable", file=sys.stderr)
    sys.exit(1)

# Chercher le prochain commentaire de section (----) apres le bloc Accueil
idx_end = app.find('\n# ---', idx_start + len(START))
if idx_end == -1:
    print("ERREUR : fin de bloc Accueil introuvable", file=sys.stderr)
    sys.exit(1)

NEW_BLOCK = r'''if page == "\U0001f3e0 Accueil":
    banniere_demo()

    st.markdown("""
    <div style="padding:1.5rem 1rem 1rem 1rem; border-bottom:2px solid #1F4E79; margin-bottom:1.5rem;">
        <h1 style="margin:0; color:#1F4E79; font-size:1.9rem;">Superviseur IA Comptable</h1>
        <p style="margin:0.4rem 0 0 0; color:#555; font-size:0.95rem;">
            SMD Global Consulting LLC &nbsp;&middot;&nbsp; Audit &amp; Finance augment&eacute;s par l'IA
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("**\U0001f50d Analyse & Audit**")
        st.caption("Factures OCR, Benford, audit balance, alertes anomalies")
    with col2:
        st.markdown("**\U0001f4ca États Financiers**")
        st.caption("Bilan, CdR/SIG, TFT, Plan de Financement, Comparatif N/N-1")
    with col3:
        st.markdown("**\U0001f4e6 Gestion & Clôture**")
        st.caption("Immobilisations, amortissements, provisions, inventaire")
    with col4:
        st.markdown("**\U0001f4c1 Reporting & Fiscal**")
        st.caption("FEC DGFiP, TVA CA3/CA12, rapports clients, veille fiscale")

    st.divider()

    user = st.session_state.get("user_email", "—")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("\U0001f464 Session", user.split("@")[0] if "@" in user else user)
    c2.metric("\U0001f4e6 Modules", "21")
    c3.metric("✅ Statut", "Opérationnel")
    c4.metric("\U0001f512 Données", "Non conservées")

    st.divider()
    st.caption("SMD Global Consulting LLC © 2026 — PCG France · ANC/CRC 99-02 · Données traitées localement, jamais stockées.")'''

# Remplacer le bloc
app = app[:idx_start] + NEW_BLOCK + app[idx_end:]

with open(app_path, "w", encoding="utf-8") as f:
    f.write(app)

print("OK  page Accueil refaite")
