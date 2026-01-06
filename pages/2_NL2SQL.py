"""Natural Language to SQL Page."""

import streamlit as st
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.styles import apply_styles
from features.nl2sql_tab import NL2SQLTab

st.set_page_config(
    page_title="NL2SQL | Clinical Report Generator",
    page_icon="CRG",
    layout="wide"
)

apply_styles()

st.markdown("## Natural Language to SQL")
st.markdown("자연어 질의를 SQL로 변환")
st.markdown("---")

try:
    nl2sql_tab = NL2SQLTab()
    nl2sql_tab.render()
except ImportError as e:
    st.error(f"NL2SQL 모듈을 찾을 수 없습니다: {e}")
except Exception as e:
    st.error(f"오류 발생: {e}")
