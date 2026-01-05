"""
Schema Chatbot Service

Provides conversational interface for answering database schema questions
using RAG pattern and LLM.
"""

from typing import Dict, List, Optional, Any
from core.schema_loader import SchemaLoader
from services.gemini_service import GeminiService
from prompts.loader import PromptLoader


class SchemaChatbot:
    """
    Chatbot for answering database schema questions.

    Uses RAG (Retrieval-Augmented Generation) to provide accurate,
    context-aware answers about database structure, relationships,
    and usage patterns.
    """

    def __init__(self):
        """Initialize chatbot with required services."""
        self.schema_loader = SchemaLoader()
        self.gemini_service = GeminiService()
        self.prompt_loader = PromptLoader()

    def ask(
        self,
        user_question: str,
        conversation_history: Optional[List[Dict]] = None,
        top_k: int = 20
    ) -> Dict[str, Any]:
        """
        Answer a schema question using RAG + LLM.

        Args:
            user_question: User's natural language question
            conversation_history: Previous conversation messages
                Format: [{"role": "user"|"assistant", "content": str}, ...]
            top_k: Number of schema items to retrieve (default: 20)

        Returns:
            {
                'answer': str,  # Natural language answer
                'relevant_tables': List[str],  # Tables referenced
                'relevant_columns': List[Dict],  # Columns with descriptions
                'success': bool,  # Whether the request succeeded
                'error_message': Optional[str]  # Error details if failed
            }
        """
        try:
            # Step 1: Retrieve relevant schema using RAG
            relevant_schema = self.schema_loader.get_relevant_schema(
                query=user_question,
                top_k=top_k,
                include_core_tables=True
            )

            # Step 2: Format schema for LLM
            schema_context = self.schema_loader.format_schema_for_llm(relevant_schema)

            # Step 3: Build prompt with schema + conversation history
            prompt = self.prompt_loader.load_schema_chatbot_prompt(
                user_question=user_question,
                schema_context=schema_context,
                conversation_history=conversation_history or []
            )

            # Step 4: Get LLM response
            response = self.gemini_service.generate_content(prompt)
            answer = response.text

            # Step 5: Extract relevant tables and columns from schema
            relevant_tables = self._extract_tables(relevant_schema)
            relevant_columns = self._extract_columns(relevant_schema)

            return {
                'success': True,
                'answer': answer,
                'relevant_tables': relevant_tables,
                'relevant_columns': relevant_columns,
                'error_message': None
            }

        except Exception as e:
            return {
                'success': False,
                'answer': '',
                'relevant_tables': [],
                'relevant_columns': [],
                'error_message': str(e)
            }

    def _extract_tables(self, schema_df) -> List[str]:
        """
        Extract unique table names from schema.

        Args:
            schema_df: DataFrame with schema information

        Returns:
            List of unique table names
        """
        if schema_df.empty:
            return []

        # Try both English and Korean column names
        table_col = 'table_name' if 'table_name' in schema_df.columns else '테이블명'
        return sorted(schema_df[table_col].unique().tolist())

    def _extract_columns(self, schema_df) -> List[Dict[str, str]]:
        """
        Extract column information from schema.

        Args:
            schema_df: DataFrame with schema information

        Returns:
            List of column dicts with table_name, column_name, description
        """
        if schema_df.empty:
            return []

        # Handle both English and Korean column names
        table_col = 'table_name' if 'table_name' in schema_df.columns else '테이블명'
        column_col = 'column_name' if 'column_name' in schema_df.columns else '컬럼명'
        desc_col = 'description' if 'description' in schema_df.columns else '설명'
        type_col = 'data_type' if 'data_type' in schema_df.columns else '데이터타입'

        columns = []
        for _, row in schema_df.iterrows():
            columns.append({
                'table_name': row.get(table_col, ''),
                'column_name': row.get(column_col, ''),
                'description': row.get(desc_col, ''),
                'data_type': row.get(type_col, '')
            })

        return columns

    def get_example_questions(self) -> List[str]:
        """
        Get list of example questions users can ask.

        Returns:
            List of example question strings
        """
        examples = self.prompt_loader.get_few_shot_examples("schema_chatbot")
        return [ex['question'] for ex in examples]

    def get_core_tables_info(self) -> str:
        """
        Get formatted information about core tables.

        Returns:
            Markdown-formatted string with core table descriptions
        """
        core_schema = self.schema_loader.get_core_tables_schema()
        return self.schema_loader.format_schema_for_llm(core_schema)
