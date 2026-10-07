import json
import logging
from datetime import UTC, datetime


class JsonFormatter(logging.Formatter):
    def format(self, record):
        # Never serialize request bodies, headers, environment or exception locals.
        payload = {
            "time": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception_type"] = record.exc_info[0].__name__
        return json.dumps(payload)
