import streamlit as st
import os
import re
import io
import yaml
import pandas as pd
import json
import google.generativeai as genai
from datetime import date, timedelta
from jinja2 import Template

# Import clinical trial agent
try:
    from clinical_trial_agent import ClinicalTrialAgent
    CLINICAL_TRIAL_AVAILABLE = True
except ImportError:
    CLINICAL_TRIAL_AVAILABLE = False

# Import queryable criteria analyzer
try:
    from queryable_criteria_analyzer import QueryableCriteriaAnalyzer, QueryabilityLevel
    QUERYABLE_CRITERIA_AVAILABLE = True
except ImportError:
    QUERYABLE_CRITERIA_AVAILABLE = False

# --- 1. Helper Functions ---

def parse_criteria_text(full_text):
    """
    전체 텍스트에서 선정기준과 제외기준을 추출하는 함수
    """
    import re

    # 텍스트를 줄별로 분리
    lines = full_text.split('\n')

    inclusion_lines = []
    exclusion_lines = []
    current_section = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 선정기준 섹션 시작 감지
        if re.search(r'(선정|포함|inclusion).*기준', line, re.IGNORECASE):
            current_section = 'inclusion'
            continue
        # 제외기준 섹션 시작 감지
        elif re.search(r'(제외|exclusion).*기준', line, re.IGNORECASE):
            current_section = 'exclusion'
            continue
        # 임상시험명이나 기타 헤더 스킵
        elif re.search(r'(임상시험|연구|제목|title)', line, re.IGNORECASE):
            current_section = None
            continue

        # 현재 섹션에 따라 라인 추가
        if current_section == 'inclusion':
            # 번호나 불릿 포인트 제거
            clean_line = re.sub(r'^[\d\.\-\*\•\s]+', '', line)
            if clean_line:
                inclusion_lines.append(clean_line)
        elif current_section == 'exclusion':
            # 번호나 불릿 포인트 제거
            clean_line = re.sub(r'^[\d\.\-\*\•\s]+', '', line)
            if clean_line:
                exclusion_lines.append(clean_line)

    # 결과 조합
    inclusion_text = '\n'.join(inclusion_lines) if inclusion_lines else "선정기준이 명시되지 않음"
    exclusion_text = '\n'.join(exclusion_lines) if exclusion_lines else "제외기준이 명시되지 않음"

    return inclusion_text, exclusion_text

@st.cache_data
def load_recipes():
    """Load all recipe YAML files from the recipes directory."""
    recipe_dir = "recipes"
    recipes = []
    if not os.path.exists(recipe_dir):
        st.error(f"Recipe directory '{recipe_dir}' not found.")
        return recipes
        
    for subdir, _, files in os.walk(recipe_dir):
        for file in files:
            if file.endswith(".yaml"):
                file_path = os.path.join(subdir, file)
                with open(file_path, "r", encoding="utf-8") as f:
                    try:
                        recipe = yaml.safe_load(f)
                        if recipe and 'name' in recipe:
                            recipe['sql_file_path'] = file_path.replace(".yaml", ".sql")
                            recipes.append(recipe)
                    except yaml.YAMLError as e:
                        st.error(f"Error loading YAML file {file_path}: {e}")
    return recipes

@st.cache_data
def load_data_dictionary():
    """Load the data dictionary CSV file."""
    dict_path = "notion_columns_improved.csv"
    if os.path.exists(dict_path):
        return pd.read_csv(dict_path)
    return None

def get_sql_from_recipe(recipe):
    """Get the SQL query content from a recipe's SQL file."""
    try:
        with open(recipe['sql_file_path'], "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return f"Error: SQL file not found at {recipe['sql_file_path']}"
    except Exception as e:
        return f"An error occurred: {e}"

def fill_sql_parameters(sql_template, params):
    """Renders the SQL template using Jinja2 to handle complex logic and special placeholders."""
    render_params = (params or {}).copy()

    for key, value in render_params.items():
        if isinstance(value, str):
            if value == '[DEFAULT_3_YEARS_AGO]':
                three_years_ago = date.today() - timedelta(days=3*365)
                render_params[key] = three_years_ago.strftime('%Y-%m-%d')
            elif value == '[CURRENT_DATE]':
                render_params[key] = date.today().strftime('%Y-%m-%d')
            elif value == '[NOT_FOUND]':
                render_params[key] = None
            else:
                match = re.match(r'\[DEFAULT_(\w+)\]', value)
                if match:
                    render_params[key] = match.group(1)

    try:
        template = Template(sql_template)
        return template.render(render_params)
    except Exception as e:
        return f"Error rendering Jinja2 template: {e}"

def get_report_structure_with_llm(user_query, all_recipes, mandatory_recipes=None):
    """Generate a report structure and extract parameters using the LLM."""
    try:
        with open("config.yaml", "r") as f:
            config = yaml.safe_load(f)
            api_key = config.get("api_keys", {}).get("gemini_api_key")

        if not api_key or api_key == "YOUR_GEMINI_API_KEY_HERE":
            st.error("Gemini API key is not configured. Please set it in `config.yaml`.")
            return None

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')

        recipe_details = []
        for r in all_recipes:
            param_info = ", ".join([p['name'] for p in r.get('parameters', [])])
            recipe_details.append(
                f"- Recipe Name: {r.get('name')}\n  Description: {r.get('description')}\n  Category: {r.get('category')}\n  Parameters: [{param_info}]"
            )
        recipe_info_for_prompt = "\n".join(recipe_details)

        mandatory_recipes_prompt_part = ""
        if mandatory_recipes:
            mandatory_recipes_list = "\n".join([f"- {r}" for r in mandatory_recipes])
            mandatory_recipes_prompt_part = f"""
        IMPORTANT: The user has explicitly requested that the following recipes MUST be included in the report. Please build your narrative and report structure around them, while also selecting other relevant recipes to complete the story.
        ---
        MANDATORY RECIPES:
        {mandatory_recipes_list}
        ---
        """

        prompt = f"""You are a seasoned consultant for pharmaceutical companies, specializing in clinical data analysis and market strategy. Your task is to create a comprehensive report outline based on a user's request, tailored for a pharmaceutical company's drug development pipeline (e.g., market analysis, patient segmentation, clinical trial feasibility).

        {mandatory_recipes_prompt_part}

        IMPORTANT CONTEXT: The data must be filtered by the disease NAME (e.g., '고혈압') in the 'res_disease_name' column, NOT by disease code. The queries will be run on a Databricks environment.

        Based on the user's query: '{user_query}'

        And the following available analysis recipes:
        ---
        {recipe_info_for_prompt}
        ---

        Perform the following tasks:
        1.  **Analyze User Intent:** Determine if the user wants a "Feasibility Report" for clinical trial recruitment or a "Market Landscape Report" for a drug pipeline.
        2.  **Create a Narrative:** Based on the intent, devise a logical narrative for the strategic report.
        3.  **Select Recipes:** Choose a sequence of 3 to 5 recipes that best fit this narrative. If mandatory recipes are provided, you must use them.
        4.  **Extract Parameters:** For each recipe, extract parameters from the user's query. Use placeholders like '[NOT_FOUND]', '[DEFAULT_3_YEARS_AGO]', '[CURRENT_DATE]', or '[DEFAULT_50]' if a value isn't present.
        5.  **Generate Report Components:** Write a professional report title, a concise executive summary explaining the report's purpose, a table of contents, and a 'rationale' for each page explaining why that analysis is important for the strategic goal.

        Your output MUST be a single JSON object. Here are two examples of the expected output structure based on the user's intent.

        ---
        **EXAMPLE 1: Feasibility Report**
        - User Query: "천식을 동반한 다년성 알레르기 비염 환자 대상 DW1807 3상 임상시험 환자 모집 타당성 분석"
        - Your JSON Output:
        ```json
        {{
            "report_title": "DW1807 임상시험 환자 모집 타당성 분석",
            "executive_summary": "본 보고서는 '천식을 동반한 다년성 알레르기 비염' 환자 대상 DW1807 3상 임상시험의 환자 모집 타당성을 분석합니다. 목표 모집 인원 200명에 대해, 현재 보유한 RWD 데이터를 기반으로 예상 모집 성공률 및 소요 기간을 예측하여 임상시험의 성공 가능성을 평가하는 것을 목적으로 합니다.",
            "table_of_contents": [
                "1. 모집 성공률 및 소요 기간 예측",
                "2. 환자군 상세 프로파일 분석",
                "3. 주요 동반 질환 분석",
                "4. 경쟁 및 기존 처방 약물 현황"
            ],
            "pages": [
                {{
                    "title": "1. 모집 성공률 및 소요 기간 예측",
                    "rationale": "전체 환자 풀에서부터 주요 포함/제외 기준을 적용하여 최종 모집 가능한 환자 수를 예측하고, 이를 통해 목표 인원 달성 가능성과 예상 소요 기간을 산출합니다.",
                    "recipe_name": "analyze_recruitment_feasibility",
                    "parameters": {{"disease_name_keyword": "알레르기 비염", "min_age": 19, "max_age": 75, "min_visits": 1, "target_enrollment": 200}}
                }},
                {{
                    "title": "2. 환자군 상세 프로파일 분석",
                    "rationale": "모집 대상 환자군의 인구통계학적 특성(성별, 연령) 및 지역적 분포를 파악하여, 리크루팅 전략 수립 시 타겟 대상을 명확히 합니다.",
                    "recipe_name": "get_demographic_distribution_by_disease",
                    "parameters": {{"disease_name_keyword": "알레르기 비염", "start_date": "[DEFAULT_3_YEARS_AGO]", "end_date": "[CURRENT_DATE]"}}
                }},
                {{
                    "title": "3. 주요 동반 질환 분석",
                    "rationale": "대상 환자군이 보유한 주요 동반 질환을 파악하여, 임상시험 진행 중 발생할 수 있는 잠재적 리스크를 관리하고, 복합적인 환자 특성을 이해합니다.",
                    "recipe_name": "get_top_comorbidities_for_cohort",
                    "parameters": {{"disease_name_keyword": "알레르기 비염", "start_date": "[DEFAULT_3_YEARS_AGO]", "end_date": "[CURRENT_DATE]", "top_n": 10}}
                }},
                {{
                    "title": "4. 경쟁 및 기존 처방 약물 현황",
                    "rationale": "현재 시장에서 처방되고 있는 주요 약물들을 파악하여, 대상 환자군의 기존 치료 패턴을 이해하고 임상시험 설계 시 대조군 설정 및 시장 진입 전략에 활용합니다.",
                    "recipe_name": "get_top_prescribed_ingredients_by_disease",
                    "parameters": {{"disease_name_keyword": "알레르기 비염", "start_date": "[DEFAULT_3_YEARS_AGO]", "end_date": "[CURRENT_DATE]", "top_n": 10}}
                }}
            ]
        }}
        ```
        ---
        **EXAMPLE 2: Market Landscape Report**
        - User Query: "원형탈모증 신약 시장성 분석"
        - Your JSON Output:
        ```json
        {{
            "report_title": "원형탈모증 시장 분석 및 환자 프로파일링",
            "executive_summary": "본 보고서는 신규 원형탈모증 치료제 개발을 위한 시장성 분석을 목적으로 합니다. RWD를 기반으로 국내 원형탈모증 시장의 규모를 추정하고, 환자 특성 및 주요 의료 이용 패턴을 분석하여, 성공적인 신약 개발 및 시장 진입 전략 수립을 위한 핵심 인사이트를 제공합니다.",
            "table_of_contents": [
                "1. 전체 시장 규모 분석",
                "2. 환자 인구통계학적 특성",
                "3. 주요 의료 이용 패턴 (병원 등급별)",
                "4. 주요 처방 약물 분석"
            ],
            "pages": [
                {{
                    "title": "1. 전체 시장 규모 분석",
                    "rationale": "국내 원형탈모증 환자의 전체 수를 파악하여 시장의 매력도를 평가하고, 잠재적 시장 규모를 예측합니다.",
                    "recipe_name": "get_patient_count_by_disease_keyword",
                    "parameters": {{"disease_keyword": "원형탈모증"}}
                }},
                {{
                    "title": "2. 환자 인구통계학적 특성",
                    "rationale": "주요 환자군의 성별 및 연령대 분포를 분석하여, 마케팅 및 개발 전략 수립 시 핵심 타겟이 될 인구통계학적 세그먼트를 식별합니다.",
                    "recipe_name": "get_demographic_distribution_by_disease",
                    "parameters": {{"disease_name_keyword": "원형탈모증", "start_date": "[DEFAULT_3_YEARS_AGO]", "end_date": "[CURRENT_DATE]"}}
                }},
                {{
                    "title": "3. 주요 의료 이용 패턴 (병원 등급별)",
                    "rationale": "환자들이 주로 이용하는 병원 등급(1, 2, 3차)을 분석하여, 제품 출시 후 영업 및 마케팅 채널 전략을 수립하는 데 활용합니다.",
                    "recipe_name": "analyze_visits_by_hospital_tier",
                    "parameters": {{"disease_keyword": "원형탈모증"}}
                }},
                {{
                    "title": "4. 주요 처방 약물 분석",
                    "rationale": "현재 시장의 표준 치료(Standard of Care)와 주요 경쟁 약물을 파악하여, 개발 중인 신약의 시장 내 포지셔닝 및 차별화 전략을 수립합니다.",
                    "recipe_name": "get_top_prescribed_ingredients_by_disease",
                    "parameters": {{"disease_name_keyword": "원형탈모증", "start_date": "[DEFAULT_3_YEARS_AGO]", "end_date": "[CURRENT_DATE]", "top_n": 10}}
                }}
            ]
        }}
        ```
        ---

        Ensure the recipe names and parameter names in your output *exactly* match the provided list. Now, generate the JSON for the user's query: '{user_query}'.
        """

        response = model.generate_content(prompt)
        cleaned_response_text = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(cleaned_response_text)

    except Exception as e:
        st.error(f"An error occurred while communicating with the LLM: {e}")
        return None

def robust_csv_parser(data_input):
    """Parses CSV-like data from a string or uploaded file using pandas' auto-detection."""
    if hasattr(data_input, 'getvalue'):
        text_data = data_input.getvalue().decode('utf-8')
    else:
        text_data = str(data_input)
    
    csv_file = io.StringIO(text_data)
    # Use sep=None and engine='python' to auto-detect separators
    df = pd.read_csv(csv_file, sep=None, engine='python')
    return df

# --- Main App Logic ---

st.set_page_config(page_title="Clinical Report Query Generator", layout="wide")
st.title("📑 Clinical Report Query Generator")
st.caption("AI-powered SQL generator for clinical data analysis...")

if 'report_structure' not in st.session_state:
    st.session_state.report_structure = None

with st.spinner("Loading recipes and data dictionary..."):
    all_recipes = load_recipes()
    recipe_dict = {recipe['name']: recipe for recipe in all_recipes if recipe}
    data_dictionary = load_data_dictionary()

if not all_recipes:
    st.stop()

# --- Sidebar ---
st.sidebar.header("User Input")
user_query = st.sidebar.text_area(
    "분석 리포트의 주제나 원하는 분석 흐름을 자유롭게 입력하세요. (예: \"20대 여성 비만 환자 프로파일링\" 또는 \"시장 규모를 먼저 보고, 다음으로 주요 처방 약물을 분석하는 보고서\")",
    height=100,
    key="user_query_input"
)

# --- New UI for mandatory recipes ---
st.sidebar.subheader("필수 포함 레시피 선택 (옵션)")
# Group full recipe objects by category
categorized_recipes = {}
for r in all_recipes:
    cat = r.get('category', 'Uncategorized')
    if cat not in categorized_recipes:
        categorized_recipes[cat] = []
    categorized_recipes[cat].append(r)

selected_recipes = []
# Sort categories for consistent order
for category in sorted(categorized_recipes.keys()):
    with st.sidebar.expander(f"카테고리: {category}", expanded=False):
        # Sort recipes within the category by name
        for recipe in sorted(categorized_recipes[category], key=lambda x: x['name']):
            recipe_name = recipe['name']
            recipe_desc = recipe.get('description', 'No description available.')
            # Use checkbox with description as label
            if st.checkbox(f"{recipe_name}: {recipe_desc}", key=f"checkbox_{recipe_name}"):
                selected_recipes.append(recipe_name)
# --- End of New UI ---

def clear_report_state():
    st.session_state.report_structure = None
    for key in list(st.session_state.keys()):
        if key.startswith('dataframe_') or key.startswith('csv_input_') or key.startswith('uploader_'):
            del st.session_state[key]

if st.sidebar.button("Generate Report", type="primary"):
    clear_report_state()
    if user_query:
        with st.spinner("AI is generating the report..."):
            # Pass selected_recipes to the LLM function
            st.session_state.report_structure = get_report_structure_with_llm(user_query, all_recipes, selected_recipes)
    else:
        st.warning("Please enter a topic for the report.")

if st.sidebar.button("Clear Report"):
    clear_report_state()

st.sidebar.divider()
if st.sidebar.toggle("Show Data Dictionary", False):
    st.subheader("Data Dictionary")
    if data_dictionary is not None:
        st.dataframe(data_dictionary)
    else:
        st.warning("Data dictionary file (`notion_columns_improved.csv`) not found.")

# --- Main Content ---
# Create main tabs
tab_names = ["📊 General Report", "🏥 Clinical Trial Screening"]
if not CLINICAL_TRIAL_AVAILABLE:
    tab_names = ["📊 General Report"]

main_tabs = st.tabs(tab_names)

# Tab 1: General Report (existing functionality)
with main_tabs[0]:
    if st.session_state.report_structure:
        report_structure = st.session_state.report_structure
        if "report_title" in report_structure and "pages" in report_structure:
            st.header(report_structure["report_title"])

            # Display Executive Summary and ToC
            if "executive_summary" in report_structure:
                st.subheader("Executive Summary")
                st.markdown(report_structure["executive_summary"])

            if "table_of_contents" in report_structure:
                st.subheader("Table of Contents")
                for item in report_structure["table_of_contents"]:
                    st.markdown(f"- {item}")

            st.divider()

            tab_titles = [page.get("title", f"Page {i+1}") for i, page in enumerate(report_structure["pages"])]
            tabs = st.tabs(tab_titles)

            for i, page in enumerate(report_structure["pages"]):
                with tabs[i]:
                    recipe_name = page.get("recipe_name")
                    recipe = recipe_dict.get(recipe_name)
                    llm_params = page.get("parameters", {})

                    if not recipe:
                        st.error(f"LLM recommended recipe '{recipe_name}', but it was not found.")
                        continue

                    # Display the rationale
                    if "rationale" in page:
                        st.info(f"**Rationale:** {page['rationale']}")

                    st.subheader(f"Recipe: `{recipe_name}`")
                    st.markdown(f"**Description:** {recipe.get('description', 'N/A')}")
                    st.json(llm_params)

                    st.subheader("Final SQL Query")
                    sql_template = get_sql_from_recipe(recipe)
                    final_sql = fill_sql_parameters(sql_template, llm_params)
                    st.code(final_sql, language="sql")

                    st.divider()
                    st.subheader("📊 Generate Visualization")
                    df_key = f"dataframe_{i}"

                    viz_tab1, viz_tab2 = st.tabs(["Paste Text", "Upload File"])

                    with viz_tab1:
                        csv_input_key = f"csv_input_{i}"
                        st.text_area("Paste CSV data...", height=150, key=csv_input_key)
                        if st.button("Generate from Text", key=f"text_button_{i}"):
                            csv_text = st.session_state.get(csv_input_key, "")
                            if csv_text:
                                try:
                                    df = robust_csv_parser(csv_text)
                                    st.session_state[df_key] = df
                                except Exception as e:
                                    st.error(f"Failed to parse CSV from text: {e}")
                                    if df_key in st.session_state: del st.session_state[df_key]
                            else:
                                st.warning("Please paste CSV data first.")

                    with viz_tab2:
                        upload_key = f"uploader_{i}"
                        uploaded_file = st.file_uploader("Upload CSV file...", type=["csv", "txt"], key=upload_key)
                        if uploaded_file is not None:
                            try:
                                df = robust_csv_parser(uploaded_file)
                                st.session_state[df_key] = df
                            except Exception as e:
                                st.error(f"Failed to parse CSV from file: {e}")
                                if df_key in st.session_state: del st.session_state[df_key]

                    if df_key in st.session_state:
                        df = st.session_state[df_key]
                        viz_info = recipe.get("visualization")

                        st.write("**Chart:**")
                        if viz_info:
                            chart_type = viz_info.get("chart_type")

                            try:
                                if chart_type == "bar_chart":
                                    x_col = viz_info.get("x_column")
                                    y_col = viz_info.get("y_column")
                                    st.bar_chart(df.set_index(x_col)[y_col])

                                elif chart_type == "metric":
                                    # For single-row dataframes, display each column as a metric
                                    if not df.empty:
                                        cols = st.columns(len(df.columns))
                                        for j, col_name in enumerate(df.columns):
                                            cols[j].metric(label=col_name, value=df.iloc[0][col_name])
                                    else:
                                        st.warning("Data is empty, cannot display metrics.")

                                else: # Default to table
                                    st.write("**Parsed Data Table:**")
                                    st.dataframe(df)

                            except Exception as e:
                                st.error(f"Failed to generate chart: {e}")
                                st.write("Displaying raw data instead:")
                                st.dataframe(df)
                        else:
                            st.write("No visualization info in recipe. Displaying raw data table.")
                            st.dataframe(df)

        else:
            st.error("Failed to generate a valid report structure from the LLM.")
    else:
        st.info("Enter a topic in the sidebar and click 'Generate Report' to begin.")

# Tab 2: Clinical Trial Screening (new functionality)
if CLINICAL_TRIAL_AVAILABLE and len(main_tabs) > 1:
    with main_tabs[1]:
        st.header("🏥 Clinical Trial Screening Automation")
        st.markdown("자연어 임상시험 조건을 입력하면 자동으로 적합한 SQL 쿼리를 생성합니다.")

        # Sub-tabs for different functionalities
        trial_sub_tabs = st.tabs(["🚀 스크리닝 실행", "🔍 기준 분석"])

        # Tab 1: Screening Execution (existing functionality)
        with trial_sub_tabs[0]:
            st.subheader("임상시험 조건 입력")
            col1, col2 = st.columns(2)
            with col1:
                trial_name = st.text_input(
                    "임상시험명",
                    value="고혈압 신약 임상시험",
                    help="분석할 임상시험의 이름을 입력하세요",
                    key="screening_trial_name"
                )
                inclusion_criteria = st.text_area(
                    "포함 기준 (Inclusion Criteria)",
                    value="""만 19세 이상 성인 남녀
Visit 1 기준 평균 좌위 수축기 혈압이 140-180 mmHg 범위
항고혈압제 복용 중인 경우, 시험자의 판단에 따라 치료 중단이 가능한 환자
여성 대상자의 경우 피임 조건 충족
시험 목적·내용 설명을 듣고 자발적 서면 동의를 한 환자""",
                    height=150,
                    help="환자가 임상시험에 참여하기 위한 포함 조건들을 입력하세요",
                    key="screening_inclusion_criteria"
                )
            with col2:
                exclusion_criteria = st.text_area(
                    "제외 기준 (Exclusion Criteria)",
                    value="""Visit 1 또는 Visit 2에서 MSSBP ≥ 180 mmHg 또는 MSDBP ≥ 110 mmHg
최근 5년 이내 악성종양 병력
최근 12개월 이내 심근경색 또는 뇌졸중 병력
임신부 또는 수유부
약물 또는 알코올 남용 병력
시험약 성분에 과민증 기왕력""",
                    height=150,
                    help="임상시험에서 제외되어야 할 조건들을 입력하세요",
                    key="screening_exclusion_criteria"
                )

                # Execution options
                dry_run = st.checkbox(
                    "Dry Run 모드 (SQL 생성만, 실행 안함)",
                    value=True,
                    help="체크하면 SQL 쿼리만 생성하고 실제 실행은 하지 않습니다",
                    key="screening_dry_run"
                )
                comprehensive_analysis = st.checkbox(
                    "종합 분석 모드 (기본 스크리닝 + LLM 기반 추가 분석)",
                    value=False,
                    help="체크하면 기본 스크리닝 후 LLM을 활용한 추가 분석을 수행합니다",
                    key="screening_comprehensive"
                )

            # Initialize clinical trial agent
            if 'clinical_agent' not in st.session_state:
                with st.spinner("임상시험 에이전트 초기화 중..."):
                    try:
                        st.session_state.clinical_agent = ClinicalTrialAgent()
                        st.success("✅ 임상시험 에이전트 준비 완료!")
                    except Exception as e:
                        st.error(f"임상시험 에이전트 초기화 실패: {e}")
                        st.stop()

        # Tab 2: Criteria Analysis (new functionality with file/text input)
        with trial_sub_tabs[1]:
            st.subheader("🔍 기준 쿼리 검증 가능성 분석")
            st.markdown("임상시험 기준 텍스트 전체를 입력하여 데이터브릭스로 검증 가능한지 분석합니다.")

            # Input method selection
            input_method = st.radio(
                "입력 방법 선택:",
                ["📝 직접 텍스트 입력", "📁 파일 업로드"],
                key="criteria_input_method"
            )
            if trial_name and inclusion_criteria and exclusion_criteria:
                spinner_text = f"임상시험 조건 분석 및 쿼리 생성 중... ({analysis_type})"
                with st.spinner(spinner_text):
                    try:
                        if comprehensive_analysis:
                            result = st.session_state.clinical_agent.run_comprehensive_clinical_analysis(
                                trial_name=trial_name,
                                inclusion_criteria=inclusion_criteria,
                                exclusion_criteria=exclusion_criteria,
                                dry_run=dry_run
                            )
                        else:
                            result = st.session_state.clinical_agent.run_clinical_trial_screening(
                                trial_name=trial_name,
                                inclusion_criteria=inclusion_criteria,
                                exclusion_criteria=exclusion_criteria,
                                dry_run=dry_run
                            )

                        st.success(f"✅ 임상시험 {analysis_type} 완료!")

                        # Handle comprehensive analysis vs basic screening results
                        if comprehensive_analysis:
                            # For comprehensive analysis
                            screening_result = result.get('screening_result', {})
                            execution_results = result.get('all_executed_recipes', [])
                            screening_success_rate = result.get('overall_success_rate', 0.0)

                            # Display LLM insights if available
                            if 'llm_insights' in result:
                                st.subheader("🤖 LLM 분석 인사이트")
                                insights = result['llm_insights']

                                if insights.get('clinical_significance'):
                                    st.info(f"**임상적 의미:** {insights['clinical_significance']}")

                                if insights.get('recommended_analyses'):
                                    st.write("**권장 추가 분석:**")
                                    for analysis in insights['recommended_analyses']:
                                        st.write(f"• {analysis}")

                                if insights.get('data_gaps'):
                                    st.warning("**데이터 부족 영역:**")
                                    for gap in insights['data_gaps']:
                                        st.write(f"• {gap}")

                                if insights.get('next_steps'):
                                    st.success(f"**다음 단계:** {insights['next_steps']}")

                                st.divider()
                        else:
                            # For basic screening
                            execution_results = result.get('execution_results', [])
                            screening_success_rate = result.get('success_rate', 0.0)

                        # Summary metrics
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("성공률", f"{screening_success_rate:.1%}")
                        with col2:
                            st.metric("실행된 레시피", f"{len(execution_results)}개")
                        with col3:
                            success_count = sum(1 for r in execution_results if r.success)
                            st.metric("성공한 레시피", f"{success_count}개")

                        st.divider()

                        # Detailed results
                        result_title = "📋 종합 분석 실행 결과" if comprehensive_analysis else "📋 기본 스크리닝 실행 결과"
                        st.subheader(result_title)

                        for i, exec_result in enumerate(execution_results, 1):
                            with st.expander(f"{i}. {exec_result.recipe_name} {'✅' if exec_result.success else '❌'}", expanded=True):
                                if exec_result.success:
                                    st.success("SQL 생성 성공")

                                    # SQL 쿼리 표시 (전체)
                                    if hasattr(exec_result, 'generated_sql') and exec_result.generated_sql:
                                        st.subheader("📝 생성된 SQL 쿼리")

                                        # SQL 길이 정보
                                        sql_length = len(exec_result.generated_sql)
                                        st.info(f"SQL 길이: {sql_length:,} 글자")

                                        # 전체 SQL 표시 (스크롤 가능)
                                        st.code(exec_result.generated_sql, language="sql", line_numbers=True)

                                        # 복사용 텍스트 영역 (선택사항)
                                        with st.expander("📋 복사용 SQL (전체 선택 가능)", expanded=False):
                                            st.text_area(
                                                "SQL 쿼리 (전체 선택 후 복사하세요)",
                                                value=exec_result.generated_sql,
                                                height=200,
                                                key=f"sql_copy_{i}",
                                                help="이 영역에서 전체 선택(Ctrl+A)후 복사(Ctrl+C)하세요"
                                            )

                                    # 파라미터 표시
                                    if hasattr(exec_result, 'parameters') and exec_result.parameters:
                                        st.subheader("⚙️ 사용된 파라미터")
                                        st.json(exec_result.parameters)

                                        # 파라미터 개수 정보
                                        param_count = len(exec_result.parameters)
                                        st.caption(f"총 {param_count}개 파라미터 사용됨")

                                else:
                                    st.error(f"실행 실패: {exec_result.error_message}")

                        # Show analyzed criteria
                        if 'analyzed_criteria' in result:
                            st.subheader("🔍 분석된 임상 조건")

                            criteria = result['analyzed_criteria']

                            col1, col2 = st.columns(2)
                            with col1:
                                st.write("**포함 조건:**")
                                for criterion in criteria.get('inclusion', []):
                                    st.write(f"• [{criterion.criteria_type.value}] {criterion.description[:100]}...")

                            with col2:
                                st.write("**제외 조건:**")
                                for criterion in criteria.get('exclusion', []):
                                    st.write(f"• [{criterion.criteria_type.value}] {criterion.description[:100]}...")

                    except Exception as e:
                        st.error(f"임상시험 스크리닝 실행 중 오류 발생: {e}")
                        st.exception(e)
            else:
                st.warning("모든 필드를 입력해주세요.")

        # Information section
        st.divider()
        st.subheader("ℹ️ 사용 방법")
        st.markdown("""
        1. **임상시험명**: 분석할 임상시험의 이름을 입력하세요
        2. **포함 기준**: 환자가 임상시험에 참여할 수 있는 조건들을 자연어로 입력하세요
        3. **제외 기준**: 임상시험에서 제외되어야 할 조건들을 자연어로 입력하세요
        4. **실행**: 시스템이 자동으로 조건을 분석하고 적합한 SQL 레시피를 선택하여 쿼리를 생성합니다

        **지원하는 조건 유형:**
        - 연령 조건 (예: "만 19세 이상", "18-65세")
        - 성별 조건 (예: "남녀", "여성")
        - 질환 조건 (예: "고혈압", "당뇨병")
        - 약물 조건 (예: "항고혈압제 복용", "인슐린 치료")
        - **생체징후** (예: "수축기 혈압 140-180 mmHg", "BMI 25 이상", "공복혈당 126mg/dL 이상")
        - 임신 관련 (예: "임신부", "수유부")

        **사용 가능한 생체징후 데이터:**
        - 혈압, 공복혈당, BMI, 콜레스테롤, 중성지방 등
        """)

        # Tab 2: Criteria Analysis (new functionality with file/text input)
        with trial_sub_tabs[1]:
            st.subheader("🔍 기준 쿼리 검증 가능성 분석")
            st.markdown("임상시험 기준 텍스트 전체를 입력하여 데이터브릭스로 검증 가능한지 분석합니다.")

            # Input method selection
            input_method = st.radio(
                "입력 방법 선택:",
                ["📝 직접 텍스트 입력", "📁 파일 업로드"],
                key="criteria_input_method"
            )

            # Input section
            trial_name_analysis = None
            full_criteria_text = None

            if input_method == "📝 직접 텍스트 입력":
                trial_name_analysis = st.text_input(
                    "임상시험명",
                    value="",
                    help="분석할 임상시험의 이름을 입력하세요",
                    key="analysis_trial_name"
                )

                full_criteria_text = st.text_area(
                    "임상시험 기준 전체 텍스트",
                    value="""임상시험명: 고혈압 신약 효능 평가 연구

선정기준:
1. 만 19세 이상 75세 이하의 성인 남녀
2. 고혈압 진단을 받고 현재 항고혈압제를 복용 중인 환자
3. 최근 6개월 이내 혈압이 140/90 mmHg 이상으로 측정된 환자
4. 연구 참여에 서면 동의한 환자
5. 연구 기간 중 지속적인 추적관찰이 가능한 환자

제외기준:
1. 임신 또는 수유 중인 여성
2. 심각한 간기능 또는 신기능 장애가 있는 환자
3. 최근 3개월 이내 심근경색이나 뇌졸중 병력이 있는 환자
4. 연구자가 부적합하다고 판단하는 환자
5. 다른 임상시험에 참여 중인 환자""",
                    height=300,
                    help="임상시험 기준 전체 텍스트를 입력하세요. 선정기준과 제외기준을 모두 포함해주세요.",
                    key="analysis_full_text"
                )

            elif input_method == "📁 파일 업로드":
                uploaded_file = st.file_uploader(
                    "임상시험 기준 파일 업로드",
                    type=["txt", "md", "docx"],
                    help="임상시험 기준이 포함된 텍스트 파일을 업로드하세요",
                    key="criteria_file_upload"
                )

                if uploaded_file is not None:
                    try:
                        # Read file content
                        if uploaded_file.type == "text/plain":
                            full_criteria_text = str(uploaded_file.read(), "utf-8")
                        else:
                            st.warning("현재는 .txt 파일만 지원합니다.")

                        # Extract trial name from filename or first line
                        trial_name_analysis = uploaded_file.name.replace('.txt', '').replace('.md', '')

                        # Show preview
                        st.text_area(
                            "업로드된 파일 내용 미리보기:",
                            value=full_criteria_text[:1000] + "..." if len(full_criteria_text) > 1000 else full_criteria_text,
                            height=200,
                            disabled=True,
                            key="file_preview"
                        )

                    except Exception as e:
                        st.error(f"파일 읽기 실패: {e}")

            # Analysis section
            if trial_name_analysis and full_criteria_text:
                col_analyze1, col_analyze2 = st.columns(2)

                with col_analyze1:
                    if QUERYABLE_CRITERIA_AVAILABLE:
                        if st.button("📊 기준 분석 실행", help="전체 텍스트에서 기준을 추출하고 검증 가능성을 분석합니다", key="criteria_analysis_button"):
                            with st.spinner("임상시험 기준 자동 추출 및 분석 중..."):
                                try:
                                    # Initialize analyzer
                                    if 'criteria_analyzer' not in st.session_state:
                                        st.session_state.criteria_analyzer = QueryableCriteriaAnalyzer()

                                    # Parse the full text to extract inclusion/exclusion criteria
                                    inclusion_text, exclusion_text = parse_criteria_text(full_criteria_text)

                                    # Analyze criteria
                                    analysis_result = st.session_state.criteria_analyzer.analyze_trial_criteria(
                                        trial_name=trial_name_analysis,
                                        inclusion_criteria=inclusion_text,
                                        exclusion_criteria=exclusion_text
                                    )

                                    # Store result in session state
                                    st.session_state.criteria_analysis_result = analysis_result

                                    st.success("✅ 기준 분석 완료!")

                                except Exception as e:
                                    st.error(f"❌ 기준 분석 실패: {e}")
                                    st.exception(e)
                    else:
                        st.warning("QueryableCriteriaAnalyzer를 사용할 수 없습니다. GEMINI_API_KEY를 확인해주세요.")

                with col_analyze2:
                    # Display analysis results if available
                    if hasattr(st.session_state, 'criteria_analysis_result'):
                        result = st.session_state.criteria_analysis_result

                        # Quick stats
                        total_criteria = result['total_criteria_count']
                        queryability_ratio = result['overall_queryability_ratio']

                        st.metric(
                            "쿼리 검증 가능률",
                            f"{queryability_ratio:.1%}",
                            f"{total_criteria}개 기준 중 {int(total_criteria * queryability_ratio)}개"
                        )

                        # Distribution
                        high_count = result['queryability_distribution']['HIGH']
                        medium_count = result['queryability_distribution']['MEDIUM']
                        low_count = result['queryability_distribution']['LOW']

                        st.write("**검증 가능성 분포:**")
                        st.write(f"🟢 HIGH: {high_count}개")
                        st.write(f"🟡 MEDIUM: {medium_count}개")
                        st.write(f"🔴 LOW: {low_count}개")
            else:
                st.info("임상시험명과 기준 텍스트를 입력하고 분석을 실행해주세요.")

            # Display detailed analysis results if available
            if hasattr(st.session_state, 'criteria_analysis_result'):
                st.divider()
                result = st.session_state.criteria_analysis_result

                # Show recommended recipes
                if result.get('recommended_recipes'):
                    st.subheader("🔧 권장 레시피")
                    for recipe in result['recommended_recipes'][:10]:  # Show top 10
                        st.write(f"• {recipe}")

                # Show queryable criteria details
                st.subheader("📋 상세 분석 결과")

                col1, col2 = st.columns(2)

                with col1:
                    st.write("**✅ 검증 가능한 기준들:**")
                    queryable_criteria = [c for c in result['inclusion_analysis'] + result['exclusion_analysis']
                                        if c.overall_queryability.value in ['HIGH', 'MEDIUM']]

                    for i, criteria in enumerate(queryable_criteria[:5], 1):  # Show top 5
                        with st.expander(f"{i}. [{criteria.overall_queryability.value}] {criteria.original_text[:50]}..."):
                            st.write(f"**원문:** {criteria.original_text}")
                            if criteria.queryable_parts:
                                st.write(f"**검증 가능 부분:** {', '.join(criteria.queryable_parts)}")
                            if criteria.suggested_query_approach:
                                st.write(f"**쿼리 접근법:** {criteria.suggested_query_approach}")

                with col2:
                    st.write("**❌ 검증 어려운 기준들:**")
                    non_queryable_criteria = [c for c in result['inclusion_analysis'] + result['exclusion_analysis']
                                            if c.overall_queryability.value == 'LOW']

                    for i, criteria in enumerate(non_queryable_criteria[:5], 1):  # Show top 5
                        with st.expander(f"{i}. {criteria.original_text[:50]}..."):
                            st.write(f"**원문:** {criteria.original_text}")
                            if criteria.non_queryable_parts:
                                st.write(f"**제약 사항:** {', '.join(criteria.non_queryable_parts)}")
                            if criteria.practical_notes:
                                st.write(f"**실무 고려사항:** {criteria.practical_notes}")

                # Report generation
                st.divider()
                if st.button("📄 분석 보고서 생성", type="secondary", key="generate_criteria_report"):
                    report = st.session_state.criteria_analyzer.generate_report(result)
                    st.subheader("📋 임상시험 기준 분석 보고서")
                    st.text(report)

else:
    if not CLINICAL_TRIAL_AVAILABLE:
        st.info("임상시험 스크리닝 기능을 사용하려면 clinical_trial_agent.py 파일이 필요합니다.")
