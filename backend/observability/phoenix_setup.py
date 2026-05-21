from utils.config import ENABLE_PHOENIX, PHOENIX_LAUNCH_APP


def setup_phoenix():
    """
    Configure Arize Phoenix tracing when ENABLE_PHOENIX=true.
    Keep this optional so Cloud Run and teammates without Phoenix can still start.
    """
    if not ENABLE_PHOENIX:
        return False

    try:
        from phoenix.otel import register

        register(project_name="opspilot-ai", auto_instrument=True)
        _maybe_launch_phoenix_app()
        return True
    except ImportError:
        pass
    except Exception as exc:
        print(f"Phoenix OTel setup skipped: {exc}")
        return False

    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from phoenix.trace.exporter import PhoenixSpanExporter
    except ImportError as exc:
        print(f"Phoenix tracing disabled; missing package: {exc}")
        return False
    except Exception as exc:
        print(f"Phoenix tracing disabled; setup import failed: {exc}")
        return False

    current_provider = trace.get_tracer_provider()
    if current_provider.__class__.__name__ != "ProxyTracerProvider":
        return True

    tracer_provider = TracerProvider()
    tracer_provider.add_span_processor(BatchSpanProcessor(PhoenixSpanExporter()))
    trace.set_tracer_provider(tracer_provider)

    _maybe_launch_phoenix_app()

    return True


def instrument_fastapi(app):
    if not ENABLE_PHOENIX:
        return False

    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    except ImportError as exc:
        print(f"FastAPI tracing disabled; missing package: {exc}")
        return False

    try:
        FastAPIInstrumentor.instrument_app(app)
        return True
    except Exception as exc:
        print(f"FastAPI tracing skipped: {exc}")
        return False


def _maybe_launch_phoenix_app():
    if not PHOENIX_LAUNCH_APP:
        return

    try:
        import phoenix as px

        px.launch_app()
    except Exception as exc:
        print(f"Phoenix local app launch skipped: {exc}")
