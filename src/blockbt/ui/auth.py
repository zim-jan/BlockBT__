"""
BlockBT UI — Authentication helper functions.

Handles password hashing/verification and the
login / registration Streamlit widgets.
"""

from __future__ import annotations

import streamlit as st
import bcrypt
from streamlit_cookies_controller import CookieController

from blockbt.db.models import User
from blockbt.db.session import get_session

cookie_controller = CookieController()

# ── Crypto helpers ────────────────────────────────────────────────────────────

def _hash_password(plain: str) -> str:
    """Return a bcrypt hash of *plain*."""
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def _verify_password(plain: str, hashed: str) -> bool:
    """Return True if *plain* matches *hashed*."""
    return bcrypt.checkpw(plain.encode(), hashed.encode())


# ── DB operations ─────────────────────────────────────────────────────────────

def _get_user_by_username(username: str) -> dict | None:
    """Return a plain dict with user fields, or None if not found.

    Using a dict (not ORM instance) avoids DetachedInstanceError
    when attributes are accessed after the session closes.
    """
    with get_session() as s:
        user = s.query(User).filter_by(username=username).first()
        if user is None:
            return None
        # Read all needed fields while the session is still open
        return {
            "id": user.id,
            "username": user.username,
            "password_hash": user.password_hash,
        }


def _try_login(username: str, password: str) -> dict | None:
    """Return user dict if credentials are valid, else None.

    Verification happens *inside* the session to avoid lazy-load errors.
    """
    with get_session() as s:
        user = s.query(User).filter_by(username=username).first()
        if user is None:
            return None
        # Access password_hash while session is alive
        if not _verify_password(password, user.password_hash):
            return None
        return {"id": user.id, "username": user.username}


def _create_user(username: str, email: str, password: str) -> int:
    """Create and persist a new User row, return the new user id."""
    with get_session() as s:
        user = User(
            username=username,
            email=email,
            password_hash=_hash_password(password),
        )
        s.add(user)
        s.flush()  # materialise auto-generated id while session is open
        user_id = user.id
    return user_id


# ── Session helpers ───────────────────────────────────────────────────────────

def is_logged_in() -> bool:
    """Return True when a user is authenticated in this session."""
    if st.session_state.get("user_id"):
        return True
        
    # Attempt to recover session from cookies (survives F5 refesh)
    try:
        c_uid = cookie_controller.get("user_id")
        c_uname = cookie_controller.get("username")
        if c_uid and c_uname:
            st.session_state["user_id"] = int(c_uid)
            st.session_state["username"] = str(c_uname)
            return True
    except Exception:
        pass
        
    return False


def logout() -> None:
    """Clear auth state from the session and browser cookies."""
    try:
        cookie_controller.remove("user_id")
        cookie_controller.remove("username")
    except Exception:
        pass
        
    for key in ("user_id", "username"):
        st.session_state.pop(key, None)


# ── UI widgets ────────────────────────────────────────────────────────────────

def render_auth_gate() -> None:
    """Display Login / Register tabs and gate access.

    Writes to ``st.session_state.user_id`` and
    ``st.session_state.username`` on success.
    Calls ``st.stop()`` so the rest of the page never renders
    when the user is not authenticated.
    """
    st.title("🔐 BlockBT — Logowanie")
    tab_login, tab_register = st.tabs(["Zaloguj się", "Zarejestruj się"])

    with tab_login:
        username = st.text_input("Nazwa użytkownika", key="login_username")
        password = st.text_input("Hasło", type="password", key="login_password")
        if st.button("Zaloguj", key="btn_login", use_container_width=True):
            # _try_login verifies the password *inside* the session —
            # no DetachedInstanceError possible.
            logged_in = _try_login(username, password)
            if logged_in:
                st.session_state["user_id"] = logged_in["id"]
                st.session_state["username"] = logged_in["username"]
                
                try:
                    cookie_controller.set("user_id", str(logged_in["id"]))
                    cookie_controller.set("username", logged_in["username"])
                except Exception:
                    pass
                    
                st.success(f"Witaj, {logged_in['username']}!")
                st.rerun()
            else:
                st.error("Nieprawidłowe dane logowania.")

    with tab_register:
        new_user = st.text_input("Nazwa użytkownika", key="reg_username")
        new_email = st.text_input("E-mail", key="reg_email")
        new_pass = st.text_input("Hasło", type="password", key="reg_password")
        new_pass2 = st.text_input("Powtórz hasło", type="password", key="reg_password2")
        if st.button("Zarejestruj", key="btn_register", use_container_width=True):
            if not new_user or not new_email or not new_pass:
                st.warning("Uzupełnij wszystkie pola.")
            elif new_pass != new_pass2:
                st.error("Hasła nie są identyczne.")
            elif _get_user_by_username(new_user) is not None:
                st.error("Użytkownik o tej nazwie już istnieje.")
            else:
                uid = _create_user(new_user, new_email, new_pass)
                st.session_state["user_id"] = uid
                st.session_state["username"] = new_user
                
                try:
                    cookie_controller.set("user_id", str(uid))
                    cookie_controller.set("username", new_user)
                except Exception:
                    pass
                    
                st.success("Konto utworzone! Przekierowuję…")
                st.rerun()

    st.stop()  # gate — nothing below is rendered when not logged in
