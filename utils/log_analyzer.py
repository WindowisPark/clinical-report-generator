"""
Log Analyzer for Performance Monitoring
로그 파일을 분석하여 성능 지표 추출
"""

import re
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional


class LogAnalyzer:
    """로그 파일 분석기"""

    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)

    def parse_nl2sql_logs(self, date: Optional[str] = None) -> pd.DataFrame:
        """
        NL2SQL 생성 로그 파싱

        Args:
            date: 날짜 (YYYY-MM-DD). None이면 오늘

        Returns:
            DataFrame with columns: timestamp, status, rag_detected, disease_codes, query
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        log_file = self.log_dir / f"nl2sql_generator_{date}.log"

        if not log_file.exists():
            return pd.DataFrame(columns=['timestamp', 'status', 'rag_detected', 'disease_codes', 'query'])

        records = []
        pattern = r'\[(.*?)\] (INFO|ERROR)\s+\[.*?\] NL2SQL Generation (SUCCESS|FAILED) \| (.*)'

        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                match = re.match(pattern, line)
                if match:
                    timestamp_str, level, status, details = match.groups()
                    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')

                    # RAG 정보 추출
                    rag_match = re.search(r'RAG: (\[.*?\])', details)
                    if rag_match:
                        rag_codes = eval(rag_match.group(1))  # ['AI1%', 'AE1%']
                        rag_detected = len(rag_codes) > 0
                        disease_codes = ','.join(rag_codes) if rag_codes else ''
                    else:
                        rag_detected = False
                        disease_codes = ''

                    # 쿼리 추출
                    query_match = re.search(r'Query: (.+)$', details)
                    query = query_match.group(1) if query_match else ''

                    records.append({
                        'timestamp': timestamp,
                        'status': status,
                        'rag_detected': rag_detected,
                        'disease_codes': disease_codes,
                        'query': query
                    })

        return pd.DataFrame(records)

    def parse_databricks_logs(self, date: Optional[str] = None) -> pd.DataFrame:
        """
        Databricks 실행 로그 파싱

        Args:
            date: 날짜 (YYYY-MM-DD). None이면 오늘

        Returns:
            DataFrame with columns: timestamp, status, execution_time, row_count, query
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        log_file = self.log_dir / f"databricks_client_{date}.log"

        if not log_file.exists():
            return pd.DataFrame(columns=['timestamp', 'status', 'execution_time', 'row_count', 'query'])

        records = []
        pattern = r'\[(.*?)\] (INFO|ERROR)\s+\[.*?\] SQL Execution (SUCCESS|FAILED) \| (.*)'

        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                match = re.match(pattern, line)
                if match:
                    timestamp_str, level, status, details = match.groups()
                    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')

                    # 실행 시간 추출
                    time_match = re.search(r'Time: ([\d.]+)s', details)
                    execution_time = float(time_match.group(1)) if time_match else None

                    # Row count 추출
                    rows_match = re.search(r'Rows: (\d+)', details)
                    row_count = int(rows_match.group(1)) if rows_match else None

                    # 쿼리 추출
                    query_match = re.search(r'Query: (.+)$', details)
                    query = query_match.group(1) if query_match else ''

                    # 에러 추출
                    error_match = re.search(r'Error: (.+?) \|', details)
                    error = error_match.group(1) if error_match else None

                    records.append({
                        'timestamp': timestamp,
                        'status': status,
                        'execution_time': execution_time,
                        'row_count': row_count,
                        'query': query,
                        'error': error
                    })

        return pd.DataFrame(records)

    def get_summary_stats(self, days: int = 7) -> Dict:
        """
        최근 N일간 요약 통계

        Args:
            days: 조회 일수

        Returns:
            Dict with summary statistics
        """
        stats = {
            'nl2sql': {
                'total': 0,
                'success': 0,
                'failed': 0,
                'rag_usage': 0,
                'success_rate': 0.0,
                'rag_rate': 0.0
            },
            'databricks': {
                'total': 0,
                'success': 0,
                'failed': 0,
                'avg_time': 0.0,
                'total_rows': 0,
                'success_rate': 0.0
            }
        }

        # 날짜 범위
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        all_nl2sql_records = []
        all_db_records = []

        # 각 날짜별로 로그 수집
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')

            # NL2SQL 로그
            nl2sql_df = self.parse_nl2sql_logs(date_str)
            if not nl2sql_df.empty:
                all_nl2sql_records.append(nl2sql_df)

            # Databricks 로그
            db_df = self.parse_databricks_logs(date_str)
            if not db_df.empty:
                all_db_records.append(db_df)

            current_date += timedelta(days=1)

        # NL2SQL 통계
        if all_nl2sql_records:
            nl2sql_combined = pd.concat(all_nl2sql_records, ignore_index=True)
            stats['nl2sql']['total'] = len(nl2sql_combined)
            stats['nl2sql']['success'] = len(nl2sql_combined[nl2sql_combined['status'] == 'SUCCESS'])
            stats['nl2sql']['failed'] = len(nl2sql_combined[nl2sql_combined['status'] == 'FAILED'])
            stats['nl2sql']['rag_usage'] = len(nl2sql_combined[nl2sql_combined['rag_detected'] == True])

            if stats['nl2sql']['total'] > 0:
                stats['nl2sql']['success_rate'] = stats['nl2sql']['success'] / stats['nl2sql']['total'] * 100
                stats['nl2sql']['rag_rate'] = stats['nl2sql']['rag_usage'] / stats['nl2sql']['total'] * 100

        # Databricks 통계
        if all_db_records:
            db_combined = pd.concat(all_db_records, ignore_index=True)
            stats['databricks']['total'] = len(db_combined)
            stats['databricks']['success'] = len(db_combined[db_combined['status'] == 'SUCCESS'])
            stats['databricks']['failed'] = len(db_combined[db_combined['status'] == 'FAILED'])

            success_records = db_combined[db_combined['status'] == 'SUCCESS']
            if not success_records.empty:
                stats['databricks']['avg_time'] = success_records['execution_time'].mean()
                stats['databricks']['total_rows'] = success_records['row_count'].sum()

            if stats['databricks']['total'] > 0:
                stats['databricks']['success_rate'] = stats['databricks']['success'] / stats['databricks']['total'] * 100

        return stats

    def get_recent_errors(self, limit: int = 10) -> List[Dict]:
        """
        최근 에러 목록

        Args:
            limit: 반환할 에러 개수

        Returns:
            List of error records
        """
        errors = []

        # 오늘과 어제 로그 확인
        for days_ago in [0, 1]:
            date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')

            # NL2SQL 에러
            nl2sql_df = self.parse_nl2sql_logs(date)
            if not nl2sql_df.empty and 'status' in nl2sql_df.columns:
                nl2sql_errors = nl2sql_df[nl2sql_df['status'] == 'FAILED']
                for _, row in nl2sql_errors.iterrows():
                    errors.append({
                        'timestamp': row['timestamp'],
                        'type': 'NL2SQL Generation',
                        'query': row['query']
                    })

            # Databricks 에러
            db_df = self.parse_databricks_logs(date)
            if not db_df.empty and 'status' in db_df.columns:
                db_errors = db_df[db_df['status'] == 'FAILED']
                for _, row in db_errors.iterrows():
                    errors.append({
                        'timestamp': row['timestamp'],
                        'type': 'SQL Execution',
                        'query': row['query'],
                        'error': row.get('error', 'Unknown')
                    })

        # 시간순 정렬 후 최근 N개 반환
        errors.sort(key=lambda x: x['timestamp'], reverse=True)
        return errors[:limit]
