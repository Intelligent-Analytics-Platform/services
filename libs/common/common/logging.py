"""Structured JSON logging setup for microservices."""

import logging
import sys

from pythonjsonlogger.json import JsonFormatter


def setup_logging(service: str, level: str = "INFO") -> None:
    """Configure root logger to emit structured JSON to stdout.

    Each log record includes a 'service' field for Loki label filtering.
    """
    handler = logging.StreamHandler(sys.stdout)
    formatter = JsonFormatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(service)s %(message)s",
        rename_fields={
            "asctime": "timestamp",
            "levelname": "level",
            "name": "logger",
        },
    )
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)

    # Inject 'service' field into every LogRecord
    old_factory = logging.getLogRecordFactory()

    def _factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        record.service = service
        return record

    logging.setLogRecordFactory(_factory)
