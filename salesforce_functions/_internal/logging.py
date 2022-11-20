import logging
from typing import Callable

import structlog


def configure_logging() -> None:
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.EventRenamer("msg"),
            structlog.processors.ExceptionRenderer(),
            # TODO: Only apply the pretty printer in development?
            structlog.processors.ExceptionPrettyPrinter(),
            structlog.processors.LogfmtRenderer(),
            # TODO: Use console renderer instead in development?
            # structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        logger_factory=structlog.WriteLoggerFactory(),
        cache_logger_on_first_use=True,
    )


get_logger: Callable[..., structlog.stdlib.BoundLogger] = structlog.stdlib.get_logger
