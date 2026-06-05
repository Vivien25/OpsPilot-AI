import json
from contextlib import contextmanager


@contextmanager
def start_span(
    name: str,
    attributes: dict | None = None,
    *,
    kind: str | None = None,
    input_value: str | None = None,
    output_value: str | None = None,
    root: bool = False,
):
    """
    Start an OpenTelemetry span when Arize AX/OpenTelemetry is installed.
    Falls back to a no-op context so local development still works before setup.
    """
    try:
        from opentelemetry import trace
        from opentelemetry.context import Context
        from opentelemetry.trace import Status, StatusCode
    except ImportError:
        yield _NoopSpan()
        return

    tracer = trace.get_tracer("opspilot-ai")
    span_context = Context() if root else None
    with tracer.start_as_current_span(name, context=span_context) as span:
        try:
            set_span_io(span, kind=kind, input_value=input_value, output_value=output_value)
            if attributes:
                set_span_attributes(span, attributes)
            yield span
            span.set_attribute("status", "success")
            span.set_attribute("status_code", "OK")
            span.set_status(Status(StatusCode.OK))
        except Exception as exc:
            span.set_attribute("status", "error")
            span.set_attribute("status_code", "ERROR")
            span.record_exception(exc)
            span.set_status(Status(StatusCode.ERROR, str(exc)))
            raise


def set_span_io(
    span,
    *,
    kind: str | None = None,
    input_value: str | None = None,
    output_value: str | None = None,
):
    attributes = {}
    if kind:
        attributes["openinference.span.kind"] = kind.upper()
    if input_value is not None:
        attributes["input.value"] = _format_io_value(input_value)
        attributes["input.mime_type"] = _mime_type(input_value)
    if output_value is not None:
        attributes["output.value"] = _format_io_value(output_value)
        attributes["output.mime_type"] = _mime_type(output_value)
    set_span_attributes(span, attributes)


def set_span_attributes(span, attributes: dict | None):
    if not attributes:
        return

    for key, value in attributes.items():
        if value is None:
            continue
        if isinstance(value, (str, bool, int, float)):
            span.set_attribute(key, value)
        elif isinstance(value, (list, tuple)):
            span.set_attribute(key, [str(item) for item in value])
        else:
            span.set_attribute(key, str(value))


class _NoopSpan:
    def set_attribute(self, *_args, **_kwargs):
        return None

    def set_status(self, *_args, **_kwargs):
        return None

    def record_exception(self, *_args, **_kwargs):
        return None


def _format_io_value(value):
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, default=str)
    return str(value)


def _mime_type(value):
    if isinstance(value, (dict, list, tuple)):
        return "application/json"
    return "text/plain"
