"""
Prompt Loader Utility

Loads and assembles prompts from external template files with
variable substitution support.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional


class PromptLoader:
    """
    Manages loading and assembling prompts from template files.

    Supports:
    - Template variable substitution ({{VAR_NAME}})
    - Shared component injection
    - Few-shot example loading
    - Hot reloading for development
    """

    def __init__(self, prompts_dir: str = "prompts"):
        """
        Initialize prompt loader.

        Args:
            prompts_dir: Root directory containing prompt templates
        """
        self.prompts_dir = Path(prompts_dir)
        self.shared_dir = self.prompts_dir / "shared"

        # Cache for shared components
        self._shared_cache: Dict[str, str] = {}

    def _load_file(self, file_path: Path) -> str:
        """Load text content from file."""
        if not file_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    def _load_json(self, file_path: Path) -> Any:
        """Load JSON content from file."""
        if not file_path.exists():
            raise FileNotFoundError(f"JSON file not found: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _get_shared_component(self, component_name: str) -> str:
        """
        Load shared component with caching.

        Args:
            component_name: Name of shared component file (without .txt)

        Returns:
            Component content
        """
        if component_name not in self._shared_cache:
            file_path = self.shared_dir / f"{component_name}.txt"
            self._shared_cache[component_name] = self._load_file(file_path)

        return self._shared_cache[component_name]

    def clear_cache(self):
        """Clear shared component cache (useful for hot reloading)."""
        self._shared_cache.clear()

    def _substitute_variables(self, template: str, variables: Dict[str, str]) -> str:
        """
        Replace {{VAR_NAME}} placeholders with values.

        Args:
            template: Template string with {{VAR_NAME}} placeholders
            variables: Dict mapping variable names to values

        Returns:
            Template with variables substituted
        """
        result = template
        for var_name, var_value in variables.items():
            placeholder = f"{{{{{var_name}}}}}"
            result = result.replace(placeholder, var_value)

        return result

    def load_report_generation_prompt(
        self,
        user_query: str,
        recipe_list: str,
        schema_info: str,
        mandatory_recipes: Optional[str] = None
    ) -> str:
        """
        Load and assemble Tab 1 (Report Generation) prompt.

        Args:
            user_query: User's natural language query
            recipe_list: Formatted list of available recipes
            schema_info: RAG schema information
            mandatory_recipes: Optional mandatory recipes section

        Returns:
            Complete assembled prompt
        """
        prompt_dir = self.prompts_dir / "report_generation"

        # Load system and user templates
        system_prompt = self._load_file(prompt_dir / "system.txt")
        user_template = self._load_file(prompt_dir / "user_template.txt")

        # Load examples
        examples_data = self._load_json(prompt_dir / "examples.json")

        # Format examples
        examples_text = "\n## 출력 예시\n\n"
        for i, example in enumerate(examples_data, 1):
            examples_text += f"### 예시 {i}: {example['type']}\n"
            examples_text += f"**사용자 쿼리:** {example['user_query']}\n\n"
            examples_text += f"**출력:**\n```json\n{json.dumps(example['output'], ensure_ascii=False, indent=2)}\n```\n\n"

        # Load shared components
        databricks_rules = self._get_shared_component("databricks_rules")
        output_validation = self._get_shared_component("output_validation")
        schema_formatting = self._get_shared_component("schema_formatting")

        # Format schema info with guidelines
        schema_section = f"""## 데이터베이스 스키마 정보 (RAG-Enhanced)

{schema_formatting}

### 제공된 스키마
---
{schema_info}
---
"""

        # Handle mandatory recipes
        if mandatory_recipes:
            mandatory_section = f"""## 필수 포함 레시피

사용자가 다음 레시피를 **반드시 포함**하도록 명시했습니다. 보고서 구조에서 이 레시피들을 중심으로 내러티브를 구성하고, 필요한 경우 추가 레시피를 선택하세요.

---
{mandatory_recipes}
---
"""
        else:
            mandatory_section = ""

        # Substitute variables in user template
        variables = {
            "MANDATORY_RECIPES_SECTION": mandatory_section,
            "DATABRICKS_RULES": databricks_rules,
            "SCHEMA_INFO": schema_section,
            "USER_QUERY": user_query,
            "RECIPE_LIST": recipe_list,
            "OUTPUT_VALIDATION": output_validation,
            "EXAMPLES": examples_text
        }

        user_prompt = self._substitute_variables(user_template, variables)

        # Combine system and user prompts
        full_prompt = f"{system_prompt}\n\n---\n\n{user_prompt}"

        return full_prompt

    def load_recipe_recommendation_prompt(
        self,
        disease_name: str,
        recipe_list: str,
        schema_info: str,
        target_count: int = 7
    ) -> str:
        """
        Load and assemble Tab 2 (Recipe Recommendation) prompt.

        Args:
            disease_name: Disease name to analyze
            recipe_list: Formatted list of available recipes
            schema_info: RAG schema information
            target_count: Number of recipes to recommend

        Returns:
            Complete assembled prompt
        """
        prompt_dir = self.prompts_dir / "recipe_recommendation"

        # Load templates
        system_prompt = self._load_file(prompt_dir / "system.txt")
        user_template = self._load_file(prompt_dir / "user_template.txt")

        # Load shared components
        output_validation = self._get_shared_component("output_validation")
        schema_formatting = self._get_shared_component("schema_formatting")

        # Format schema info
        schema_section = f"""## 데이터베이스 스키마 정보 (RAG-Enhanced)

{schema_formatting}

### 제공된 스키마
---
{schema_info}
---
"""

        # Substitute variables
        variables = {
            "DISEASE_NAME": disease_name,
            "SCHEMA_INFO": schema_section,
            "TARGET_COUNT": str(target_count),
            "RECIPE_LIST": recipe_list,
            "OUTPUT_VALIDATION": output_validation
        }

        user_prompt = self._substitute_variables(user_template, variables)

        # Combine
        full_prompt = f"{system_prompt}\n\n---\n\n{user_prompt}"

        return full_prompt

    def load_nl2sql_prompt(
        self,
        user_query: str,
        schema_context: str,
        relevant_examples: Optional[List[Dict]] = None
    ) -> str:
        """
        Load and assemble Tab 3 (NL2SQL) prompt.

        Args:
            user_query: User's natural language SQL request
            schema_context: RAG schema context
            relevant_examples: List of relevant few-shot examples (or None for all)

        Returns:
            Complete assembled prompt
        """
        prompt_dir = self.prompts_dir / "nl2sql"

        # Load templates
        system_prompt = self._load_file(prompt_dir / "system.txt")
        user_template = self._load_file(prompt_dir / "user_template.txt")

        # Load examples
        all_examples = self._load_json(prompt_dir / "examples.json")

        # Use relevant examples or all examples
        examples_to_use = relevant_examples if relevant_examples is not None else all_examples

        # Format examples
        examples_text = ""
        if examples_to_use:
            examples_text = "\n## Few-Shot 예시\n\n"
            examples_text += "다음 예시들을 참고하여 쿼리를 작성하세요:\n\n"
            for i, ex in enumerate(examples_to_use, 1):
                examples_text += f"### 예시 {i}\n"
                examples_text += f"**질문:** {ex['question']}\n\n"
                examples_text += f"**SQL:**\n```sql\n{ex['sql']}\n```\n\n"
                if 'explanation' in ex:
                    examples_text += f"**설명:** {ex['explanation']}\n\n"

        # Load shared components
        databricks_rules = self._get_shared_component("databricks_rules")
        output_validation = self._get_shared_component("output_validation")

        # Substitute variables
        variables = {
            "SCHEMA_CONTEXT": schema_context,
            "EXAMPLES": examples_text,
            "DATABRICKS_RULES": databricks_rules,
            "USER_QUERY": user_query,
            "OUTPUT_VALIDATION": output_validation
        }

        user_prompt = self._substitute_variables(user_template, variables)

        # Combine
        full_prompt = f"{system_prompt}\n\n---\n\n{user_prompt}"

        return full_prompt

    def load_schema_chatbot_prompt(
        self,
        user_question: str,
        schema_context: str,
        conversation_history: Optional[List[Dict]] = None
    ) -> str:
        """
        Load and assemble Schema Chatbot prompt.

        Args:
            user_question: User's question about the schema
            schema_context: RAG schema context
            conversation_history: List of previous messages [{"role": "user"|"assistant", "content": str}]

        Returns:
            Complete assembled prompt
        """
        prompt_dir = self.prompts_dir / "schema_chatbot"

        # Load templates
        system_prompt = self._load_file(prompt_dir / "system.txt")
        user_template = self._load_file(prompt_dir / "user_template.txt")

        # Format conversation history
        history_text = ""
        if conversation_history:
            history_text = "\n**이전 대화:**\n"
            for msg in conversation_history[-4:]:  # Last 4 messages for context
                role = "사용자" if msg["role"] == "user" else "어시스턴트"
                history_text += f"{role}: {msg['content']}\n"
            history_text += "\n"

        # Substitute variables
        variables = {
            "schema_context": schema_context,
            "conversation_history": history_text,
            "user_question": user_question
        }

        user_prompt = self._substitute_variables(user_template, variables)

        # Combine
        full_prompt = f"{system_prompt}\n\n---\n\n{user_prompt}"

        return full_prompt

    def get_few_shot_examples(self, prompt_type: str) -> List[Dict]:
        """
        Get all few-shot examples for a given prompt type.

        Args:
            prompt_type: One of "report_generation", "recipe_recommendation", "nl2sql", "schema_chatbot"

        Returns:
            List of example dictionaries
        """
        if prompt_type == "report_generation":
            file_path = self.prompts_dir / "report_generation" / "examples.json"
        elif prompt_type == "nl2sql":
            file_path = self.prompts_dir / "nl2sql" / "examples.json"
        elif prompt_type == "schema_chatbot":
            file_path = self.prompts_dir / "schema_chatbot" / "examples.json"
        else:
            # Recipe recommendation doesn't have examples file
            return []

        return self._load_json(file_path)


# Convenience function for backward compatibility
def load_prompt(prompt_type: str, **kwargs) -> str:
    """
    Convenience function to load prompts.

    Args:
        prompt_type: One of "report_generation", "recipe_recommendation", "nl2sql"
        **kwargs: Arguments to pass to specific loader method

    Returns:
        Assembled prompt string
    """
    loader = PromptLoader()

    if prompt_type == "report_generation":
        return loader.load_report_generation_prompt(**kwargs)
    elif prompt_type == "recipe_recommendation":
        return loader.load_recipe_recommendation_prompt(**kwargs)
    elif prompt_type == "nl2sql":
        return loader.load_nl2sql_prompt(**kwargs)
    else:
        raise ValueError(f"Unknown prompt type: {prompt_type}")
