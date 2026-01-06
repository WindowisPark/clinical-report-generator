"""Common authentication check for pages."""

import streamlit as st


def require_auth():
    """
    Check if user is authenticated.
    Redirects to home page if not authenticated.
    Returns username if authenticated.
    """
    authentication_status = st.session_state.get('authentication_status')
    username = st.session_state.get('username')

    if not authentication_status or not username:
        st.warning("Please login first.")
        st.page_link("app.py", label="Go to Login", icon=None)
        st.stop()

    return username


def get_current_user():
    """Get current user info."""
    return {
        'username': st.session_state.get('username'),
        'name': st.session_state.get('name'),
        'authenticated': st.session_state.get('authentication_status', False)
    }
