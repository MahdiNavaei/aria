"""OpenTelemetry tracing setup for ARIA."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter, SpanExporter

if TYPE_CHECKING:
    from opentelemetry.trace import Tracer


def configure_tracing(
    env: str,
    service_name: str = "aria",
    otlp_endpoint: str | None = None,
) -> TracerProvider:
    """Configure OpenTelemetry tracing.

    Args:
        env: Environment name.
        service_name: Service name for traces.
        otlp_endpoint: Optional OTLP endpoint URL.

    """
    resource = Resource.create(
        {
            "service.name": service_name,
            "service.environment": env,
        },
    )

    provider = TracerProvider(resource=resource)

    exporter: SpanExporter | None = None
    endpoint = otlp_endpoint or os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if endpoint:
        try:
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import (  # noqa: PLC0415
                OTLPSpanExporter,
            )

            exporter = OTLPSpanExporter(endpoint=endpoint)
        except ImportError:
            exporter = None

    if exporter is None:
        exporter = ConsoleSpanExporter()

    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    return provider


def get_tracer(name: str = "aria") -> Tracer:
    """Return a tracer instance."""
    return trace.get_tracer(name)
