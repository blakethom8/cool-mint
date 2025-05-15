import base64
import os

from dotenv import load_dotenv
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider, Tracer
from opentelemetry.sdk.trace.export import SimpleSpanProcessor

load_dotenv()


class LangfuseConfig:

    @staticmethod
    def get_tracer() -> Tracer:
        LANGFUSE_AUTH = base64.b64encode(
            f"{os.getenv('LANGFUSE_PUBLIC_KEY')}:{os.getenv('LANGFUSE_SECRET_KEY')}".encode()
        ).decode()

        os.environ["OTEL_EXPORTER_OTLP_HEADERS"] = f"Authorization=Basic {LANGFUSE_AUTH}"

        import logfire

        logfire.configure(
            send_to_logfire=False,
        )

        trace_provider = TracerProvider()
        trace_provider.add_span_processor(SimpleSpanProcessor(OTLPSpanExporter()))
        return trace.get_tracer("workflow-tracer")
