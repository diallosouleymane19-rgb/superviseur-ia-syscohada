import re, shutil

REPO = "C:/Users/blois/superviseur-ia"

# ── 1. Écrire utils/plan_financement.py ──────────────────────────────────────
plan_content = open("/tmp/plan_financement.py", encoding="utf-8").read()
with open(f"{REPO}/utils/plan_financement.py", "w", encoding="utf-8") as f:
    f.write(plan_content)
print("OK: utils/plan_financement.py écrit")

# ── 2. Modifier app.py ───────────────────────────────────────────────────────
with open(f"{REPO}/app.py", encoding="utf-8") as f:
    app = f.read()

# 2a. Ajouter import après la dernière import utils
old_import = "from utils.coherence import verifier_coherence"
new_import = (old_import + "\n"
              "from utils.plan_financement import page_plan_financement")
if "plan_financement" not in app:
    app = app.replace(old_import, new_import)
    print("OK: import ajouté")

# 2b. Ajouter entrée menu dans le selectbox (après "─── États Financiers ───")
old_menu = '"─── États Financiers ───",'
new_menu = '"─── États Financiers ───",\n        "📐 Plan de Financement",'
if '"📐 Plan de Financement"' not in app:
    app = app.replace(old_menu, new_menu)
    print("OK: menu ajouté")

# 2c. Ajouter dans la liste separateurs
old_sep = '["─── Analyse & Audit ───", "─── États Financiers ───",'
new_sep = '["─── Analyse & Audit ───", "─── États Financiers ───", "📐 Plan de Financement" if False else "─── États Financiers ───",'
# Approche plus simple : ajouter routing avant le footer
old_footer = "# =============================================================================\n# FOOTER"
new_routing = '''elif page == "📐 Plan de Financement":
    page_plan_financement()

# =============================================================================
# FOOTER'''
if 'page_plan_financement()' not in app:
    app = app.replace("# =============================================================================\n# FOOTER", new_routing)
    print("OK: routing ajouté")

with open(f"{REPO}/app.py", "w", encoding="utf-8") as f:
    f.write(app)
print("OK: app.py mis à jour")
print("DONE")
