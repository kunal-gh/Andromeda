"""Custom Prometheus metrics for the Worknoon agent."""
import logging

logger = logging.getLogger(__name__)

class MockCounter:
    def __init__(self): pass
    def labels(self, **kwargs): return self
    def inc(self, amount=1): pass

try:
    from prometheus_client import Counter, Histogram, Gauge, Info

    # Request metrics
    REQUEST_COUNT = Counter("worknoon_requests_total", "Total requests", ["endpoint", "method", "status"])
    REQUEST_LATENCY = Histogram("worknoon_request_duration_seconds", "Request latency", ["endpoint"])
    AGENT_DECISION_COUNT = Counter("worknoon_agent_decisions_total", "Agent decisions", ["decision_type", "agent_name"])
    LLM_TOKEN_COUNT = Counter("worknoon_llm_tokens_total", "LLM tokens consumed", ["model", "provider"])
    INJECTION_ATTEMPT_COUNT = Counter("worknoon_injection_attempts_total", "Injection attempts", ["risk_level", "blocked"])
    CONVERSATION_GAUGE = Gauge("worknoon_active_conversations", "Active conversations")
    SYSTEM_INFO = Info("worknoon_system", "System information")
except ImportError:
    logger.warning("prometheus_client not installed. Metrics disabled.")
    AGENT_DECISION_COUNT = MockCounter()
    INJECTION_ATTEMPT_COUNT = MockCounter()
    LLM_TOKEN_COUNT = MockCounter()

def record_agent_decision(decision: str, agent_name: str = "policy"):
    AGENT_DECISION_COUNT.labels(decision_type=decision, agent_name=agent_name).inc()

def record_injection_attempt(risk_level: str, blocked: bool):
    INJECTION_ATTEMPT_COUNT.labels(risk_level=risk_level, blocked=str(blocked)).inc()

def record_llm_tokens(model: str, provider: str, tokens: int):
    LLM_TOKEN_COUNT.labels(model=model, provider=provider).inc(tokens)
