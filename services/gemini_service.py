"""
Centralized Gemini API service
Handles all LLM interactions
"""

from typing import Optional, Any
import google.generativeai as genai
from google.generativeai.types import GenerateContentResponse
from config.config_loader import get_config, ConfigurationError


class GeminiService:
    """Singleton Gemini API client"""

    _instance: Optional['GeminiService'] = None
    _initialized: bool = False

    def __new__(cls, model_name: str = 'gemini-2.5-flash') -> 'GeminiService':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, model_name: str = 'gemini-2.5-flash') -> None:
        """
        Initialize Gemini API client.

        Args:
            model_name: Gemini model identifier

        Raises:
            ConfigurationError: If API key is not found or invalid
        """
        if self._initialized:
            return

        # Use centralized config loader
        config = get_config()
        api_key: str = config.get_gemini_api_key()

        genai.configure(api_key=api_key)
        self.model: genai.GenerativeModel = genai.GenerativeModel(model_name)
        self._initialized = True

    def generate_content(self, prompt: str) -> GenerateContentResponse:
        """
        Generate content using Gemini API.

        Args:
            prompt: Input prompt

        Returns:
            API response object
        """
        return self.model.generate_content(prompt)
