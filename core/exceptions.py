"""
Custom exception types for clinical report generator
Provides specific error types for better error handling and debugging
"""


class ClinicalReportError(Exception):
    """Base exception for all clinical report generator errors"""
    pass


class RecipeNotFoundError(ClinicalReportError):
    """Raised when a recipe file cannot be found"""
    pass


class RecipeValidationError(ClinicalReportError):
    """Raised when recipe metadata validation fails"""
    pass


class TemplateRenderError(ClinicalReportError):
    """Raised when SQL template rendering fails"""
    pass


class ParameterExtractionError(ClinicalReportError):
    """Raised when parameter extraction from user query fails"""
    pass


class LLMAPIError(ClinicalReportError):
    """Raised when LLM API calls fail"""
    pass
