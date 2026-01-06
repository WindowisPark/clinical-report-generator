"""Schema Chatbot Page."""

import streamlit as st
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.styles import apply_styles
from components.common import require_auth

st.set_page_config(
    page_title="Schema Chatbot | Clinical Report Generator",
    page_icon="CRG",
    layout="wide"
)

apply_styles()

# Auth check
username = require_auth()

st.markdown("## Schema Chatbot")
st.markdown("DB 스키마 관련 질문에 대한 대화형 Q&A")
st.markdown("---")

try:
    from features.schema_chatbot_tab import SchemaChatbotTab
    chatbot_tab = SchemaChatbotTab()
    chatbot_tab.render()
except ImportError as e:
    st.error(f"Schema Chatbot 모듈을 찾을 수 없습니다: {e}")
except Exception as e:
    st.error(f"오류 발생: {e}")
