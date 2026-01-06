"""
Streamlit session state management helpers
"""

import streamlit as st
from typing import List


def clear_report_state():
    """Clear all report-related session state."""
    st.session_state.report_structure = None
    for key in list(st.session_state.keys()):
        if key.startswith('dataframe_') or key.startswith('csv_input_') or key.startswith('uploader_'):
            del st.session_state[key]


def initialize_report_state():
    """Initialize report session state if not exists."""
    if 'report_structure' not in st.session_state:
        st.session_state.report_structure = None
