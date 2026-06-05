# -*- coding: utf-8 -*-
REPO = r"C:\Users\blois\superviseur-ia"

with open(REPO + r"\app.py", encoding="utf-8") as f:
    app = f.read()

# Ajouter "📐 Plan de Financement" après "📋 Inventaire & Clôture" dans le menu
old = '        "📋 Inventaire & Clôture",\n        "─── Supervision & Reporting ───",'
new = '        "📋 Inventaire & Clôture",\n        "📐 Plan de Financement",\n        "─── Supervision & Reporting ───",'

if "📐 Plan de Financement" not in app:
    app = app.replace(old, new)
    print("OK: menu ajouté")
else:
    print("-- menu déjà présent")

with open(REPO + r"\app.py", "w", encoding="utf-8") as f:
    f.write(app)

import py_compile
try:
    py_compile.compile(REPO + r"\app.py", doraise=True)
    print("Syntaxe OK")
except py_compile.PyCompileError as e:
    print(f"ERREUR SYNTAXE: {e}")

# Vérification finale
with open(REPO + r"\app.py", encoding="utf-8") as f:
    content = f.read()
print("Menu OK:", "📐 Plan de Financement" in content)
print("Import OK:", "page_plan_financement" in content)
print("Routing OK:", "page_plan_financement()" in content)
