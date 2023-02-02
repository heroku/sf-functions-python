import logging

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


def get_logger() -> structlog.stdlib.BoundLogger:
    """
    Create a logger instance that outputs logs in logfmt style.

    The logger's API matches the stdlib's `logger.Logger`, but the output
    is in the structured `logfmt` logging style.

    Example:

    ```python
    from salesforce_functions import get_logger

    logger = get_logger()

    async def function(event: InvocationEvent[Any], context: Context):
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")

        logger.info("Info message with an additional structured log attribute", record_id=12345)
    ```
    """
    # structlog's `get_logger()` returns a proxy that only instantiates the logger on first usage.
    # Calling `bind()` here ensures that this instantiation doesn't have to occur each time a
    # the function is invoked. `configure_logging()` must be called (by us) prior to `get_logger()`
    # being used for the first time.
    return structlog.stdlib.get_logger().bind()
