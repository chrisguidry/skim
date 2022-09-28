import os

from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader


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
