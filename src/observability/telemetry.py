"""
OpenTelemetry Observability
- Distributed tracing: one root span per pipeline run, child spans per agent call
- Metrics: agent call counter, latency histogram, error counter
- Exporters: console (default) + OTLP (when OTEL_EXPORTER_OTLP_ENDPOINT is set)
"""
import time
import logging
import os
from contextlib import contextmanager
from typing import Any

from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import ConsoleMetricExporter, PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource

logger = logging.getLogger(__name__)

# ── Provider setup ────────────────────────────────────────────────────────────

_resource = Resource.create({"service.name": "timetable-ai", "service.version": "1.0.0"})

# Tracer
_tracer_provider = TracerProvider(resource=_resource)

otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "")
if otlp_endpoint:
    try:
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        _tracer_provider.add_span_processor(
            BatchSpanProcessor(OTLPSpanExporter(endpoint=otlp_endpoint))
        )
        logger.info(f"[OTEL] OTLP trace exporter → {otlp_endpoint}")
    except Exception as e:
        logger.warning(f"[OTEL] OTLP exporter failed, falling back to console: {e}")
        _tracer_provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
else:
    # Console exporter in dev — silent unless LOG_LEVEL=DEBUG
    if os.getenv("OTEL_CONSOLE_EXPORT", "false").lower() == "true":
        _tracer_provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

trace.set_tracer_provider(_tracer_provider)
tracer = trace.get_tracer("timetable-ai.agents")

# Meter
_metric_reader    = PeriodicExportingMetricReader(ConsoleMetricExporter(), export_interval_millis=60_000)
_meter_provider   = MeterProvider(resource=_resource, metric_readers=[_metric_reader])
metrics.set_meter_provider(_meter_provider)
meter = metrics.get_meter("timetable-ai.agents")

# ── Instruments ───────────────────────────────────────────────────────────────

agent_call_counter = meter.create_counter(
    "agent.calls.total",
    description="Total number of agent method calls",
)

agent_error_counter = meter.create_counter(
    "agent.errors.total",
    description="Total number of agent errors",
)

agent_latency_histogram = meter.create_histogram(
    "agent.call.duration_ms",
    description="Agent call duration in milliseconds",
    unit="ms",
)

pipeline_counter = meter.create_counter(
    "pipeline.runs.total",
    description="Total pipeline runs",
)


# ── Context managers ──────────────────────────────────────────────────────────

@contextmanager
def pipeline_span(run_id: str, solver_mode: str = "unknown"):
    """Root span for an entire pipeline run."""
    with tracer.start_as_current_span("pipeline.run") as span:
        span.set_attribute("run_id", run_id)
        span.set_attribute("solver_mode", solver_mode)
        pipeline_counter.add(1, {"solver_mode": solver_mode})
        try:
            yield span
        except Exception as e:
            span.record_exception(e)
            span.set_status(trace.StatusCode.ERROR, str(e))
            raise


@contextmanager
def agent_span(agent_name: str, method: str, run_id: str = ""):
    """Child span for a single agent method call."""
    start = time.time()
    attrs = {"agent": agent_name, "method": method, "run_id": run_id}

    with tracer.start_as_current_span(f"{agent_name}.{method}") as span:
        span.set_attribute("agent.name", agent_name)
        span.set_attribute("agent.method", method)
        span.set_attribute("run_id", run_id)
        agent_call_counter.add(1, attrs)
        try:
            yield span
        except Exception as e:
            span.record_exception(e)
            span.set_status(trace.StatusCode.ERROR, str(e))
            agent_error_counter.add(1, attrs)
            raise
        finally:
            duration_ms = (time.time() - start) * 1000
            agent_latency_histogram.record(duration_ms, attrs)
            span.set_attribute("duration_ms", round(duration_ms, 2))


def get_current_trace_id() -> str:
    """Returns the current trace ID as a hex string, or empty string if no active span."""
    ctx = trace.get_current_span().get_span_context()
    if ctx and ctx.is_valid:
        return format(ctx.trace_id, "032x")
    return ""


def get_current_span_id() -> str:
    ctx = trace.get_current_span().get_span_context()
    if ctx and ctx.is_valid:
        return format(ctx.span_id, "016x")
    return ""
