"""LangFuse integration for LLM tracing and monitoring."""
import os
import logging
from functools import wraps

logger = logging.getLogger(__name__)

# Try to initialize langfuse
try:
    from langfuse import Langfuse
    # Reads LANGFUSE_SECRET_KEY, LANGFUSE_PUBLIC_KEY, LANGFUSE_HOST from env
    langfuse_client = Langfuse()
    _enabled = True
except ImportError:
    langfuse_client = None
    _enabled = False
    logger.warning("langfuse not installed. LLM tracing disabled.")

def trace_llm_call(name: str = None):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not _enabled:
                return await func(*args, **kwargs)
                
            trace_name = name or func.__name__
            trace = langfuse_client.trace(name=trace_name)
            generation = trace.generation(
                name=f"{trace_name}_generation",
                model="gpt-4o-mini",
                input=str(kwargs) or str(args)
            )
            
            try:
                result = await func(*args, **kwargs)
                generation.end(output=str(result))
                return result
            except Exception as e:
                generation.end(level="ERROR", status_message=str(e))
                raise e
        return wrapper
    return decorator
