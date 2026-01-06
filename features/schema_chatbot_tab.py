"""
Schema Chatbot Tab

Interactive chat interface for database schema questions.
"""

import streamlit as st
from typing import List, Dict, Any
from services.schema_chatbot import SchemaChatbot


class SchemaChatbotTab:
    """
    Tab for schema chatbot interaction.

    Provides:
    - Chat message history (user + assistant)
    - Example question quick-start buttons
    - Relevant tables/columns display
    - Clear conversation functionality
    """

    def __init__(self):
        """Initialize chatbot tab."""
        self.chatbot = SchemaChatbot()
        self._initialize_session_state()

    def _initialize_session_state(self):
        """Initialize Streamlit session state for chat history."""
        if 'chatbot_messages' not in st.session_state:
            st.session_state.chatbot_messages = []

    def render(self):
        """Render the schema chatbot tab."""
        st.header("💬 스키마 도우미")
        st.markdown("데이터베이스 스키마에 대해 무엇이든 물어보세요")

        # Example questions section
        self._render_example_questions()

        st.markdown("---")

        # Chat history display
        self._render_chat_history()

        # Input section
        self._render_input_section()

        # Action buttons
        col1, col2 = st.columns([1, 5])
        with col1:
            if st.button("🗑️ 대화 초기화", key="clear_chat"):
                st.session_state.chatbot_messages = []
                st.rerun()

    def _render_example_questions(self):
        """Render example question buttons."""
        st.markdown("**💡 예시 질문:**")

        example_questions = self.chatbot.get_example_questions()

        # Display in 2 columns
        cols = st.columns(2)
        for i, question in enumerate(example_questions[:6]):  # Show first 6
            col_idx = i % 2
            with cols[col_idx]:
                if st.button(
                    question[:50] + "..." if len(question) > 50 else question,
                    key=f"example_q_{i}",
                    use_container_width=True
                ):
                    self._process_question(question)

    def _render_chat_history(self):
        """Render chat message history."""
        if not st.session_state.chatbot_messages:
            st.info("👆 위의 예시 질문을 클릭하거나 아래에 질문을 입력하세요")
            return

        st.markdown("### 💬 대화 내역")

        for message in st.session_state.chatbot_messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

                # Show relevant tables/columns for assistant messages
                if message["role"] == "assistant" and "metadata" in message:
                    self._render_metadata(message["metadata"])

    def _render_metadata(self, metadata: Dict[str, Any]):
        """
        Render metadata (relevant tables/columns) in an expander.

        Args:
            metadata: Dict with 'relevant_tables' and 'relevant_columns'
        """
        if not metadata:
            return

        with st.expander("📊 관련 테이블/컬럼 정보", expanded=False):
            # Relevant tables
            relevant_tables = metadata.get('relevant_tables', [])
            if relevant_tables:
                st.markdown("**관련 테이블:**")
                st.code(", ".join(relevant_tables))

            # Relevant columns (show first 10)
            relevant_columns = metadata.get('relevant_columns', [])
            if relevant_columns:
                st.markdown("**주요 컬럼:**")
                for col in relevant_columns[:10]:
                    st.markdown(
                        f"- `{col['table_name']}.{col['column_name']}` "
                        f"({col.get('data_type', 'N/A')}): {col.get('description', 'N/A')}"
                    )

                if len(relevant_columns) > 10:
                    st.caption(f"... 외 {len(relevant_columns) - 10}개 컬럼")

    def _render_input_section(self):
        """Render user input section."""
        # Chat input
        user_question = st.chat_input("스키마에 대해 질문하세요...", key="chat_input")

        if user_question:
            self._process_question(user_question)

    def _process_question(self, question: str):
        """
        Process user question and generate response.

        Args:
            question: User's question string
        """
        # Add user message to history
        st.session_state.chatbot_messages.append({
            "role": "user",
            "content": question
        })

        # Show typing indicator
        with st.spinner("🤔 생각 중..."):
            # Get conversation history (last 10 messages)
            history = st.session_state.chatbot_messages[-10:]

            # Call chatbot
            result = self.chatbot.ask(
                user_question=question,
                conversation_history=history,
                top_k=20
            )

        # Handle response
        if result['success']:
            # Add assistant message to history
            st.session_state.chatbot_messages.append({
                "role": "assistant",
                "content": result['answer'],
                "metadata": {
                    "relevant_tables": result['relevant_tables'],
                    "relevant_columns": result['relevant_columns']
                }
            })
        else:
            # Show error
            error_msg = f"❌ 오류가 발생했습니다: {result['error_message']}"
            st.session_state.chatbot_messages.append({
                "role": "assistant",
                "content": error_msg
            })

        # Force rerun to display messages immediately
        st.rerun()

    def _render_core_tables_info(self):
        """Render core tables information (optional feature)."""
        with st.expander("📖 핵심 테이블 정보", expanded=False):
            core_info = self.chatbot.get_core_tables_info()
            st.markdown(core_info)
