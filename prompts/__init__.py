"""
Prompt Management System

External prompt templates for LLM interactions with version control,
A/B testing support, and clear separation from code logic.
"""

from .loader import PromptLoader

__all__ = ['PromptLoader']
