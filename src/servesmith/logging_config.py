"""Structured logging with JSON output and request ID tracking."""

import logging
import json
import sys
import uuid
from contextvars import ContextVar

request_id_var: ContextVar[str] = ContextVar("request_id", default="")


class JSONFormatter(logging.Formatter):
    """JSON log formatter with request ID context."""

    def format(self, record: logging.LogRecord) -> str:
        log = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        rid = request_id_var.get("")
        if rid:
            log["request_id"] = rid
        if record.exc_info and record.exc_info[0]:
            log["exception"] = self.formatException(record.exc_info)
        return json.dumps(log)


def setup_logging(json_output: bool = False) -> None:
    """Configure logging. JSON mode for production, text for dev."""
    handler = logging.StreamHandler(sys.stdout)
    if json_output:
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        ))
    logging.basicConfig(level=logging.INFO, handlers=[handler], force=True)


def generate_request_id() -> str:
    """Generate a short request ID."""
    return uuid.uuid4().hex[:8]
