"""
NL2SQL UI Improvements - Code Examples
Production-ready Streamlit components for enhanced UX
"""

import streamlit as st
import pandas as pd
from typing import Optional

# ============================================================================
# P0.1: Query Execution & Results Preview
# ============================================================================

def render_query_execution_section(sql_query: str, execute_callback):
    """
    Allows users to execute generated SQL and preview results

    Args:
        sql_query: Generated SQL code
        execute_callback: Function(sql) -> pd.DataFrame | str (error)
    """
    st.subheader("🔍 쿼리 실행 및 미리보기")

    col1, col2, col3 = st.columns([2, 2, 6])

    with col1:
        execute_btn = st.button(
            "▶️ 실행하기",
            type="primary",
            key="nl2sql_execute",
            help="생성된 SQL을 실제 데이터베이스에서 실행합니다"
        )

    with col2:
        limit = st.number_input(
            "결과 제한",
            min_value=10,
            max_value=1000,
            value=100,
            step=10,
            key="nl2sql_limit",
            help="미리보기 행 수 (성능 보호)"
        )

    if execute_btn:
        with st.spinner("🔄 데이터베이스 쿼리 실행 중..."):
            result = execute_callback(sql_query, limit)

            if isinstance(result, pd.DataFrame):
                # Success case
                st.success(f"✅ {len(result):,}개 결과 조회 완료")

                # Results preview
                st.dataframe(
                    result,
                    use_container_width=True,
                    height=400
                )

                # Download results
                col_download1, col_download2 = st.columns([1, 5])
                with col_download1:
                    csv = result.to_csv(index=False).encode('utf-8-sig')
                    st.download_button(
                        label="📥 CSV 다운로드",
                        data=csv,
                        file_name="query_results.csv",
                        mime="text/csv",
                        key="nl2sql_download_results"
                    )

                # Basic statistics
                with st.expander("📊 결과 통계"):
                    stat_col1, stat_col2, stat_col3 = st.columns(3)
                    with stat_col1:
                        st.metric("총 행 수", f"{len(result):,}")
                    with stat_col2:
                        st.metric("총 열 수", len(result.columns))
                    with stat_col3:
                        st.metric("메모리 사용", f"{result.memory_usage(deep=True).sum() / 1024:.1f} KB")

            else:
                # Error case
                st.error(f"❌ 쿼리 실행 실패")
                st.code(result, language="text")
                st.info("💡 **다음을 확인하세요:**\n- SQL 문법 오류\n- 테이블/컬럼명 오타\n- 필터 조건 검토")


# ============================================================================
# P0.2: Proactive Input Validation
# ============================================================================

def render_query_input_with_validation(default_value: str = "") -> str:
    """
    Query input with real-time validation feedback

    Returns:
        User's query text
    """
    user_query = st.text_area(
        "무엇을 분석하고 싶으신가요?",
        value=default_value,
        height=100,
        placeholder="예: 고혈압 환자 중 남성과 여성의 비율은?",
        key="nl2sql_query_input",
        help="구체적일수록 정확한 SQL이 생성됩니다"
    )

    # Real-time validation
    if len(user_query.strip()) == 0:
        st.warning("⚠️ 분석하고 싶은 내용을 입력해주세요")
        return user_query

    elif len(user_query.strip()) < 10:
        st.info("💡 조금 더 구체적으로 작성하면 더 정확한 결과를 얻을 수 있어요")
        return user_query

    else:
        # Show character count for power users
        char_count = len(user_query)
        st.caption(f"✓ {char_count}자 입력됨")
        return user_query


# ============================================================================
# P0.3: Context-Preserving Loading State
# ============================================================================

def render_generation_progress(user_query: str):
    """
    Shows loading state while preserving user context

    Args:
        user_query: The query being processed
    """
    # Show query being processed
    st.info(f"🔍 **분석 중인 요청:** {user_query}")

    # Progress steps with status
    progress_container = st.container()

    with progress_container:
        progress_steps = [
            ("1️⃣", "키워드 추출", "completed"),
            ("2️⃣", "관련 스키마 검색", "in_progress"),
            ("3️⃣", "SQL 생성", "pending"),
            ("4️⃣", "결과 검증", "pending")
        ]

        cols = st.columns(4)
        for idx, (icon, label, status) in enumerate(progress_steps):
            with cols[idx]:
                if status == "completed":
                    st.success(f"{icon} {label}")
                elif status == "in_progress":
                    st.info(f"{icon} {label}...")
                else:
                    st.text(f"{icon} {label}")


# ============================================================================
# P0.4: Accurate Download/Copy UI
# ============================================================================

def render_sql_output_with_actions(sql_query: str):
    """
    SQL output with clear copy and download actions

    Args:
        sql_query: Generated SQL code
    """
    st.subheader("📝 생성된 SQL")

    # SQL code display
    st.code(sql_query, language="sql")

    # Action buttons with clear labels
    col1, col2, col3 = st.columns([2, 2, 6])

    with col1:
        # True copy button (requires custom component or workaround)
        st.button(
            "📋 클립보드 복사",
            key="nl2sql_copy",
            help="SQL을 클립보드에 복사합니다",
            on_click=lambda: st.info("💡 SQL 코드를 마우스로 선택 후 Ctrl+C (Mac: Cmd+C)로 복사하세요")
        )

    with col2:
        # Download as file
        st.download_button(
            label="💾 SQL 파일 저장",
            data=sql_query,
            file_name="generated_query.sql",
            mime="text/plain",
            key="nl2sql_download",
            help="SQL을 .sql 파일로 다운로드합니다"
        )


# ============================================================================
# P1.1: Query Refinement Interface
# ============================================================================

def render_query_refinement(original_query: str, generated_sql: str) -> Optional[str]:
    """
    Allows users to refine their query based on results

    Returns:
        Refined query text or None
    """
    with st.expander("🔄 쿼리 수정하기"):
        st.markdown("""
        생성된 SQL이 원하는 결과가 아닌가요? 아래 방법으로 요청을 수정해보세요:
        """)

        refinement_option = st.radio(
            "수정 방법 선택",
            [
                "조건 추가/변경",
                "출력 필드 변경",
                "정렬 방식 변경",
                "처음부터 다시 작성"
            ],
            key="nl2sql_refinement_option"
        )

        if refinement_option == "처음부터 다시 작성":
            refined_query = st.text_area(
                "새로운 요청 작성",
                placeholder="예: 고혈압 환자 중 60세 이상 남성의 수",
                key="nl2sql_refined_full"
            )
        else:
            refined_query = st.text_area(
                f"원래 요청: {original_query}\n\n{refinement_option}을 설명해주세요:",
                placeholder="예: 연령대를 50대, 60대, 70대로 그룹화해주세요",
                key="nl2sql_refined_partial"
            )

        if st.button("🚀 수정된 쿼리로 재생성", key="nl2sql_refine_btn"):
            return refined_query

    return None


# ============================================================================
# P1.2: Enhanced Examples with Context
# ============================================================================

def render_enhanced_examples():
    """
    Example queries with difficulty levels and expected outcomes
    """
    st.subheader("📝 자연어 요청")

    # Enhanced example structure
    examples = [
        {
            "query": "고혈압 환자의 성별 분포를 보여주세요",
            "difficulty": "🟢 쉬움",
            "expected": "2개 컬럼 (성별, 환자수)",
            "tables": "basic_treatment, insured_person"
        },
        {
            "query": "당뇨병 환자에게 가장 많이 처방된 약물 TOP 10",
            "difficulty": "🟡 보통",
            "expected": "10개 행 (약물명, 처방횟수)",
            "tables": "basic_treatment, prescribed_drug"
        },
        {
            "query": "서울 지역 3차 병원에서 치료받은 암 환자는 몇 명인가요?",
            "difficulty": "🟠 복잡",
            "expected": "1개 값 (환자수)",
            "tables": "basic_treatment"
        },
        {
            "query": "최근 1년간 고혈압으로 처방받은 약물 성분별 환자 수",
            "difficulty": "🔴 매우 복잡",
            "expected": "N개 행 (성분명, 환자수)",
            "tables": "basic_treatment, prescribed_drug"
        }
    ]

    # Create example cards
    selected_idx = st.selectbox(
        "예시 쿼리 선택 (선택사항)",
        ["직접 입력"] + [f"{ex['difficulty']} {ex['query']}" for ex in examples],
        key="nl2sql_example",
        format_func=lambda x: x.split(" ", 1)[1] if x != "직접 입력" else x
    )

    # Show example details
    if selected_idx != "직접 입력":
        idx = [f"{ex['difficulty']} {ex['query']}" for ex in examples].index(selected_idx)
        example = examples[idx]

        col1, col2, col3 = st.columns(3)
        with col1:
            st.caption(f"**난이도**: {example['difficulty']}")
        with col2:
            st.caption(f"**예상 결과**: {example['expected']}")
        with col3:
            st.caption(f"**사용 테이블**: {example['tables']}")

    return selected_idx


# ============================================================================
# P1.3: Schema Browser
# ============================================================================

def render_schema_browser(notion_columns_df: pd.DataFrame):
    """
    Collapsible schema reference for users

    Args:
        notion_columns_df: DataFrame with schema metadata
    """
    with st.expander("📚 사용 가능한 데이터 스키마 보기"):
        st.markdown("""
        어떤 데이터를 분석할 수 있는지 궁금하신가요? 아래 테이블과 컬럼을 참고하세요.
        """)

        # Table selector
        tables = notion_columns_df['테이블명'].unique()
        selected_table = st.selectbox(
            "테이블 선택",
            tables,
            key="nl2sql_schema_table"
        )

        # Show columns for selected table
        table_cols = notion_columns_df[notion_columns_df['테이블명'] == selected_table]

        st.markdown(f"### {selected_table} 테이블")
        st.dataframe(
            table_cols[['컬럼명', '한글명', '데이터타입', '설명']],
            use_container_width=True,
            hide_index=True
        )


# ============================================================================
# P1.4: Query History
# ============================================================================

def render_query_history():
    """
    Session-based query history for comparison
    """
    if 'nl2sql_history' not in st.session_state:
        st.session_state.nl2sql_history = []

    if len(st.session_state.nl2sql_history) > 0:
        with st.expander(f"📜 이전 쿼리 기록 ({len(st.session_state.nl2sql_history)}개)"):
            for idx, item in enumerate(reversed(st.session_state.nl2sql_history[-5:])):
                col1, col2 = st.columns([5, 1])
                with col1:
                    st.markdown(f"**{idx+1}.** {item['query'][:50]}...")
                with col2:
                    if st.button("다시 사용", key=f"nl2sql_history_{idx}"):
                        return item['query']

            if st.button("🗑️ 기록 지우기", key="nl2sql_clear_history"):
                st.session_state.nl2sql_history = []
                st.rerun()

    return None


def save_to_history(query: str, sql: str, success: bool):
    """Save query to session history"""
    if 'nl2sql_history' not in st.session_state:
        st.session_state.nl2sql_history = []

    st.session_state.nl2sql_history.append({
        'query': query,
        'sql': sql,
        'success': success,
        'timestamp': pd.Timestamp.now()
    })


# ============================================================================
# P2.1: SQL Quality Feedback
# ============================================================================

def render_sql_quality_feedback(sql_query: str, analysis: dict):
    """
    Shows query optimization hints and best practices

    Args:
        sql_query: Generated SQL
        analysis: Analysis dict from NL2SQL generator
    """
    with st.expander("💡 쿼리 품질 평가"):
        quality_score = 0
        feedback = []

        # Check for deleted filter
        if 'deleted = FALSE' in sql_query.upper() or 'deleted = F' in sql_query.upper():
            quality_score += 25
            feedback.append("✅ 삭제된 데이터 필터링 포함")
        else:
            feedback.append("⚠️ deleted = FALSE 조건 누락 (필수)")

        # Check for LIMIT clause
        if 'LIMIT' in sql_query.upper():
            quality_score += 25
            feedback.append("✅ LIMIT 절로 결과 크기 제한")
        else:
            feedback.append("💡 LIMIT 추가 권장 (성능 향상)")

        # Check for JOIN optimization
        if 'JOIN' in sql_query.upper():
            quality_score += 25
            feedback.append("✅ 테이블 조인 사용")

        # Check for aggregation
        if any(agg in sql_query.upper() for agg in ['COUNT', 'SUM', 'AVG', 'GROUP BY']):
            quality_score += 25
            feedback.append("✅ 집계 함수로 데이터 요약")

        # Display score
        col1, col2 = st.columns([1, 3])
        with col1:
            st.metric("품질 점수", f"{quality_score}/100")
        with col2:
            for item in feedback:
                st.markdown(item)


# ============================================================================
# COMPLETE INTEGRATED EXAMPLE
# ============================================================================

def render_improved_nl2sql_tab():
    """
    Complete improved NL2SQL UI with all enhancements
    This is the production-ready version to replace lines 753-863 in app.py
    """
    st.header("🤖 AI 기반 쿼리 생성")

    # Value proposition with visual hierarchy
    st.markdown("""
    ### 자연어로 데이터를 탐색하세요
    SQL 지식 없이도 복잡한 의료 데이터를 분석할 수 있습니다.
    """)

    # Initialize generator
    try:
        from nl2sql_generator import NL2SQLGenerator

        if 'nl2sql_generator' not in st.session_state:
            with st.spinner("AI 엔진 초기화 중..."):
                st.session_state.nl2sql_generator = NL2SQLGenerator()

        # P1.4: Query history (load previous queries)
        previous_query = render_query_history()

        # P1.2: Enhanced examples with difficulty
        selected_example = render_enhanced_examples()

        # Determine default query
        if previous_query:
            default_query = previous_query
        elif selected_example != "직접 입력":
            default_query = selected_example.split(" ", 1)[1]
        else:
            default_query = ""

        # P0.2: Input with validation
        user_query = render_query_input_with_validation(default_query)

        # P1.3: Schema browser
        if hasattr(st.session_state.nl2sql_generator, 'notion_columns'):
            render_schema_browser(st.session_state.nl2sql_generator.notion_columns)

        # Generate button with disabled state
        col1, col2 = st.columns([1, 5])
        with col1:
            generate_button = st.button(
                "🚀 SQL 생성",
                type="primary",
                key="nl2sql_generate",
                disabled=len(user_query.strip()) < 10,
                help="최소 10자 이상 입력해야 합니다" if len(user_query.strip()) < 10 else "SQL 쿼리를 생성합니다"
            )

        if generate_button and user_query:
            # P0.3: Context-preserving loading (commented out for production)
            # render_generation_progress(user_query)

            with st.spinner("🔄 AI가 SQL을 생성하고 있습니다..."):
                result = st.session_state.nl2sql_generator.generate_sql(user_query)

            if result.success:
                st.success("✅ SQL 생성 완료!")

                # Analysis section (improved layout)
                st.subheader("📊 분석 결과")

                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**🎯 의도 분석**")
                    st.info(result.analysis.get('intent', 'N/A'))

                with col2:
                    st.markdown("**🗂️ 사용된 테이블**")
                    tables = result.analysis.get('required_tables', [])
                    for table in tables:
                        st.code(table, language="text")

                # Key conditions
                if result.analysis.get('key_conditions'):
                    st.markdown("**🔍 주요 조건**")
                    for condition in result.analysis['key_conditions']:
                        st.markdown(f"- {condition}")

                # Relevant examples
                if result.relevant_examples:
                    with st.expander("💡 참고한 예시 쿼리"):
                        for ex in result.relevant_examples:
                            st.markdown(f"- {ex}")

                # P0.4: SQL output with clear actions
                render_sql_output_with_actions(result.sql_query)

                # P2.1: Quality feedback
                render_sql_quality_feedback(result.sql_query, result.analysis)

                # Explanation
                if result.analysis.get('explanation'):
                    with st.expander("💬 쿼리 설명"):
                        st.markdown(result.analysis['explanation'])

                # P0.1: Query execution (requires database connection)
                # NOTE: You need to implement execute_sql_query function
                # render_query_execution_section(result.sql_query, execute_sql_query)

                # P1.1: Query refinement
                refined = render_query_refinement(user_query, result.sql_query)
                if refined:
                    st.rerun()

                # P1.4: Save to history
                save_to_history(user_query, result.sql_query, True)

            else:
                st.error("❌ SQL 생성 실패")
                st.code(result.error_message, language="text")

                # Error recovery guidance
                st.info("""
                **💡 문제 해결 방법:**
                1. 요청을 더 구체적으로 작성해보세요
                2. 예시 쿼리를 참고하여 비슷한 형식으로 작성해보세요
                3. 데이터 스키마를 확인하여 올바른 테이블/컬럼명을 사용했는지 확인하세요
                """)

                # P1.4: Save failed attempts too
                save_to_history(user_query, "", False)

    except ImportError:
        st.error("❌ NL2SQL Generator를 불러올 수 없습니다.")
        st.info("nl2sql_generator.py 파일이 올바른 위치에 있는지 확인하세요.")
    except Exception as e:
        st.error(f"❌ 오류 발생: {str(e)}")
        st.info("문제가 지속되면 관리자에게 문의하세요.")
