"""Structured logging without secrets."""
import logging
import re

SECRET_PAT = re.compile(r"(api[_-]?key|token|password|secret)\s*[:=]\s*\S+", re.I)


class RedactFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        try:
            record.msg = SECRET_PAT.sub(r"\1=***", str(record.getMessage()))
            record.args = ()
        except Exception:
            pass
        return True


def setup_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        "%(asctime)s %(levelname)s [rajiblabs] %(name)s :: %(message)s"))
    root = logging.getLogger("rajiblabs")
    root.setLevel(logging.INFO)
    root.handlers = [handler]
    root.addFilter(RedactFilter())
