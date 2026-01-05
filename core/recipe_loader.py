"""
Recipe Loader - Load and manage SQL recipe metadata
레시피 메타데이터 관리 모듈
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class RecipeLoader:
    """레시피 메타데이터 로더"""

    def __init__(self, recipes_dir: str = "recipes") -> None:
        self.recipes_dir: Path = Path(recipes_dir)
        self.recipe_metadata: Dict[str, Dict[str, Any]] = {}
        self.all_recipes: List[Dict[str, Any]] = []
        self._load_recipe_metadata()

    def _load_recipe_metadata(self) -> None:
        """모든 레시피의 메타데이터 로드"""
        logger.info("Loading recipe metadata...")

        for category_dir in ["pool", "profile"]:
            category_path = self.recipes_dir / category_dir
            if not category_path.exists():
                continue

            yaml_files = list(category_path.glob("*.yaml"))
            for yaml_file in yaml_files:
                try:
                    with open(yaml_file, 'r', encoding='utf-8') as f:
                        metadata = yaml.safe_load(f)
                        recipe_name = metadata.get('name', yaml_file.stem)

                        recipe_info = {
                            'name': recipe_name,
                            'description': metadata.get('description', 'N/A'),
                            'category': category_dir,
                            'tags': metadata.get('tags', []),
                            'parameters': metadata.get('parameters', []),
                            'visualization': metadata.get('visualization'),
                            'path': str(yaml_file),
                            'sql_file_path': str(yaml_file.with_suffix('.sql')),
                            'sql_path': str(yaml_file.with_suffix('.sql'))
                        }

                        self.recipe_metadata[recipe_name] = recipe_info
                        self.all_recipes.append(recipe_info)

                except Exception as e:
                    logger.warning(f"Error loading {yaml_file}: {e}")

        logger.info(f"Loaded {len(self.recipe_metadata)} recipe metadata files")

    def get_recipe_by_name(self, recipe_name: str) -> Optional[Dict[str, Any]]:
        """레시피 이름으로 메타데이터 조회"""
        return self.recipe_metadata.get(recipe_name)

    def get_all_recipes(self) -> List[Dict[str, Any]]:
        """모든 레시피 목록 반환"""
        return self.all_recipes

    def get_recipes_by_category(self, category: str) -> List[Dict[str, Any]]:
        """카테고리별 레시피 목록"""
        return [r for r in self.all_recipes if r['category'] == category]

    def search_recipes_by_tag(self, tag: str) -> List[Dict[str, Any]]:
        """태그로 레시피 검색"""
        return [r for r in self.all_recipes if tag in r['tags']]
