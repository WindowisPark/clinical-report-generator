"""Disease Pipeline Analysis Page."""

import streamlit as st
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.styles import apply_styles
from components.common import require_auth

st.set_page_config(
    page_title="Disease Pipeline | Clinical Report Generator",
    page_icon="CRG",
    layout="wide"
)

apply_styles()

# Auth check
username = require_auth()

st.markdown("## Disease Pipeline Analysis")
st.markdown("질환 키워드 기반 자동 분석 파이프라인")
st.markdown("---")

try:
    from features.disease_pipeline_tab import DiseasePipelineTab
    disease_tab = DiseasePipelineTab(recipe_dir="recipes")
    disease_tab.render()
except ImportError as e:
    st.error(f"Disease Pipeline 모듈을 찾을 수 없습니다: {e}")
except Exception as e:
    st.error(f"오류 발생: {e}")
