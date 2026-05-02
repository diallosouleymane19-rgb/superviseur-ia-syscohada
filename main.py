# main.py
import streamlit as st
import pandas as pd
import os
from utils.ai import ComptableSupervisorAgent
from data.plan_comptable_syscohada import PLAN_COMPTABLE_SYSCOHADA

st.set_page_config(page_title="Superviseur IA SYSCOHADA", page_icon="📊", layout="wide")
st.title("🤖 Superviseur IA Comptable - Normes SYSCOHADA")
st.markdown("Validation de comptes, suggestions d'imputation et analyse d'anomalies via Mistral AI.")

@st.cache_resource
def load_agent():
    try:
        return ComptableSupervisorAgent()
    except ValueError as e:
        st.error(f"⚠️ Clé API manquante : {e}")
        return None

agent = load_agent()

if agent:
    col1, col2 = st.columns(2)

    with col1:
        st.header("1️⃣ Validation de Compte")
        acc = st.text_input("Numéro de compte (ex: 6011, 4011)", placeholder="Entrez le numéro...")
        if st.button("✅ Valider", type="primary"):
            if acc:
                res = agent.validate_account_number(acc)
                if res["valid"]:
                    st.success(f"✅ {res['message']}")
                else:
                    st.error(f"❌ {res['message']}")
                    if "suggestion" in res:
                        st.info(f"💡 {res['suggestion']}")
            else:
                st.warning("Veuillez entrer un numéro.")

    with col2:
        st.header("2️⃣ Suggestion d'Imputation (IA)")
        desc = st.text_area("Description de l'opération", placeholder="Ex: Achat de fournitures de bureau")
        if st.button("🔍 Suggérer un compte", type="primary"):
            if desc:
                with st.spinner("Analyse IA en cours..."):
                    sugg = agent.suggest_account(desc)
                st.info(sugg)
            else:
                st.warning("Décrivez l'opération.")

    st.divider()
    st.header("📁 3. Analyse de Fichier (Balance/Grand Livre)")
    uploaded = st.file_uploader("Glissez un fichier .csv ou .xlsx", type=["csv", "xlsx"])
    if uploaded:
        try:
            df = pd.read_csv(uploaded) if uploaded.name.endswith(".csv") else pd.read_excel(uploaded)
            st.dataframe(df.head(10))
            st.caption(f"{len(df)} lignes chargées. Module d'analyse IA en cours de développement.")
        except Exception as e:
            st.error(f"Erreur de lecture : {e}")
else:
    st.stop()

st.caption("💡 N'oubliez pas de créer un fichier `.env` avec `MISTRAL_API_KEY=votre_clé` à la racine du projet.")