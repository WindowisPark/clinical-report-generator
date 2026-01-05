# Clinical Report Query Generator - Codebase Guide

> **Purpose**: Quick reference for Claude Code to understand project structure, locate files, and navigate dependencies.

## Project Overview

AI-powered SQL query generator for clinical data analysis with real-time execution. Three main workflows:
1. **Disease Pipeline**: Disease-centric analysis with 4 core + 7 recommended recipes
2. **NL2SQL**: Natural language to SQL with RAG pattern + real-time execution + query history
3. **Schema Chatbot**: Interactive Q&A assistant for database schema understanding

**Stack**: Streamlit + Google Gemini API + Plotly + Jinja2 + Databricks SQL Connector
**Target DB**: Databricks (Spark SQL)

---

## Architecture Map

```
app.py (324 lines) ← Entry point
│
├─ features/ ← UI Components (Streamlit tabs)
│  ├─ disease_pipeline_tab.py (269 lines)
│  ├─ nl2sql_tab.py (520 lines) ← Phase 12/19: +Execution +History
│  └─ schema_chatbot_tab.py (158 lines) ← Phase 11
│
├─ pipelines/ ← Business Logic Orchestration
│  ├─ disease_pipeline.py (498 lines) → DiseaseAnalysisPipeline
│  └─ nl2sql_generator.py (392 lines) → NL2SQLGenerator
│
├─ components/ ← Reusable UI Components (Phase 13)
│  └─ chart_builder.py (518 lines) → ChartBuilder (8 chart types, 7 palettes)
│
├─ core/ ← Domain Logic
│  ├─ recipe_loader.py (60 lines) → RecipeLoader
│  └─ sql_template_engine.py (50 lines) → SQLTemplateEngine
│
├─ services/ ← External APIs
│  ├─ gemini_service.py (72 lines) → GeminiService (Singleton)
│  ├─ databricks_client.py (315 lines) → DatabricksClient (Phase 12)
│  ├─ schema_chatbot.py (152 lines) → SchemaChatbot (Phase 11)
│  └─ parameter_extractor.py (59 lines)
│
└─ utils/ ← Pure Utilities
   ├─ parsers.py (33 lines)
   ├─ formatters.py (54 lines)
   ├─ visualization.py (131 lines)
   ├─ session_state.py (19 lines)
   ├─ query_history.py (361 lines) ← Phase 19: Persistent storage
   └─ chart_recommender.py (346 lines) ← Phase 18: Auto recommendation
```

**Dependency Flow**: app.py → features → pipelines/components → core/services → utils

---

## Quick File Locator

### When you need to...

| Task | File | Key Function/Class |
|------|------|-------------------|
| Modify Tab 1 UI | `features/disease_pipeline_tab.py` | `DiseasePipelineTab.render()` |
| Modify Tab 2 UI | `features/nl2sql_tab.py` | `NL2SQLTab.render()` |
| Modify Tab 3 UI | `features/schema_chatbot_tab.py` | `SchemaChatbotTab.render()` |
| Change disease pipeline logic | `pipelines/disease_pipeline.py` | `DiseaseAnalysisPipeline.execute_core_recipes()` |
| Fix NL2SQL generation | `pipelines/nl2sql_generator.py` | `NL2SQLGenerator.generate_sql()` |
| Execute Databricks queries | `services/databricks_client.py` | `DatabricksClient.execute_query()` |
| Build professional charts | `components/chart_builder.py` | `ChartBuilder.render()` |
| Manage query history | `utils/query_history.py` | `QueryHistory.add_query()`, `get_favorites()` |
| Auto-recommend chart types | `utils/chart_recommender.py` | `ChartRecommender.recommend()` |
| Load/modify recipes | `core/recipe_loader.py` | `RecipeLoader.get_all_recipes()` |
| Render SQL templates | `core/sql_template_engine.py` | `SQLTemplateEngine.render()` |
| Change LLM API calls | `services/gemini_service.py` | `GeminiService.generate_content()` |
| Schema chatbot Q&A | `services/schema_chatbot.py` | `SchemaChatbot.ask()` |
| Parse CSV data | `utils/parsers.py` | `robust_csv_parser()` |
| Create charts | `utils/visualization.py` | `create_bar_chart()`, `render_chart_from_recipe()` |
| Manage session state | `utils/session_state.py` | `initialize_report_state()`, `clear_report_state()` |

---

## Critical Information

### 🔴 Databricks Date Field Bug

**Problem**: `birthday` and `res_treat_start_date` are CHAR fields with 'YYYYMMDD' string format, NOT DATE type.

**Wrong SQL** (causes CAST_INVALID_INPUT error):
```sql
YEAR(birthday)  -- ❌ Fails
CAST(res_treat_start_date AS DATE)  -- ❌ Fails
```

**Correct SQL**:
```sql
YEAR(TO_DATE(birthday, 'yyyyMMdd'))  -- ✅ Age
YEAR(CURRENT_DATE) - YEAR(TO_DATE(birthday, 'yyyyMMdd'))  -- ✅ Age calculation
TO_DATE(res_treat_start_date, 'yyyyMMdd') >= DATE_SUB(CURRENT_DATE, 365)  -- ✅ Date filter
```

**Where to fix**:
- `app.py` line 89-95: LLM prompt for Home tab report generation
- `pipelines/nl2sql_generator.py` line 257: Schema description for `birthday`
- `pipelines/nl2sql_generator.py` line 150-167: Few-shot example #5

---

## Key Classes & APIs

### `app.py` (app:324)

**Purpose**: Streamlit entry point + sidebar + tab orchestration

**Key Functions**:
```python
@st.cache_data
def load_recipes() -> List[Dict[str, Any]]
    # Loads 42 recipes using RecipeLoader

def get_report_structure_with_llm(
    user_query: str,
    all_recipes: List[Dict[str, Any]],
    mandatory_recipes: Optional[List[str]] = None
) -> Optional[Dict[str, Any]]
    # Gemini API call to generate report structure
    # Returns: {"report_title", "executive_summary", "table_of_contents", "pages": [...]}
```

**Imports**: features, core, services, utils

---


### `features/disease_pipeline_tab.py` (disease_pipeline_tab:269)

**Purpose**: Tab 1 UI - Disease pipeline with 5-step workflow

```python
class DiseasePipelineTab:
    def __init__(self, recipe_dir: str = "recipes")

    def render() -> None
        # Orchestrates 5 steps:
        # Step 1: Disease input
        # Step 2: Execute 4 core recipes + get 7 LLM recommendations
        # Step 3: Display recommendations with checkboxes
        # Step 4: Natural language refinement (optional)
        # Step 5: Final execution of approved recipes

    def _render_disease_input() -> None
    def _render_analysis_button() -> None
    def _render_core_results() -> None
    def _render_recommendations(pipeline) -> None
    def _render_nl_refinement(pipeline) -> None
    def _render_final_execution(pipeline) -> None
    def _render_final_results() -> None
```

**Session State Keys**:
- `pipeline_core_results`
- `pipeline_recommended`
- `pipeline_disease_name`
- `pipeline_checkboxes` (Dict[recipe_name, bool])
- `pipeline_final_results`
- `pipeline_success_rate`

**Dependencies**: pipelines.disease_pipeline.DiseaseAnalysisPipeline

---

### `features/nl2sql_tab.py` (nl2sql_tab:520)

**Purpose**: Tab 2 UI - NL2SQL with real-time execution & history

```python
class NL2SQLTab:
    def __init__(self)

    def render() -> None
        # 2-column layout: Main area (3/4) + History sidebar (1/4)
        # User input → Generate → Execute → Visualize → Save to history

    def _render_input_section() -> None
        # Text area + example queries dropdown

    def _process_generation(user_query: str) -> None
        # Calls NL2SQLGenerator.generate_sql()
        # Auto-saves to query history (Phase 19)

    def _render_success_result(result, user_query: str) -> None
        # SQL display, quality metrics, validation, download

    def _render_action_buttons(sql_query: str) -> None
        # [Download SQL] [▶️ Execute Query] buttons
        # Updates query history with execution results (Phase 19)

    def _execute_query(sql_query: str) -> None
        # Calls DatabricksClient.execute_query() (Phase 12)
        # Stores results in session state

    def _render_execution_results() -> None
        # DataFrame display + ChartBuilder (Phase 13)
        # Auto chart recommendation (Phase 18)

    def _render_history_sidebar() -> None
        # Recent queries + Favorites tabs (Phase 19)
        # Statistics display

    @staticmethod
    def _validate_databricks_sql(sql: str) -> dict
        # Returns: {"issues": [...], "warnings": [...]}
        # Checks: deleted=FALSE, TO_DATE usage, REGEXP vs RLIKE

    def _render_error_result(result) -> None
        # Shows error + troubleshooting guide
```

**Dependencies**:
- pipelines.nl2sql_generator.NL2SQLGenerator
- services.databricks_client.DatabricksClient (Phase 12)
- components.chart_builder.ChartBuilder (Phase 13)
- utils.query_history.QueryHistory (Phase 19)

---

### `pipelines/disease_pipeline.py` (disease_pipeline:498)

**Purpose**: Disease analysis orchestration

```python
class DiseaseAnalysisPipeline:
    CORE_RECIPES = [
        "get_patient_count_by_disease_keyword",
        "get_demographic_distribution_by_disease",
        "analyze_screened_regional_distribution",
        "get_top_prescribed_ingredients_by_disease"
    ]

    def __init__(self, recipe_dir: str = "recipes")
        self.recipe_loader = RecipeLoader(recipes_dir=recipe_dir)
        self.template_engine = SQLTemplateEngine()
        self.gemini_service = GeminiService()

    def execute_core_recipes(disease_name: str) -> List[Dict]
        # Executes 4 core recipes, returns results with SQL

    def recommend_additional_recipes(
        disease_name: str,
        target_count: int = 7
    ) -> List[str]
        # LLM call to recommend recipes based on disease

    def refine_recommendations_with_nl(
        disease_name: str,
        current_recipes: List[str],
        feedback: str
    ) -> List[str]
        # LLM call to adjust recommendations based on user feedback

    def execute_approved_recipes(
        disease_name: str,
        recipe_names: List[str]
    ) -> List[Dict]
        # Executes user-approved recipes
```

**Dependencies**: core.{RecipeLoader, SQLTemplateEngine}, services.GeminiService

---

### `pipelines/nl2sql_generator.py` (nl2sql_generator:392)

**Purpose**: Natural language to SQL with RAG pattern

```python
class NL2SQLGenerator:
    def __init__(self, schema_file: str = "notion_columns_improved.csv")
        self.schema_df = pd.read_csv(schema_file)
        self.gemini_service = GeminiService()
        self.few_shot_examples = [...]  # 5 examples

    def generate_sql(question: str) -> NL2SQLResult
        # Main API: question → SQL
        # Steps:
        # 1. Extract relevant schema
        # 2. Select relevant few-shot examples
        # 3. Build prompt with schema + examples
        # 4. Call Gemini API
        # 5. Parse response
        # Returns: NL2SQLResult(success, sql_query, analysis, relevant_examples, error_message)

    def _get_relevant_schema(question: str) -> pd.DataFrame
    def _select_relevant_examples(question: str) -> List[Dict]
    def _build_prompt(question: str, schema: pd.DataFrame, examples: List) -> str
    def _parse_llm_response(response_text: str) -> Dict
```

**Important**: Few-shot example #5 (line 150-167) shows correct date handling with TO_DATE()

**Dependencies**: services.GeminiService

---

### `core/recipe_loader.py` (recipe_loader:60)

**Purpose**: Load 42 recipes from YAML files

```python
class RecipeLoader:
    def __init__(self, recipes_dir: str = "recipes")
        self.recipes_dir = Path(recipes_dir)
        self.recipe_metadata = {}  # Dict[recipe_name, recipe_info]
        self.all_recipes = []  # List[recipe_info]
        self._load_recipe_metadata()

    def _load_recipe_metadata() -> None
        # Scans recipes/pool/ and recipes/profile/
        # Loads *.yaml files

    def get_recipe_by_name(recipe_name: str) -> Optional[Dict]
    def get_all_recipes() -> List[Dict]
```

**Recipe Info Structure**:
```python
{
    'name': str,
    'description': str,
    'category': str,  # 'pool' or 'profile'
    'tags': List[str],
    'parameters': List[Dict],  # [{'name', 'type', 'description', 'required'}]
    'visualization': Dict,  # {'chart_type', 'x_column', 'y_column', 'title'}
    'sql_file_path': str,  # Path to .sql file (for backward compat)
    'sql_path': str,  # Same as sql_file_path
    'path': str  # Path to .yaml file
}
```

---

### `core/sql_template_engine.py` (sql_template_engine:50)

**Purpose**: Jinja2 SQL rendering with special placeholders

```python
class SQLTemplateEngine:
    @staticmethod
    def render(sql_template: str, params: Dict[str, Any]) -> str
        # Handles special placeholders:
        # [DEFAULT_3_YEARS_AGO] → date.today() - 3 years
        # [CURRENT_DATE] → date.today()
        # [NOT_FOUND] → None
        # [DEFAULT_*] → extract * as value
```

**Note**: `utils/formatters.py` has duplicate function `fill_sql_parameters()` - consider consolidating.

---

### `services/gemini_service.py` (gemini_service:72)

**Purpose**: Singleton Gemini API client

```python
class GeminiService:
    _instance = None  # Singleton

    def __new__(cls, model_name: str = 'gemini-2.5-flash')
        # Returns existing instance if exists

    def __init__(self, model_name: str = 'gemini-2.5-flash')
        if self._initialized:
            return
        self._load_api_key()  # From config.yaml
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        self._initialized = True

    def generate_content(prompt: str, **kwargs)
        # Returns: genai.GenerateContentResponse
```

**Config**: Loads from `config.yaml` → `api_keys.gemini_api_key`

---

### `services/parameter_extractor.py` (parameter_extractor:59)

**Purpose**: Parse LLM JSON responses

```python
def extract_json_from_llm_response(response_text: str) -> Dict
    # Removes ```json markers, parses JSON

def validate_recipe_parameters(recipe: Dict, params: Dict) -> bool
    # Validates extracted params against recipe schema
```

---

### `components/chart_builder.py` (chart_builder:518) - Phase 13

**Purpose**: Professional chart building with 8 types and 7 color palettes

```python
class ChartBuilder:
    def __init__(self, df: pd.DataFrame, config: Optional[Dict] = None)
        self.df = df
        self.config = config or {}

    def render() -> None
        # Main entry point
        # 1. Auto-recommend chart type (Phase 18)
        # 2. Display recommendation info
        # 3. Render chart config UI
        # 4. Create and display chart
        # 5. Show export buttons

    def _render_chart_config(recommendation: Optional[Dict]) -> Dict
        # Chart type selectbox (8 options)
        # X/Y/Color column selectors
        # Color scheme selector (7 palettes)
        # Chart title input
        # Returns config dict

    def _render_chart(config: Dict) -> None
        # Dispatches to specific chart method based on config['chart_type']

    # 8 Chart Creation Methods:
    def _create_bar_chart(config: Dict) -> go.Figure
    def _create_line_chart(config: Dict) -> go.Figure
    def _create_scatter_chart(config: Dict) -> go.Figure
    def _create_line_scatter_chart(config: Dict) -> go.Figure
    def _create_pie_chart(config: Dict) -> go.Figure
    def _create_area_chart(config: Dict) -> go.Figure
    def _create_box_chart(config: Dict) -> go.Figure
    def _create_histogram(config: Dict) -> go.Figure

    def _apply_professional_layout(fig: go.Figure, config: Dict) -> go.Figure
        # Applies professional styling:
        # - Font: Arial 12px/16px
        # - Grid: #e0e0e0 with mirrored borders
        # - Height: 600px
        # - Margins: 80px padding

    def _get_color_sequence(color_scheme: str) -> List[str]
        # Returns color palette for 7 schemes:
        # clinical, nature, science, colorblind, blue_gradient, professional, default

    def _render_export_buttons(fig: go.Figure) -> None
        # PNG (1920x1080 @2x), SVG, HTML export
```

**7 Color Palettes**:
- **clinical**: #2E86AB, #A23B72, #F18F01, #C73E1D, #6A994E, #BC4B51
- **nature**: #E64B35, #4DBBD5, #00A087, #3C5488, #F39B7F, #8491B4
- **science**: #3B4992, #EE0000, #008B45, #631879, #008280, #BB0021
- **colorblind**: Okabe-Ito palette (#E69F00, #56B4E9, #009E73...)
- **blue_gradient**: #08519c → #deebf7
- **professional**: Plotly professional palette
- **default**: Plotly default colors

---

### `utils/query_history.py` (query_history:361) - Phase 19

**Purpose**: Persistent query history storage with favorites

```python
@dataclass
class QueryRecord:
    id: str
    timestamp: str
    user_query: str
    sql_query: str
    success: bool
    is_favorite: bool = False
    executed: bool = False
    execution_success: Optional[bool] = None
    row_count: Optional[int] = None
    execution_time: Optional[float] = None
    tags: List[str] = field(default_factory=list)
    notes: str = ""

class QueryHistory:
    def __init__(self, storage_file: str = "data/query_history.json")
        self.storage_file = storage_file
        self.queries: List[QueryRecord] = []
        self._load_from_file()

    def add_query(user_query: str, sql_query: str, success: bool) -> str
        # Adds new query with duplicate prevention
        # Returns: query ID

    def update_execution_result(
        query_id: str,
        execution_success: bool,
        row_count: Optional[int] = None,
        execution_time: Optional[float] = None
    ) -> None
        # Updates query with execution results

    def toggle_favorite(query_id: str) -> None
        # Toggles favorite status

    def get_recent(limit: int = 10) -> List[QueryRecord]
        # Returns recent queries (newest first)

    def get_favorites() -> List[QueryRecord]
        # Returns favorited queries only

    def search(keyword: str) -> List[QueryRecord]
        # Searches in user_query and sql_query

    def get_statistics() -> Dict[str, Any]
        # Returns: {total_queries, total_favorites, success_rate, avg_execution_time}

    def delete_query(query_id: str) -> None
        # Removes query from history

    def export_to_sql_file(query_ids: List[str], output_path: str) -> None
        # Exports selected queries to SQL file
```

**Storage**: JSON file at `data/query_history.json` with UTF-8 encoding

---

### `utils/chart_recommender.py` (chart_recommender:346) - Phase 18

**Purpose**: Automatic chart type recommendation based on data analysis

```python
class ChartRecommender:
    def __init__(self, df: pd.DataFrame)
        self.df = df
        self.column_info = {}  # Analyzed column metadata

    def recommend() -> Dict[str, Any]
        # Main API
        # Returns: {
        #     'chart_type': str,
        #     'x_column': str,
        #     'y_column': str,
        #     'color_column': Optional[str],
        #     'reason': str,
        #     'confidence': float,
        #     'alternatives': List[str]
        # }

    def _analyze_columns() -> Dict[str, Dict]
        # Analyzes each column:
        # - dtype, unique_count, null_ratio
        # - is_numeric, is_categorical
        # - cardinality: binary/low/medium/high
        # - For numeric: mean, std

    def _recommend_by_pattern() -> Dict
        # Pattern matching:
        # 1 column: histogram or bar/pie
        # 2 columns: categorical+numeric → pie/bar, numeric+numeric → scatter
        # 3+ columns: bar with optional color grouping
```

**Cardinality Levels**:
- Binary: unique_count = 2
- Low: unique_count ≤ 10
- Medium: 10 < unique_count ≤ 50
- High: unique_count > 50

---

### `services/databricks_client.py` (databricks_client:315) - Phase 12

**Purpose**: Singleton client for Databricks SQL Warehouse

```python
class DatabricksClient:
    _instance = None  # Singleton

    def __new__(cls, config_source: str = "config")
        # Returns existing instance if exists

    def __init__(self, config_source: str = "config")
        if self._initialized:
            return
        self._load_config()  # From config.yaml or env vars
        self._initialized = True

    def execute_query(
        sql_query: str,
        max_rows: int = 10000
    ) -> Dict[str, Any]
        # Returns: {
        #     'success': bool,
        #     'data': pd.DataFrame or None,
        #     'row_count': int,
        #     'execution_time': float,
        #     'error_message': str or None
        # }

    def test_connection() -> bool
        # Quick health check with SELECT 1

    def get_table_preview(table_name: str, limit: int = 10) -> Dict
        # Convenience method for exploring tables
```

**Configuration** (2 methods):
1. `config.yaml`:
```yaml
databricks:
  server_hostname: "adb-xxx.azuredatabricks.net"
  http_path: "/sql/1.0/warehouses/abc123"
  access_token: "dapi1234567890abcdef"
```

2. Environment variables:
```bash
export DATABRICKS_SERVER_HOSTNAME="adb-xxx.azuredatabricks.net"
export DATABRICKS_HTTP_PATH="/sql/1.0/warehouses/abc123"
export DATABRICKS_TOKEN="dapi1234567890abcdef"
```

**Important**: SSL verification disabled with `_tls_no_verify=True` for development

---

### `services/schema_chatbot.py` (schema_chatbot:152) - Phase 11

**Purpose**: Schema Q&A chatbot with RAG pattern

```python
class SchemaChatbot:
    def __init__(self)
        self.schema_loader = SchemaLoader()
        self.gemini_service = GeminiService()
        self.prompt_loader = PromptLoader()

    def ask(
        user_question: str,
        conversation_history: Optional[List[Dict]] = None
    ) -> Dict[str, Any]
        # Main API
        # Steps:
        # 1. RAG retrieves top-20 relevant schema entries
        # 2. Build prompt with schema + history
        # 3. LLM generates answer
        # Returns: {
        #     'answer': str,
        #     'retrieved_tables': List[str],
        #     'retrieved_columns': List[Dict],
        #     'confidence': str
        # }

    def _extract_metadata(schema_df: pd.DataFrame) -> Tuple
        # Extracts unique tables and column details
```

**Example Questions**:
- "basic_treatment 테이블 구조는?"
- "환자 나이는 어디에 있어?"
- "deleted 컬럼은 어떻게 사용하나요?"

---

### `utils/visualization.py` (visualization:131)

**Purpose**: Plotly chart builders (legacy, use ChartBuilder for new code)

```python
def create_bar_chart(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    title: str = ""
) -> go.Figure

def create_line_chart(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    title: str = ""
) -> go.Figure

def render_chart_from_recipe(df: pd.DataFrame, recipe: Dict) -> None
    # Reads recipe['visualization']
    # Renders: bar_chart, line_chart, metric, or table (default)
    # Uses streamlit (st.plotly_chart, st.metric, st.dataframe)
```

**Note**: For new chart requirements, prefer `components/chart_builder.py` (Phase 13)

---

### `utils/session_state.py` (session_state:19)

**Purpose**: Streamlit session state helpers

```python
def initialize_report_state() -> None
    # Sets st.session_state.report_structure = None if not exists

def clear_report_state() -> None
    # Clears report_structure and all dataframe_* keys
```

---

## Data Files

### `recipes/` (42 recipes = 84 files)

**Structure**:
```
recipes/
├── pool/ (10 recipes)
│   ├── get_patient_count_by_disease_keyword.yaml + .sql
│   ├── screen_patients_by_age_group.yaml + .sql
│   └── ...
└── profile/ (32 recipes)
    ├── get_demographic_distribution_by_disease.yaml + .sql
    ├── get_top_prescribed_ingredients_by_disease.yaml + .sql
    └── ...
```

**YAML Format**:
```yaml
name: recipe_name
description: "What this recipe does"
category: pool  # or profile
tags: [tag1, tag2]
parameters:
  - name: disease_keyword
    type: string
    description: "Disease name to search"
    required: true
visualization:
  chart_type: bar_chart  # or line_chart, metric
  x_column: disease_name
  y_column: patient_count
  title: "Patient Count by Disease"
```

---

### `notion_columns_improved.csv`

**Purpose**: Database schema dictionary (Korean)
- Used by NL2SQL generator for schema-aware SQL generation
- Columns: table_name, column_name, description, keywords

---

### `config.yaml`

**Required**:
```yaml
api_keys:
  gemini_api_key: "YOUR_API_KEY_HERE"
```

**Used by**: `services/gemini_service.py`

---

## Common Patterns

### Adding a New Tab
1. Create `features/new_tab.py`:
```python
class NewTab:
    def __init__(self):
        pass

    def render(self):
        st.header("New Tab")
```

2. Import in `app.py`:
```python
from features.new_tab import NewTab
```

3. Add to main_tabs:
```python
with main_tabs[3]:
    new_tab = NewTab()
    new_tab.render()
```

---

### Adding a New Recipe
1. Create `recipes/pool/my_recipe.yaml`:
```yaml
name: my_recipe
description: "Does something useful"
category: pool
parameters:
  - name: param1
    type: string
    required: true
visualization:
  chart_type: bar_chart
  x_column: col1
  y_column: col2
```

2. Create `recipes/pool/my_recipe.sql`:
```sql
SELECT {{ param1 }} FROM table WHERE condition;
```

3. Restart app - RecipeLoader auto-discovers new recipes

---

### Calling Gemini API
```python
from services.gemini_service import GeminiService

service = GeminiService()  # Singleton
response = service.generate_content(prompt="Your prompt here")
result_text = response.text
```

---

### Rendering SQL Template
```python
from core.sql_template_engine import SQLTemplateEngine

sql = SQLTemplateEngine.render(
    sql_template="SELECT * FROM table WHERE disease = {{disease_name}}",
    params={"disease_name": "고혈압"}
)
```

---

## Troubleshooting Guide

### Import Error: "No module named 'features'"
**Cause**: Running from wrong directory
**Fix**: `cd /Users/park/clinical_report_generator && streamlit run app.py`

---

### Recipe Not Found
**Cause**: Recipe YAML missing or malformed
**Fix**: Check `recipes/pool/` or `recipes/profile/` for .yaml file

---

### CAST_INVALID_INPUT Error
**Cause**: Wrong date field handling (see Critical Information section)
**Fix**: Use `TO_DATE(field, 'yyyyMMdd')` not `CAST(field AS DATE)`

---

### Gemini API Error
**Cause**: Missing or invalid API key
**Fix**: Check `config.yaml` has correct `api_keys.gemini_api_key`

---

## Development Workflow

### Testing Locally
```bash
streamlit run app.py
# Access at http://localhost:8501
```

### Checking Imports
```bash
python3 -c "from features import HomeTab; print('OK')"
```

### Viewing Logs
- Streamlit shows errors in browser
- RecipeLoader prints "Loading recipe metadata..." and "✅ Loaded X recipes"

---

## For More Information

- **Development History**: See `DEVLOG.md` for Phase 1-7 timeline
- **Architecture Decisions**: Phase 7 refactoring rationale in `DEVLOG.md`
- **Bug Fixes**: Date handling fixes documented in `DEVLOG.md`
