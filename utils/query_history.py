"""
Query History Management
생성된 SQL 쿼리 히스토리 저장 및 관리
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict


@dataclass
class QueryRecord:
    """쿼리 기록 데이터 클래스"""
    id: str  # 타임스탬프 기반 고유 ID
    timestamp: str  # ISO format
    user_query: str  # 자연어 요청
    sql_query: str  # 생성된 SQL
    success: bool  # 생성 성공 여부
    is_favorite: bool = False  # 즐겨찾기 여부
    executed: bool = False  # 실행 여부
    execution_success: Optional[bool] = None  # 실행 성공 여부
    row_count: Optional[int] = None  # 결과 행 수
    execution_time: Optional[float] = None  # 실행 시간
    tags: List[str] = None  # 태그 (예: ['고혈압', '성별분포'])
    notes: str = ""  # 사용자 메모

    def __post_init__(self):
        if self.tags is None:
            self.tags = []


class QueryHistory:
    """쿼리 히스토리 관리 클래스"""

    def __init__(self, history_file: str = "data/query_history.json"):
        """
        초기화

        Args:
            history_file: 히스토리 저장 파일 경로
        """
        self.history_file = Path(history_file)
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        self._load_history()

    def _load_history(self):
        """히스토리 파일 로드"""
        if self.history_file.exists():
            with open(self.history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.records = [QueryRecord(**record) for record in data]
        else:
            self.records = []

    def _save_history(self):
        """히스토리 파일 저장"""
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(
                [asdict(record) for record in self.records],
                f,
                ensure_ascii=False,
                indent=2
            )

    def add_query(
        self,
        user_query: str,
        sql_query: str,
        success: bool,
        tags: Optional[List[str]] = None
    ) -> str:
        """
        새 쿼리 추가

        Args:
            user_query: 사용자 자연어 요청
            sql_query: 생성된 SQL
            success: 생성 성공 여부
            tags: 태그 리스트

        Returns:
            생성된 쿼리 ID
        """
        # 중복 체크 (같은 SQL이 최근 10개 내에 있으면 추가하지 않음)
        recent_sqls = [r.sql_query for r in self.records[-10:]]
        if sql_query in recent_sqls:
            # 기존 레코드 반환
            for record in reversed(self.records):
                if record.sql_query == sql_query:
                    return record.id

        # 새 레코드 생성
        timestamp = datetime.now()
        record = QueryRecord(
            id=timestamp.strftime("%Y%m%d_%H%M%S_%f"),
            timestamp=timestamp.isoformat(),
            user_query=user_query,
            sql_query=sql_query,
            success=success,
            tags=tags or []
        )

        self.records.append(record)
        self._save_history()
        return record.id

    def update_execution_result(
        self,
        query_id: str,
        execution_success: bool,
        row_count: Optional[int] = None,
        execution_time: Optional[float] = None
    ):
        """
        쿼리 실행 결과 업데이트

        Args:
            query_id: 쿼리 ID
            execution_success: 실행 성공 여부
            row_count: 결과 행 수
            execution_time: 실행 시간
        """
        for record in self.records:
            if record.id == query_id:
                record.executed = True
                record.execution_success = execution_success
                record.row_count = row_count
                record.execution_time = execution_time
                self._save_history()
                break

    def toggle_favorite(self, query_id: str) -> bool:
        """
        즐겨찾기 토글

        Args:
            query_id: 쿼리 ID

        Returns:
            토글 후 즐겨찾기 상태
        """
        for record in self.records:
            if record.id == query_id:
                record.is_favorite = not record.is_favorite
                self._save_history()
                return record.is_favorite
        return False

    def add_note(self, query_id: str, note: str):
        """
        메모 추가

        Args:
            query_id: 쿼리 ID
            note: 메모 내용
        """
        for record in self.records:
            if record.id == query_id:
                record.notes = note
                self._save_history()
                break

    def delete_query(self, query_id: str):
        """
        쿼리 삭제

        Args:
            query_id: 쿼리 ID
        """
        self.records = [r for r in self.records if r.id != query_id]
        self._save_history()

    def get_all(self, reverse: bool = True) -> List[QueryRecord]:
        """
        전체 히스토리 조회

        Args:
            reverse: 최신순 정렬 여부

        Returns:
            쿼리 레코드 리스트
        """
        if reverse:
            return list(reversed(self.records))
        return self.records

    def get_favorites(self) -> List[QueryRecord]:
        """즐겨찾기 쿼리 조회"""
        return [r for r in reversed(self.records) if r.is_favorite]

    def get_recent(self, limit: int = 10) -> List[QueryRecord]:
        """
        최근 쿼리 조회

        Args:
            limit: 조회 개수

        Returns:
            최근 쿼리 레코드 리스트
        """
        return list(reversed(self.records))[:limit]

    def search(
        self,
        keyword: str,
        search_in: List[str] = None
    ) -> List[QueryRecord]:
        """
        키워드 검색

        Args:
            keyword: 검색 키워드
            search_in: 검색 대상 필드 리스트 (기본: ['user_query', 'sql_query'])

        Returns:
            검색 결과 리스트
        """
        if search_in is None:
            search_in = ['user_query', 'sql_query']

        keyword_lower = keyword.lower()
        results = []

        for record in reversed(self.records):
            match = False
            if 'user_query' in search_in and keyword_lower in record.user_query.lower():
                match = True
            if 'sql_query' in search_in and keyword_lower in record.sql_query.lower():
                match = True
            if 'tags' in search_in and any(keyword_lower in tag.lower() for tag in record.tags):
                match = True

            if match:
                results.append(record)

        return results

    def filter_by_tags(self, tags: List[str]) -> List[QueryRecord]:
        """
        태그 필터링

        Args:
            tags: 필터링할 태그 리스트

        Returns:
            필터링 결과
        """
        results = []
        tags_lower = [tag.lower() for tag in tags]

        for record in reversed(self.records):
            if any(tag.lower() in tags_lower for tag in record.tags):
                results.append(record)

        return results

    def get_statistics(self) -> Dict:
        """
        히스토리 통계

        Returns:
            {
                'total': int,
                'favorites': int,
                'executed': int,
                'success_rate': float,
                'avg_execution_time': float
            }
        """
        total = len(self.records)
        favorites = len([r for r in self.records if r.is_favorite])
        executed = len([r for r in self.records if r.executed])
        successful_executions = len([
            r for r in self.records
            if r.executed and r.execution_success
        ])

        execution_times = [
            r.execution_time for r in self.records
            if r.execution_time is not None
        ]

        return {
            'total': total,
            'favorites': favorites,
            'executed': executed,
            'success_rate': (successful_executions / executed * 100) if executed > 0 else 0,
            'avg_execution_time': sum(execution_times) / len(execution_times) if execution_times else 0
        }

    def clear_history(self, keep_favorites: bool = True):
        """
        히스토리 삭제

        Args:
            keep_favorites: 즐겨찾기는 유지할지 여부
        """
        if keep_favorites:
            self.records = [r for r in self.records if r.is_favorite]
        else:
            self.records = []

        self._save_history()

    def export_to_sql_file(self, output_file: str, include_favorites_only: bool = False):
        """
        SQL 파일로 내보내기

        Args:
            output_file: 출력 파일 경로
            include_favorites_only: 즐겨찾기만 내보낼지 여부
        """
        records = self.get_favorites() if include_favorites_only else self.get_all()

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("-- Query History Export\n")
            f.write(f"-- Generated: {datetime.now().isoformat()}\n")
            f.write(f"-- Total Queries: {len(records)}\n\n")

            for i, record in enumerate(records, 1):
                f.write(f"-- Query {i}\n")
                f.write(f"-- Timestamp: {record.timestamp}\n")
                f.write(f"-- User Query: {record.user_query}\n")
                if record.is_favorite:
                    f.write(f"-- ⭐ FAVORITE\n")
                if record.notes:
                    f.write(f"-- Notes: {record.notes}\n")
                f.write(f"\n{record.sql_query}\n\n")
                f.write("-" * 80 + "\n\n")


if __name__ == "__main__":
    # 테스트
    history = QueryHistory("test_history.json")

    # 쿼리 추가
    query_id = history.add_query(
        user_query="고혈압 환자의 성별 분포",
        sql_query="SELECT gender, COUNT(*) FROM patients WHERE disease='고혈압' GROUP BY gender",
        success=True,
        tags=['고혈압', '성별']
    )

    print(f"Added query: {query_id}")

    # 실행 결과 업데이트
    history.update_execution_result(query_id, execution_success=True, row_count=2, execution_time=0.5)

    # 즐겨찾기 추가
    history.toggle_favorite(query_id)

    # 통계 확인
    stats = history.get_statistics()
    print(f"Statistics: {stats}")

    # 최근 쿼리 조회
    recent = history.get_recent(5)
    print(f"Recent queries: {len(recent)}")
