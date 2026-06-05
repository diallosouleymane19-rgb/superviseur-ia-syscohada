# -*- coding: utf-8 -*-
import sys

REPO = r"C:\Users\blois\superviseur-ia"

with open(REPO + r"\app.py", encoding="utf-8") as f:
    app = f.read()

changed = False

# 1. Import
if "plan_financement" not in app:
    app = app.replace(
        "from utils.coherence import verifier_coherence",
        "from utils.coherence import verifier_coherence\nfrom utils.plan_financement import page_plan_financement"
    )
    changed = True
    print("OK: import ajoute")
else:
    print("-- import deja present")

# 2. Menu
if "Plan de Financement" not in app:
    old = '"─── États Financiers ───",'
    new = '"─── États Financiers ───",\n        "📐 Plan de Financement",'
    app = app.replace(old, new)
    changed = True
    print("OK: menu ajoute")
else:
    print("-- menu deja present")

# 3. Routing
if "page_plan_financement()" not in app:
    old = "# =============================================================================\n# FOOTER"
    new = 'elif page == "📐 Plan de Financement":\n    page_plan_financement()\n\n# =============================================================================\n# FOOTER'
    app = app.replace(old, new)
    changed = True
    print("OK: routing ajoute")
else:
    print("-- routing deja present")

if changed:
    with open(REPO + r"\app.py", "w", encoding="utf-8") as f:
        f.write(app)
    print("OK: app.py sauvegarde")
else:
    print("Rien a modifier")
