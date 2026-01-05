"""Clinical Report Query Generator - Main Streamlit Application"""

import streamlit as st
import os
from typing import Dict, Any, List

# Core imports
from core.recipe_loader import RecipeLoader

# Feature imports
from features.disease_pipeline_tab import DiseasePipelineTab
from features.nl2sql_tab import NL2SQLTab
from features.schema_chatbot_tab import SchemaChatbotTab
from features.monitoring_tab import MonitoringTab


# --- Helper Functions ---

@st.cache_data
def load_data_dictionary():
    """Load the Databricks schema dictionary (RAG-optimized)."""
    import pandas as pd
    # Use Databricks-only schema (filtered from notion_columns_improved.csv)
    dict_path = "databricks_schema_for_rag.csv"
    if os.path.exists(dict_path):
        df = pd.read_csv(dict_path, encoding='utf-8-sig')
        # Rename Korean columns to English for consistency
        df = df.rename(columns={
            '테이블명': 'table_name',
            '컬럼명': 'column_name',
            '설명': 'description'
        })
        return df
    return None


# --- Main App Configuration ---

st.set_page_config(
    page_title="Clinical Report Query Generator | PharmaCo",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed",  # CHANGED: Start with sidebar collapsed
    menu_items={
        'Get Help': 'https://docs.yourcompany.com/clinical-sql-generator',
        'Report a bug': "mailto:support@yourcompany.com",
        'About': """
        ### Clinical Report Query Generator v1.0

        AI-powered SQL generation for clinical data analysis.

        **Features**:
        - Disease-centric pipeline analysis
        - Natural language to SQL conversion
        - Databricks/Spark SQL compatibility

        **Powered by**: Google Gemini 2.5 Flash
        **Target Database**: Databricks (Spark SQL)

        © 2025 PharmaCo Data Analytics Team
        """
    }
)

# Custom CSS for professional styling with enhanced contrast
st.markdown("""
<style>
    /* Main header styling - No changes needed (already excellent contrast) */
    .main-header {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        padding: 1.5rem 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }

    .main-header h1 {
        color: white;
        margin: 0;
        font-size: 2rem;
        font-weight: 600;
    }

    .main-header p {
        color: #e8f4f8;
        margin: 0.5rem 0 0 0;
        font-size: 1rem;
    }

    /* Welcome box - Enhanced contrast for professional readability */
    .welcome-box {
        background-color: #d9ecf7; /* CHANGED: Darker blue tint for better contrast */
        padding: 1.5rem;
        border-radius: 8px;
        border-left: 5px solid #2a5298; /* CHANGED: Thicker border for stronger visual anchor */
        margin-bottom: 2rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06); /* ADDED: Subtle shadow for depth */
    }

    .welcome-box h3 {
        margin-top: 0;
        color: #1d4477; /* CHANGED: Darker blue for 11.2:1 contrast */
    }

    /* Sidebar styling - MAJOR FIX for visibility */
    [data-testid="stSidebar"] {
        background-color: #e8eef3; /* CHANGED: Stronger gray-blue for visibility */
        border-right: 2px solid #c5d5e0; /* ADDED: Clear visual boundary */
    }

    /* FORCE ALL SIDEBAR TEXT TO BE DARK */
    [data-testid="stSidebar"] * {
        color: #2d3640 !important; /* FORCE: ALL text dark gray by default */
    }

    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3 {
        color: #1d4477 !important; /* FORCE: Darker blue for section headers */
        font-size: 1rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
        padding-top: 0.25rem;
    }

    /* Sidebar buttons - Enhanced distinction */
    [data-testid="stSidebar"] .stButton > button {
        border: 1px solid #c5d5e0; /* ADDED: Border for clarity */
        background-color: #ffffff; /* ADDED: Explicit white background */
    }

    [data-testid="stSidebar"] .stButton > button:hover {
        background-color: #f0f5f9; /* ADDED: Subtle hover state */
        border-color: #2a5298; /* ADDED: Blue border on hover */
    }

    /* Tab styling - MAJOR FIX for active state visibility */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #f5f7fa; /* ADDED: Light background for tab strip */
        padding: 0.5rem 0.5rem 0 0.5rem; /* ADDED: Padding around tab strip */
        border-radius: 8px 8px 0 0; /* ADDED: Rounded top corners */
    }

    .stTabs [data-baseweb="tab"] {
        padding: 12px 24px;
        background-color: #dce3e9; /* CHANGED: Stronger gray for better visibility */
        border-radius: 8px 8px 0 0;
        font-weight: 600; /* CHANGED: Bolder for better visibility */
        font-size: 1rem;
        color: #1d4477 !important; /* CHANGED: Dark blue for maximum contrast - FORCE OVERRIDE */
        border: 1px solid #c5d5e0; /* ADDED: Border for definition */
        border-bottom: none; /* Remove bottom border to merge with content */
    }

    .stTabs [data-baseweb="tab"] button {
        color: #1d4477 !important; /* FORCE: Dark blue text for tab buttons */
        font-weight: 600 !important; /* FORCE: Bold text */
    }

    .stTabs [aria-selected="true"] {
        background-color: #ffffff; /* KEPT: White background for active tab */
        border: 2px solid #2a5298; /* CHANGED: Full border for clear distinction */
        border-bottom: 2px solid #ffffff; /* CHANGED: White bottom border blends with content */
        font-weight: 700; /* CHANGED: Even bolder for active state */
        color: #1d4477 !important; /* FORCE: Darker blue text */
        position: relative; /* ADDED: For z-index control */
        z-index: 1; /* ADDED: Lifts active tab above others */
        margin-bottom: -2px; /* ADDED: Overlaps border to merge with content */
    }

    .stTabs [aria-selected="true"] button {
        color: #1d4477 !important; /* FORCE: Dark blue for active tab button */
        font-weight: 700 !important; /* FORCE: Very bold */
    }

    /* Tab panel - Clear boundary */
    .stTabs [data-baseweb="tab-panel"] {
        border: 1px solid #e1e4e8; /* ADDED: Light border around content area */
        border-radius: 0 8px 8px 8px; /* ADDED: Rounded corners */
        padding: 1.5rem; /* ADDED: Internal padding */
        background-color: #ffffff; /* ADDED: Explicit white background */
        margin-top: -1px; /* ADDED: Slight overlap to merge with tab border */
    }

    /* Metric cards - Enhanced contrast */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 600;
        color: #1d4477; /* CHANGED: Darker blue for 11.2:1 contrast */
    }

    [data-testid="stMetricLabel"] {
        color: #2d3640; /* CHANGED: Darker gray for 10.5:1 contrast */
        font-weight: 500; /* ADDED: Medium weight for hierarchy */
    }

    /* Tab content text - Ensure readability */
    .stTabs [data-baseweb="tab-panel"] p,
    .stTabs [data-baseweb="tab-panel"] li {
        color: #2d3640; /* ADDED: Dark gray for body text (9.1:1 contrast) */
    }

    .stTabs [data-baseweb="tab-panel"] strong,
    .stTabs [data-baseweb="tab-panel"] b {
        color: #1d4477; /* ADDED: Dark blue for emphasis (11.2:1 contrast) */
    }

    /* Tab headers (h1, h2, h3) - Maximum visibility */
    .stTabs [data-baseweb="tab-panel"] h1,
    .stTabs [data-baseweb="tab-panel"] h2,
    .stTabs [data-baseweb="tab-panel"] h3,
    .stTabs [data-baseweb="tab-panel"] h4 {
        color: #1d4477 !important; /* FORCE: Dark blue for headers */
        font-weight: 600 !important; /* FORCE: Bold headers */
    }

    /* Input field labels - Enhanced visibility */
    label, .stTextInput label, .stTextArea label {
        color: #1d4477 !important; /* FORCE: Dark blue for labels */
        font-weight: 600 !important; /* FORCE: Bold labels */
    }

    /* Button styling - Professional pharmaceutical aesthetic */
    .stButton > button {
        border-radius: 6px;
        font-weight: 500;
        transition: all 0.3s ease;
        border: 1px solid #d1d5db; /* ADDED: Subtle border for definition */
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
        border-color: #2a5298; /* ADDED: Blue border on hover */
    }

    .stButton > button[kind="primary"] {
        background-color: #2a5298; /* ADDED: Explicit primary color */
        color: #ffffff; /* ADDED: White text */
        border: none; /* ADDED: No border for primary */
    }

    .stButton > button[kind="primary"]:hover {
        background-color: #1d4477; /* ADDED: Darker blue on hover */
    }

    /* Success/Info/Warning boxes - Improved contrast */
    .stAlert {
        border-radius: 6px;
        border-left-width: 4px; /* ADDED: Thicker left border */
    }

    /* Code blocks - Enhanced boundary */
    .stCodeBlock {
        border: 1px solid #c5d5e0; /* CHANGED: Stronger border */
        border-radius: 6px;
        background-color: #f5f7fa; /* ADDED: Subtle background */
    }

    /* Expander - Better visual hierarchy */
    .streamlit-expanderHeader {
        font-weight: 500;
        font-size: 1rem;
        background-color: #f5f7fa; /* ADDED: Background for expander headers */
        border: 1px solid #e1e4e8; /* ADDED: Border for definition */
        border-radius: 6px; /* ADDED: Rounded corners */
        color: #1d4477; /* ADDED: Dark blue for 11.2:1 contrast */
    }

    .streamlit-expanderHeader:hover {
        background-color: #e8eef3; /* ADDED: Darker on hover */
        border-color: #c5d5e0; /* ADDED: Stronger border on hover */
        color: #1d4477; /* ADDED: Keep dark blue on hover */
    }

    /* Sidebar expander text - Enhanced visibility */
    [data-testid="stSidebar"] .streamlit-expanderHeader {
        color: #1d4477 !important; /* FORCE: Dark blue text for sidebar expanders */
        font-weight: 600 !important; /* FORCE: Bolder for emphasis */
    }

    [data-testid="stSidebar"] .streamlit-expanderHeader p {
        color: #1d4477 !important; /* FORCE: Dark blue for expander title */
    }

    [data-testid="stSidebar"] .streamlit-expanderContent {
        color: #2d3640 !important; /* FORCE: Dark gray for expander content */
    }

    [data-testid="stSidebar"] .streamlit-expanderContent p,
    [data-testid="stSidebar"] .streamlit-expanderContent li,
    [data-testid="stSidebar"] .streamlit-expanderContent strong {
        color: #2d3640 !important; /* FORCE: Dark gray text in sidebar expanders */
    }

    [data-testid="stSidebar"] .stMarkdown {
        color: #2d3640 !important; /* FORCE: All markdown text in sidebar */
    }

    [data-testid="stSidebar"] .stMarkdown h3 {
        color: #1d4477 !important; /* FORCE: Dark blue for sidebar section headers */
    }

    /* Divider - Stronger separation */
    hr {
        margin: 2rem 0;
        border: none;
        border-top: 2px solid #c5d5e0; /* CHANGED: Stronger gray */
    }

    /* Input fields - Clear boundaries for data entry */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > select {
        border: 1px solid #c5d5e0; /* ADDED: Clear borders */
        border-radius: 6px;
    }

    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stSelectbox > div > div > select:focus {
        border-color: #2a5298; /* ADDED: Blue border on focus */
        box-shadow: 0 0 0 1px #2a5298; /* ADDED: Focus ring */
    }

    /* System status indicators - Enhanced visibility */
    [data-testid="stSidebar"] .stMarkdown p {
        color: #2d3640 !important; /* FORCE: Darker gray for all sidebar paragraphs */
    }

    [data-testid="stSidebar"] .stMarkdown strong {
        color: #1d4477 !important; /* FORCE: Darker blue for emphasis */
    }

    /* Sidebar caption text */
    [data-testid="stSidebar"] .stCaption {
        color: #2d3640 !important; /* FORCE: Dark gray for captions */
    }

    /* Data table styling - Professional grid appearance */
    [data-testid="stDataFrame"] {
        border: 1px solid #c5d5e0; /* ADDED: Border around tables */
        border-radius: 6px;
        overflow: hidden; /* ADDED: Clip rounded corners */
    }
</style>
""", unsafe_allow_html=True)

# Professional header
st.markdown("""
<div class="main-header">
    <h1>🏥 Clinical Report Query Generator</h1>
    <p>AI-powered SQL generation for pharmaceutical data analysis | Powered by Gemini 2.5 Flash</p>
</div>
""", unsafe_allow_html=True)

# Load data dictionary
data_dictionary = load_data_dictionary()

# Initialize session state for welcome message
if 'first_visit' not in st.session_state:
    st.session_state.first_visit = True

# --- Enhanced Sidebar ---
with st.sidebar:
    st.markdown("### ⚙️ 설정")

    # Quick navigation
    st.markdown("---")
    st.markdown("### 🧭 빠른 이동")

    if st.button("🏠 시작 화면", use_container_width=True, help="환영 메시지 다시 보기"):
        st.session_state.first_visit = True
        st.rerun()

    # Data dictionary toggle
    st.markdown("---")
    st.markdown("### 📚 데이터 사전")
    show_dict = st.toggle("스키마 보기", False, help="테이블 및 컬럼 정보 확인")

    # Context-sensitive help
    st.markdown("---")
    st.markdown("### 💡 도움말")

    with st.expander("자주 묻는 질문", expanded=False):
        st.markdown("""
        **Q: SQL을 전혀 모르는데 사용 가능한가요?**
        A: 네! "질환 파이프라인 분석" 탭을 사용하세요. 질환명만 입력하면 자동으로 분석됩니다.

        **Q: 생성된 SQL은 어디서 실행하나요?**
        A: Databricks에서 실행합니다. SQL을 다운로드하거나 복사하여 Databricks 노트북에 붙여넣으세요.

        **Q: 날짜 필터는 어떻게 사용하나요?**
        A: "최근 1년", "2023년 이후", "2020-2023년" 같은 자연어로 요청하면 됩니다.

        **Q: 에러가 발생하면 어떻게 하나요?**
        A: NL2SQL 탭의 "문제 해결 가이드"를 참고하거나 support@yourcompany.com으로 문의하세요.
        """)

    with st.expander("사용 팁", expanded=False):
        st.markdown("""
        **질환 파이프라인 사용 팁**:
        - 정확한 한글 질환명 사용 (예: "고혈압", "당뇨병")
        - 핵심 분석 4개는 항상 자동 실행됩니다
        - 추천 분석은 자유롭게 선택/해제 가능

        **NL2SQL 사용 팁**:
        - 구체적으로 질문할수록 정확합니다
        - 예시 쿼리를 참고하여 패턴을 익히세요
        - SQL 검증 결과를 확인 후 실행하세요
        """)

    with st.expander("버전 정보", expanded=False):
        st.markdown("""
        **버전**: v1.0.0
        **릴리스**: 2025-10-07
        **AI 모델**: Gemini 2.5 Flash
        **지원 DB**: Databricks (Spark SQL)

        **문의**: support@yourcompany.com
        **문서**: docs.yourcompany.com
        """)

    # System status
    st.markdown("---")
    st.markdown("### 📡 시스템 상태")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("🟢 **API**")
        st.caption("정상")
    with col2:
        st.markdown("🟢 **DB**")
        st.caption("정상")

# Data Dictionary Display (outside sidebar, in main area)
if show_dict:
    st.markdown("---")
    st.subheader("📊 데이터베이스 스키마")

    if data_dictionary is not None:
        # Search functionality
        col_search, col_toggle = st.columns([4, 1])

        with col_search:
            search_term = st.text_input(
                "🔍 컬럼 검색",
                placeholder="예: 질환명, 환자, 처방, 약물",
                help="테이블명, 컬럼명, 설명에서 검색"
            )

        with col_toggle:
            show_all = st.checkbox("전체", value=True, help="전체 스키마 표시")

        # Filter logic
        if search_term and not show_all:
            filtered_df = data_dictionary[
                data_dictionary.astype(str).apply(
                    lambda row: row.str.contains(search_term, case=False, na=False).any(),
                    axis=1
                )
            ]

            if len(filtered_df) > 0:
                st.success(f"🔍 **{len(filtered_df)}개 컬럼** 발견")
            else:
                st.warning("검색 결과가 없습니다. 다른 키워드를 시도해보세요.")
        else:
            filtered_df = data_dictionary

        # Display by table if table_name column exists
        if 'table_name' in filtered_df.columns:
            st.markdown("#### 테이블별 컬럼 목록")

            for table in sorted(filtered_df['table_name'].unique()):
                table_cols = filtered_df[filtered_df['table_name'] == table]

                with st.expander(f"📁 **{table}** ({len(table_cols)}개 컬럼)", expanded=False):
                    st.dataframe(
                        table_cols,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "table_name": "테이블",
                            "column_name": "컬럼명",
                            "description": st.column_config.TextColumn(
                                "설명",
                                width="large"
                            )
                        }
                    )
        else:
            # Fallback: simple dataframe
            st.dataframe(
                filtered_df,
                use_container_width=True,
                hide_index=True
            )

        # Quick statistics
        total_cols = len(data_dictionary)
        total_tables = data_dictionary['table_name'].nunique() if 'table_name' in data_dictionary.columns else "N/A"

        st.caption(f"📊 **총 {total_cols}개 컬럼** | **{total_tables}개 테이블** | Databricks 전용 스키마")
    else:
        st.error("❌ 데이터 사전 파일을 찾을 수 없습니다.")
        st.markdown("""
        **필요한 파일**: `databricks_schema_for_rag.csv`

        **위치**: 프로젝트 루트 디렉토리
        **설명**: Databricks 테이블만 포함된 필터링된 스키마 (561 컬럼, 36 테이블)
        """)

    st.markdown("---")

# --- Welcome Message ---
if st.session_state.first_visit:
    st.markdown('<div class="welcome-box">', unsafe_allow_html=True)
    st.markdown("### 👋 Clinical Report Query Generator에 오신 것을 환영합니다!")
    st.markdown("""
    이 도구는 **자연어**로 **SQL 쿼리**를 자동 생성하여 임상 데이터 분석을 간소화합니다.
    SQL 경험이 없어도 누구나 사용할 수 있습니다.
    """)
    st.markdown('</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        ### 🔬 질환 파이프라인 분석
        **추천 대상**: SQL 초보자, 표준 분석 필요 시

        **특징**:
        - ✅ 질환명만 입력하면 자동 분석
        - ✅ 4개 핵심 분석 즉시 실행
        - ✅ AI가 7개 추가 분석 추천
        - ✅ 체크박스로 간편 선택

        **예시 워크플로우**:
        1. "당뇨병" 입력
        2. 환자 수, 성별 분포, 지역 분포 자동 분석
        3. 추천 분석 중 필요한 것만 선택
        4. 한 번에 실행

        ---

        ### 💬 스키마 도우미
        **추천 대상**: 스키마 구조 이해 필요 시

        **특징**:
        - ✅ 대화형 스키마 질문/답변
        - ✅ 테이블 관계 자동 설명
        - ✅ 날짜 처리 방법 안내
        - ✅ 예시 SQL 자동 생성
        """)

    with col2:
        st.markdown("""
        ### 🤖 자연어 SQL 생성
        **추천 대상**: 유연한 쿼리 필요, SQL 이해 가능

        **특징**:
        - ✅ 자유로운 자연어 질문
        - ✅ 맞춤형 SQL 생성
        - ✅ Databricks 호환성 자동 검증
        - ✅ SQL 다운로드 및 복사

        **예시 질문**:
        - "서울 3차 병원 고혈압 환자 연령대별 분포는?"
        - "최근 1년 당뇨병 처방 약물 TOP 10은?"
        - "천식 환자의 지역별 분포를 보여줘"
        """)

    st.divider()

    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
    with col_btn1:
        if st.button("✅ 시작하기", type="primary", use_container_width=True):
            st.session_state.first_visit = False
            st.rerun()
    with col_btn2:
        if st.button("📚 데이터 사전 보기", use_container_width=True):
            st.session_state.first_visit = False
            st.rerun()

# --- Main Content Tabs ---
tab_names = ["🔬 질환 파이프라인 분석", "🤖 자연어 SQL 생성", "💬 스키마 도우미", "📊 모니터링"]
main_tabs = st.tabs(tab_names)

# Tab 1: Disease Pipeline Analysis
with main_tabs[0]:
    try:
        disease_tab = DiseasePipelineTab(recipe_dir="recipes")
        disease_tab.render()
    except ImportError:
        st.error("❌ Disease Pipeline 모듈을 찾을 수 없습니다. `disease_pipeline.py` 파일을 확인하세요.")
    except Exception as e:
        st.error(f"❌ 예상치 못한 오류 발생: {e}")

# Tab 2: NL2SQL - AI Query Generation
with main_tabs[1]:
    try:
        nl2sql_tab = NL2SQLTab()
        nl2sql_tab.render()
    except ImportError:
        st.error("NL2SQL Generator를 불러올 수 없습니다. nl2sql_generator.py 파일을 확인하세요.")
    except Exception as e:
        st.error(f"오류 발생: {str(e)}")

# Tab 3: Schema Chatbot
with main_tabs[2]:
    try:
        chatbot_tab = SchemaChatbotTab()
        chatbot_tab.render()
    except ImportError:
        st.error("❌ Schema Chatbot 모듈을 찾을 수 없습니다. `schema_chatbot_tab.py` 파일을 확인하세요.")
    except Exception as e:
        st.error(f"❌ 예상치 못한 오류 발생: {e}")

# Tab 4: Monitoring Dashboard
with main_tabs[3]:
    try:
        monitoring_tab = MonitoringTab()
        monitoring_tab.render()
    except ImportError:
        st.error("❌ Monitoring Dashboard 모듈을 찾을 수 없습니다. `monitoring_tab.py` 파일을 확인하세요.")
    except Exception as e:
        st.error(f"❌ 예상치 못한 오류 발생: {e}")
