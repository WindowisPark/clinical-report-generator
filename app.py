"""Clinical Report Query Generator - Main Application Entry Point."""

import streamlit as st
import os
import pandas as pd

from config.styles import apply_styles

# --- Page Configuration ---
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

        © 2025 PharmaCo Data Analytics Team
        """
    }
)

# Apply global styles
apply_styles()


# --- Helper Functions ---
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
    <p>AI-powered SQL generation for pharmaceutical data analysis | Powered by Gemini 2.5 Flash</p>
</div>
""", unsafe_allow_html=True)


# --- Sidebar ---
with st.sidebar:
    st.markdown("### Navigation")
    st.markdown("""
    Use the sidebar to navigate between pages:
    - **Disease Pipeline**: 질환 기반 자동 분석
    - **NL2SQL**: 자연어 SQL 변환
    - **Schema Chatbot**: DB 스키마 Q&A
    - **Monitoring**: 시스템 모니터링
    """)

    st.markdown("---")
    st.markdown("### System Status")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**API**: Online")
    with col2:
        st.markdown("**DB**: Online")


# --- Main Content (Home Page) ---
st.markdown('<div class="welcome-box">', unsafe_allow_html=True)
st.markdown("### Clinical Report Query Generator")
st.markdown("""
이 도구는 **자연어**로 **SQL 쿼리**를 자동 생성하여 임상 데이터 분석을 간소화합니다.
SQL 경험이 없어도 누구나 사용할 수 있습니다.
""")
st.markdown('</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    ### Disease Pipeline Analysis
    **추천 대상**: SQL 초보자, 표준 분석 필요 시

    **특징**:
    - 질환명만 입력하면 자동 분석
    - 4개 핵심 분석 즉시 실행
    - AI가 7개 추가 분석 추천

    ---

    ### Schema Chatbot
    **추천 대상**: 스키마 구조 이해 필요 시

    **특징**:
    - 대화형 스키마 질문/답변
    - 테이블 관계 자동 설명
    - 예시 SQL 자동 생성
    """)

with col2:
    st.markdown("""
    ### Natural Language SQL Generation
    **추천 대상**: 유연한 쿼리 필요, SQL 이해 가능

    **특징**:
    - 자유로운 자연어 질문
    - 맞춤형 SQL 생성
    - Databricks 호환성 자동 검증

    **예시 질문**:
    - "서울 3차 병원 고혈압 환자 연령대별 분포는?"
    - "최근 1년 당뇨병 처방 약물 TOP 10은?"
    """)

st.markdown("---")

# Quick navigation buttons
st.markdown("### Quick Start")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.page_link("pages/1_Disease_Pipeline.py", label="Disease Pipeline", icon=None)
with col2:
    st.page_link("pages/2_NL2SQL.py", label="NL2SQL", icon=None)
with col3:
    st.page_link("pages/3_Schema_Chatbot.py", label="Schema Chatbot", icon=None)
with col4:
    st.page_link("pages/4_Monitoring.py", label="Monitoring", icon=None)


# --- Data Dictionary Section ---
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
        st.warning("Schema file not found: databricks_schema_for_rag.csv")
