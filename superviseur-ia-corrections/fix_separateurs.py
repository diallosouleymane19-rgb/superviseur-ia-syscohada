# -*- coding: utf-8 -*-
REPO = r"C:\Users\blois\superviseur-ia"

with open(REPO + r"\app.py", encoding="utf-8") as f:
    lines = f.readlines()

fixed = []
for line in lines:
    if line.strip() == '"📐 Plan de Financement",':
        print(f"Supprimé: {line.rstrip()}")
        continue
    fixed.append(line)

with open(REPO + r"\app.py", "w", encoding="utf-8") as f:
    f.writelines(fixed)

print(f"OK: {len(lines)} -> {len(fixed)} lignes")

import py_compile
try:
    py_compile.compile(REPO + r"\app.py", doraise=True)
    print("Syntaxe OK")
except py_compile.PyCompileError as e:
    print(f"ERREUR: {e}")
