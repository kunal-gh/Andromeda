"""OpenTelemetry tracing setup for the Worknoon agent."""
import logging

logger = logging.getLogger(__name__)

def setup_fastapi_tracing(app):
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        FastAPIInstrumentor.instrument_app(app)
        logger.info("FastAPI OpenTelemetry instrumentation enabled.")
    except ImportError:
        logger.warning("opentelemetry not installed. Skipping FastAPI tracing.")

def setup_sqlalchemy_tracing(engine):
    try:
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
        SQLAlchemyInstrumentor().instrument(engine=engine)
        logger.info("SQLAlchemy OpenTelemetry instrumentation enabled.")
    except ImportError:
        logger.warning("opentelemetry not installed. Skipping SQLAlchemy tracing.")

def init_tracer():
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import Resource, SERVICE_NAME

        resource = Resource(attributes={
            SERVICE_NAME: "worknoon-agent", 
            "service.version": "2.0.0", 
            "deployment.environment": "production"
        })
        tracer_provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(tracer_provider)
        
        # otel-collector should be running locally via docker-compose
        otlp_exporter = OTLPSpanExporter(endpoint="http://localhost:4317", insecure=True)
        span_processor = BatchSpanProcessor(otlp_exporter)
        tracer_provider.add_span_processor(span_processor)
        
        return trace.get_tracer("worknoon.agent")
    except ImportError:
        logger.warning("opentelemetry not installed. Skipping global tracer init.")
        return None
