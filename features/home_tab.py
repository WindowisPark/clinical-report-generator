"""Home Tab - LLM-powered report builder with recipe selection"""

import streamlit as st
from typing import Dict, Any, Optional, List
from utils.parsers import robust_csv_parser
from utils.visualization import render_chart_from_recipe
from core.sql_template_engine import SQLTemplateEngine


class HomeTab:
    """Handles Tab 1: Home - AI report generation with dynamic recipe selection"""

    def __init__(self, recipe_dict: Dict[str, Any]):
        """
        Initialize Home Tab

        Args:
            recipe_dict: Dictionary mapping recipe names to recipe objects
        """
        self.recipe_dict = recipe_dict
        self.sql_engine = SQLTemplateEngine()

    def render(self):
        """Main render method for the Home tab"""
        if st.session_state.report_structure:
            self._render_report()
        else:
            st.info("Enter a topic in the sidebar and click 'Generate Report' to begin.")

    def _render_report(self):
        """Render the generated report structure"""
        report_structure = st.session_state.report_structure

        if "report_title" not in report_structure or "pages" not in report_structure:
            st.error("Failed to generate a valid report structure from the LLM.")
            return

        # Display report header
        st.header(report_structure["report_title"])

        # Display Executive Summary
        if "executive_summary" in report_structure:
            st.subheader("Executive Summary")
            st.markdown(report_structure["executive_summary"])

        # Display Table of Contents
        if "table_of_contents" in report_structure:
            st.subheader("Table of Contents")
            for item in report_structure["table_of_contents"]:
                st.markdown(f"- {item}")

        st.divider()

        # Create tabs for each page
        tab_titles = [
            page.get("title", f"Page {i+1}")
            for i, page in enumerate(report_structure["pages"])
        ]
        tabs = st.tabs(tab_titles)

        # Render each page
        for i, page in enumerate(report_structure["pages"]):
            with tabs[i]:
                self._render_page(page, i)

    def _render_page(self, page: Dict[str, Any], page_index: int):
        """
        Render a single page within the report

        Args:
            page: Page configuration from report structure
            page_index: Index of the page (for session state keys)
        """
        recipe_name = page.get("recipe_name")
        recipe = self.recipe_dict.get(recipe_name)
        llm_params = page.get("parameters", {})

        if not recipe:
            st.error(f"LLM recommended recipe '{recipe_name}', but it was not found.")
            return

        # Display rationale
        if "rationale" in page:
            st.info(f"**Rationale:** {page['rationale']}")

        # Display recipe information
        st.subheader(f"Recipe: `{recipe_name}`")
        st.markdown(f"**Description:** {recipe.get('description', 'N/A')}")
        st.json(llm_params)

        # Display SQL query
        st.subheader("Final SQL Query")
        sql_template = self._get_sql_from_recipe(recipe)
        final_sql = self.sql_engine.render(sql_template, llm_params)
        st.code(final_sql, language="sql")

        st.divider()

        # Visualization section
        self._render_visualization_section(recipe, page_index)

    def _render_visualization_section(self, recipe: Dict[str, Any], page_index: int):
        """
        Render the visualization section with data input and chart generation

        Args:
            recipe: Recipe configuration
            page_index: Index for session state keys
        """
        st.subheader("📊 Generate Visualization")
        df_key = f"dataframe_{page_index}"

        viz_tab1, viz_tab2 = st.tabs(["Paste Text", "Upload File"])

        # Tab 1: Paste text
        with viz_tab1:
            csv_input_key = f"csv_input_{page_index}"
            st.text_area("Paste CSV data...", height=150, key=csv_input_key)

            if st.button("Generate from Text", key=f"text_button_{page_index}"):
                csv_text = st.session_state.get(csv_input_key, "")
                if csv_text:
                    try:
                        df = robust_csv_parser(csv_text)
                        st.session_state[df_key] = df
                    except Exception as e:
                        st.error(f"Failed to parse CSV from text: {e}")
                        if df_key in st.session_state:
                            del st.session_state[df_key]
                else:
                    st.warning("Please paste CSV data first.")

        # Tab 2: Upload file
        with viz_tab2:
            upload_key = f"uploader_{page_index}"
            uploaded_file = st.file_uploader(
                "Upload CSV file...",
                type=["csv", "txt"],
                key=upload_key
            )

            if uploaded_file is not None:
                try:
                    df = robust_csv_parser(uploaded_file)
                    st.session_state[df_key] = df
                except Exception as e:
                    st.error(f"Failed to parse CSV from file: {e}")
                    if df_key in st.session_state:
                        del st.session_state[df_key]

        # Display chart if data is available
        if df_key in st.session_state:
            df = st.session_state[df_key]
            st.write("**Chart:**")
            render_chart_from_recipe(df, recipe)

    @staticmethod
    def _get_sql_from_recipe(recipe: Dict[str, Any]) -> str:
        """
        Get the SQL query content from a recipe's SQL file

        Args:
            recipe: Recipe configuration with sql_file_path

        Returns:
            SQL query string or error message
        """
        try:
            with open(recipe['sql_file_path'], "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return f"Error: SQL file not found at {recipe['sql_file_path']}"
        except Exception as e:
            return f"An error occurred: {e}"
