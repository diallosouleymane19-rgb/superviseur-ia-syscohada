# -*- coding: utf-8 -*-
"""Deploy Module 4 - Aide TVA CA3/CA12"""
import shutil, sys, os

BASE = r"C:\Users\blois\superviseur-ia"
CORR = r"C:\Users\blois\superviseur-ia-syscohada\superviseur-ia-corrections"

errors = []

# 1. Copier tva.py dans utils/
src = os.path.join(CORR, "tva.py")
dst = os.path.join(BASE, "utils", "tva.py")
try:
    shutil.copy2(src, dst)
    print("OK  utils/tva.py copie")
except Exception as e:
    errors.append(f"ERREUR copie tva.py : {e}")

# 2. Lire app.py
app_path = os.path.join(BASE, "app.py")
with open(app_path, encoding="utf-8") as f:
    app = f.read()

# 3. Import
import_line = "from utils.tva import page_tva"
if import_line not in app:
    old = "from utils.comparatif import page_comparatif"
    new = "from utils.comparatif import page_comparatif\nfrom utils.tva import page_tva"
    if old in app:
        app = app.replace(old, new, 1)
        print("OK  import ajoute")
    else:
        errors.append("ERREUR : marqueur import comparatif introuvable")
else:
    print("OK  import deja present")

# 4. Menu selectbox
menu_entry = '        "\U0001f9fe Aide TVA CA3/CA12",'
if menu_entry not in app:
    old_menu = '        "\U0001f4ca Comparatif N/N-1",'
    new_menu = '        "\U0001f4ca Comparatif N/N-1",\n        "\U0001f9fe Aide TVA CA3/CA12",'
    if old_menu in app:
        app = app.replace(old_menu, new_menu, 1)
        print("OK  menu ajoute")
    else:
        errors.append(f"ERREUR : marqueur menu Comparatif introuvable.")
else:
    print("OK  menu deja present")

# 5. Routing
routing = 'elif page == "\U0001f9fe Aide TVA CA3/CA12":\n    page_tva()'
if routing not in app:
    old_route = 'elif page == "\U0001f4ca Comparatif N/N-1":\n    page_comparatif()'
    new_route = 'elif page == "\U0001f4ca Comparatif N/N-1":\n    page_comparatif()\n\nelif page == "\U0001f9fe Aide TVA CA3/CA12":\n    page_tva()'
    if old_route in app:
        app = app.replace(old_route, new_route, 1)
        print("OK  routing ajoute")
    else:
        errors.append(f"ERREUR : marqueur routing Comparatif introuvable.")
else:
    print("OK  routing deja present")

# 6. Ecrire app.py
if not errors:
    with open(app_path, "w", encoding="utf-8") as f:
        f.write(app)
    print("OK  app.py ecrit")
else:
    for e in errors:
        print(e, file=sys.stderr)
    sys.exit(1)

print("\nDeploy Module 4 OK")
