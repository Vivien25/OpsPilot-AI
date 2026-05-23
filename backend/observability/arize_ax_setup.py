import os

from utils.config import ARIZE_PROJECT_NAME, ENABLE_ARIZE_AX

_TRACER_PROVIDER = None


def setup_arize_ax():
    """
    Configure Arize AX tracing when ENABLE_ARIZE_AX=true.

    Required environment variables for AX export:
    - ARIZE_SPACE_ID
    - ARIZE_API_KEY
    Optional:
    - ARIZE_PROJECT_NAME
    """
    global _TRACER_PROVIDER

    if not ENABLE_ARIZE_AX:
        return False

    space_id = os.getenv("ARIZE_SPACE_ID")
    api_key = os.getenv("ARIZE_API_KEY")

    if not space_id or not api_key:
        print("Arize AX tracing disabled; missing ARIZE_SPACE_ID or ARIZE_API_KEY.")
        return False

    try:
        from arize.otel import register
    except ImportError as exc:
        print(f"Arize AX tracing disabled; missing package: {exc}")
        return False

    try:
        batch_spans = os.getenv("ARIZE_BATCH_SPANS", "true").lower() == "true"
        log_to_console = os.getenv("ARIZE_LOG_TO_CONSOLE", "false").lower() == "true"
        _TRACER_PROVIDER = register(
            space_id=space_id,
            api_key=api_key,
            project_name=ARIZE_PROJECT_NAME,
            batch=batch_spans,
            log_to_console=log_to_console,
        )
        print(f"Arize AX tracing enabled for project '{ARIZE_PROJECT_NAME}'.")
        _instrument_google_genai()
        return True
    except Exception as exc:
        print(f"Arize AX tracing skipped: {exc}")
        return False


def instrument_fastapi(app):
    if not ENABLE_ARIZE_AX:
        return False

    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    except ImportError as exc:
        print(f"FastAPI tracing disabled; missing package: {exc}")
        return False

    try:
        FastAPIInstrumentor.instrument_app(app, tracer_provider=_TRACER_PROVIDER)
        return True
    except Exception as exc:
        print(f"FastAPI tracing skipped: {exc}")
        return False


def _instrument_google_genai():
    try:
        from openinference.instrumentation.google_genai import GoogleGenAIInstrumentor
    except ImportError:
        return False

    try:
        GoogleGenAIInstrumentor().instrument(tracer_provider=_TRACER_PROVIDER)
        return True
    except Exception as exc:
        print(f"Google GenAI tracing skipped: {exc}")
        return False
