"""Disease Pipeline Tab - Disease-centric analysis with core + recommended recipes"""

import streamlit as st
from typing import Optional
from pipelines.disease_pipeline import DiseaseAnalysisPipeline


class DiseasePipelineTab:
    """Handles Tab 2: Disease Pipeline - Automated analysis workflow"""

    def __init__(self, recipe_dir: str = "recipes"):
        """
        Initialize Disease Pipeline Tab

        Args:
            recipe_dir: Directory containing recipe files
        """
        self.recipe_dir = recipe_dir
        self._initialize_pipeline()

    def _initialize_pipeline(self):
        """Initialize the DiseaseAnalysisPipeline if not already in session state"""
        if 'disease_pipeline' not in st.session_state:
            try:
                st.session_state.disease_pipeline = DiseaseAnalysisPipeline(
                    recipe_dir=self.recipe_dir
                )
            except Exception as e:
                st.error(f"파이프라인 초기화 실패: {e}")
                st.session_state.disease_pipeline = None

    def render(self):
        """Main render method for the Disease Pipeline tab"""
        st.header("🔬 질환 중심 파이프라인 분석")
        st.markdown("**질환명만 입력하면 자동으로 핵심 분석과 맞춤 추천 분석을 제공합니다.**")

        if st.session_state.disease_pipeline is None:
            st.error("❌ Disease Pipeline을 초기화할 수 없습니다.")
            return

        pipeline = st.session_state.disease_pipeline

        # Step 1: Disease input
        self._render_disease_input()

        # Step 2: Analysis execution
        self._render_analysis_button()

        # Step 3: Show core results and recommendations
        if 'pipeline_core_results' in st.session_state:
            self._render_core_results()
            self._render_recommendations(pipeline)
            self._render_nl_refinement(pipeline)
            self._render_final_execution(pipeline)

        # Step 4: Display final results
        if 'pipeline_final_results' in st.session_state:
            self._render_final_results()

    def _render_disease_input(self):
        """Render Step 1: Disease name input"""
        st.subheader("1️⃣ 질환명 입력")
        st.text_input(
            "분석하고 싶은 질환명을 입력하세요",
            value="당뇨병",
            help="예: 당뇨병, 고혈압, 천식, 골다공증 등",
            key="pipeline_disease_input"
        )

    def _render_analysis_button(self):
        """Render Step 2: Analysis execution button"""
        if st.button("🔍 분석 시작", type="primary", key="start_pipeline_analysis"):
            disease_name = st.session_state.get("pipeline_disease_input", "")

            if disease_name:
                with st.spinner("🔄 핵심 분석 실행 및 추천 레시피 생성 중..."):
                    pipeline = st.session_state.disease_pipeline

                    # Execute core recipes
                    core_results = pipeline.execute_core_recipes(disease_name)

                    # Get LLM recommendations
                    recommended = pipeline.recommend_additional_recipes(
                        disease_name,
                        target_count=7
                    )

                    # Store in session state
                    st.session_state.pipeline_core_results = core_results
                    st.session_state.pipeline_recommended = recommended
                    st.session_state.pipeline_disease_name = disease_name

                    # Initialize checkbox states
                    if 'pipeline_checkboxes' not in st.session_state:
                        st.session_state.pipeline_checkboxes = {}
                    for recipe_name in recommended:
                        if recipe_name not in st.session_state.pipeline_checkboxes:
                            st.session_state.pipeline_checkboxes[recipe_name] = True

                st.success(f"✅ '{disease_name}' 분석 준비 완료!")
            else:
                st.warning("⚠️ 질환명을 입력해주세요.")

    def _render_core_results(self):
        """Render core recipe results summary"""
        st.divider()
        st.subheader("2️⃣ 자동 실행될 핵심 분석 (4개)")

        core_results = st.session_state.pipeline_core_results
        core_success = sum(1 for r in core_results if r.get('success', False))

        st.info(f"✅ {core_success}/{len(core_results)} 개 핵심 레시피 준비됨")

        with st.expander("핵심 레시피 상세보기"):
            for result in core_results:
                if result.get('success'):
                    st.markdown(f"**✓ {result['recipe_name']}**")
                    st.caption(result.get('metadata', {}).get('description', 'N/A'))
                else:
                    error_msg = result.get('error', 'Unknown')
                    st.markdown(f"**✗ {result['recipe_name']}** - ❌ Error: {error_msg}")

    def _render_recommendations(self, pipeline: DiseaseAnalysisPipeline):
        """Render recommended recipes with checkboxes"""
        st.divider()
        st.subheader("3️⃣ 추천 분석 선택")

        disease_name = st.session_state.pipeline_disease_name
        recommended = st.session_state.pipeline_recommended

        st.markdown(
            f"**'{disease_name}'** 질환에 적합한 {len(recommended)}개 추가 분석이 추천되었습니다."
        )
        st.markdown("**체크박스로 원하는 분석을 선택하세요:**")

        # Initialize checkboxes if not exists
        if 'pipeline_checkboxes' not in st.session_state:
            st.session_state.pipeline_checkboxes = {}

        for idx, recipe_name in enumerate(recommended):
            recipe = pipeline.recipe_loader.get_recipe_by_name(recipe_name)
            description = (
                recipe.get('description', 'No description')
                if recipe else 'Recipe not found'
            )

            # Initialize checkbox state
            if recipe_name not in st.session_state.pipeline_checkboxes:
                st.session_state.pipeline_checkboxes[recipe_name] = True

            # Render checkbox
            is_checked = st.checkbox(
                f"**{recipe_name}**",
                value=st.session_state.pipeline_checkboxes[recipe_name],
                key=f"pipeline_cb_{idx}_{recipe_name[:20]}",
                help=description
            )
            st.session_state.pipeline_checkboxes[recipe_name] = is_checked
            st.caption(f"📝 {description}")
            st.markdown("")

    def _render_nl_refinement(self, pipeline: DiseaseAnalysisPipeline):
        """Render natural language refinement section"""
        st.divider()
        st.subheader("4️⃣ 자연어로 추가 요청 (선택사항)")

        nl_feedback = st.text_area(
            "추가로 원하는 분석이 있으면 자연어로 입력하세요",
            placeholder="예: 비용 관련 분석을 더 추가해줘\n예: 시간 경과에 따른 분석은 빼줘",
            help="체크박스 선택을 자연어로 조정할 수 있습니다",
            key="pipeline_nl_feedback"
        )

        if nl_feedback and st.button("🔄 추천 조정", key="refine_recommendations"):
            with st.spinner("🤖 자연어 피드백 반영 중..."):
                disease_name = st.session_state.pipeline_disease_name
                current_recommended = st.session_state.pipeline_recommended

                refined = pipeline.refine_recommendations_with_nl(
                    disease_name,
                    current_recommended,
                    nl_feedback
                )
                st.session_state.pipeline_recommended = refined

                # Reset checkboxes
                st.session_state.pipeline_checkboxes = {}
                for recipe_name in refined:
                    st.session_state.pipeline_checkboxes[recipe_name] = True

                # No need for st.rerun() - Streamlit automatically reruns after button click

    def _render_final_execution(self, pipeline: DiseaseAnalysisPipeline):
        """Render final execution button"""
        st.divider()
        st.subheader("5️⃣ 최종 실행")

        approved_count = sum(
            1 for checked in st.session_state.pipeline_checkboxes.values()
            if checked
        )
        total_count = 4 + approved_count

        st.info(
            f"총 **{total_count}개** 레시피가 실행됩니다 "
            f"(핵심 4개 + 선택 {approved_count}개)"
        )

        if st.button(
            f"🚀 {total_count}개 레시피 실행",
            type="primary",
            key="execute_pipeline"
        ):
            # Get approved recipes
            approved_recipes = [
                name for name, checked in st.session_state.pipeline_checkboxes.items()
                if checked
            ]

            with st.spinner(f"⏳ {total_count}개 레시피 실행 중..."):
                # Execute approved recipes
                approved_results = pipeline.execute_approved_recipes(
                    st.session_state.pipeline_disease_name,
                    approved_recipes
                )

                # Combine with core results
                all_results = st.session_state.pipeline_core_results + approved_results

                # Calculate success rate
                success_count = sum(1 for r in all_results if r.get('success', False))
                success_rate = success_count / len(all_results) if all_results else 0

                # Store results
                st.session_state.pipeline_final_results = all_results
                st.session_state.pipeline_success_rate = success_rate

            st.success(
                f"✅ 분석 완료! 성공률: {success_rate*100:.1f}% "
                f"({success_count}/{len(all_results)})"
            )
            st.balloons()

    def _render_final_results(self):
        """Render final analysis results"""
        st.divider()
        st.header("📊 분석 결과")

        results = st.session_state.pipeline_final_results
        success_rate = st.session_state.pipeline_success_rate

        # Summary metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("총 실행 레시피", len(results))
        with col2:
            success_count = sum(1 for r in results if r.get('success', False))
            st.metric("성공", success_count)
        with col3:
            st.metric("성공률", f"{success_rate*100:.1f}%")

        # Display each result
        st.subheader("상세 결과")
        for idx, result in enumerate(results, 1):
            recipe_name = result.get('recipe_name', 'Unknown')
            success = result.get('success', False)

            if success:
                with st.expander(f"✅ {idx}. {recipe_name}", expanded=False):
                    metadata = result.get('metadata', {})
                    st.markdown(f"**설명:** {metadata.get('description', 'N/A')}")

                    params = result.get('parameters', {})
                    if params:
                        st.markdown("**파라미터:**")
                        st.json(params)

                    st.markdown("**생성된 SQL:**")
                    st.code(result.get('sql_query', 'No SQL'), language='sql')
            else:
                with st.expander(f"❌ {idx}. {recipe_name} - 실패", expanded=False):
                    st.error(f"오류: {result.get('error', 'Unknown error')}")
