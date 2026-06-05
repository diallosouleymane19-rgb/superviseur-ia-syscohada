# -*- coding: utf-8 -*-
"""
utils/stripe_billing.py - SMD Global Consulting LLC / SYSCOHADA
Integration Stripe Billing : checkout, customer portal, webhooks.
Prix en FCFA (XOF) - devise zero-decimal Stripe.
Import stripe lazy pour eviter les echecs au demarrage.
"""

import os
from datetime import datetime


# --- Configuration ---

def _get_stripe_key():
    try:
        import streamlit as st
        key = st.secrets.get("STRIPE_SECRET_KEY", "")
        if key:
            return key
    except Exception:
        pass
    return os.getenv("STRIPE_SECRET_KEY", "")


def _get_webhook_secret():
    try:
        import streamlit as st
        return st.secrets.get("STRIPE_WEBHOOK_SECRET", "")
    except Exception:
        pass
    return os.getenv("STRIPE_WEBHOOK_SECRET", "")


def _get_app_url():
    try:
        import streamlit as st
        return st.secrets.get("APP_URL", "http://localhost:8501")
    except Exception:
        pass
    return os.getenv("APP_URL", "http://localhost:8501")


def _init_stripe():
    import stripe
    key = _get_stripe_key()
    if not key:
        raise RuntimeError(
            "Cle Stripe manquante. Ajoutez STRIPE_SECRET_KEY dans .streamlit/secrets.toml"
        )
    stripe.api_key = key
    return stripe


# --- Catalogue Price IDs Stripe (a remplacer par vos vrais IDs) ---

STRIPE_PRICES = {
    "syscohada": {
        "starter":    {"monthly": "price_sysc_starter_monthly",    "annual": "price_sysc_starter_annual"},
        "pro":        {"monthly": "price_sysc_pro_monthly",        "annual": "price_sysc_pro_annual"},
        "enterprise": {"monthly": "price_sysc_enterprise_monthly", "annual": "price_sysc_enterprise_annual"},
    },
    "pcg": {
        "starter":    {"monthly": "price_pcg_starter_monthly",    "annual": "price_pcg_starter_annual"},
        "pro":        {"monthly": "price_pcg_pro_monthly",        "annual": "price_pcg_pro_annual"},
        "enterprise": {"monthly": "price_pcg_enterprise_monthly", "annual": "price_pcg_enterprise_annual"},
    },
    "multi": {
        "starter":    {"monthly": "price_multi_starter_monthly",    "annual": "price_multi_starter_annual"},
        "pro":        {"monthly": "price_multi_pro_monthly",        "annual": "price_multi_pro_annual"},
        "enterprise": {"monthly": "price_multi_enterprise_monthly", "annual": "price_multi_enterprise_annual"},
    },
}

# Tarifs FCFA (XOF zero-decimal : 1 unite = 1 FCFA)
PRICING = {
    "starter":    {"monthly": 19000,  "annual": 182000,  "label": "Starter",    "quota": 50},
    "pro":        {"monthly": 52000,  "annual": 499000,  "label": "Pro",        "quota": 200},
    "enterprise": {"monthly": 130000, "annual": 1249000, "label": "Entreprise", "quota": -1},
}

CURRENCY = "xof"


# --- Customer ---

def get_or_create_customer(email, nom="", app="syscohada"):
    stripe = _init_stripe()
    try:
        from utils.auth_rbac import get_user, mettre_a_jour_stripe
        user = get_user(email)
        if user and user.get("stripe_customer_id"):
            return user["stripe_customer_id"]
    except Exception:
        pass
    existing = stripe.Customer.list(email=email, limit=1)
    if existing.data:
        customer_id = existing.data[0].id
    else:
        customer = stripe.Customer.create(
            email=email,
            name=nom or email,
            metadata={"app": app, "source": "smd_consulting"}
        )
        customer_id = customer.id
    try:
        from utils.auth_rbac import mettre_a_jour_stripe
        mettre_a_jour_stripe(email, customer_id, "")
    except Exception:
        pass
    return customer_id


# --- Checkout Session ---

def creer_checkout_session(email, plan, app="syscohada", billing="monthly", nom=""):
    stripe = _init_stripe()
    if plan not in STRIPE_PRICES.get(app, {}):
        raise ValueError("Plan '" + plan + "' non disponible pour l app '" + app + "'")
    price_id    = STRIPE_PRICES[app][plan][billing]
    app_url     = _get_app_url()
    customer_id = get_or_create_customer(email, nom, app)
    session = stripe.checkout.Session.create(
        customer             = customer_id,
        payment_method_types = ["card"],
        mode                 = "subscription",
        line_items           = [{"price": price_id, "quantity": 1}],
        success_url          = app_url + "?stripe=success&plan=" + plan + "&app=" + app,
        cancel_url           = app_url + "?stripe=cancel",
        metadata             = {"email": email, "plan": plan, "app": app},
        subscription_data    = {"metadata": {"email": email, "plan": plan, "app": app}},
        allow_promotion_codes = True,
    )
    return session.url


# --- Customer Portal ---

def creer_portal_session(email, app="syscohada"):
    stripe  = _init_stripe()
    app_url = _get_app_url()
    customer_id = get_or_create_customer(email, app=app)
    session = stripe.billing_portal.Session.create(
        customer   = customer_id,
        return_url = app_url + "?stripe=portal_return",
    )
    return session.url


# --- Webhook Handler ---

def traiter_webhook(payload, sig_header):
    stripe         = _init_stripe()
    webhook_secret = _get_webhook_secret()
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except Exception as e:
        return {"error": str(e)}

    event_type = event["type"]

    if event_type in ("customer.subscription.created", "customer.subscription.updated"):
        sub    = event["data"]["object"]
        meta   = sub.get("metadata", {})
        email  = meta.get("email", "")
        plan   = meta.get("plan", "starter")
        app    = meta.get("app", "syscohada")
        sub_id = sub["id"]
        status = sub.get("status", "")
        if email and status in ("active", "trialing"):
            try:
                from utils.auth_rbac import mettre_a_jour_plan, mettre_a_jour_stripe, log_action
                mettre_a_jour_plan(email, plan)
                mettre_a_jour_stripe(email, sub.get("customer", ""), sub_id)
                log_action(email, "plan_upgraded:" + plan, app=app)
            except Exception as e:
                return {"error": "Erreur mise a jour plan: " + str(e)}

    elif event_type == "customer.subscription.deleted":
        sub   = event["data"]["object"]
        meta  = sub.get("metadata", {})
        email = meta.get("email", "")
        app   = meta.get("app", "syscohada")
        if email:
            try:
                from utils.auth_rbac import mettre_a_jour_plan, log_action
                mettre_a_jour_plan(email, "free")
                log_action(email, "plan_cancelled:free", app=app)
            except Exception as e:
                return {"error": "Erreur retrogradation: " + str(e)}

    elif event_type == "invoice.payment_failed":
        pass

    return {"ok": True, "event": event_type}


# --- Abonnement actuel ---

def get_abonnement_actuel(email):
    try:
        stripe = _init_stripe()
        from utils.auth_rbac import get_user
        user = get_user(email)
        if not user or not user.get("stripe_customer_id"):
            return None
        subs = stripe.Subscription.list(
            customer=user["stripe_customer_id"], status="active", limit=1
        )
        if not subs.data:
            return None
        sub   = subs.data[0]
        item  = sub["items"]["data"][0]
        price = item["price"]
        return {
            "subscription_id": sub["id"],
            "status":          sub["status"],
            "plan":            sub["metadata"].get("plan", "unknown"),
            "amount":          price["unit_amount"],
            "currency":        price["currency"].upper(),
            "interval":        price["recurring"]["interval"],
            "current_period_end": datetime.fromtimestamp(
                sub["current_period_end"]
            ).strftime("%d/%m/%Y"),
            "cancel_at_period_end": sub.get("cancel_at_period_end", False),
        }
    except Exception:
        return None


# --- Retour Stripe (query params) ---

def gerer_retour_stripe():
    try:
        import streamlit as st
        params = st.query_params
        if params.get("stripe") == "success":
            plan = params.get("plan", "")
            st.success("Abonnement " + plan.capitalize() + " active ! Bienvenue sur SMD SYSCOHADA.")
            st.balloons()
            st.query_params.clear()
        elif params.get("stripe") == "cancel":
            st.info("Paiement annule. Vous restez sur votre plan actuel.")
            st.query_params.clear()
        elif params.get("stripe") == "portal_return":
            st.success("Votre abonnement a ete mis a jour.")
            st.query_params.clear()
    except Exception:
        pass
