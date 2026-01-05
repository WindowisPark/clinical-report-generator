"""
Interactive Chart Builder Component
사용자가 결과 데이터를 다양한 차트로 시각화할 수 있는 컴포넌트
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Optional, List, Dict
from utils.chart_recommender import ChartRecommender


class ChartBuilder:
    """인터랙티브 차트 빌더"""

    CHART_TYPES = {
        'bar': {'name': '📊 막대 차트', 'icon': '📊'},
        'line': {'name': '📈 선 차트', 'icon': '📈'},
        'scatter': {'name': '📍 산점도', 'icon': '📍'},
        'line_scatter': {'name': '📉 선+점 차트', 'icon': '📉'},
        'pie': {'name': '🥧 파이 차트', 'icon': '🥧'},
        'area': {'name': '📊 영역 차트', 'icon': '📊'},
        'box': {'name': '📦 박스 플롯', 'icon': '📦'},
        'histogram': {'name': '📊 히스토그램', 'icon': '📊'}
    }

    COLOR_SCHEMES = {
        'clinical': 'Clinical (의료 리포트)',
        'nature': 'Nature (학술 저널)',
        'science': 'Science (과학 저널)',
        'colorblind': 'Colorblind Safe (색맹 친화)',
        'blue_gradient': 'Blue Gradient (블루 그라데이션)',
        'professional': 'Professional (비즈니스)',
        'default': 'Plotly Default'
    }

    def __init__(self, df: pd.DataFrame, key_prefix: str = "chart"):
        """
        초기화

        Args:
            df: 차트로 표시할 DataFrame
            key_prefix: Streamlit 위젯 키 접두사
        """
        self.df = df
        self.key_prefix = key_prefix

    def render(self):
        """차트 빌더 UI 렌더링"""
        if len(self.df) == 0:
            st.info("데이터가 없어서 차트를 생성할 수 없습니다.")
            return

        st.subheader("📊 데이터 시각화")

        # 자동 추천 시스템
        recommender = ChartRecommender(self.df)
        recommendation = recommender.recommend()

        # 추천 알림
        st.info(f"💡 **추천**: {self.CHART_TYPES[recommendation['chart_type']]['name']} - {recommendation['reason']}")

        # 차트 설정 섹션
        with st.expander("⚙️ 차트 설정", expanded=True):
            config = self._render_chart_config(recommendation)

        # 차트 생성
        if config:
            self._render_chart(config)

    def _render_chart_config(self, recommendation: Dict) -> Optional[Dict]:
        """차트 설정 UI 렌더링"""
        col1, col2, col3 = st.columns(3)

        # 추천 차트를 기본값으로 설정
        chart_types_list = list(self.CHART_TYPES.keys())
        default_chart_idx = chart_types_list.index(recommendation['chart_type']) if recommendation['chart_type'] in chart_types_list else 0

        with col1:
            # 차트 유형 선택
            chart_type = st.selectbox(
                "차트 유형",
                options=chart_types_list,
                format_func=lambda x: self.CHART_TYPES[x]['name'],
                index=default_chart_idx,
                key=f"{self.key_prefix}_chart_type"
            )

        # 사용 가능한 컬럼 분석
        numeric_cols = self._get_numeric_columns()
        categorical_cols = self._get_categorical_columns()
        all_cols = list(self.df.columns)

        # 추천 컬럼을 기본값으로 설정
        with col2:
            # X축 선택
            x_options = all_cols if chart_type != 'pie' else categorical_cols
            default_x_idx = 0
            if recommendation['x_column'] and recommendation['x_column'] in x_options:
                default_x_idx = x_options.index(recommendation['x_column'])

            x_col = st.selectbox(
                "X축" if chart_type != 'pie' else "카테고리",
                options=x_options,
                index=default_x_idx,
                key=f"{self.key_prefix}_x_col"
            )

        with col3:
            # Y축 선택
            y_options = numeric_cols if numeric_cols else all_cols
            default_y_idx = 0
            if recommendation['y_column'] and recommendation['y_column'] in y_options:
                default_y_idx = y_options.index(recommendation['y_column'])
            elif chart_type in ['pie', 'histogram'] and len(y_options) > 0:
                default_y_idx = 0

            if chart_type in ['pie', 'histogram']:
                y_col = st.selectbox(
                    "값",
                    options=y_options,
                    index=default_y_idx,
                    key=f"{self.key_prefix}_y_col"
                )
            else:
                y_col = st.selectbox(
                    "Y축",
                    options=y_options,
                    index=default_y_idx,
                    key=f"{self.key_prefix}_y_col"
                )

        # 고급 설정
        col4, col5 = st.columns(2)

        with col4:
            color_scheme = st.selectbox(
                "색상 테마",
                options=list(self.COLOR_SCHEMES.keys()),
                format_func=lambda x: self.COLOR_SCHEMES[x],
                key=f"{self.key_prefix}_color"
            )

        with col5:
            show_legend = st.checkbox(
                "범례 표시",
                value=True,
                key=f"{self.key_prefix}_legend"
            )

        # 차트 제목
        chart_title = st.text_input(
            "차트 제목 (선택사항)",
            value=f"{y_col} by {x_col}",
            key=f"{self.key_prefix}_title"
        )

        return {
            'chart_type': chart_type,
            'x_col': x_col,
            'y_col': y_col,
            'color_scheme': color_scheme,
            'show_legend': show_legend,
            'title': chart_title
        }

    def _get_color_sequence(self, color_scheme: str):
        """색상 스킴을 Plotly 색상 시퀀스로 변환"""
        color_map = {
            # 의료 리포트용 - 신뢰감 있는 블루/그린 계열
            'clinical': ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#6A994E', '#BC4B51'],

            # Nature 저널 스타일 - 과학 논문용
            'nature': ['#E64B35', '#4DBBD5', '#00A087', '#3C5488', '#F39B7F', '#8491B4'],

            # Science 저널 스타일
            'science': ['#3B4992', '#EE0000', '#008B45', '#631879', '#008280', '#BB0021'],

            # 색맹 친화 (Okabe-Ito palette)
            'colorblind': ['#E69F00', '#56B4E9', '#009E73', '#F0E442', '#0072B2', '#D55E00', '#CC79A7'],

            # 블루 그라데이션 (단일색 계열)
            'blue_gradient': ['#08519c', '#3182bd', '#6baed6', '#9ecae1', '#c6dbef', '#deebf7'],

            # 비즈니스 프로페셔널
            'professional': ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b'],

            # Plotly 기본
            'default': px.colors.qualitative.Plotly
        }
        return color_map.get(color_scheme, color_map['clinical'])

    def _apply_professional_layout(self, fig: go.Figure, config: Dict):
        """전문적인 레이아웃 스타일 적용"""
        fig.update_layout(
            # 폰트 설정 - 학술/전문 문서 스타일
            font=dict(
                family="Arial, Helvetica, sans-serif",
                size=12,
                color="#2b2b2b"
            ),
            title=dict(
                font=dict(size=16, color="#1a1a1a", family="Arial Black, sans-serif"),
                x=0.5,
                xanchor='center',
                y=0.95,
                yanchor='top'
            ),

            # 배경 설정
            plot_bgcolor='white',
            paper_bgcolor='white',

            # 축 스타일
            xaxis=dict(
                showgrid=True,
                gridwidth=0.5,
                gridcolor='#e0e0e0',
                linecolor='#2b2b2b',
                linewidth=1.5,
                mirror=True,
                ticks='outside',
                tickfont=dict(size=11),
                title_font=dict(size=13, color="#1a1a1a")
            ),
            yaxis=dict(
                showgrid=True,
                gridwidth=0.5,
                gridcolor='#e0e0e0',
                linecolor='#2b2b2b',
                linewidth=1.5,
                mirror=True,
                ticks='outside',
                tickfont=dict(size=11),
                title_font=dict(size=13, color="#1a1a1a"),
                separatethousands=True  # 천단위 콤마
            ),

            # 범례 설정
            legend=dict(
                bgcolor='rgba(255, 255, 255, 0.9)',
                bordercolor='#2b2b2b',
                borderwidth=1,
                font=dict(size=11),
                orientation='v',
                yanchor='top',
                y=0.99,
                xanchor='right',
                x=0.99
            ),

            # 여백 설정
            margin=dict(l=80, r=80, t=100, b=80),

            # 기타
            showlegend=config['show_legend'],
            height=600,  # 500 → 600으로 증가
            hovermode='closest'
        )

        return fig

    def _render_chart(self, config: Dict):
        """선택된 설정으로 차트 렌더링"""
        chart_type = config['chart_type']

        # 차트 생성
        try:
            if chart_type == 'bar':
                fig = self._create_bar_chart(config)
            elif chart_type == 'line':
                fig = self._create_line_chart(config)
            elif chart_type == 'scatter':
                fig = self._create_scatter_chart(config)
            elif chart_type == 'line_scatter':
                fig = self._create_line_scatter_chart(config)
            elif chart_type == 'pie':
                fig = self._create_pie_chart(config)
            elif chart_type == 'area':
                fig = self._create_area_chart(config)
            elif chart_type == 'box':
                fig = self._create_box_chart(config)
            elif chart_type == 'histogram':
                fig = self._create_histogram(config)
            else:
                st.error(f"지원하지 않는 차트 유형: {chart_type}")
                return

            # 전문적인 레이아웃 적용
            fig = self._apply_professional_layout(fig, config)

            # 차트 표시
            st.plotly_chart(fig, use_container_width=True)

            # 이미지 다운로드 버튼
            self._render_export_buttons(fig)

        except Exception as e:
            st.error(f"차트 생성 실패: {e}")
            st.info("다른 컬럼을 선택하거나 차트 유형을 변경해보세요.")

    def _create_bar_chart(self, config: Dict) -> go.Figure:
        """막대 차트 생성"""
        colors = self._get_color_sequence(config['color_scheme'])
        fig = px.bar(
            self.df,
            x=config['x_col'],
            y=config['y_col'],
            title=config['title'],
            color_discrete_sequence=colors
        )
        # 막대 스타일 개선
        fig.update_traces(
            marker=dict(
                line=dict(color='#2b2b2b', width=0.5),  # 테두리
                opacity=0.9
            ),
            texttemplate='%{y:,.0f}',
            textposition='outside'
        )
        return fig

    def _create_line_chart(self, config: Dict) -> go.Figure:
        """선 차트 생성"""
        colors = self._get_color_sequence(config['color_scheme'])
        fig = px.line(
            self.df,
            x=config['x_col'],
            y=config['y_col'],
            title=config['title'],
            markers=False,
            color_discrete_sequence=colors
        )
        # 선 스타일 개선
        fig.update_traces(
            line=dict(width=2.5),  # 선 두께 증가
            opacity=0.9
        )
        return fig

    def _create_scatter_chart(self, config: Dict) -> go.Figure:
        """산점도 생성"""
        colors = self._get_color_sequence(config['color_scheme'])
        fig = px.scatter(
            self.df,
            x=config['x_col'],
            y=config['y_col'],
            title=config['title'],
            color_discrete_sequence=colors
        )
        # 마커 스타일 개선
        fig.update_traces(
            marker=dict(
                size=10,
                line=dict(color='white', width=1),
                opacity=0.8
            )
        )
        return fig

    def _create_line_scatter_chart(self, config: Dict) -> go.Figure:
        """선+점 차트 생성"""
        colors = self._get_color_sequence(config['color_scheme'])
        fig = px.line(
            self.df,
            x=config['x_col'],
            y=config['y_col'],
            title=config['title'],
            markers=True,
            color_discrete_sequence=colors
        )
        # 선+마커 스타일 개선
        fig.update_traces(
            line=dict(width=2.5),
            marker=dict(
                size=10,
                line=dict(color='white', width=1.5),
                opacity=0.9
            )
        )
        return fig

    def _create_pie_chart(self, config: Dict) -> go.Figure:
        """파이 차트 생성"""
        colors = self._get_color_sequence(config['color_scheme'])
        fig = px.pie(
            self.df,
            names=config['x_col'],
            values=config['y_col'],
            title=config['title'],
            color_discrete_sequence=colors
        )
        # 파이 차트 스타일 개선
        fig.update_traces(
            textposition='inside',
            textinfo='percent+label',
            textfont_size=12,
            marker=dict(
                line=dict(color='white', width=2)
            ),
            pull=[0.05] * len(self.df)  # 약간 분리 효과
        )
        return fig

    def _create_area_chart(self, config: Dict) -> go.Figure:
        """영역 차트 생성"""
        colors = self._get_color_sequence(config['color_scheme'])
        fig = px.area(
            self.df,
            x=config['x_col'],
            y=config['y_col'],
            title=config['title'],
            color_discrete_sequence=colors
        )
        # 영역 차트 스타일 개선
        fig.update_traces(
            line=dict(width=2),
            opacity=0.6
        )
        return fig

    def _create_box_chart(self, config: Dict) -> go.Figure:
        """박스 플롯 생성"""
        colors = self._get_color_sequence(config['color_scheme'])
        fig = px.box(
            self.df,
            x=config['x_col'],
            y=config['y_col'],
            title=config['title'],
            color_discrete_sequence=colors
        )
        # 박스 플롯 스타일 개선
        fig.update_traces(
            marker=dict(
                size=6,
                line=dict(width=1.5)
            ),
            line=dict(width=1.5),
            opacity=0.8
        )
        return fig

    def _create_histogram(self, config: Dict) -> go.Figure:
        """히스토그램 생성"""
        colors = self._get_color_sequence(config['color_scheme'])
        fig = px.histogram(
            self.df,
            x=config['y_col'],
            title=config['title'],
            nbins=30,
            color_discrete_sequence=colors
        )
        # 히스토그램 스타일 개선
        fig.update_traces(
            marker=dict(
                line=dict(color='#2b2b2b', width=1),
                opacity=0.8
            )
        )
        return fig

    def _render_export_buttons(self, fig: go.Figure):
        """차트 이미지 export 버튼"""
        col1, col2, col3, col4 = st.columns([1, 1, 1, 6])

        with col1:
            # PNG 다운로드 (고해상도 - 300 DPI 상당)
            png_bytes = fig.to_image(
                format="png",
                width=1920,  # 1200 → 1920 (Full HD)
                height=1080,  # 800 → 1080
                scale=2  # 레티나 디스플레이 품질
            )
            st.download_button(
                label="📥 PNG",
                data=png_bytes,
                file_name="chart_hq.png",
                mime="image/png",
                key=f"{self.key_prefix}_png"
            )

        with col2:
            # SVG 다운로드 (벡터 - 무한 확대 가능)
            svg_bytes = fig.to_image(
                format="svg",
                width=1920,
                height=1080
            )
            st.download_button(
                label="📥 SVG",
                data=svg_bytes,
                file_name="chart.svg",
                mime="image/svg+xml",
                key=f"{self.key_prefix}_svg"
            )

        with col3:
            # HTML 다운로드 (인터랙티브)
            html_str = fig.to_html()
            st.download_button(
                label="📥 HTML",
                data=html_str,
                file_name="chart_interactive.html",
                mime="text/html",
                key=f"{self.key_prefix}_html"
            )

    def _get_numeric_columns(self) -> List[str]:
        """숫자형 컬럼 목록 반환"""
        return [col for col in self.df.columns
                if pd.api.types.is_numeric_dtype(self.df[col])]

    def _get_categorical_columns(self) -> List[str]:
        """카테고리형 컬럼 목록 반환"""
        return [col for col in self.df.columns
                if self.df[col].dtype == 'object' or
                self.df[col].nunique() < 20]
