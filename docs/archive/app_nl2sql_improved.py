# Tab 3: AI 쿼리 생성 (NL2SQL - Pattern II RAG)
# IMPROVED VERSION with better UX for SQL code generation workflow

with main_tabs[2]:
    st.header("🤖 AI 기반 쿼리 생성")

    # P0.1: Purpose clarity banner
    st.info("""
📌 **이 도구는 SQL 코드 생성기입니다**
• ✅ 자연어 → SQL 쿼리 자동 변환
• ✅ 생성된 SQL을 복사하여 Databricks에서 실행
• ❌ 이 화면에서는 데이터를 조회하지 않습니다
    """)

    st.markdown("""
    자연어로 요청하면 스키마와 참조 데이터를 활용하여 SQL을 자동 생성합니다.
    **레시피 없이** 자유로운 데이터 탐색이 가능합니다.
    """)

    # Initialize NL2SQL generator
    try:
        from nl2sql_generator import NL2SQLGenerator

        if 'nl2sql_generator' not in st.session_state:
            with st.spinner("NL2SQL Generator 초기화 중..."):
                st.session_state.nl2sql_generator = NL2SQLGenerator()

        # User input
        st.subheader("📝 자연어 요청")

        # P2.1: Prompt engineering help
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

        # Example queries
        example_queries = [
            "고혈압 환자의 성별 분포를 보여주세요",
            "당뇨병 환자에게 가장 많이 처방된 약물 TOP 10",
            "서울 지역 3차 병원에서 치료받은 암 환자는 몇 명인가요?",
            "최근 1년간 고혈압으로 처방받은 약물 성분별 환자 수",
        ]

        selected_example = st.selectbox(
            "예시 쿼리 선택 (선택사항)",
            ["직접 입력"] + example_queries,
            key="nl2sql_example"
        )

        if selected_example != "직접 입력":
            default_query = selected_example
        else:
            default_query = ""

        user_query = st.text_area(
            "무엇을 분석하고 싶으신가요?",
            value=default_query,
            height=100,
            placeholder="예: 고혈압 환자 중 서울 지역 3차 병원에서 치료받은 환자의 연령대별 분포",
            help="구체적으로 작성할수록 정확한 SQL이 생성됩니다",
            key="nl2sql_query_input"
        )

        col1, col2 = st.columns([1, 5])
        with col1:
            generate_button = st.button("🚀 SQL 생성", type="primary", key="nl2sql_generate")

        if generate_button and user_query:
            with st.spinner("SQL 생성 중..."):
                result = st.session_state.nl2sql_generator.generate_sql(user_query)

            if result.success:
                st.success("✅ SQL 생성 완료!")

                # P1.2: SQL first (most important output)
                st.subheader("📝 생성된 SQL")

                # P1.1: SQL quality indicators
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("테이블 사용", len(result.analysis.get('required_tables', [])))
                with col2:
                    st.metric("조건 수", len(result.analysis.get('key_conditions', [])))
                with col3:
                    complexity = "간단" if len(result.sql_query.split('\n')) < 10 else "보통" if len(result.sql_query.split('\n')) < 20 else "복잡"
                    st.metric("복잡도", complexity)

                # Display SQL with line numbers
                st.code(result.sql_query, language="sql", line_numbers=True)

                # P0.2: Improved copy mechanism
                col1, col2 = st.columns([3, 7])
                with col1:
                    st.download_button(
                        label="💾 SQL 파일 다운로드",
                        data=result.sql_query,
                        file_name="generated_query.sql",
                        mime="text/plain",
                        key="nl2sql_download",
                        help="SQL을 .sql 파일로 저장 후 Databricks에서 실행하세요"
                    )

                st.caption("💡 **Tip**: SQL 코드 블록을 마우스로 선택하여 복사할 수 있습니다 (Ctrl+C / Cmd+C)")

                # P1.3: SQL Validation
                def validate_databricks_sql(sql: str) -> dict:
                    """Validate SQL against Databricks/Spark SQL rules"""
                    issues = []
                    warnings = []

                    # Critical issues
                    if "deleted = FALSE" not in sql and "basic_treatment" in sql:
                        issues.append("basic_treatment 테이블 사용 시 'deleted = FALSE' 필터 필수")

                    if "deleted = FALSE" not in sql and "prescribed_drug" in sql:
                        issues.append("prescribed_drug 테이블 사용 시 'deleted = FALSE' 필터 필수")

                    # Warnings
                    if "res_treat_start_date" in sql and "TO_DATE" not in sql:
                        warnings.append("res_treat_start_date는 char 타입 - TO_DATE() 변환 권장")

                    if "REGEXP" in sql:
                        warnings.append("Spark SQL에서는 RLIKE 사용 권장 (REGEXP 대신)")

                    return {"issues": issues, "warnings": warnings}

                validation = validate_databricks_sql(result.sql_query)

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

                # P1.2: Analysis in expander (less prominent)
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

                # Explanation
                if result.analysis.get('explanation'):
                    with st.expander("💬 쿼리 설명"):
                        st.markdown(result.analysis['explanation'])

                # P2.3: Learning section
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

            else:
                # P0.3: Error with recovery guidance
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

        elif generate_button:
            st.warning("⚠️ 자연어 요청을 입력해주세요.")

    except ImportError:
        st.error("NL2SQL Generator를 불러올 수 없습니다. nl2sql_generator.py 파일을 확인하세요.")
    except Exception as e:
        st.error(f"오류 발생: {str(e)}")
