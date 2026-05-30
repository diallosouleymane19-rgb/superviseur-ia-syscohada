# -*- coding: utf-8 -*-
"""Deploy Module 3 - Comparatif N vs N-1"""
import shutil, sys, os

BASE = r"C:\Users\blois\superviseur-ia"
CORR = r"C:\Users\blois\superviseur-ia-syscohada\superviseur-ia-corrections"

errors = []

# 1. Copier comparatif.py dans utils/
src = os.path.join(CORR, "comparatif.py")
dst = os.path.join(BASE, "utils", "comparatif.py")
try:
    shutil.copy2(src, dst)
    print(f"OK  utils/comparatif.py copie")
except Exception as e:
    errors.append(f"ERREUR copie comparatif.py : {e}")

# 2. Lire app.py
app_path = os.path.join(BASE, "app.py")
with open(app_path, encoding="utf-8") as f:
    app = f.read()

# 3. Import
import_line = "from utils.comparatif import page_comparatif"
if import_line not in app:
    old = "from utils.tft import page_tft"
    new = "from utils.tft import page_tft\nfrom utils.comparatif import page_comparatif"
    if old in app:
        app = app.replace(old, new, 1)
        print("OK  import ajoute")
    else:
        errors.append("ERREUR : marqueur import tft introuvable")
else:
    print("OK  import deja present")

# 4. Menu selectbox - ajouter apres TFT
menu_entry = '        "📊 Comparatif N/N-1",'
if menu_entry not in app:
    old_menu = '        "\U0001f4b9 TFT Trésorerie",'
    new_menu = '        "\U0001f4b9 TFT Trésorerie",\n        "\U0001f4ca Comparatif N/N-1",'
    if old_menu in app:
        app = app.replace(old_menu, new_menu, 1)
        print("OK  menu ajoute")
    else:
        errors.append(f"ERREUR : marqueur menu TFT introuvable. Cherche: {repr(old_menu)}")
else:
    print("OK  menu deja present")

# 5. Routing elif
routing = 'elif page == "\U0001f4ca Comparatif N/N-1":\n    page_comparatif()'
if routing not in app:
    old_route = 'elif page == "\U0001f4b9 TFT Trésorerie":\n    page_tft()'
    new_route = 'elif page == "\U0001f4b9 TFT Trésorerie":\n    page_tft()\n\nelif page == "\U0001f4ca Comparatif N/N-1":\n    page_comparatif()'
    if old_route in app:
        app = app.replace(old_route, new_route, 1)
        print("OK  routing ajoute")
    else:
        errors.append(f"ERREUR : marqueur routing TFT introuvable. Cherche: {repr(old_route)}")
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

print("\nDeploy Module 3 OK")
