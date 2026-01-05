"""
Centralized Logging System
프로덕션 환경을 위한 통합 로깅
"""

import logging
import sys
from pathlib import Path
from datetime import datetime


def setup_logger(
    name: str = "clinical_report_generator",
    level: int = logging.INFO,
    log_to_file: bool = True,
    log_dir: str = "logs"
) -> logging.Logger:
    """
    통합 로거 설정

    Args:
        name: 로거 이름
        level: 로깅 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: 파일 로깅 여부
        log_dir: 로그 파일 디렉토리

    Returns:
        logging.Logger
    """
    logger = logging.getLogger(name)

    # 이미 핸들러가 있으면 재설정하지 않음 (중복 방지)
    if logger.handlers:
        return logger

    logger.setLevel(level)

    # 포맷 설정
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)-8s [%(name)s:%(lineno)d] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 콘솔 핸들러
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 파일 핸들러 (옵션)
    if log_to_file:
        # 로그 디렉토리 생성
        log_path = Path(log_dir)
        log_path.mkdir(exist_ok=True)

        # 날짜별 로그 파일
        today = datetime.now().strftime('%Y-%m-%d')
        log_file = log_path / f"{name}_{today}.log"

        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        logger.info(f"Logging to file: {log_file}")

    return logger


def log_sql_execution(
    logger: logging.Logger,
    query: str,
    success: bool,
    execution_time: float = None,
    row_count: int = None,
    error: str = None
):
    """
    SQL 실행 로깅 (구조화된 로그)

    Args:
        logger: 로거 인스턴스
        query: 실행된 쿼리
        success: 성공 여부
        execution_time: 실행 시간 (초)
        row_count: 반환된 행 수
        error: 에러 메시지
    """
    query_preview = query[:100] + "..." if len(query) > 100 else query

    if success:
        logger.info(
            f"SQL Execution SUCCESS | "
            f"Time: {execution_time:.2f}s | "
            f"Rows: {row_count} | "
            f"Query: {query_preview}"
        )
    else:
        logger.error(
            f"SQL Execution FAILED | "
            f"Error: {error} | "
            f"Query: {query_preview}"
        )


def log_nl2sql_generation(
    logger: logging.Logger,
    user_query: str,
    success: bool,
    rag_detected: bool = False,
    disease_codes: list = None,
    error: str = None
):
    """
    NL2SQL 생성 로깅

    Args:
        logger: 로거 인스턴스
        user_query: 사용자 쿼리
        success: 생성 성공 여부
        rag_detected: RAG 질병 코드 감지 여부
        disease_codes: 감지된 질병 코드 리스트
        error: 에러 메시지
    """
    if success:
        rag_info = f"RAG: {disease_codes}" if rag_detected else "RAG: N/A"
        logger.info(
            f"NL2SQL Generation SUCCESS | "
            f"{rag_info} | "
            f"Query: {user_query}"
        )
    else:
        logger.error(
            f"NL2SQL Generation FAILED | "
            f"Error: {error} | "
            f"Query: {user_query}"
        )


# 기본 로거 인스턴스
default_logger = setup_logger()
