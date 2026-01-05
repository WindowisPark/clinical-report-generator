"""
Databricks SQL Warehouse 클라이언트
Production-ready singleton client with context manager pattern
"""

from databricks import sql
import pandas as pd
from typing import Optional, Dict, Any
from contextlib import contextmanager
import logging
import time

from utils.logger import setup_logger, log_sql_execution
from config.config_loader import get_config, ConfigurationError

logger = setup_logger("databricks_client")


class DatabricksClient:
    """
    Databricks SQL Warehouse 연결 및 쿼리 실행 클라이언트

    싱글톤 패턴으로 구현하여 연결 재사용
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """초기화 (한 번만 실행)"""
        if self._initialized:
            return

        # Use centralized config loader
        try:
            config = get_config()
            databricks_config = config.get_databricks_config()

            self.server_hostname = databricks_config['server_hostname']
            self.http_path = databricks_config['http_path']
            self.access_token = databricks_config['access_token']

            self._initialized = True
            logger.info("DatabricksClient initialized successfully")
        except ConfigurationError as e:
            logger.error(f"Failed to initialize DatabricksClient: {e}")
            raise

    @contextmanager
    def get_connection(self):
        """
        연결 컨텍스트 매니저

        사용 예:
            with client.get_connection() as conn:
                df = client.execute_query(conn, "SELECT * FROM table")
        """
        connection = None
        try:
            connection = sql.connect(
                server_hostname=self.server_hostname,
                http_path=self.http_path,
                access_token=self.access_token,
                _retry_stop_after_attempts_count=3,  # 재시도 3회로 제한 (기본값: 24)
                _socket_timeout=30,  # 30초 소켓 타임아웃
                _tls_no_verify=True,  # SSL 검증 완전 비활성화 (개인 사용)
                user_agent_entry="clinical_report_generator"
            )
            yield connection
        except Exception as e:
            logger.error(f"Databricks connection failed: {e}")
            raise
        finally:
            if connection:
                connection.close()

    def execute_query(
        self,
        sql_query: str,
        max_rows: int = 10000
    ) -> Dict[str, Any]:
        """
        SQL 쿼리 실행 및 결과 반환

        Args:
            sql_query: 실행할 SQL 쿼리
            max_rows: 최대 반환 행 수 (기본 10,000)

        Returns:
            {
                'success': bool,
                'data': pd.DataFrame or None,
                'row_count': int,
                'execution_time': float (seconds),
                'error_message': str or None
            }
        """
        start_time = time.time()

        try:
            logger.debug("Connecting to Databricks...")
            with self.get_connection() as connection:
                logger.debug("Connection established")
                cursor = connection.cursor()

                try:
                    # 쿼리 실행
                    logger.debug("Executing query...")
                    cursor.execute(sql_query)
                    logger.debug("Query executed, fetching results...")

                    # 결과 가져오기 (최대 max_rows)
                    result = cursor.fetchmany(max_rows)
                    logger.debug(f"Fetched {len(result) if result else 0} rows")

                    # DataFrame 변환
                    if result:
                        columns = [desc[0] for desc in cursor.description]
                        df = pd.DataFrame(result, columns=columns)
                        row_count = len(df)
                    else:
                        df = pd.DataFrame()
                        row_count = 0

                    execution_time = time.time() - start_time
                    logger.debug(f"Query completed in {execution_time:.2f}s")

                    # 로깅
                    log_sql_execution(
                        logger,
                        query=sql_query,
                        success=True,
                        execution_time=execution_time,
                        row_count=row_count
                    )

                    return {
                        'success': True,
                        'data': df,
                        'row_count': row_count,
                        'execution_time': round(execution_time, 2),
                        'error_message': None
                    }

                finally:
                    cursor.close()

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)
            error_type = type(e).__name__

            # 더 친절한 에러 메시지 (에러 타입별 분류)
            if "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
                error_msg = (
                    f"⏱️ 연결 시간 초과 ({execution_time:.1f}초)\n\n"
                    "원인:\n"
                    "1. SQL Warehouse가 중단됨 (가장 가능성 높음)\n"
                    "2. 네트워크 문제\n\n"
                    "해결 방법:\n"
                    "• Databricks → SQL → SQL Warehouses → Start 클릭\n"
                    "• Warehouse가 'Running' 상태가 되면 다시 실행\n\n"
                    f"기술 상세: {e}"
                )
            elif "CANNOT_PARSE_TIMESTAMP" in error_msg:
                error_msg = (
                    f"📅 날짜 형식 오류\n\n"
                    "데이터베이스에 잘못된 날짜 형식이 있습니다.\n"
                    "TRY_TO_DATE()를 사용하면 해결됩니다.\n\n"
                    f"상세: {e}"
                )
            elif "MISSING_GROUP_BY" in error_msg or "MISSING_AGGREGATION" in error_msg:
                error_msg = (
                    f"📊 SQL 집계 오류\n\n"
                    "GROUP BY 절이 누락되었거나 집계 함수가 잘못되었습니다.\n"
                    "쿼리를 재생성하세요.\n\n"
                    f"상세: {e}"
                )
            elif "INVALID_IDENTIFIER" in error_msg:
                error_msg = (
                    f"🔤 컬럼명 오류\n\n"
                    "존재하지 않는 컬럼을 참조했거나 한글 별칭에 백틱(`)이 누락되었습니다.\n\n"
                    f"상세: {e}"
                )
            else:
                # 일반 에러
                error_msg = f"❌ {error_type}: {error_msg}"

            logger.debug(f"Query failed: {error_msg}")

            # 로깅
            log_sql_execution(
                logger,
                query=sql_query,
                success=False,
                error=error_msg
            )

            return {
                'success': False,
                'data': None,
                'row_count': 0,
                'execution_time': round(execution_time, 2),
                'error_message': error_msg
            }

    def test_connection(self) -> bool:
        """
        연결 테스트

        Returns:
            True if connection successful, False otherwise
        """
        try:
            result = self.execute_query("SELECT 1 as test")
            return result['success']
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

    def get_table_preview(
        self,
        table_name: str,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        테이블 미리보기

        Args:
            table_name: 테이블명
            limit: 반환할 행 수

        Returns:
            execute_query() 결과와 동일한 형식
        """
        sql = f"SELECT * FROM {table_name} LIMIT {limit}"
        return self.execute_query(sql)


# 사용 예시
if __name__ == "__main__":
    # 클라이언트 초기화
    client = DatabricksClient()

    # 연결 테스트
    if client.test_connection():
        logger.info("Databricks 연결 성공!")

        # 쿼리 실행
        sql = """
        SELECT
            res_disease_name,
            COUNT(*) AS patient_count
        FROM basic_treatment
        WHERE deleted = FALSE
        GROUP BY res_disease_name
        ORDER BY patient_count DESC
        LIMIT 5
        """

        result = client.execute_query(sql)

        if result['success']:
            logger.info(f"쿼리 결과 ({result['row_count']}행, {result['execution_time']}초)")
            print(result['data'])
        else:
            logger.error(f"쿼리 실패: {result['error_message']}")
    else:
        logger.error("Databricks 연결 실패")
