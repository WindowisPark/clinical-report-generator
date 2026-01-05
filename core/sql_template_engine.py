"""
SQL Template Engine - Render SQL templates with parameters
Jinja2 기반 SQL 템플릿 렌더링 엔진
"""

import re
from datetime import date, timedelta
from jinja2 import Template, TemplateError
from pathlib import Path
from typing import Dict, Any, Optional

from core.exceptions import TemplateRenderError, RecipeNotFoundError


class SQLTemplateEngine:
    """SQL 템플릿 렌더링 엔진 (통합 버전)"""

    def __init__(self, recipes_dir: str = "recipes") -> None:
        self.recipes_dir: Path = Path(recipes_dir)

    def _process_special_placeholders(self, params: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        특수 플레이스홀더 처리

        Special Placeholders:
            [DEFAULT_3_YEARS_AGO] → YYYY-MM-DD (3 years ago)
            [CURRENT_DATE] → YYYY-MM-DD (today)
            [DEFAULT_XXX] → XXX
            [NOT_FOUND] → None

        Args:
            params: 원본 파라미터 딕셔너리

        Returns:
            처리된 파라미터 딕셔너리
        """
        if not params:
            return {}

        processed_params = params.copy()

        for key, value in processed_params.items():
            if isinstance(value, str):
                if value == '[DEFAULT_3_YEARS_AGO]':
                    three_years_ago = date.today() - timedelta(days=3*365)
                    processed_params[key] = three_years_ago.strftime('%Y-%m-%d')
                elif value == '[CURRENT_DATE]':
                    processed_params[key] = date.today().strftime('%Y-%m-%d')
                elif value == '[NOT_FOUND]':
                    processed_params[key] = None
                else:
                    match = re.match(r'\[DEFAULT_(\w+)\]', value)
                    if match:
                        processed_params[key] = match.group(1)

        return processed_params

    def render(self, sql_template: str, parameters: Optional[Dict[str, Any]] = None) -> str:
        """
        SQL 템플릿 문자열을 파라미터로 렌더링 (특수 플레이스홀더 지원)

        Args:
            sql_template: SQL 템플릿 문자열
            parameters: 템플릿 변수 딕셔너리

        Returns:
            렌더링된 SQL 쿼리 문자열
        """
        # 1. 특수 플레이스홀더 처리
        processed_params = self._process_special_placeholders(parameters)

        # 2. Jinja2 템플릿 렌더링
        try:
            template = Template(sql_template)
            return template.render(**processed_params)
        except TemplateError as e:
            raise TemplateRenderError(f"Failed to render SQL template: {e}") from e
        except Exception as e:
            raise TemplateRenderError(f"Unexpected error during template rendering: {e}") from e

    def render_template(self, recipe_name: str, parameters: Dict[str, Any]) -> str:
        """
        SQL 템플릿 파일을 읽어 파라미터로 렌더링

        Args:
            recipe_name: 레시피 이름
            parameters: 템플릿 변수 딕셔너리

        Returns:
            렌더링된 SQL 쿼리 문자열
        """
        # SQL 파일 찾기 (pool 또는 profile 디렉토리)
        sql_path = None
        for category in ["pool", "profile"]:
            candidate_path = self.recipes_dir / category / f"{recipe_name}.sql"
            if candidate_path.exists():
                sql_path = candidate_path
                break

        if not sql_path:
            raise RecipeNotFoundError(f"SQL template file not found for recipe: {recipe_name}")

        # SQL 템플릿 읽기
        try:
            with open(sql_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
        except IOError as e:
            raise TemplateRenderError(f"Failed to read SQL template file: {e}") from e

        # render() 메서드를 통해 통합 렌더링 수행
        return self.render(template_content, parameters)

    def get_sql_template_path(self, recipe_name: str) -> Path:
        """레시피의 SQL 템플릿 파일 경로 반환"""
        for category in ["pool", "profile"]:
            candidate_path = self.recipes_dir / category / f"{recipe_name}.sql"
            if candidate_path.exists():
                return candidate_path

        raise RecipeNotFoundError(f"SQL template file not found for recipe: {recipe_name}")
