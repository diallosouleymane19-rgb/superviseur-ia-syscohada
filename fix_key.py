# -*- coding: utf-8 -*-
with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Correction du mime type cassé
content = content.replace(
    'mime="application/vnd.openxmlformats-\n                            officedocument.spreadsheetml.sheet",',
    'mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",'
)

# Ajout clé unique sur chaque download_button Excel
import re
counter = [0]
def add_key(match):
    counter[0] += 1
    return match.group(0).replace(
        'use_container_width=True)',
        f'key="dl_excel_{counter[0]}", use_container_width=True)'
    )

content = re.sub(
    r'st\.download_button\("📊 Télécharger États Financiers Excel.*?use_container_width=True\)',
    add_key,
    content,
    flags=re.DOTALL
)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Correction appliquée !")