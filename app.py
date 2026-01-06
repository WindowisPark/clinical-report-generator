"""Clinical Report Query Generator - Main Application with Authentication."""

import streamlit as st
import os
import pandas as pd

from config.styles import apply_styles
from utils.auth import AuthManager, render_signup_page

# --- Page Configuration (must be first) ---
st.set_page_config(
    page_title="Clinical Report Generator",
    page_icon="CRG",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://docs.yourcompany.com/clinical-sql-generator',
        'Report a bug': "mailto:support@yourcompany.com",
        'About': """
        ### Clinical Report Query Generator v1.0

        AI-powered SQL generation for clinical data analysis.

        **Powered by**: Google Gemini 2.5 Flash
        **Target Database**: Databricks (Spark SQL)
        """
    }
)

# Apply styles
apply_styles()


# --- Authentication ---
if 'auth_manager' not in st.session_state:
    st.session_state['auth_manager'] = AuthManager()

auth_manager = st.session_state['auth_manager']

# Show signup page if requested
if st.session_state.get('show_signup', False):
    render_signup_page()
    st.stop()

# Check authentication status before rendering
authentication_status = st.session_state.get('authentication_status')
name = st.session_state.get('name')
username = st.session_state.get('username')

# Not authenticated - show login page
if not authentication_status:
    # Login page CSS
    st.markdown("""
    <style>
        .login-header {
            text-align: center;
            margin-bottom: 1.5rem;
        }
        .login-header h1 {
            color: #0066cc;
            font-size: 1.8rem;
            margin-bottom: 0.5rem;
        }
        .login-header p {
            color: #666;
            font-size: 0.95rem;
        }
        .signup-section {
            text-align: center;
            margin-top: 1rem;
            padding-top: 1rem;
            border-top: 1px solid #eee;
        }
        /* Hide sidebar on login page */
        [data-testid="stSidebar"] {
            display: none;
        }
    </style>
    """, unsafe_allow_html=True)

    # Centered layout
    col1, col2, col3 = st.columns([1, 1.5, 1])

    with col2:
        # Header
        st.markdown("""
        <div class="login-header">
            <h1>Clinical Report Generator</h1>
            <p>AI-Powered SQL Query Generation Platform</p>
        </div>
        """, unsafe_allow_html=True)

        # Login form
        auth_manager.login()

        # Error message
        if authentication_status == False:
            st.error('Username or password is incorrect.')

        # Signup link
        st.markdown("<div class='signup-section'>", unsafe_allow_html=True)
        st.markdown("Don't have an account?")
        if st.button("Create Account", use_container_width=True, type="secondary"):
            st.session_state['show_signup'] = True
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    st.stop()


# --- Authenticated User Content ---

# Helper function
@st.cache_data
def load_data_dictionary():
    """Load the Databricks schema dictionary."""
    dict_path = "databricks_schema_for_rag.csv"
    if os.path.exists(dict_path):
        df = pd.read_csv(dict_path, encoding='utf-8-sig')
        df = df.rename(columns={
            '테이블명': 'table_name',
            '컬럼명': 'column_name',
            '설명': 'description'
        })
        return df
    return None


# --- Header ---
st.markdown("""
<div class="main-header">
    <h1>Clinical Report Query Generator</h1>
    <p>AI-powered SQL generation for pharmaceutical data analysis</p>
</div>
""", unsafe_allow_html=True)


# --- Sidebar ---
with st.sidebar:
    st.markdown(f"### {name}")
    st.caption(f"@{username}")

    if st.button("Logout", use_container_width=True):
        auth_manager.logout()
        st.rerun()

    st.markdown("---")
    st.markdown("### Navigation")
    st.markdown("""
    - **Disease Pipeline**: 질환 기반 자동 분석
    - **NL2SQL**: 자연어 SQL 변환
    - **Schema Chatbot**: DB 스키마 Q&A
    - **Monitoring**: 시스템 모니터링
    """)

    st.markdown("---")
    st.markdown("### System Status")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<span class="status-online">API: Online</span>', unsafe_allow_html=True)
    with col2:
        st.markdown('<span class="status-online">DB: Online</span>', unsafe_allow_html=True)


# --- Main Content ---
st.markdown('<div class="welcome-box">', unsafe_allow_html=True)
st.markdown(f"### Welcome, {name}")
st.markdown("""
**자연어**로 **SQL 쿼리**를 자동 생성하여 임상 데이터 분석을 간소화합니다.
""")
st.markdown('</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    ### Disease Pipeline Analysis
    질환명만 입력하면 자동 분석
    - 4개 핵심 분석 즉시 실행
    - AI가 7개 추가 분석 추천

    ---

    ### Schema Chatbot
    대화형 스키마 질문/답변
    - 테이블 관계 자동 설명
    - 예시 SQL 자동 생성
    """)

with col2:
    st.markdown("""
    ### Natural Language SQL
    자유로운 자연어 질문
    - 맞춤형 SQL 생성
    - Databricks 호환성 자동 검증

    **예시 질문**:
    - "고혈압 환자 연령대별 분포"
    - "당뇨병 처방 약물 TOP 10"
    """)

st.markdown("---")

# Quick navigation
st.markdown("### Quick Start")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.page_link("pages/1_Disease_Pipeline.py", label="Disease Pipeline")
with col2:
    st.page_link("pages/2_NL2SQL.py", label="NL2SQL")
with col3:
    st.page_link("pages/3_Schema_Chatbot.py", label="Schema Chatbot")
with col4:
    st.page_link("pages/4_Monitoring.py", label="Monitoring")


# --- Schema Reference ---
st.markdown("---")
with st.expander("Database Schema Reference", expanded=False):
    data_dictionary = load_data_dictionary()

    if data_dictionary is not None:
        search_term = st.text_input(
            "Search columns",
            placeholder="예: 질환명, 환자, 처방",
            key="schema_search"
        )

        if search_term:
            filtered_df = data_dictionary[
                data_dictionary.astype(str).apply(
                    lambda row: row.str.contains(search_term, case=False, na=False).any(),
                    axis=1
                )
            ]
        else:
            filtered_df = data_dictionary

        st.dataframe(filtered_df, use_container_width=True, hide_index=True)

        total_cols = len(data_dictionary)
        total_tables = data_dictionary['table_name'].nunique() if 'table_name' in data_dictionary.columns else "N/A"
        st.caption(f"Total: {total_cols} columns | {total_tables} tables")
    else:
        st.warning("Schema file not found.")

# Log usage
auth_manager.log_usage(username, 'view_home')
