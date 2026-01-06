"""
Monitoring Dashboard Tab
시스템 성능 모니터링 및 로그 분석 대시보드
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta

from utils.log_analyzer import LogAnalyzer


class MonitoringTab:
    """모니터링 대시보드 탭"""

    def __init__(self):
        self.analyzer = LogAnalyzer()

    def render(self):
        """대시보드 렌더링"""
        st.header("📊 시스템 모니터링 대시보드")
        st.markdown("NL2SQL 생성 및 쿼리 실행 성능을 실시간 모니터링합니다.")

        # 새로고침 버튼
        col1, col2, col3 = st.columns([1, 1, 4])
        with col1:
            if st.button("🔄 새로고침", use_container_width=True):
                st.rerun()
        with col2:
            days = st.selectbox("조회 기간", [1, 7, 30], index=1)

        st.markdown("---")

        # 요약 통계
        self._render_summary_stats(days)

        st.markdown("---")

        # 성능 차트
        col1, col2 = st.columns(2)
        with col1:
            self._render_nl2sql_chart(days)
        with col2:
            self._render_execution_time_chart(days)

        st.markdown("---")

        # RAG 사용 통계
        self._render_rag_stats()

        st.markdown("---")

        # 최근 에러
        self._render_recent_errors()

    def _render_summary_stats(self, days: int):
        """요약 통계 카드"""
        st.subheader("📈 요약 통계")

        stats = self.analyzer.get_summary_stats(days=days)

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                label="SQL 생성 성공률",
                value=f"{stats['nl2sql']['success_rate']:.1f}%",
                delta=f"{stats['nl2sql']['success']}/{stats['nl2sql']['total']}"
            )

        with col2:
            st.metric(
                label="RAG 사용률",
                value=f"{stats['nl2sql']['rag_rate']:.1f}%",
                delta=f"{stats['nl2sql']['rag_usage']} 건"
            )

        with col3:
            st.metric(
                label="쿼리 실행 성공률",
                value=f"{stats['databricks']['success_rate']:.1f}%",
                delta=f"{stats['databricks']['success']}/{stats['databricks']['total']}"
            )

        with col4:
            st.metric(
                label="평균 실행 시간",
                value=f"{stats['databricks']['avg_time']:.2f}s",
                delta=f"{stats['databricks']['total_rows']:,} rows"
            )

    def _render_nl2sql_chart(self, days: int):
        """NL2SQL 생성 성공률 차트"""
        st.subheader("🔍 SQL 생성 추이")

        # 날짜별 데이터 수집
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        daily_data = []
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            df = self.analyzer.parse_nl2sql_logs(date_str)

            if not df.empty:
                total = len(df)
                success = len(df[df['status'] == 'SUCCESS'])
                failed = total - success

                daily_data.append({
                    'date': current_date,
                    'success': success,
                    'failed': failed,
                    'total': total
                })

            current_date += timedelta(days=1)

        if daily_data:
            df_daily = pd.DataFrame(daily_data)

            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=df_daily['date'],
                y=df_daily['success'],
                name='Success',
                marker_color='#2ecc71'
            ))
            fig.add_trace(go.Bar(
                x=df_daily['date'],
                y=df_daily['failed'],
                name='Failed',
                marker_color='#e74c3c'
            ))

            fig.update_layout(
                barmode='stack',
                height=300,
                margin=dict(l=0, r=0, t=30, b=0),
                xaxis_title="날짜",
                yaxis_title="건수",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("데이터가 없습니다. 쿼리를 생성해보세요.")

    def _render_execution_time_chart(self, days: int):
        """쿼리 실행 시간 분포"""
        st.subheader("⏱️ 실행 시간 분포")

        # 최근 N일 데이터
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        all_records = []
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            df = self.analyzer.parse_databricks_logs(date_str)

            if not df.empty:
                success_df = df[df['status'] == 'SUCCESS']
                if not success_df.empty:
                    all_records.append(success_df)

            current_date += timedelta(days=1)

        if all_records:
            combined_df = pd.concat(all_records, ignore_index=True)

            fig = px.histogram(
                combined_df,
                x='execution_time',
                nbins=20,
                labels={'execution_time': '실행 시간 (초)', 'count': '건수'},
                color_discrete_sequence=['#3498db']
            )

            fig.update_layout(
                height=300,
                margin=dict(l=0, r=0, t=30, b=0),
                showlegend=False
            )

            st.plotly_chart(fig, use_container_width=True)

            # 통계 정보
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("평균", f"{combined_df['execution_time'].mean():.2f}s")
            with col2:
                st.metric("중앙값", f"{combined_df['execution_time'].median():.2f}s")
            with col3:
                st.metric("최대", f"{combined_df['execution_time'].max():.2f}s")
        else:
            st.info("데이터가 없습니다. 쿼리를 실행해보세요.")

    def _render_rag_stats(self):
        """RAG 질병 코드 사용 통계"""
        st.subheader("💡 RAG 질병 코드 사용 현황")

        # 오늘 데이터
        today_df = self.analyzer.parse_nl2sql_logs()

        if not today_df.empty:
            # RAG 사용 여부
            rag_used = len(today_df[today_df['rag_detected'] == True])
            total = len(today_df)

            col1, col2 = st.columns([1, 2])

            with col1:
                # 파이 차트
                fig = go.Figure(data=[go.Pie(
                    labels=['RAG 사용', 'RAG 미사용'],
                    values=[rag_used, total - rag_used],
                    hole=0.4,
                    marker=dict(colors=['#2ecc71', '#95a5a6'])
                )])

                fig.update_layout(
                    height=250,
                    margin=dict(l=0, r=0, t=0, b=0),
                    showlegend=True
                )

                st.plotly_chart(fig, use_container_width=True)

            with col2:
                # 질병 코드별 사용 빈도
                rag_records = today_df[today_df['rag_detected'] == True]

                if not rag_records.empty:
                    # 코드 카운트
                    code_counts = {}
                    for codes_str in rag_records['disease_codes']:
                        if codes_str:
                            codes = codes_str.split(',')
                            for code in codes:
                                code_counts[code] = code_counts.get(code, 0) + 1

                    if code_counts:
                        code_df = pd.DataFrame([
                            {'질병 코드': code, '사용 횟수': count}
                            for code, count in sorted(code_counts.items(), key=lambda x: x[1], reverse=True)
                        ])

                        st.dataframe(code_df, use_container_width=True, hide_index=True)
                    else:
                        st.info("질병 코드 데이터가 없습니다.")
                else:
                    st.info("RAG가 사용된 쿼리가 없습니다.")
        else:
            st.info("오늘 생성된 쿼리가 없습니다.")

    def _render_recent_errors(self):
        """최근 에러 목록"""
        st.subheader("❌ 최근 에러 (최근 10건)")

        errors = self.analyzer.get_recent_errors(limit=10)

        if errors:
            for i, error in enumerate(errors, 1):
                with st.expander(
                    f"#{i} [{error['type']}] {error['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}"
                ):
                    st.write(f"**쿼리**: {error['query']}")
                    if 'error' in error:
                        st.error(f"**에러**: {error['error']}")
        else:
            st.success("✅ 최근 에러가 없습니다!")


def render():
    """모니터링 탭 렌더링 (외부 호출용)"""
    tab = MonitoringTab()
    tab.render()
