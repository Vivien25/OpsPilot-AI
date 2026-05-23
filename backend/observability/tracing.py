from contextlib import contextmanager


@contextmanager
def start_span(name: str, attributes: dict | None = None):
    """
    Start an OpenTelemetry span when Arize AX/OpenTelemetry is installed.
    Falls back to a no-op context so local development still works before setup.
    """
    try:
        from opentelemetry import trace
    except ImportError:
        yield _NoopSpan()
        return

    tracer = trace.get_tracer("opspilot-ai")
    with tracer.start_as_current_span(name) as span:
        if attributes:
            set_span_attributes(span, attributes)
        yield span


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
