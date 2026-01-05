# Prompt Optimization Implementation Guide

## Overview

This guide provides step-by-step instructions for migrating from hardcoded prompts to the new external template system.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [File Structure](#file-structure)
3. [Migration Steps](#migration-steps)
4. [Code Integration Examples](#code-integration-examples)
5. [Testing Strategy](#testing-strategy)
6. [Rollback Plan](#rollback-plan)
7. [A/B Testing Setup](#ab-testing-setup)

---

## Architecture Overview

### Design Principles

1. **Separation of Concerns**
   - Prompts are external templates (version controlled separately)
   - Code logic focuses on data preparation and API calls
   - Shared components prevent duplication

2. **Maintainability**
   - Single source of truth for prompt components
   - Easy to iterate on prompt quality
   - Clear versioning and change tracking

3. **Flexibility**
   - Hot-reloading in development
   - A/B testing support
   - Environment-specific prompt variants

### Key Components

```
prompts/
├── loader.py              # PromptLoader class
├── shared/                # Reusable components
│   ├── databricks_rules.txt
│   ├── output_validation.txt
│   └── schema_formatting.txt
├── report_generation/     # Tab 1 prompts
│   ├── system.txt
│   ├── user_template.txt
│   └── examples.json
├── recipe_recommendation/ # Tab 2 prompts
│   ├── system.txt
│   └── user_template.txt
└── nl2sql/               # Tab 3 prompts
    ├── system.txt
    ├── user_template.txt
    └── examples.json
```

---

## File Structure

### Shared Components

#### `databricks_rules.txt`
- Databricks/Spark SQL syntax rules
- Date handling (CHAR to DATE conversion)
- Common pitfalls and corrections
- Used by: Tab 1, Tab 3

#### `output_validation.txt`
- JSON output requirements
- Common error patterns
- Validation checklist
- Used by: All tabs

#### `schema_formatting.txt`
- How to interpret RAG schema information
- Table relationship guidelines
- Column usage best practices
- Used by: All tabs

### Tab-Specific Files

Each tab has:
- **system.txt**: Role definition, expertise, principles
- **user_template.txt**: Task instructions with `{{VARIABLES}}`
- **examples.json**: Few-shot examples (where applicable)

---

## Migration Steps

### Phase 1: Setup (No Code Changes)

**Estimated Time:** 15 minutes

1. **Verify File Structure**
   ```bash
   cd /Users/park/clinical_report_generator
   ls -la prompts/
   ```

2. **Test Prompt Loader**
   ```python
   # Test script: test_prompt_loader.py
   from prompts.loader import PromptLoader

   loader = PromptLoader()

   # Test Tab 1
   prompt1 = loader.load_report_generation_prompt(
       user_query="고혈압 환자 분석",
       recipe_list="Recipe 1, Recipe 2",
       schema_info="Schema info here"
   )
   print("Tab 1 prompt length:", len(prompt1))

   # Test Tab 2
   prompt2 = loader.load_recipe_recommendation_prompt(
       disease_name="당뇨병",
       recipe_list="Recipe 1, Recipe 2",
       schema_info="Schema info here"
   )
   print("Tab 2 prompt length:", len(prompt2))

   # Test Tab 3
   prompt3 = loader.load_nl2sql_prompt(
       user_query="고혈압 환자 수",
       schema_context="Schema context"
   )
   print("Tab 3 prompt length:", len(prompt3))
   ```

   ```bash
   python test_prompt_loader.py
   ```

### Phase 2: Tab 3 Migration (Lowest Risk)

**Estimated Time:** 30 minutes

Tab 3 has the most structured prompt and is easiest to migrate.

#### Before (nl2sql_generator.py:186-269)

```python
def _create_llm_prompt(self, query: str, schema_context: str, examples: List[Dict]) -> str:
    """LLM 프롬프트 생성"""

    # Few-shot examples
    examples_text = ""
    if examples:
        examples_text = "\n## 예시\n\n"
        for i, ex in enumerate(examples, 1):
            examples_text += f"### 예시 {i}\n"
            examples_text += f"**질문**: {ex['question']}\n"
            examples_text += f"**SQL**:\n```sql\n{ex['sql']}\n```\n\n"

    prompt = f"""당신은 Databricks/Spark SQL 전문가입니다.
사용자의 자연어 요청을 정확한 SQL로 변환하세요.

{schema_context}

{examples_text}

## Databricks 실제 테이블 스키마
[... 80 lines of hardcoded rules ...]

JSON만 반환하세요."""

    return prompt
```

#### After (with PromptLoader)

```python
from prompts.loader import PromptLoader

class NL2SQLGenerator:
    def __init__(self, schema_file: str = "notion_columns_improved.csv"):
        # ... existing code ...
        self.prompt_loader = PromptLoader()  # ADD THIS

    def _create_llm_prompt(self, query: str, schema_context: str, examples: List[Dict]) -> str:
        """LLM 프롬프트 생성"""
        return self.prompt_loader.load_nl2sql_prompt(
            user_query=query,
            schema_context=schema_context,
            relevant_examples=examples
        )
```

**Changes Required:**
- Add import: `from prompts.loader import PromptLoader`
- Add instance variable: `self.prompt_loader = PromptLoader()`
- Replace entire method body with single loader call

**Testing:**
1. Run NL2SQL tab with test query
2. Verify SQL output is identical or improved
3. Check response time (should be similar)

### Phase 3: Tab 2 Migration (Medium Risk)

**Estimated Time:** 30 minutes

#### Before (disease_pipeline.py:172-210)

```python
def recommend_additional_recipes(...):
    # ... recipe filtering code ...

    recipe_descriptions = "\n".join([
        f"- {r['name']}: {r['description']}"
        for r in available_recipes
    ])

    prompt = f"""당신은 임상 데이터 분석 전문가입니다.

질환명: {disease_name}

**DATABASE SCHEMA INFORMATION (RAG-Enhanced):**
[... schema info ...]

위 질환에 대한 데이터 분석 파이프라인을 구성하려고 합니다.
[... instructions ...]

응답 형식 (JSON):
{{
  "recommended_recipes": [...],
  "reasoning": "추천 이유 간단히"
}}
"""

    try:
        response = self.model.generate_content(prompt)
        # ... parsing code ...
```

#### After (with PromptLoader)

```python
from prompts.loader import PromptLoader

class DiseaseAnalysisPipeline:
    def __init__(self, recipe_dir: str = "recipes"):
        # ... existing code ...
        self.prompt_loader = PromptLoader()  # ADD THIS

    def recommend_additional_recipes(
        self,
        disease_name: str,
        target_count: int = 7
    ) -> List[str]:
        # ... existing filtering code ...

        # Format recipe list
        recipe_descriptions = "\n".join([
            f"- {r['name']}: {r['description']}"
            for r in available_recipes
        ])

        # Get RAG schema info (reuse existing logic)
        schema_info = self._get_schema_info_for_disease(disease_name)

        # Load prompt
        prompt = self.prompt_loader.load_recipe_recommendation_prompt(
            disease_name=disease_name,
            recipe_list=recipe_descriptions,
            schema_info=schema_info,
            target_count=target_count
        )

        try:
            response = self.model.generate_content(prompt)
            # ... existing parsing code ...
```

**New Helper Method (if RAG not already extracted):**

```python
def _get_schema_info_for_disease(self, disease_name: str) -> str:
    """Extract RAG schema info for disease (reuse existing logic)"""
    # If you already have this logic, use it
    # Otherwise, implement basic schema extraction
    return "Basic schema info"  # Placeholder
```

**Testing:**
1. Test with 3-4 different diseases (common, rare, acute, chronic)
2. Verify recommendation quality
3. Check JSON parsing still works

### Phase 4: Tab 1 Migration (Highest Risk, Highest Value)

**Estimated Time:** 45 minutes

#### Before (app.py:88-220)

```python
def get_report_structure_with_llm(...):
    # ... mandatory recipes logic ...

    prompt = f"""You are a seasoned consultant for pharmaceutical companies...

{mandatory_recipes_prompt_part}

IMPORTANT CONTEXT: The data must be filtered by the disease NAME...

**CRITICAL: Databricks/Spark SQL Date Handling Rules**
[... 120+ lines ...]

Your output MUST be a single JSON object. Here are two examples...
[... embedded examples ...]
"""

    response = model.generate_content(prompt)
    cleaned_response_text = response.text.strip().replace("```json", "").replace("```", "")
    return json.loads(cleaned_response_text)
```

#### After (with PromptLoader)

```python
from prompts.loader import PromptLoader

# Initialize loader at module level or pass as parameter
prompt_loader = PromptLoader()

def get_report_structure_with_llm(
    user_query: str,
    all_recipes: List[Dict[str, Any]],
    mandatory_recipes: Optional[List[str]] = None
) -> Optional[Dict[str, Any]]:
    """Generate report structure using LLM"""

    try:
        # Format recipe list (existing logic)
        recipe_info_for_prompt = "\n".join([
            f"- **{r['name']}**: {r['description']}\n  "
            f"Parameters: {', '.join([p['name'] for p in r.get('parameters', [])])}"
            for r in all_recipes
        ])

        # Get RAG schema info (existing logic)
        schema_info_for_prompt = get_schema_info(user_query)  # Your existing function

        # Format mandatory recipes if provided
        mandatory_recipes_text = None
        if mandatory_recipes:
            mandatory_recipes_text = "\n".join([
                f"- {recipe_name}"
                for recipe_name in mandatory_recipes
            ])

        # Load prompt using PromptLoader
        prompt = prompt_loader.load_report_generation_prompt(
            user_query=user_query,
            recipe_list=recipe_info_for_prompt,
            schema_info=schema_info_for_prompt,
            mandatory_recipes=mandatory_recipes_text
        )

        # Call API (existing)
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)

        # Parse response (existing)
        cleaned_response_text = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(cleaned_response_text)

    except Exception as e:
        st.error(f"An error occurred while communicating with the LLM: {e}")
        return None
```

**Testing:**
1. Test with 5+ different report types:
   - Feasibility report with mandatory recipes
   - Market landscape without mandatory recipes
   - Edge case (rare disease, minimal data)
   - Ambiguous query
   - Multi-disease query

2. Compare outputs:
   - Recipe selection quality
   - Parameter extraction accuracy
   - Rationale clarity
   - JSON validity

---

## Code Integration Examples

### Example 1: Basic Integration (app.py)

**File:** `/Users/park/clinical_report_generator/app.py`

```python
# ADD at top of file
from prompts.loader import PromptLoader

# INITIALIZE after imports
prompt_loader = PromptLoader()

# REPLACE get_report_structure_with_llm function (line 70-220)
def get_report_structure_with_llm(
    user_query: str,
    all_recipes: List[Dict[str, Any]],
    mandatory_recipes: Optional[List[str]] = None
) -> Optional[Dict[str, Any]]:
    """
    Generate report structure using LLM with external prompt templates.

    Args:
        user_query: User's natural language query
        all_recipes: List of all available recipe dictionaries
        mandatory_recipes: Optional list of recipe names that must be included

    Returns:
        Parsed JSON response or None if error
    """
    try:
        # Format recipe list
        recipe_info_for_prompt = "\n".join([
            f"- **{r['name']}**: {r['description']}\n  "
            f"Parameters: {', '.join([p['name'] for p in r.get('parameters', [])])}"
            for r in all_recipes
        ])

        # Get schema info (reuse existing RAG logic)
        schema_info_for_prompt = """
질환 분석을 위한 주요 테이블 정보입니다.
(여기에 기존 RAG 로직의 schema_info를 삽입)
"""  # TODO: Replace with actual RAG retrieval

        # Format mandatory recipes
        mandatory_recipes_text = None
        if mandatory_recipes:
            mandatory_recipes_text = "\n".join([
                f"- {recipe_name}"
                for recipe_name in mandatory_recipes
            ])

        # Load prompt
        prompt = prompt_loader.load_report_generation_prompt(
            user_query=user_query,
            recipe_list=recipe_info_for_prompt,
            schema_info=schema_info_for_prompt,
            mandatory_recipes=mandatory_recipes_text
        )

        # Call Gemini API
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)

        # Parse JSON response
        cleaned_response_text = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(cleaned_response_text)

    except Exception as e:
        st.error(f"An error occurred while communicating with the LLM: {e}")
        return None
```

### Example 2: disease_pipeline.py Integration

**File:** `/Users/park/clinical_report_generator/pipelines/disease_pipeline.py`

```python
# ADD import
from prompts.loader import PromptLoader

class DiseaseAnalysisPipeline:
    def __init__(self, recipe_dir: str = "recipes"):
        self.recipe_loader = RecipeLoader(recipes_dir=recipe_dir)
        self.template_engine = SQLTemplateEngine()
        self.gemini_service = GeminiService()
        self.prompt_loader = PromptLoader()  # ADD THIS

    def recommend_additional_recipes(
        self,
        disease_name: str,
        target_count: int = 7
    ) -> List[str]:
        """
        Recommend additional analysis recipes using LLM with external prompts.
        """
        # Filter out core recipes (existing logic)
        available_recipes = [
            r for r in self.recipe_loader.get_all_recipes()
            if r['name'] not in self.CORE_RECIPES
        ]

        # Format recipe list
        recipe_descriptions = "\n".join([
            f"- {r['name']}: {r['description']}"
            for r in available_recipes
        ])

        # Get schema info (implement RAG retrieval)
        schema_info = self._get_schema_info_for_disease(disease_name)

        # Load prompt
        prompt = self.prompt_loader.load_recipe_recommendation_prompt(
            disease_name=disease_name,
            recipe_list=recipe_descriptions,
            schema_info=schema_info,
            target_count=target_count
        )

        try:
            # Call API
            response = self.gemini_service.generate_content(prompt)
            response_text = response.text.strip()

            # Parse JSON (existing logic)
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0].strip()

            result = json.loads(response_text)
            return result.get("recommended_recipes", [])

        except Exception as e:
            print(f"Error recommending recipes: {e}")
            return []

    def _get_schema_info_for_disease(self, disease_name: str) -> str:
        """
        Get relevant schema information for disease analysis.

        TODO: Implement RAG retrieval logic
        For now, return basic schema info.
        """
        return """
주요 테이블:
- basic_treatment: 질환 치료 정보
- insured_person: 환자 인구통계 정보
- prescribed_drug: 처방 약물 정보
"""
```

### Example 3: nl2sql_generator.py Integration

**File:** `/Users/park/clinical_report_generator/pipelines/nl2sql_generator.py`

```python
# ADD import
from prompts.loader import PromptLoader

class NL2SQLGenerator:
    def __init__(self, schema_file: str = "notion_columns_improved.csv"):
        self.schema_df = pd.read_csv(schema_file)
        self.gemini_service = GeminiService()
        self.prompt_loader = PromptLoader()  # ADD THIS
        # Remove hardcoded few_shot_examples - now in external file

    def _create_llm_prompt(self, query: str, schema_context: str, examples: List[Dict]) -> str:
        """Generate LLM prompt using external templates"""
        return self.prompt_loader.load_nl2sql_prompt(
            user_query=query,
            schema_context=schema_context,
            relevant_examples=examples
        )

    # Rest of the class remains the same
```

---

## Testing Strategy

### Unit Tests

Create `/Users/park/clinical_report_generator/tests/test_prompts.py`:

```python
import pytest
from prompts.loader import PromptLoader


class TestPromptLoader:
    def setup_method(self):
        self.loader = PromptLoader()

    def test_shared_components_exist(self):
        """Test that all shared components can be loaded"""
        databricks_rules = self.loader._get_shared_component("databricks_rules")
        assert "TO_DATE" in databricks_rules
        assert "CHAR(200)" in databricks_rules

        output_validation = self.loader._get_shared_component("output_validation")
        assert "JSON" in output_validation

        schema_formatting = self.loader._get_shared_component("schema_formatting")
        assert "res_disease_name" in schema_formatting

    def test_report_generation_prompt(self):
        """Test Tab 1 prompt assembly"""
        prompt = self.loader.load_report_generation_prompt(
            user_query="고혈압 환자 분석",
            recipe_list="Recipe 1, Recipe 2",
            schema_info="Schema info"
        )

        # Check key sections exist
        assert "제약회사" in prompt  # From system.txt
        assert "고혈압 환자 분석" in prompt  # User query
        assert "Recipe 1" in prompt  # Recipe list
        assert "TO_DATE" in prompt  # Databricks rules
        assert "예시" in prompt  # Examples

    def test_recipe_recommendation_prompt(self):
        """Test Tab 2 prompt assembly"""
        prompt = self.loader.load_recipe_recommendation_prompt(
            disease_name="당뇨병",
            recipe_list="Recipe 1, Recipe 2",
            schema_info="Schema info",
            target_count=7
        )

        assert "당뇨병" in prompt
        assert "7개" in prompt
        assert "recommended_recipes" in prompt

    def test_nl2sql_prompt(self):
        """Test Tab 3 prompt assembly"""
        prompt = self.loader.load_nl2sql_prompt(
            user_query="고혈압 환자 수",
            schema_context="Schema context"
        )

        assert "Databricks/Spark SQL" in prompt
        assert "고혈압 환자 수" in prompt
        assert "TO_DATE" in prompt
        assert "예시" in prompt  # Examples included

    def test_mandatory_recipes_section(self):
        """Test mandatory recipes are properly inserted"""
        prompt = self.loader.load_report_generation_prompt(
            user_query="Test query",
            recipe_list="Recipe 1",
            schema_info="Schema",
            mandatory_recipes="Recipe A\nRecipe B"
        )

        assert "Recipe A" in prompt
        assert "Recipe B" in prompt
        assert "필수" in prompt

    def test_cache_clearing(self):
        """Test cache can be cleared"""
        self.loader._get_shared_component("databricks_rules")
        assert len(self.loader._shared_cache) > 0

        self.loader.clear_cache()
        assert len(self.loader._shared_cache) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

Run tests:
```bash
cd /Users/park/clinical_report_generator
pytest tests/test_prompts.py -v
```

### Integration Tests

Create `/Users/park/clinical_report_generator/tests/test_integration.py`:

```python
import json
from prompts.loader import PromptLoader
from services.gemini_service import GeminiService


class TestIntegration:
    """
    Integration tests with actual Gemini API calls.
    WARNING: These consume API quota. Run sparingly.
    """

    def setup_method(self):
        self.loader = PromptLoader()
        self.gemini = GeminiService()

    def test_tab1_end_to_end(self):
        """Test complete Tab 1 flow with API call"""
        prompt = self.loader.load_report_generation_prompt(
            user_query="고혈압 환자 대상 임상시험 타당성 분석",
            recipe_list="- get_patient_count_by_disease_keyword: 환자 수 조회",
            schema_info="basic_treatment, insured_person 테이블 사용 가능"
        )

        response = self.gemini.generate_content(prompt)
        response_text = response.text.strip().replace("```json", "").replace("```", "")

        # Parse JSON
        result = json.loads(response_text)

        # Validate structure
        assert "report_title" in result
        assert "executive_summary" in result
        assert "table_of_contents" in result
        assert "pages" in result
        assert len(result["pages"]) >= 3

    def test_tab2_end_to_end(self):
        """Test complete Tab 2 flow"""
        prompt = self.loader.load_recipe_recommendation_prompt(
            disease_name="당뇨병",
            recipe_list="Recipe 1\nRecipe 2",
            schema_info="Schema",
            target_count=7
        )

        response = self.gemini.generate_content(prompt)
        response_text = response.text.strip().replace("```json", "").replace("```", "")

        result = json.loads(response_text)

        assert "recommended_recipes" in result
        assert "reasoning" in result
        assert len(result["recommended_recipes"]) == 7

    def test_tab3_end_to_end(self):
        """Test complete Tab 3 flow"""
        prompt = self.loader.load_nl2sql_prompt(
            user_query="고혈압 환자의 연령대별 분포",
            schema_context="basic_treatment, insured_person 테이블"
        )

        response = self.gemini.generate_content(prompt)
        response_text = response.text.strip().replace("```json", "").replace("```", "")

        result = json.loads(response_text)

        assert "analysis" in result
        assert "sql" in result
        assert "explanation" in result
        assert "SELECT" in result["sql"]
        assert "TO_DATE" in result["sql"]  # Proper date handling


# Run manually with: pytest tests/test_integration.py -v --tb=short
```

---

## Rollback Plan

If issues arise after migration, you can quickly rollback:

### Option 1: Keep Old Functions (Recommended for Phase Rollout)

```python
# In app.py
def get_report_structure_with_llm_NEW(...):
    """New version with PromptLoader"""
    # ... new implementation

def get_report_structure_with_llm_OLD(...):
    """Original hardcoded version (backup)"""
    # ... original implementation

# Use new version by default, easy to switch
get_report_structure_with_llm = get_report_structure_with_llm_NEW
# To rollback: get_report_structure_with_llm = get_report_structure_with_llm_OLD
```

### Option 2: Feature Flag

```python
# In config.yaml
features:
  use_external_prompts: true  # Set to false to rollback

# In code
from config import load_config

config = load_config()

if config['features']['use_external_prompts']:
    prompt = prompt_loader.load_report_generation_prompt(...)
else:
    prompt = f"""Hardcoded prompt..."""  # Original
```

### Option 3: Git Revert

```bash
# If fully committed, just revert
git log --oneline  # Find commit hash before migration
git revert <commit-hash>
```

---

## A/B Testing Setup

To compare old vs new prompt performance:

### Setup Logging

```python
# utils/prompt_logger.py
import json
import time
from pathlib import Path
from typing import Dict, Any


class PromptLogger:
    """Log prompts and responses for A/B testing"""

    def __init__(self, log_dir: str = "logs/prompts"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def log_interaction(
        self,
        prompt_version: str,  # "old" or "new"
        tab_name: str,  # "tab1", "tab2", "tab3"
        user_query: str,
        prompt: str,
        response: str,
        metadata: Dict[str, Any]
    ):
        """Log a single prompt-response interaction"""
        timestamp = time.time()
        log_entry = {
            "timestamp": timestamp,
            "prompt_version": prompt_version,
            "tab_name": tab_name,
            "user_query": user_query,
            "prompt": prompt,
            "response": response,
            "metadata": metadata
        }

        # Save to JSON Lines file
        log_file = self.log_dir / f"{tab_name}_{prompt_version}.jsonl"
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')


# In app.py
from utils.prompt_logger import PromptLogger

logger = PromptLogger()

# After API call
logger.log_interaction(
    prompt_version="new",
    tab_name="tab1",
    user_query=user_query,
    prompt=prompt,
    response=response.text,
    metadata={
        "recipe_count": len(all_recipes),
        "has_mandatory": mandatory_recipes is not None,
        "response_time_ms": response_time
    }
)
```

### Analysis Script

```python
# scripts/analyze_ab_test.py
import json
from pathlib import Path
from collections import defaultdict


def analyze_ab_test(tab_name: str):
    """Compare old vs new prompt performance"""

    log_dir = Path("logs/prompts")

    old_logs = list((log_dir / f"{tab_name}_old.jsonl").open())
    new_logs = list((log_dir / f"{tab_name}_new.jsonl").open())

    print(f"=== A/B Test Results for {tab_name} ===\n")
    print(f"Old version: {len(old_logs)} interactions")
    print(f"New version: {len(new_logs)} interactions")

    # Parse success rates
    old_success = sum(1 for line in old_logs if is_valid_json(line))
    new_success = sum(1 for line in new_logs if is_valid_json(line))

    print(f"\nSuccess Rate:")
    print(f"  Old: {old_success/len(old_logs)*100:.1f}%")
    print(f"  New: {new_success/len(new_logs)*100:.1f}%")

    # ... add more metrics


if __name__ == "__main__":
    analyze_ab_test("tab1")
    analyze_ab_test("tab2")
    analyze_ab_test("tab3")
```

---

## Maintenance Best Practices

### 1. Prompt Versioning

Use git tags for prompt versions:

```bash
# After making significant prompt changes
git add prompts/
git commit -m "Improve Tab 1 few-shot examples with edge cases"
git tag prompt-v1.1
git push origin prompt-v1.1
```

### 2. Prompt Quality Monitoring

Set up weekly reviews:
- Check logs for parsing errors
- Review response quality samples
- Update examples based on real user queries

### 3. Documentation Updates

When changing prompts:
1. Update IMPLEMENTATION_GUIDE.md
2. Document reasoning in commit message
3. Add entry to CHANGELOG.md

---

## Troubleshooting

### Issue: FileNotFoundError

```
FileNotFoundError: Prompt file not found: prompts/shared/databricks_rules.txt
```

**Solution:** Verify file structure
```bash
ls -la prompts/shared/
# Should show databricks_rules.txt, output_validation.txt, schema_formatting.txt
```

### Issue: JSON Parsing Error

```
json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
```

**Solution:** LLM returned non-JSON response. Check:
1. OUTPUT_VALIDATION component is included
2. System prompt emphasizes JSON-only output
3. Response cleaning logic is applied

### Issue: Variable Not Substituted

```
# Prompt contains: {{USER_QUERY}} instead of actual query
```

**Solution:** Check variable name matches exactly:
```python
# In template: {{USER_QUERY}}
# In code: variables = {"USER_QUERY": user_query}  # Must match case
```

---

## Next Steps

After successful migration:

1. **Collect Baseline Metrics** (Week 1)
   - Response quality scores
   - JSON parse success rate
   - User feedback

2. **Iterate on Prompts** (Week 2-4)
   - Add more few-shot examples
   - Refine instructions based on errors
   - Optimize for token efficiency

3. **Advanced Features** (Month 2+)
   - Multi-language support (if needed)
   - Prompt compression techniques
   - Fine-tuned model experiments

---

## Support

For questions or issues:
1. Check this guide first
2. Review error logs in `logs/prompts/`
3. Test with `test_prompt_loader.py`
4. Check git history: `git log prompts/`

Good luck with the migration!
