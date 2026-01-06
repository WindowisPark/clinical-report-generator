"""NL2SQL Tab - Natural language to SQL query generation with RAG"""

import streamlit as st
from typing import List, Optional
from pipelines.nl2sql_generator import NL2SQLGenerator
from services.databricks_client import DatabricksClient
import plotly.graph_objects as go
from components.chart_builder import ChartBuilder
from utils.query_history import QueryHistory


class NL2SQLTab:
    """Handles Tab 3: NL2SQL - AI-powered SQL code generation"""

    def __init__(self):
        """Initialize NL2SQL Tab"""
        self._initialize_generator()
        self._initialize_databricks_client()
        self._initialize_history()

    def _initialize_generator(self):
        """Initialize the NL2SQLGenerator if not already in session state"""
        # Version check: Force re-initialization if refine_sql method is missing
        GENERATOR_VERSION = "2.2"  # Fixed schema format method name

        needs_reinit = (
            'nl2sql_generator' not in st.session_state or
            st.session_state.get('nl2sql_generator_version') != GENERATOR_VERSION or
            not hasattr(st.session_state.nl2sql_generator, 'refine_sql')
        )

        if needs_reinit:
            with st.spinner("NL2SQL Generator 초기화 중..."):
                st.session_state.nl2sql_generator = NL2SQLGenerator()
                st.session_state.nl2sql_generator_version = GENERATOR_VERSION

    def _initialize_databricks_client(self):
        """Initialize the DatabricksClient if not already in session state"""
        if 'databricks_client' not in st.session_state:
            try:
                st.session_state.databricks_client = DatabricksClient()
                st.session_state.databricks_available = True
            except ValueError as e:
                # Databricks credentials not configured
                st.session_state.databricks_client = None
                st.session_state.databricks_available = False

    def _initialize_history(self):
        """Initialize QueryHistory if not already in session state"""
        if 'query_history' not in st.session_state:
            st.session_state.query_history = QueryHistory()

    def render(self):
        """Main render method for the NL2SQL tab"""
        st.header("🤖 AI 기반 쿼리 생성 및 실행")

        # Two-column layout: Main + History sidebar
        col_main, col_history = st.columns([3, 1])

        with col_main:
            # Databricks connection status
            if st.session_state.databricks_available:
                st.success("✅ Databricks 연결 가능")
            else:
                st.warning("⚠️ Databricks 연결 정보 없음 - SQL 생성만 가능합니다")

            st.markdown("""
            자연어로 요청하면 스키마와 참조 데이터를 활용하여 SQL을 자동 생성합니다.
            **레시피 없이** 자유로운 데이터 탐색이 가능합니다.
            """)

            # User input section
            self._render_input_section()

            # Generate button
            generate_button = st.button(
                "🚀 SQL 생성",
                type="primary",
                key="nl2sql_generate"
            )

            # Process generation
            if generate_button:
                user_query = st.session_state.get("nl2sql_query_input", "")
                if user_query:
                    self._process_generation(user_query)
                else:
                    st.warning("⚠️ 자연어 요청을 입력해주세요.")

            # Display previous result if exists (and not just generated)
            elif 'nl2sql_result' in st.session_state and 'nl2sql_user_query' in st.session_state:
                result = st.session_state.nl2sql_result
                user_query = st.session_state.nl2sql_user_query

                if result.success:
                    self._render_success_result(result, user_query)
                else:
                    self._render_error_result(result)

        with col_history:
            # History sidebar
            self._render_history_sidebar()

    def _render_input_section(self):
        """Render the user input section"""
        st.subheader("📝 자연어 요청")

        # Prompt engineering help
        self._render_help_expander()

        # Check if there's a query to reuse from history
        default_value = ""
        if 'nl2sql_reuse_query' in st.session_state:
            default_value = st.session_state.nl2sql_reuse_query
            del st.session_state.nl2sql_reuse_query

        st.text_area(
            "무엇을 분석하고 싶으신가요?",
            value=default_value,
            height=120,
            placeholder="예: 고혈압 환자의 성별 분포를 보여주세요",
            help="구체적으로 작성할수록 정확한 SQL이 생성됩니다",
            key="nl2sql_query_input"
        )

    def _render_help_expander(self):
        """Render the help expander for effective query writing"""
        with st.expander("💡 효과적인 요청 작성법", expanded=False):
            st.markdown("""
            ### 좋은 요청 예시:

            ✅ **구체적인 질문**
            - "고혈압 환자의 성별 분포를 보여주세요"
            - "당뇨병 환자에게 가장 많이 처방된 약물 TOP 10"

            ✅ **조건 포함**
            - "서울 지역 3차 병원에서 치료받은 암 환자는 몇 명?"
            - "최근 1년간 고혈압으로 처방받은 약물 성분별 환자 수"

            ❌ **피해야 할 요청**
            - "고혈압" (너무 모호함)
            - "Show me hypertension patients" (영문 지원 안 됨)
            - "모든 정보 보여줘" (범위 불명확)

            ### 요청 구조 패턴:
            `[질환명] + [분석 대상] + [조건(선택)]`
            - 질환명: "고혈압", "당뇨병", "암"
            - 분석 대상: "환자 수", "성별 분포", "처방 약물"
            - 조건: "지역", "병원 등급", "기간"
            """)


    def _process_generation(self, user_query: str):
        """
        Process SQL generation from user query

        Args:
            user_query: Natural language query from user
        """
        with st.spinner("SQL 생성 중..."):
            generator = st.session_state.nl2sql_generator
            result = generator.generate_sql(user_query)

        # Store result in session state to persist across reruns
        st.session_state.nl2sql_result = result
        st.session_state.nl2sql_user_query = user_query

        # Save to history
        if result.success:
            query_id = st.session_state.query_history.add_query(
                user_query=user_query,
                sql_query=result.sql_query,
                success=True
            )
            st.session_state.current_query_id = query_id  # 실행 결과 업데이트용
            self._render_success_result(result, user_query)
        else:
            # 실패한 쿼리도 히스토리에 저장 (디버깅용)
            st.session_state.query_history.add_query(
                user_query=user_query,
                sql_query="",
                success=False
            )
            self._render_error_result(result)

    def _render_success_result(self, result, user_query: str):
        """Render successful SQL generation result"""

        # Show improvement banner if SQL was just improved
        if st.session_state.get('nl2sql_just_improved', False):
            st.info("🎉 **SQL 개선 완료!** 아래에서 개선된 쿼리를 확인하세요.", icon="✨")
            # Clear the flag after showing
            st.session_state.nl2sql_just_improved = False
        else:
            st.success("✅ SQL 생성 완료!")

        # SQL quality indicators
        st.subheader("📝 생성된 SQL")
        self._render_quality_metrics(result)

        # Display SQL with line numbers
        st.code(result.sql_query, language="sql", line_numbers=True)

        # Download and Execute buttons
        self._render_action_buttons(result.sql_query)

        # SQL Validation
        self._render_validation_section(result.sql_query)

        # Query execution results (if executed)
        if 'nl2sql_execution_result' in st.session_state:
            self._render_execution_results()

        # Analysis details
        self._render_analysis_details(result)

        # Explanation
        if result.analysis.get('explanation'):
            with st.expander("💬 쿼리 설명"):
                st.markdown(result.analysis['explanation'])

        # SQL Refinement Section
        st.markdown("---")
        self._render_refinement_section(user_query, result.sql_query)

        # Learning section
        self._render_learning_section(user_query)

    def _render_quality_metrics(self, result):
        """Render SQL quality metrics"""
        col1, col2, col3 = st.columns(3)

        with col1:
            tables_count = len(result.analysis.get('required_tables', []))
            st.metric("테이블 사용", tables_count)

        with col2:
            conditions_count = len(result.analysis.get('key_conditions', []))
            st.metric("조건 수", conditions_count)

        with col3:
            line_count = len(result.sql_query.split('\n'))
            if line_count < 10:
                complexity = "간단"
            elif line_count < 20:
                complexity = "보통"
            else:
                complexity = "복잡"
            st.metric("복잡도", complexity)

    def _render_action_buttons(self, sql_query: str):
        """Render SQL download and execution buttons"""
        col1, col2 = st.columns([1, 1])

        with col1:
            st.download_button(
                label="💾 SQL 파일 다운로드",
                data=sql_query,
                file_name="generated_query.sql",
                mime="text/plain",
                key="nl2sql_download",
                help="SQL을 .sql 파일로 저장 후 Databricks에서 실행하세요"
            )

        with col2:
            # Execute button (only if Databricks is available)
            if st.session_state.databricks_available:
                execute_button = st.button(
                    "▶️ 쿼리 실행",
                    type="primary",
                    key="nl2sql_execute",
                    help="Databricks에서 쿼리를 실행하고 결과를 표시합니다"
                )

                if execute_button:
                    # Clear previous execution result
                    if 'nl2sql_execution_result' in st.session_state:
                        del st.session_state.nl2sql_execution_result

                    client = st.session_state.databricks_client
                    with st.spinner("쿼리 실행 중..."):
                        result = client.execute_query(sql_query, max_rows=10000)

                    # Store result and display immediately
                    st.session_state.nl2sql_execution_result = result

                    # Update history with execution result
                    if 'current_query_id' in st.session_state:
                        st.session_state.query_history.update_execution_result(
                            query_id=st.session_state.current_query_id,
                            execution_success=result['success'],
                            row_count=result.get('row_count'),
                            execution_time=result.get('execution_time')
                        )
            else:
                st.button(
                    "▶️ 쿼리 실행 (연결 필요)",
                    disabled=True,
                    key="nl2sql_execute_disabled",
                    help="Databricks 연결 정보를 설정해야 실행할 수 있습니다"
                )

        st.caption(
            "💡 **Tip**: SQL 코드 블록을 마우스로 선택하여 복사할 수 있습니다 "
            "(Ctrl+C / Cmd+C)"
        )

    def _render_validation_section(self, sql_query: str):
        """Render SQL validation results"""
        validation = self._validate_databricks_sql(sql_query)

        if validation['issues']:
            st.error("🚨 **SQL 검증 실패** - 실행 전 수정 필요:")
            for issue in validation['issues']:
                st.markdown(f"- ❌ {issue}")

        if validation['warnings']:
            st.warning("⚠️ **권장사항**:")
            for warning in validation['warnings']:
                st.markdown(f"- {warning}")

        if not validation['issues'] and not validation['warnings']:
            st.success("✅ Databricks 호환성 검증 통과")

    @staticmethod
    def _validate_databricks_sql(sql: str) -> dict:
        """
        Validate SQL against Databricks/Spark SQL rules

        Args:
            sql: SQL query string

        Returns:
            Dictionary with 'issues' and 'warnings' lists
        """
        issues = []
        warnings = []

        # Critical issues - deleted filter
        if "deleted = FALSE" not in sql and "basic_treatment" in sql:
            issues.append(
                "basic_treatment 테이블 사용 시 'deleted = FALSE' 필터 필수"
            )

        if "deleted = FALSE" not in sql and "prescribed_drug" in sql:
            issues.append(
                "prescribed_drug 테이블 사용 시 'deleted = FALSE' 필터 필수"
            )

        # Date conversion issues
        if "res_treat_start_date" in sql:
            if "CAST" in sql and "AS DATE" in sql:
                issues.append(
                    "res_treat_start_date는 YYYYMMDD 문자열 - "
                    "TO_DATE(res_treat_start_date, 'yyyyMMdd') 사용 필수"
                )
            elif "TO_DATE(res_treat_start_date)" in sql and "yyyyMMdd" not in sql:
                issues.append(
                    "TO_DATE는 형식 지정 필수 - "
                    "TO_DATE(res_treat_start_date, 'yyyyMMdd')"
                )

        # Warnings
        if "res_treat_start_date" in sql and "TO_DATE" not in sql:
            warnings.append(
                "res_treat_start_date 날짜 비교 시 "
                "TO_DATE(res_treat_start_date, 'yyyyMMdd') 변환 필요"
            )

        if "REGEXP" in sql:
            warnings.append("Spark SQL에서는 RLIKE 사용 권장 (REGEXP 대신)")

        return {"issues": issues, "warnings": warnings}

    def _render_analysis_details(self, result):
        """Render analysis details in expander"""
        with st.expander("📊 분석 상세정보", expanded=False):
            analysis_col1, analysis_col2 = st.columns(2)

            with analysis_col1:
                st.markdown("**의도 분석**")
                st.info(result.analysis.get('intent', 'N/A'))

                st.markdown("**주요 조건**")
                if result.analysis.get('key_conditions'):
                    for condition in result.analysis['key_conditions']:
                        st.markdown(f"- {condition}")

            with analysis_col2:
                st.markdown("**사용된 테이블**")
                tables = result.analysis.get('required_tables', [])
                for table in tables:
                    st.code(table, language="text")

                if result.relevant_examples:
                    st.markdown("**참고한 예시**")
                    for ex in result.relevant_examples:
                        st.markdown(f"- {ex}")

    def _render_refinement_section(self, original_query: str, current_sql: str):
        """Render SQL refinement section for iterative improvements"""
        st.subheader("🔄 쿼리 개선하기")
        st.markdown("생성된 SQL에 조건을 추가하거나 수정할 사항을 자연어로 입력하세요.")

        # Refinement examples
        with st.expander("💡 개선 요청 예시", expanded=False):
            st.markdown("""
            - "서울 지역만 필터링해주세요"
            - "최근 1년 데이터만 조회하도록 수정"
            - "연령대별로 그룹핑 추가"
            - "3차 병원 환자만 포함"
            - "결과를 상위 20개로 제한"
            - "정렬 기준을 환자 수 내림차순으로 변경"
            """)

        # Refinement input
        refinement_input = st.text_area(
            "개선 요청사항",
            height=80,
            placeholder="예: 서울 지역 3차 병원 환자만 필터링해주세요",
            key="nl2sql_refinement_input"
        )

        # Refine button
        if st.button("✨ SQL 개선", type="primary", key="nl2sql_refine_button"):
            if refinement_input.strip():
                self._process_refinement(original_query, current_sql, refinement_input)
            else:
                st.warning("⚠️ 개선 요청사항을 입력해주세요.")

    def _process_refinement(self, original_query: str, current_sql: str, refinement_request: str):
        """Process SQL refinement request"""
        with st.spinner("🔄 SQL 개선 중..."):
            generator = st.session_state.nl2sql_generator
            result = generator.refine_sql(
                original_query=original_query,
                current_sql=current_sql,
                refinement_request=refinement_request
            )

        if result.success:
            # Update session state with refined SQL
            st.session_state.nl2sql_result = result
            st.session_state.nl2sql_user_query = f"{original_query} (개선: {refinement_request})"

            # Clear previous execution result
            if 'nl2sql_execution_result' in st.session_state:
                del st.session_state.nl2sql_execution_result

            # Set flag to show improvement banner
            st.session_state.nl2sql_just_improved = True

            st.rerun()
        else:
            st.error(f"❌ SQL 개선 실패: {result.error_message}")

    def _render_learning_section(self, user_query: str):
        """Render learning section with similar query patterns"""
        with st.expander("📚 비슷한 질문 패턴 배우기", expanded=False):
            st.markdown(f"""
            ### 이 쿼리와 비슷한 패턴:

            **현재 요청**: {user_query}

            **동일 패턴 다른 질환**:
            - "{user_query.replace('고혈압', '당뇨병')}"
            - "{user_query.replace('고혈압', '암')}"

            **조건 추가 버전**:
            - "{user_query} (최근 1년)"
            - "{user_query} (서울 지역 병원)"

            **다른 분석 각도**:
            """)

            if "성별" in user_query:
                st.markdown("- 같은 질환의 '연령대별 분포'")
                st.markdown("- 같은 질환의 '지역별 분포'")
            elif "약물" in user_query or "처방" in user_query:
                st.markdown("- 같은 질환의 '처방 성분별 환자 수'")
                st.markdown("- 같은 질환의 '처방 빈도 추이'")

    def _render_execution_results(self):
        """Render query execution results"""
        result = st.session_state.nl2sql_execution_result

        st.divider()
        st.subheader("📊 쿼리 실행 결과")

        if result['success']:
            # Success metrics
            col1, col2 = st.columns(2)
            with col1:
                st.metric("반환된 행 수", f"{result['row_count']:,}")
            with col2:
                st.metric("실행 시간", f"{result['execution_time']}초")

            # Display data
            if result['row_count'] > 0:
                st.dataframe(
                    result['data'],
                    use_container_width=True,
                    height=400
                )

                # Export to CSV
                csv = result['data'].to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    label="📥 CSV로 다운로드",
                    data=csv,
                    file_name="query_result.csv",
                    mime="text/csv",
                    key="nl2sql_csv_download"
                )

                # Interactive chart builder
                st.divider()
                chart_builder = ChartBuilder(result['data'], key_prefix="nl2sql_chart")
                chart_builder.render()
            else:
                st.info("쿼리가 성공적으로 실행되었지만 결과가 없습니다.")

            # Clear button - just flag for deletion, will be removed on next render
            if st.button("🗑️ 결과 지우기", key="nl2sql_clear_results"):
                if 'nl2sql_execution_result' in st.session_state:
                    del st.session_state.nl2sql_execution_result

        else:
            # Error display
            st.error(f"❌ 쿼리 실행 실패")
            st.code(result['error_message'], language="text")

            with st.expander("🔧 오류 해결 가이드"):
                st.markdown("""
                ### 일반적인 오류 해결:

                **CAST_INVALID_INPUT 오류**
                - 원인: 날짜 필드 형식 불일치
                - 해결: `TO_DATE(res_treat_start_date, 'yyyyMMdd')` 사용

                **TABLE_OR_VIEW_NOT_FOUND 오류**
                - 원인: 테이블명 오류 또는 권한 부족
                - 확인: 좌측 사이드바 "데이터 사전"에서 테이블명 확인

                **컬럼명 오류**
                - 확인: 좌측 사이드바에서 정확한 컬럼명 확인
                - 대소문자 구분 주의

                **deleted 필터 누락**
                - basic_treatment, prescribed_drug 테이블은 `deleted = FALSE` 필수
                """)

            # Clear button
            if st.button("🗑️ 결과 지우기", key="nl2sql_clear_error"):
                if 'nl2sql_execution_result' in st.session_state:
                    del st.session_state.nl2sql_execution_result

    def _render_error_result(self, result):
        """Render error result with recovery guidance"""
        st.error(f"❌ SQL 생성 실패: {result.error_message}")

        with st.expander("🔧 문제 해결 가이드", expanded=True):
            st.markdown("""
            ### SQL 생성 실패 시 확인사항:

            1. **질환명 확인**
               - ✅ 정확한 한글 질환명 사용 (예: "고혈압", "당뇨병")
               - ❌ 영문명은 인식 안 됨 (예: "hypertension" → "고혈압")

            2. **요청 구체화**
               - ✅ "고혈압 환자의 성별 분포"
               - ❌ "고혈압 정보" (너무 모호함)

            3. **테이블 제약 확인**
               - 사용 가능: basic_treatment, prescribed_drug, insured_person, hospital
               - 질환 필터: basic_treatment.res_disease_name
               - 약물 정보: prescribed_drug.res_drug_name

            4. **예시 쿼리 참고**
               - 위의 예시 선택 드롭다운에서 유사한 패턴 확인
            """)

            st.info("💡 **추천**: 위의 '예시 쿼리 선택'에서 유사한 질문을 선택해보세요")

    def _render_history_sidebar(self):
        """히스토리 사이드바 렌더링"""
        st.markdown("### 📜 쿼리 히스토리")

        history = st.session_state.query_history

        # 탭: 최근 / 즐겨찾기
        tab1, tab2 = st.tabs(["최근", "⭐"])

        with tab1:
            recent_queries = history.get_recent(limit=10)
            if recent_queries:
                for record in recent_queries:
                    self._render_history_item(record, context="recent")
            else:
                st.info("히스토리가 없습니다")

        with tab2:
            favorites = history.get_favorites()
            if favorites:
                for record in favorites:
                    self._render_history_item(record, context="favorite")
            else:
                st.info("즐겨찾기가 없습니다")

        # 통계
        st.markdown("---")
        stats = history.get_statistics()
        st.caption(f"📊 총 {stats['total']}개 쿼리")
        st.caption(f"⭐ {stats['favorites']}개 즐겨찾기")

    def _render_history_item(self, record, context="recent"):
        """히스토리 아이템 렌더링"""
        with st.expander(f"{'⭐ ' if record.is_favorite else ''}{record.user_query[:30]}...", expanded=False):
            st.caption(f"🕒 {record.timestamp[:19]}")

            # SQL 미리보기
            st.code(record.sql_query[:100] + "..." if len(record.sql_query) > 100 else record.sql_query, language="sql")

            # 액션 버튼
            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("🔄", key=f"reuse_{context}_{record.id}", help="재사용"):
                    # 쿼리를 임시 변수에 저장 (위젯 키는 직접 수정 불가)
                    st.session_state.nl2sql_reuse_query = record.user_query
                    st.rerun()

            with col2:
                star_icon = "⭐" if record.is_favorite else "☆"
                if st.button(star_icon, key=f"fav_{context}_{record.id}", help="즐겨찾기"):
                    st.session_state.query_history.toggle_favorite(record.id)
                    st.rerun()

            with col3:
                if st.button("🗑️", key=f"del_{context}_{record.id}", help="삭제"):
                    st.session_state.query_history.delete_query(record.id)
                    st.rerun()
