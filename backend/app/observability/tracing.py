"""
Phase 5 — Observability: Langfuse + OpenTelemetry instrumentation.

Provides two complementary observability layers:
  1. Langfuse:    LLM-aware tracing (tokens, cost, latency per call)
  2. OpenTelemetry: Infrastructure spans (HTTP, DB, startup)

Both are opt-in via env vars — the agent runs normally with all keys absent.
Langfuse is free on cloud.langfuse.com (no credit card required).
"""

from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Any

from app.core.config import get_settings


# ── Langfuse client singleton ─────────────────────────────────────────────

_langfuse_client = None
_langfuse_enabled = False


def _init_langfuse():
    global _langfuse_client, _langfuse_enabled
    settings = get_settings()
    if not (settings.langfuse_public_key and settings.langfuse_secret_key):
        return
    if settings.langfuse_public_key.startswith("pk-lf-your"):
        return  # Placeholder key — skip

    try:
        from langfuse import Langfuse
        _langfuse_client = Langfuse(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            host=settings.langfuse_host,
        )
        _langfuse_enabled = True
    except ImportError:
        pass
    except Exception as exc:
        import logging
        logging.getLogger("andromeda.observability").warning(
            f"Langfuse init failed (continuing without tracing): {exc}"
        )


def get_langfuse():
    """Return the Langfuse client, or None if not configured."""
    global _langfuse_client, _langfuse_enabled
    if _langfuse_client is None and not _langfuse_enabled:
        _init_langfuse()
    return _langfuse_client if _langfuse_enabled else None


# ── Trace context manager ──────────────────────────────────────────────────

@contextmanager
def langfuse_trace(name: str, conversation_id: str, metadata: dict | None = None):
    """
    Context manager that creates a Langfuse trace for one agent run.

    Usage (in runner.py):
        with langfuse_trace("run_refund_agent", conversation_id) as trace:
            state["_lf_trace"] = trace
            ...

    Yields the trace object (or None if Langfuse is not configured).
    """
    lf = get_langfuse()
    if lf is None:
        yield None
        return

    trace = lf.trace(
        name=name,
        id=conversation_id,
        metadata=metadata or {},
        tags=["andromeda", "agent"],
    )
    start = time.perf_counter()
    try:
        yield trace
    finally:
        trace.update(
            output={"duration_ms": round((time.perf_counter() - start) * 1000)}
        )
        lf.flush()


def record_llm_span(
    trace,
    name: str,
    model: str,
    input_text: str,
    output_text: str,
    latency_ms: float,
    token_counts: dict | None = None,
):
    """Record a single LLM call as a Langfuse generation span."""
    if trace is None:
        return
    try:
        trace.generation(
            name=name,
            model=model,
            input=input_text,
            output=output_text,
            usage=token_counts or {},
            metadata={"latency_ms": latency_ms},
        )
    except Exception:
        pass  # Never fail the main request due to observability


def record_tool_span(trace, name: str, input_data: Any, output_data: Any, latency_ms: float):
    """Record a tool call as a Langfuse span."""
    if trace is None:
        return
    try:
        trace.span(
            name=name,
            input=input_data,
            output=output_data,
            metadata={"latency_ms": latency_ms},
        )
    except Exception:
        pass


# ── OpenTelemetry setup ───────────────────────────────────────────────────

def setup_opentelemetry(app):
    """
    Instrument the FastAPI app with OpenTelemetry.
    Called from app/main.py during startup.

    Instruments:
      - HTTP requests (FastAPI middleware)
      - SQLAlchemy queries
      - Outgoing HTTP calls (httpx)
    """
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

        provider = TracerProvider()
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
        trace.set_tracer_provider(provider)

        FastAPIInstrumentor.instrument_app(app)

        from app.db.database import engine
        SQLAlchemyInstrumentor().instrument(engine=engine)

    except ImportError:
        pass  # OTEL packages not installed — skip
    except Exception as exc:
        import logging
        logging.getLogger("andromeda.observability").warning(f"OTEL init failed: {exc}")
