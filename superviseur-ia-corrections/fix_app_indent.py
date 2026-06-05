# -*- coding: utf-8 -*-
REPO = r"C:\Users\blois\superviseur-ia"

with open(REPO + r"\app.py", encoding="utf-8") as f:
    lines = f.readlines()

fixed = []
i = 0
while i < len(lines):
    line = lines[i]
    # Supprimer la ligne parasite insérée par erreur dans le bloc indenté
    if (line.strip() == "from utils.plan_financement import page_plan_financement, generer_rapport_coherence"
            and i > 0 and lines[i-1].startswith("        from utils.coherence")):
        print(f"Supprimé ligne {i+1}: {line.rstrip()}")
        i += 1
        continue
    fixed.append(line)
    i += 1

with open(REPO + r"\app.py", "w", encoding="utf-8") as f:
    f.writelines(fixed)

print(f"OK: {len(lines)} -> {len(fixed)} lignes")

# Vérification syntaxe
import py_compile, sys
try:
    py_compile.compile(REPO + r"\app.py", doraise=True)
    print("Syntaxe OK")
except py_compile.PyCompileError as e:
    print(f"ERREUR: {e}")
