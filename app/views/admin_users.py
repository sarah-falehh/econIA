from __future__ import annotations

import pandas as pd
import streamlit as st

from app.services.auth_service import (
    ROLE_LABELS, create_user, has_permission, list_audit_logs, list_users,
    reset_password, update_user,
)


def render_admin_users() -> None:
    current = st.session_state.get("user")
    if not has_permission(current, "manage_users"):
        st.error("Accès refusé. Cette rubrique est réservée aux administrateurs.")
        st.stop()

    st.title("Administration")
    st.caption("Gestion des utilisateurs, des rôles et du journal d’activité.")

    tab_create, tab_users, tab_logs = st.tabs(["Gestion des utilisateurs", "Comptes existants", "Journal d’activité"])
    with tab_create:
        st.subheader("Créer un utilisateur")
        with st.form("admin_create_user"):
            c1, c2 = st.columns(2)
            first_name = c1.text_input("Prénom")
            last_name = c2.text_input("Nom")
            email = st.text_input("Email")
            c3, c4 = st.columns(2)
            password = c3.text_input("Mot de passe initial", type="password")
            confirm = c4.text_input("Confirmation du mot de passe", type="password")
            c5, c6 = st.columns(2)
            role = c5.selectbox("Rôle", list(ROLE_LABELS), format_func=lambda x: ROLE_LABELS[x])
            active = c6.selectbox("Statut du compte", [True, False], format_func=lambda x: "Actif" if x else "Désactivé")
            submitted = st.form_submit_button("Créer l’utilisateur", type="primary")
        if submitted:
            if password != confirm:
                st.error("Les mots de passe ne correspondent pas.")
            else:
                ok, message = create_user(first_name, last_name, "ITCEQ", email, password, role, active, acting_user=current)
                (st.success if ok else st.error)(message)
                if ok: st.rerun()

    with tab_users:
        users = list_users(acting_user=current)
        if not users:
            st.info("Aucun utilisateur enregistré.")
        else:
            st.dataframe(pd.DataFrame(users), use_container_width=True, hide_index=True)
            for user in users:
                with st.expander(f"{user['first_name']} {user['last_name']} — {user['email']}"):
                    c1, c2, c3 = st.columns([2,1,1])
                    opts = list(ROLE_LABELS)
                    role_value = c1.selectbox("Rôle", opts, index=opts.index(user["role"]), format_func=lambda x: ROLE_LABELS[x], key=f"role_{user['id']}")
                    active_value = c2.toggle("Compte actif", value=bool(user["is_active"]), key=f"active_{user['id']}")
                    c3.metric("Dernière connexion", user["last_login"][:10] if user["last_login"] else "Jamais")
                    if st.button("Enregistrer le compte", key=f"save_{user['id']}", type="primary"):
                        if current.get("id") == user["id"] and not active_value:
                            st.error("Vous ne pouvez pas désactiver votre propre compte pendant la session.")
                        else:
                            update_user(user["id"], role_value, active_value, acting_user=current)
                            st.success("Utilisateur mis à jour.")
                            st.rerun()
                    with st.form(f"reset_{user['id']}"):
                        p1 = st.text_input("Nouveau mot de passe", type="password", key=f"p1_{user['id']}")
                        p2 = st.text_input("Confirmation", type="password", key=f"p2_{user['id']}")
                        do_reset = st.form_submit_button("Réinitialiser le mot de passe")
                    if do_reset:
                        if p1 != p2:
                            st.error("Les mots de passe ne correspondent pas.")
                        else:
                            ok, message = reset_password(user["id"], p1, acting_user=current)
                            (st.success if ok else st.error)(message)

    with tab_logs:
        logs = list_audit_logs(acting_user=current)
        if logs:
            st.dataframe(pd.DataFrame(logs), use_container_width=True, hide_index=True)
        else:
            st.info("Aucune activité enregistrée.")
