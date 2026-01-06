"""
Minimal CSS styles for custom components only.
Base theme is handled by .streamlit/config.toml
"""

MAIN_CSS = """
<style>
    /* Custom header component */
    .main-header {
        background: linear-gradient(135deg, #0066cc 0%, #004499 100%);
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
    }

    .main-header h1 {
        color: #ffffff;
        margin: 0;
        font-size: 1.75rem;
        font-weight: 600;
    }

    .main-header p {
        color: rgba(255, 255, 255, 0.85);
        margin: 0.5rem 0 0 0;
        font-size: 0.95rem;
    }

    /* Info box component */
    .welcome-box {
        background-color: #f0f7ff;
        padding: 1.25rem;
        border-radius: 8px;
        border-left: 4px solid #0066cc;
        margin-bottom: 1.5rem;
    }

    .welcome-box h3 {
        margin-top: 0;
        color: #1a1a2e;
        font-size: 1.1rem;
    }

    /* Card component */
    .card {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 1.25rem;
        margin-bottom: 1rem;
    }

    .card:hover {
        border-color: #0066cc;
        box-shadow: 0 2px 8px rgba(0, 102, 204, 0.1);
    }

    /* Status indicator */
    .status-online {
        color: #059669;
        font-weight: 500;
    }

    .status-offline {
        color: #dc2626;
        font-weight: 500;
    }

    /* Hide default Streamlit branding (optional) */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
"""


def apply_styles():
    """Apply minimal custom CSS styles."""
    import streamlit as st
    st.markdown(MAIN_CSS, unsafe_allow_html=True)
