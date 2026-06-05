# RevisionPro SYSCOHADA
### Assistant de Révision Comptable OHADA/UEMOA — SMD Global Consulting LLC

> *"Vous gardez le contrôle total. Nous sécurisons la conformité."*

---

## À propos

**RevisionPro SYSCOHADA** est une plateforme de contrôle et de conformité comptable dédiée aux **8 pays de la zone UEMOA** (Sénégal, Côte d'Ivoire, Mali, Burkina Faso, Niger, Togo, Bénin, Guinée-Bissau).

Conçu pour les **Experts-Comptables, DAF et cabinets d'audit**, il génère automatiquement les états financiers officiels SYSCOHADA révisé 2017 à partir d'une balance générale — sans ressaisie, sans mise en forme manuelle.

L'Expert-Comptable reste le seul décisionnaire. RevisionPro signale, le professionnel valide.

---

## Fonctionnalités

### États Financiers Officiels DGID (Sénégal)
- **Bilan Actif & Passif** — format SAES SYSCOHADA, lignes AA→DZ / CA→HZ
- **Compte de Résultat** — Soldes Intermédiaires de Gestion (SIG) XA→XI
- **TAFIRE** — Tableau de Financement des Ressources et Emplois
- **Notes Annexes A à E** — Immobilisations, Amortissements, Provisions, Créances, Dettes
- **Export Excel 7 onglets** — stylisé aux couleurs DGID, prêt pour dépôt fiscal

### Analyse de Balance SYSCOHADA
- Détection des anomalies et risques de non-conformité
- Vérification des imputations par classe de comptes
- Analyse des ratios financiers clés (liquidité, solvabilité, rentabilité)
- Rapport de contrôle structuré, prêt pour le dossier de révision

### Liasse Fiscale & Veille Réglementaire
- Liasse fiscale IS/IR adaptée par pays UEMOA
- Veille fiscale et sociale (taux IS, TVA, obligations déclaratives)
- Calendrier fiscal par pays

### Modules de Gestion
- Balance âgée clients/fournisseurs
- Rapprochement bancaire
- Trésorerie prévisionnelle
- Plan de financement
- Tableau de Flux de Trésorerie (TFT)

---

## Sécurité & Confidentialité

- **Données hébergées sur Supabase (Union Européenne)**
- Aucune donnée client utilisée à des fins d'entraînement externe
- Authentification sécurisée par cabinet
- Isolation des données par entreprise et par exercice

---

## Stack technique

| Composant | Technologie |
|-----------|-------------|
| Interface | Streamlit |
| Calculs financiers | Python / pandas |
| Export Excel | openpyxl |
| Base de données | Supabase (PostgreSQL) |
| Modèle d'analyse | Mistral AI (infrastructure EU) |
| Déploiement | Streamlit Cloud |

---

## Installation locale

```bash
git clone https://github.com/diallosouleymane19-rgb/superviseur-ia-syscohada.git
cd superviseur-ia-syscohada
pip install -r requirements.txt
```

Créer un fichier `.env` à la racine :

```env
MISTRAL_API_KEY=votre_clé_mistral
SUPABASE_URL=votre_url_supabase
SUPABASE_KEY=votre_clé_supabase
```

> ⚠️ Le fichier `.env` est dans `.gitignore` — ne jamais le pousser sur GitHub.

```bash
streamlit run app.py
```

---

## Pays UEMOA couverts

| Pays | Taux IS | Taux TVA |
|------|---------|----------|
| 🇸🇳 Sénégal | 30% | 18% |
| 🇨🇮 Côte d'Ivoire | 25% | 18% |
| 🇲🇱 Mali | 30% | 18% |
| 🇧🇫 Burkina Faso | 27,5% | 18% |
| 🇳🇪 Niger | 30% | 19% |
| 🇹🇬 Togo | 27% | 18% |
| 🇧🇯 Bénin | 30% | 18% |
| 🇬🇼 Guinée-Bissau | 25% | 15% |

---

## Structure du projet

```
├── app.py                    # Application principale
├── liasse_sn.py              # Liasse officielle DGID Sénégal
├── auth.py                   # Authentification
├── utils/
│   ├── ai.py                 # Moteur d'analyse
│   ├── etats_financiers.py   # Génération états financiers
│   ├── export_excel.py       # Export Excel
│   └── database.py           # Accès Supabase
├── data/
│   └── plan_comptable_syscohada.py  # Plan de comptes + fiscalité UEMOA
├── requirements.txt
└── .env                      # ⚠️ Non versionné
```

---

## Auteur

**Souleymane Diallo** — Comptable confirmé freelance  
SMD Global Consulting LLC — Blois (41), interventions Centre-Val de Loire et UEMOA  
📧 contact@smdconsulting.pro  
🌐 [www.smdconsulting.pro](https://smdconsulting.pro)

---

*RevisionPro SYSCOHADA — SMD Global Consulting LLC © 2026*
