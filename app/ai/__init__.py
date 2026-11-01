"""Quark AI package initialization."""
from app.ai.quark import QuarkCompanion
from app.ai.fallback_knowledge import get_curated_explanation, EXPERIMENT_EXPLANATIONS

__all__ = ["QuarkCompanion", "get_curated_explanation", "EXPERIMENT_EXPLANATIONS"]
