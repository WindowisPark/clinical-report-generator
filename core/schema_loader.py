"""
Database Schema Loader for RAG-enhanced SQL generation
Databricks 스키마 정보를 로드하고 RAG 검색을 지원
"""

import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class ColumnInfo:
    """컬럼 정보"""
    table_name: str
    column_name: str
    korean_name: str
    description: str
    data_type: str
    column_type: str
    nullable: str
    keywords: str
    category: str
    importance: str


class SchemaLoader:
    """Databricks 스키마 로더 (RAG용)"""

    def __init__(self, schema_path: str = "databricks_schema_for_rag.csv") -> None:
        """
        Initialize schema loader

        Args:
            schema_path: RAG용 스키마 CSV 파일 경로
        """
        self.schema_path = Path(schema_path)
        self.schema_df: pd.DataFrame = self._load_schema()

    def _load_schema(self) -> pd.DataFrame:
        """스키마 CSV 로드"""
        import logging
        logger = logging.getLogger(__name__)

        if not self.schema_path.exists():
            raise FileNotFoundError(
                f"Schema file not found: {self.schema_path}\n"
                "Please run the schema preparation script first."
            )

        df = pd.read_csv(self.schema_path, encoding='utf-8-sig')
        logger.info(f"Loaded schema: {len(df)} columns from {df['테이블명'].nunique()} tables")
        return df

    def get_relevant_schema(
        self,
        query: str,
        top_k: int = 30,
        include_core_tables: bool = True
    ) -> pd.DataFrame:
        """
        사용자 쿼리에서 관련 스키마 추출 (핵심 테이블 우선 포함)

        Args:
            query: 사용자 쿼리 (자연어)
            top_k: 반환할 최대 컬럼 수
            include_core_tables: 핵심 테이블 자동 포함 여부

        Returns:
            관련 스키마 DataFrame (점수 순 정렬)
        """
        # 1. 핵심 테이블 먼저 포함 (항상)
        core_tables = ['basic_treatment', 'prescribed_drug', 'insured_person']

        if include_core_tables:
            core_schema = self.schema_df[
                self.schema_df['테이블명'].str.lower().isin(core_tables)
            ].copy()
            core_schema['relevance_score'] = 0.8  # 높은 기본 점수
        else:
            core_schema = pd.DataFrame()

        # 2. 쿼리 기반 추가 검색
        query_lower = query.lower()
        import re
        query_words = [w for w in re.findall(r'[\w]+', query_lower) if len(w) > 1]

        def calculate_score(row) -> float:
            search_text = row['search_text']
            if pd.isna(search_text):
                return 0.0

            search_lower = str(search_text).lower()
            table_name = row['테이블명'].lower()

            # 핵심 테이블은 이미 포함되었으므로 스킵
            if table_name in core_tables:
                return 0.0

            # 부분 매칭 점수
            matches = sum(1 for word in query_words if word in search_lower)

            # 키워드 가중치
            important_keywords = ['환자', '질환', '질병', '약물', '처방', '병원', '나이', '연령', '성별', '지역', 'user', 'hospital']
            bonus = sum(0.3 for kw in important_keywords if kw in query_lower and kw in search_lower)

            return matches * 0.1 + bonus

        self.schema_df['relevance_score'] = self.schema_df.apply(calculate_score, axis=1)

        # 점수 있는 것만 필터링
        additional_schema = self.schema_df[self.schema_df['relevance_score'] > 0].copy()
        additional_schema = additional_schema.sort_values('relevance_score', ascending=False)

        # 3. 핵심 테이블 + 추가 스키마 병합
        if len(core_schema) > 0 and len(additional_schema) > 0:
            # 핵심 테이블 + top_k 추가
            remaining = max(0, top_k - len(core_schema))
            combined = pd.concat([core_schema, additional_schema.head(remaining)], ignore_index=True)
        elif len(core_schema) > 0:
            combined = core_schema
        else:
            combined = additional_schema.head(top_k)

        return combined.sort_values('relevance_score', ascending=False)

    def get_table_schema(self, table_name: str) -> pd.DataFrame:
        """특정 테이블의 전체 스키마 반환"""
        return self.schema_df[
            self.schema_df['테이블명'].str.lower() == table_name.lower()
        ].copy()

    def get_core_tables_schema(self) -> pd.DataFrame:
        """핵심 테이블들의 스키마만 반환"""
        core_tables = ['basic_treatment', 'prescribed_drug', 'insured_person', 'user', 'hospital']
        return self.schema_df[
            self.schema_df['테이블명'].str.lower().isin([t.lower() for t in core_tables])
        ].copy()

    def format_schema_for_llm(self, schema_df: pd.DataFrame) -> str:
        """
        스키마를 LLM 프롬프트용 텍스트로 포맷팅

        Args:
            schema_df: 스키마 DataFrame

        Returns:
            LLM용 포맷팅된 스키마 텍스트
        """
        if len(schema_df) == 0:
            return "No relevant schema found."

        # 테이블별로 그룹핑
        tables = schema_df.groupby('테이블명')

        formatted_lines = []
        formatted_lines.append("=== Database Schema Information ===\n")

        for table_name, cols in tables:
            formatted_lines.append(f"**Table: {table_name}**")

            for _, col in cols.iterrows():
                col_info = (
                    f"  - {col['컬럼명']} ({col['한글명']}): "
                    f"{col['데이터타입']} "
                    f"{'[NULL 허용]' if col['NULL허용'] == '예' else '[NOT NULL]'}"
                )

                if pd.notna(col['설명']) and col['설명']:
                    col_info += f"\n    설명: {col['설명']}"

                if pd.notna(col['키워드']) and col['키워드']:
                    col_info += f"\n    키워드: {col['키워드']}"

                formatted_lines.append(col_info)

            formatted_lines.append("")  # 테이블 간 빈 줄

        return "\n".join(formatted_lines)

    def get_table_list(self) -> List[str]:
        """전체 테이블 목록 반환"""
        return sorted(self.schema_df['테이블명'].unique().tolist())

    def get_column_count(self) -> Dict[str, int]:
        """테이블별 컬럼 수 반환"""
        return self.schema_df.groupby('테이블명').size().to_dict()
