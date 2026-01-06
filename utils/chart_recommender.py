"""
Chart Recommendation Engine
데이터 패턴을 분석하여 최적의 차트 타입을 자동 추천
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime


class ChartRecommender:
    """데이터 분석 기반 차트 추천 엔진"""

    def __init__(self, df: pd.DataFrame):
        """
        초기화

        Args:
            df: 분석할 DataFrame
        """
        self.df = df
        self.column_types = self._analyze_column_types()
        self.data_shape = self._analyze_data_shape()

    def _analyze_column_types(self) -> Dict[str, Dict]:
        """컬럼별 타입 및 특성 분석"""
        analysis = {}

        for col in self.df.columns:
            col_data = self.df[col]
            analysis[col] = {
                'dtype': str(col_data.dtype),
                'unique_count': col_data.nunique(),
                'null_count': col_data.isnull().sum(),
                'null_ratio': col_data.isnull().sum() / len(col_data),
                'is_numeric': pd.api.types.is_numeric_dtype(col_data),
                'is_datetime': pd.api.types.is_datetime64_any_dtype(col_data),
                'is_categorical': self._is_categorical(col_data),
                'is_binary': col_data.nunique() == 2,
                'cardinality': self._get_cardinality(col_data)
            }

            # 숫자형 컬럼 통계
            if analysis[col]['is_numeric']:
                analysis[col].update({
                    'mean': float(col_data.mean()),
                    'std': float(col_data.std()),
                    'min': float(col_data.min()),
                    'max': float(col_data.max()),
                    'range': float(col_data.max() - col_data.min())
                })

        return analysis

    def _is_categorical(self, series: pd.Series) -> bool:
        """카테고리형 데이터 여부 판단"""
        if pd.api.types.is_numeric_dtype(series):
            # 고유값이 적고(<=10) 정수형이면 카테고리로 간주
            if series.nunique() <= 10 and all(series.dropna().apply(lambda x: float(x).is_integer())):
                return True
            return False
        return True

    def _get_cardinality(self, series: pd.Series) -> str:
        """카디널리티 분류"""
        unique_count = series.nunique()
        total_count = len(series)
        ratio = unique_count / total_count if total_count > 0 else 0

        if unique_count <= 2:
            return 'binary'
        elif unique_count <= 10:
            return 'low'
        elif unique_count <= 50 or ratio < 0.5:
            return 'medium'
        else:
            return 'high'

    def _analyze_data_shape(self) -> Dict:
        """데이터 구조 분석"""
        numeric_cols = [col for col, info in self.column_types.items() if info['is_numeric']]
        categorical_cols = [col for col, info in self.column_types.items() if info['is_categorical']]

        return {
            'row_count': len(self.df),
            'col_count': len(self.df.columns),
            'numeric_count': len(numeric_cols),
            'categorical_count': len(categorical_cols),
            'has_datetime': any(info['is_datetime'] for info in self.column_types.values()),
            'has_high_cardinality': any(info['cardinality'] == 'high' for info in self.column_types.values())
        }

    def recommend(self) -> Dict[str, any]:
        """
        최적 차트 추천

        Returns:
            {
                'chart_type': str,  # 추천 차트 타입
                'x_column': str,     # X축 컬럼
                'y_column': str,     # Y축 컬럼 (optional)
                'color_column': str, # 색상 구분 컬럼 (optional)
                'reason': str,       # 추천 이유
                'confidence': float, # 확신도 (0-1)
                'alternatives': List[str]  # 대안 차트 타입들
            }
        """
        # 1. 컬럼 수가 1개인 경우
        if self.data_shape['col_count'] == 1:
            return self._recommend_single_column()

        # 2. 컬럼 수가 2개인 경우
        if self.data_shape['col_count'] == 2:
            return self._recommend_two_columns()

        # 3. 컬럼 수가 3개 이상인 경우
        return self._recommend_multi_columns()

    def _recommend_single_column(self) -> Dict:
        """단일 컬럼 차트 추천"""
        col = self.df.columns[0]
        col_info = self.column_types[col]

        if col_info['is_numeric']:
            return {
                'chart_type': 'histogram',
                'x_column': col,
                'y_column': None,
                'color_column': None,
                'reason': f"숫자형 데이터 '{col}'의 분포를 히스토그램으로 표시",
                'confidence': 0.9,
                'alternatives': ['box']
            }
        else:
            # 카테고리형 빈도 분석
            value_counts = self.df[col].value_counts()
            if len(value_counts) <= 10:
                return {
                    'chart_type': 'bar',
                    'x_column': col,
                    'y_column': None,
                    'color_column': None,
                    'reason': f"카테고리 '{col}'의 빈도를 막대 차트로 표시",
                    'confidence': 0.85,
                    'alternatives': ['pie']
                }
            else:
                return {
                    'chart_type': 'bar',
                    'x_column': col,
                    'y_column': None,
                    'color_column': None,
                    'reason': f"카테고리 '{col}'의 상위 항목을 막대 차트로 표시",
                    'confidence': 0.75,
                    'alternatives': []
                }

    def _recommend_two_columns(self) -> Dict:
        """2개 컬럼 차트 추천"""
        cols = list(self.df.columns)
        col1_info = self.column_types[cols[0]]
        col2_info = self.column_types[cols[1]]

        # Pattern 1: 카테고리 + 숫자
        if col1_info['is_categorical'] and col2_info['is_numeric']:
            x_col, y_col = cols[0], cols[1]
            cardinality = col1_info['cardinality']

            if cardinality in ['binary', 'low']:
                # 카테고리가 적으면 파이 or 막대
                if col1_info['unique_count'] <= 5:
                    return {
                        'chart_type': 'pie',
                        'x_column': x_col,
                        'y_column': y_col,
                        'color_column': None,
                        'reason': f"'{x_col}' 카테고리별 '{y_col}' 비율 비교 (파이 차트)",
                        'confidence': 0.8,
                        'alternatives': ['bar']
                    }
                else:
                    return {
                        'chart_type': 'bar',
                        'x_column': x_col,
                        'y_column': y_col,
                        'color_column': None,
                        'reason': f"'{x_col}' 카테고리별 '{y_col}' 값 비교 (막대 차트)",
                        'confidence': 0.85,
                        'alternatives': ['line']
                    }
            else:
                # 카테고리가 많으면 막대 (상위 N개)
                return {
                    'chart_type': 'bar',
                    'x_column': x_col,
                    'y_column': y_col,
                    'color_column': None,
                    'reason': f"'{x_col}' 상위 항목의 '{y_col}' 값 비교 (막대 차트)",
                    'confidence': 0.75,
                    'alternatives': []
                }

        # Pattern 2: 숫자 + 카테고리 (순서 바뀐 경우)
        elif col1_info['is_numeric'] and col2_info['is_categorical']:
            return self._recommend_two_columns()  # 재귀 호출 (컬럼 순서 무관)

        # Pattern 3: 숫자 + 숫자 (산점도)
        elif col1_info['is_numeric'] and col2_info['is_numeric']:
            return {
                'chart_type': 'scatter',
                'x_column': cols[0],
                'y_column': cols[1],
                'color_column': None,
                'reason': f"'{cols[0]}'와 '{cols[1]}' 간 상관관계 분석 (산점도)",
                'confidence': 0.9,
                'alternatives': ['line', 'line_scatter']
            }

        # Pattern 4: 카테고리 + 카테고리
        else:
            return {
                'chart_type': 'bar',
                'x_column': cols[0],
                'y_column': None,
                'color_column': cols[1],
                'color_column': None,
                'reason': f"'{cols[0]}' 및 '{cols[1]}' 교차 분석 (막대 차트)",
                'confidence': 0.6,
                'alternatives': []
            }

    def _recommend_multi_columns(self) -> Dict:
        """3개 이상 컬럼 차트 추천"""
        # 휴리스틱: 첫 번째 카테고리 컬럼 + 첫 번째 숫자 컬럼
        categorical_cols = [col for col, info in self.column_types.items() if info['is_categorical']]
        numeric_cols = [col for col, info in self.column_types.items() if info['is_numeric']]

        if len(categorical_cols) >= 1 and len(numeric_cols) >= 1:
            x_col = categorical_cols[0]
            y_col = numeric_cols[0]

            # 추가 카테고리 컬럼이 있으면 색상으로 사용
            color_col = categorical_cols[1] if len(categorical_cols) >= 2 else None

            cardinality = self.column_types[x_col]['cardinality']

            if cardinality in ['binary', 'low']:
                return {
                    'chart_type': 'bar',
                    'x_column': x_col,
                    'y_column': y_col,
                    'color_column': color_col,
                    'reason': f"'{x_col}' 카테고리별 '{y_col}' 비교" + (f" ('{color_col}'로 구분)" if color_col else ""),
                    'confidence': 0.8,
                    'alternatives': ['line' if cardinality == 'low' else 'scatter']
                }
            else:
                return {
                    'chart_type': 'bar',
                    'x_column': x_col,
                    'y_column': y_col,
                    'color_column': color_col,
                    'reason': f"'{x_col}' 상위 항목의 '{y_col}' 비교",
                    'confidence': 0.7,
                    'alternatives': []
                }

        # 숫자 컬럼만 있는 경우
        elif len(numeric_cols) >= 2:
            return {
                'chart_type': 'line',
                'x_column': numeric_cols[0],
                'y_column': numeric_cols[1],
                'color_column': None,
                'reason': f"'{numeric_cols[0]}'와 '{numeric_cols[1]}' 추세 비교 (선 차트)",
                'confidence': 0.7,
                'alternatives': ['scatter', 'line_scatter']
            }

        # 기본값: 첫 2개 컬럼 막대 차트
        else:
            return {
                'chart_type': 'bar',
                'x_column': self.df.columns[0],
                'y_column': self.df.columns[1] if len(self.df.columns) > 1 else None,
                'color_column': None,
                'reason': "일반적인 비교 분석 (막대 차트)",
                'confidence': 0.5,
                'alternatives': ['line', 'scatter']
            }

    def get_column_suggestions(self) -> Dict[str, List[str]]:
        """
        컬럼 역할별 추천 (ChartBuilder UI용)

        Returns:
            {
                'x_axis': List[str],  # X축 추천 컬럼
                'y_axis': List[str],  # Y축 추천 컬럼
                'color': List[str]    # 색상 구분 추천 컬럼
            }
        """
        categorical_cols = [col for col, info in self.column_types.items() if info['is_categorical']]
        numeric_cols = [col for col, info in self.column_types.items() if info['is_numeric']]

        # X축: 카테고리 우선, 카디널리티 낮은 순
        x_candidates = sorted(
            categorical_cols,
            key=lambda col: self.column_types[col]['unique_count']
        )

        # Y축: 숫자형 컬럼
        y_candidates = numeric_cols

        # 색상: 카디널리티 낮은 카테고리
        color_candidates = [
            col for col in categorical_cols
            if self.column_types[col]['cardinality'] in ['binary', 'low']
        ]

        return {
            'x_axis': x_candidates if x_candidates else list(self.df.columns),
            'y_axis': y_candidates if y_candidates else list(self.df.columns),
            'color': color_candidates
        }


if __name__ == "__main__":
    # 테스트
    test_data = pd.DataFrame({
        '질병명': ['고혈압', '당뇨병', '암', '심장병', '뇌졸중'],
        '환자수': [1500, 1200, 800, 600, 400],
        '평균연령': [65, 58, 62, 70, 68]
    })

    recommender = ChartRecommender(test_data)
    recommendation = recommender.recommend()

    print("=== 추천 결과 ===")
    print(f"차트 타입: {recommendation['chart_type']}")
    print(f"X축: {recommendation['x_column']}")
    print(f"Y축: {recommendation['y_column']}")
    print(f"이유: {recommendation['reason']}")
    print(f"확신도: {recommendation['confidence']}")
    print(f"대안: {recommendation['alternatives']}")
