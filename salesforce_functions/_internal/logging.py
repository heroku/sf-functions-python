import logging
from typing import Callable

import structlog


def configure_logging() -> None:
    """
    Configure structlog to output logs in logfmt format, using options recommended for best performance.

    https://www.brandur.org/logfmt
    https://www.structlog.org/en/stable/performance.html
    """
    structlog.configure(
        processors=[
            # Adds any log attributes bound to the request context (such as `invocationId`).
            structlog.contextvars.merge_contextvars,
            # Adds the log event level as `level={info,warning,...}`.
            structlog.processors.add_log_level,
            # Override the default structlog message key name of `event`.
            structlog.processors.EventRenamer("msg"),
            # Pretty print any exceptions prior to the logfmt log line referencing the exception.
            # The output is not in logfmt style, but makes the exception much easier to read than
            # trying to newline escape it and output it under an attribute on the log line itself.
            structlog.processors.ExceptionPrettyPrinter(),
            structlog.processors.LogfmtRenderer(),
        ],
        # Only output log level info and above.
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        logger_factory=structlog.WriteLoggerFactory(),
        cache_logger_on_first_use=True,
    )


get_logger: Callable[..., structlog.stdlib.BoundLogger] = structlog.stdlib.get_logger
