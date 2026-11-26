"""Model layer: pure data containers and the GUI-agnostic search pipeline."""

from src.models.pattern_config import (
    IssueField,
    PatternCategory,
    PatternConfig,
    PatternRule,
    ValidationIssue,
)
from src.models.pipeline_engine import CancellationToken, PipelineCancelled, PipelineEngine
from src.models.search_config import (
    EXCEL_MAX_DATA_ROWS,
    SearchConfig,
    SearchPhase,
    SearchProgress,
    SearchResult,
    SearchStatus,
)

__all__ = [
    "EXCEL_MAX_DATA_ROWS",
    "CancellationToken",
    "IssueField",
    "PatternCategory",
    "PatternConfig",
    "PatternRule",
    "PipelineCancelled",
    "PipelineEngine",
    "SearchConfig",
    "SearchPhase",
    "SearchProgress",
    "SearchResult",
    "SearchStatus",
    "ValidationIssue",
]
