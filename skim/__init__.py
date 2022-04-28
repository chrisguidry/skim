import os

from opentelemetry import _metrics as metrics
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc._metric_exporter import OTLPMetricExporter
from opentelemetry.sdk._metrics import MeterProvider
from opentelemetry.sdk._metrics.export import PeriodicExportingMetricReader


def configure_metrics():  # pragma: no cover
    if not os.environ.get('OTEL_EXPORTER_OTLP_ENDPOINT'):
        return

    metrics.set_meter_provider(
        MeterProvider(
            metric_readers=[
                PeriodicExportingMetricReader(
                    OTLPMetricExporter(
                        endpoint=os.environ.get('OTEL_EXPORTER_OTLP_ENDPOINT'),
                        insecure=os.environ.get('OTEL_EXPORTER_OTLP_INSECURE'),
                    )
                )
            ],
            resource=trace.get_tracer_provider().resource,
        )
    )
