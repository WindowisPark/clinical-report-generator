"""Clinical Report Query Generator - Main Application with Authentication"""

import streamlit as st
import os
from utils.auth import AuthManager, render_login_page, render_signup_page, render_token_input_page

# Set page config first (before any other st commands)
st.set_page_config(
    page_title="Clinical Report Generator",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize authentication
if 'auth_manager' not in st.session_state:
    st.session_state['auth_manager'] = AuthManager()

auth_manager = st.session_state['auth_manager']

# Check if showing signup page
if st.session_state.get('show_signup', False):
    render_login_page()  # Header
    render_signup_page()
    st.stop()

# Authentication flow - this will show login form if not authenticated
auth_manager.login()

# Get authentication status from session state
authentication_status = st.session_state.get('authentication_status')
name = st.session_state.get('name')
username = st.session_state.get('username')

# Not authenticated - show login page
if not authentication_status or not username:
    render_login_page()  # Show header and signup button
    if authentication_status == False:
        st.error('❌ 사용자명 또는 비밀번호가 올바르지 않습니다.')
    st.stop()

# User is authenticated
if authentication_status and username:
    # Log login
    auth_manager.log_usage(username, 'login')

    # Check if Databricks token is validated
    if 'token_validated' not in st.session_state or not st.session_state.get('token_validated'):
        # Show token input page
        render_token_input_page(username)
        st.stop()

    # Token is validated - show main app
    # Import main app logic here
    from typing import Dict, Any, List

    # Core imports
    from core.recipe_loader import RecipeLoader

    # Feature imports
    from features.disease_pipeline_tab import DiseasePipelineTab
    from features.nl2sql_tab import NL2SQLTab
    from features.schema_chatbot_tab import SchemaChatbotTab
    from features.monitoring_tab import MonitoringTab

    # Set page config
    st.set_page_config(
        page_title="Clinical Report Query Generator | PharmaCo",
        page_icon="🏥",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Sidebar with user info and logout
    with st.sidebar:
        st.markdown(f"### 👤 {name}")
        st.markdown(f"*{username}*")
        st.markdown("---")

        if st.button("🚪 Logout"):
            # Call logout method to clear everything
            auth_manager.logout()
            # Immediate rerun without showing message
            st.rerun()

        st.markdown("---")
        st.markdown("### 🔐 Databricks Connection")
        st.success("✅ Token Validated")

        if st.button("🔄 Update Token"):
            st.session_state['token_validated'] = False
            st.rerun()

    # Main app header
    st.markdown("""
    <div style="
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        padding: 1.5rem 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    ">
        <h1 style="color: white; margin: 0;">🏥 Clinical Report Generator</h1>
        <p style="color: #e8f4f8; margin: 0.5rem 0 0 0;">AI-Powered SQL Query Generation Platform</p>
    </div>
    """, unsafe_allow_html=True)

    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "🔍 Disease Pipeline",
        "💬 NL2SQL",
        "📚 Schema Chatbot",
        "📊 Monitoring"
    ])

    with tab1:
        disease_tab = DiseasePipelineTab()
        disease_tab.render()
        # Log usage
        auth_manager.log_usage(username, 'use_disease_pipeline')

    with tab2:
        nl2sql_tab = NL2SQLTab()
        nl2sql_tab.render()
        # Log usage
        auth_manager.log_usage(username, 'use_nl2sql')

    with tab3:
        chatbot_tab = SchemaChatbotTab()
        chatbot_tab.render()
        # Log usage
        auth_manager.log_usage(username, 'use_chatbot')

    with tab4:
        monitoring_tab = MonitoringTab()
        monitoring_tab.render()
        # Log usage
        auth_manager.log_usage(username, 'use_monitoring')
