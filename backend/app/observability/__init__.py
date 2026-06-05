"""
Phase 5 — Observability package.
Exports the Langfuse tracing helpers and OTEL setup.
"""
from app.observability.tracing import (
    get_langfuse,
    langfuse_trace,
    record_llm_span,
    record_tool_span,
    setup_opentelemetry,
)

__all__ = [
    "get_langfuse",
    "langfuse_trace",
    "record_llm_span",
    "record_tool_span",
    "setup_opentelemetry",
]
