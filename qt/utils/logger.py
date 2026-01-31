def get_logger(name: str):
    import logging
    import json
    import os

    class JsonFormatter(logging.Formatter):
        def format(self, record: logging.LogRecord) -> str:
            payload = {
                "ts": self.formatTime(record, self.datefmt),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
            }
            return json.dumps(payload)

    logger = logging.getLogger(name)
    if not logger.handlers:
        h = logging.StreamHandler()
        log_format = os.getenv("QT_LOG_FORMAT", "plain").lower()
        if log_format == "json":
            fmt = JsonFormatter()
        else:
            fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
        h.setFormatter(fmt)
        logger.addHandler(h)
        logger.setLevel(logging.INFO)
    return logger
