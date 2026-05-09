# -*- coding: utf-8 -*-
"""Script patch - Connexion module export Excel dans app.py"""

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# ── 1. AJOUT IMPORT ────────────────────────────────────────────────────────
content = content.replace(
    'from auth import login, logout, is_connecte',
    'from auth import login, logout, is_connecte\nfrom utils.export_excel import export_etats_financiers_excel'
)

# ── 2. BOUTON EXCEL — BILAN ─────────────────────────────────────────────────
content = content.replace(
    '''            if st.button("💾 Sauvegarder dans dossier", use_container_width=True):
                        sauvegarder_si_entreprise(ent_id, "📋 Bilan", f"Bilan {exercice}", st.session_state.bil_resultat, info_pays['nom'], exercice)''',
    '''            if st.button("💾 Sauvegarder dans dossier", use_container_width=True):
                        sauvegarder_si_entreprise(ent_id, "📋 Bilan", f"Bilan {exercice}", st.session_state.bil_resultat, info_pays['nom'], exercice)
                with st.container():
                    st.markdown("#### 📥 Export Excel Professionnel")
                    try:
                        excel_buf = export_etats_financiers_excel(
                            df, code_pays, ent_nom, exercice
                        )
                        st.download_button(
                            "📊 Télécharger États Financiers Excel (Bilan + CR + TAFIRE + Ratios)",
                            excel_buf,
                            f"Etats_Financiers_{ent_nom}_{exercice}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                    except Exception as e:
                        st.error(f"Erreur export Excel : {e}")'''
)

# ── 3. BOUTON EXCEL — COMPTE DE RÉSULTAT ────────────────────────────────────
content = content.replace(
    '''            if st.button("💾 Sauvegarder dans dossier", use_container_width=True):
                        sauvegarder_si_entreprise(ent_id, "📈 CR", f"CR {exercice}", st.session_state.cr_resultat, info_pays['nom'], exercice)''',
    '''            if st.button("💾 Sauvegarder dans dossier", use_container_width=True):
                        sauvegarder_si_entreprise(ent_id, "📈 CR", f"CR {exercice}", st.session_state.cr_resultat, info_pays['nom'], exercice)
                with st.container():
                    st.markdown("#### 📥 Export Excel Professionnel")
                    try:
                        excel_buf = export_etats_financiers_excel(
                            df, code_pays, ent_nom, exercice
                        )
                        st.download_button(
                            "📊 Télécharger États Financiers Excel (Bilan + CR + TAFIRE + Ratios)",
                            excel_buf,
                            f"Etats_Financiers_{ent_nom}_{exercice}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                    except Exception as e:
                        st.error(f"Erreur export Excel : {e}")'''
)

# ── 4. BOUTON EXCEL — TAFIRE ─────────────────────────────────────────────────
content = content.replace(
    '''            if st.button("💾 Sauvegarder dans dossier", use_container_width=True):
                        sauvegarder_si_entreprise(ent_id, "💰 TAFIRE", f"TAFIRE {exercice}", st.session_state.taf_resultat, info_pays['nom'], exercice)''',
    '''            if st.button("💾 Sauvegarder dans dossier", use_container_width=True):
                        sauvegarder_si_entreprise(ent_id, "💰 TAFIRE", f"TAFIRE {exercice}", st.session_state.taf_resultat, info_pays['nom'], exercice)
                with st.container():
                    st.markdown("#### 📥 Export Excel Professionnel")
                    try:
                        excel_buf = export_etats_financiers_excel(
                            df, code_pays, ent_nom, exercice
                        )
                        st.download_button(
                            "📊 Télécharger États Financiers Excel (Bilan + CR + TAFIRE + Ratios)",
                            excel_buf,
                            f"Etats_Financiers_{ent_nom}_{exercice}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                    except Exception as e:
                        st.error(f"Erreur export Excel : {e}")'''
)

# ── 5. BOUTON EXCEL — ANALYSE BALANCE ────────────────────────────────────────
content = content.replace(
    '''            if st.button("💾 Sauvegarder dans dossier", use_container_width=True):
                    sauvegarder_si_entreprise(ent_id, "📊 Balance", fichier.name, st.session_state.bal_resultat, info_pays['nom'], exercice)''',
    '''            if st.button("💾 Sauvegarder dans dossier", use_container_width=True):
                    sauvegarder_si_entreprise(ent_id, "📊 Balance", fichier.name, st.session_state.bal_resultat, info_pays['nom'], exercice)
                with st.container():
                    st.markdown("#### 📥 Export Excel Professionnel")
                    try:
                        excel_buf = export_etats_financiers_excel(
                            df, code_pays, ent_nom, exercice
                        )
                        st.download_button(
                            "📊 Télécharger États Financiers Excel (Bilan + CR + TAFIRE + Ratios)",
                            excel_buf,
                            f"Etats_Financiers_{ent_nom}_{exercice}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                    except Exception as e:
                        st.error(f"Erreur export Excel : {e}")'''
)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Patch Excel appliqué avec succès !")
print("   - Import ajouté")
print("   - Bouton Excel sur Bilan")
print("   - Bouton Excel sur Compte de Résultat")
print("   - Bouton Excel sur TAFIRE")
print("   - Bouton Excel sur Analyse Balance")