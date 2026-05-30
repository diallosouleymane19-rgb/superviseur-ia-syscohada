# -*- coding: utf-8 -*-
REPO = r"C:\Users\blois\superviseur-ia"

with open(REPO + r"\app.py", encoding="utf-8") as f:
    app = f.read()

# Vérification précise : dans le selectbox
in_selectbox = '        "📐 Plan de Financement",' in app
print("Dans selectbox:", in_selectbox)

if not in_selectbox:
    old = '        "📋 Inventaire & Clôture",\n        "─── Supervision & Reporting ───",'
    new = '        "📋 Inventaire & Clôture",\n        "\U0001f4d0 Plan de Financement",\n        "─── Supervision & Reporting ───",'
    if old in app:
        app = app.replace(old, new)
        with open(REPO + r"\app.py", "w", encoding="utf-8") as f:
            f.write(app)
        print("OK: entrée menu ajoutée")
    else:
        print("ERREUR: ancre non trouvée dans le selectbox")
        # Afficher contexte autour de Inventaire
        idx = app.find("Inventaire")
        print("Contexte:", repr(app[idx-20:idx+80]))
else:
    print("Déjà dans le selectbox - rien à faire")
