"""
Parameter extraction from user queries using LLM
"""

import json
from typing import Dict, List, Any, Optional


def extract_json_from_llm_response(response_text: str) -> Dict:
    """
    Extract JSON from LLM response, handling markdown code blocks.

    Args:
        response_text: Raw LLM response

    Returns:
        Parsed JSON dictionary
    """
    cleaned_text = response_text.strip()

    # Remove markdown code blocks
    if '```json' in cleaned_text:
        cleaned_text = cleaned_text.split('```json')[1].split('```')[0].strip()
    elif '```' in cleaned_text:
        cleaned_text = cleaned_text.split('```')[1].split('```')[0].strip()

    return json.loads(cleaned_text)


def validate_recipe_parameters(
    recipe: Dict[str, Any],
    extracted_params: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Validate extracted parameters against recipe schema.

    Args:
        recipe: Recipe metadata with parameter definitions
        extracted_params: Parameters extracted from user query

    Returns:
        Validated and normalized parameters
    """
    validated = {}
    required_params = recipe.get('parameters', [])

    for param in required_params:
        param_name = param['name']
        if param_name in extracted_params:
            validated[param_name] = extracted_params[param_name]
        elif 'default' in param:
            validated[param_name] = param['default']
        else:
            # Set placeholder for missing required params
            validated[param_name] = '[NOT_FOUND]'

    return validated
