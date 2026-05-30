# -*- coding: utf-8 -*-
import shutil, py_compile

REPO   = r"C:\Users\blois\superviseur-ia"
SRC    = r"C:\Users\blois\superviseur-ia-syscohada\superviseur-ia-corrections\tft.py"
DEST   = REPO + r"\utils\tft.py"

shutil.copy2(SRC, DEST)
print("OK: utils/tft.py copié")

with open(REPO + r"\app.py", encoding="utf-8") as f:
    app = f.read()

# Import
if "from utils.tft import page_tft" not in app:
    app = app.replace(
        "from utils.plan_financement import page_plan_financement",
        "from utils.plan_financement import page_plan_financement\nfrom utils.tft import page_tft"
    )
    print("OK: import ajouté")

# Menu — après Plan de Financement
if '"💹 TFT Trésorerie"' not in app:
    app = app.replace(
        '        "📐 Plan de Financement",',
        '        "📐 Plan de Financement",\n        "💹 TFT Trésorerie",'
    )
    print("OK: menu ajouté")

# Routing — avant FOOTER
if "page_tft()" not in app:
    app = app.replace(
        'elif page == "📐 Plan de Financement":\n    page_plan_financement()',
        'elif page == "📐 Plan de Financement":\n    page_plan_financement()\n\nelif page == "💹 TFT Trésorerie":\n    page_tft()'
    )
    print("OK: routing ajouté")

with open(REPO + r"\app.py", "w", encoding="utf-8") as f:
    f.write(app)

try:
    py_compile.compile(REPO + r"\app.py", doraise=True)
    print("Syntaxe OK")
except py_compile.PyCompileError as e:
    print(f"ERREUR: {e}")

print("import:", "from utils.tft" in app)
print("menu:  ", '"💹 TFT Trésorerie"' in app)
print("routing:", "page_tft()" in app)
