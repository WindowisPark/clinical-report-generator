"""Monitoring Dashboard Page."""

import streamlit as st
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.styles import apply_styles
from components.common import require_auth

st.set_page_config(
    page_title="Monitoring | Clinical Report Generator",
    page_icon="CRG",
    layout="wide"
)

apply_styles()

# Auth check
username = require_auth()

st.markdown("## Monitoring Dashboard")
st.markdown("시스템 상태 및 사용량 모니터링")
st.markdown("---")

try:
    from features.monitoring_tab import MonitoringTab
    monitoring_tab = MonitoringTab()
    monitoring_tab.render()
except ImportError as e:
    st.error(f"Monitoring 모듈을 찾을 수 없습니다: {e}")
except Exception as e:
    st.error(f"오류 발생: {e}")
