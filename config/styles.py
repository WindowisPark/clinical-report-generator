"""Global CSS styles for the application."""

MAIN_CSS = """
<style>
    /* Main header styling */
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

    /* Welcome box */
    .welcome-box {
        background-color: #d9ecf7;
        padding: 1.5rem;
        border-radius: 8px;
        border-left: 5px solid #2a5298;
        margin-bottom: 2rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
    }

    .welcome-box h3 {
        margin-top: 0;
        color: #1d4477;
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #e8eef3;
        border-right: 2px solid #c5d5e0;
    }

    [data-testid="stSidebar"] * {
        color: #2d3640 !important;
    }

    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3 {
        color: #1d4477 !important;
        font-size: 1rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
        padding-top: 0.25rem;
    }

    [data-testid="stSidebar"] .stButton > button {
        border: 1px solid #c5d5e0;
        background-color: #ffffff;
    }

    [data-testid="stSidebar"] .stButton > button:hover {
        background-color: #f0f5f9;
        border-color: #2a5298;
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #f5f7fa;
        padding: 0.5rem 0.5rem 0 0.5rem;
        border-radius: 8px 8px 0 0;
    }

    .stTabs [data-baseweb="tab"] {
        padding: 12px 24px;
        background-color: #dce3e9;
        border-radius: 8px 8px 0 0;
        font-weight: 600;
        font-size: 1rem;
        color: #1d4477 !important;
        border: 1px solid #c5d5e0;
        border-bottom: none;
    }

    .stTabs [data-baseweb="tab"] button {
        color: #1d4477 !important;
        font-weight: 600 !important;
    }

    .stTabs [aria-selected="true"] {
        background-color: #ffffff;
        border: 2px solid #2a5298;
        border-bottom: 2px solid #ffffff;
        font-weight: 700;
        color: #1d4477 !important;
        position: relative;
        z-index: 1;
        margin-bottom: -2px;
    }

    .stTabs [aria-selected="true"] button {
        color: #1d4477 !important;
        font-weight: 700 !important;
    }

    .stTabs [data-baseweb="tab-panel"] {
        border: 1px solid #e1e4e8;
        border-radius: 0 8px 8px 8px;
        padding: 1.5rem;
        background-color: #ffffff;
        margin-top: -1px;
    }

    /* Metric cards */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 600;
        color: #1d4477;
    }

    [data-testid="stMetricLabel"] {
        color: #2d3640;
        font-weight: 500;
    }

    /* Tab content text */
    .stTabs [data-baseweb="tab-panel"] p,
    .stTabs [data-baseweb="tab-panel"] li {
        color: #2d3640;
    }

    .stTabs [data-baseweb="tab-panel"] strong,
    .stTabs [data-baseweb="tab-panel"] b {
        color: #1d4477;
    }

    .stTabs [data-baseweb="tab-panel"] h1,
    .stTabs [data-baseweb="tab-panel"] h2,
    .stTabs [data-baseweb="tab-panel"] h3,
    .stTabs [data-baseweb="tab-panel"] h4 {
        color: #1d4477 !important;
        font-weight: 600 !important;
    }

    /* Input field labels */
    label, .stTextInput label, .stTextArea label {
        color: #1d4477 !important;
        font-weight: 600 !important;
    }

    /* Button styling */
    .stButton > button {
        border-radius: 6px;
        font-weight: 500;
        transition: all 0.3s ease;
        border: 1px solid #d1d5db;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
        border-color: #2a5298;
    }

    .stButton > button[kind="primary"] {
        background-color: #2a5298;
        color: #ffffff;
        border: none;
    }

    .stButton > button[kind="primary"]:hover {
        background-color: #1d4477;
    }

    /* Alert boxes */
    .stAlert {
        border-radius: 6px;
        border-left-width: 4px;
    }

    /* Code blocks */
    .stCodeBlock {
        border: 1px solid #c5d5e0;
        border-radius: 6px;
        background-color: #f5f7fa;
    }

    /* Expander */
    .streamlit-expanderHeader {
        font-weight: 500;
        font-size: 1rem;
        background-color: #f5f7fa;
        border: 1px solid #e1e4e8;
        border-radius: 6px;
        color: #1d4477;
    }

    .streamlit-expanderHeader:hover {
        background-color: #e8eef3;
        border-color: #c5d5e0;
        color: #1d4477;
    }

    /* Sidebar expander */
    [data-testid="stSidebar"] .streamlit-expanderHeader {
        color: #1d4477 !important;
        font-weight: 600 !important;
    }

    [data-testid="stSidebar"] .streamlit-expanderHeader p {
        color: #1d4477 !important;
    }

    [data-testid="stSidebar"] .streamlit-expanderContent {
        color: #2d3640 !important;
    }

    [data-testid="stSidebar"] .streamlit-expanderContent p,
    [data-testid="stSidebar"] .streamlit-expanderContent li,
    [data-testid="stSidebar"] .streamlit-expanderContent strong {
        color: #2d3640 !important;
    }

    [data-testid="stSidebar"] .stMarkdown {
        color: #2d3640 !important;
    }

    [data-testid="stSidebar"] .stMarkdown h3 {
        color: #1d4477 !important;
    }

    /* Divider */
    hr {
        margin: 2rem 0;
        border: none;
        border-top: 2px solid #c5d5e0;
    }

    /* Input fields */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > select {
        border: 1px solid #c5d5e0;
        border-radius: 6px;
    }

    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stSelectbox > div > div > select:focus {
        border-color: #2a5298;
        box-shadow: 0 0 0 1px #2a5298;
    }

    /* Sidebar text */
    [data-testid="stSidebar"] .stMarkdown p {
        color: #2d3640 !important;
    }

    [data-testid="stSidebar"] .stMarkdown strong {
        color: #1d4477 !important;
    }

    [data-testid="stSidebar"] .stCaption {
        color: #2d3640 !important;
    }

    /* Data table */
    [data-testid="stDataFrame"] {
        border: 1px solid #c5d5e0;
        border-radius: 6px;
        overflow: hidden;
    }
</style>
"""


def apply_styles():
    """Apply global CSS styles."""
    import streamlit as st
    st.markdown(MAIN_CSS, unsafe_allow_html=True)
