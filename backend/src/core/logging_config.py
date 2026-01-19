import structlog
import logging
import sys
from typing import Any, Dict

def configure_logging():
    """
    Configures structlog to work with standard logging and output JSON.
    """
    
    # 1. Configure Standard Library Logging (for libraries like uvicorn, sqlalchemy)
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )

    # 2. Configure Structlog Processors
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars, # Merge async context (request_id)
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer() # Output as JSON
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # 3. Intercept standard logging messages and redirect to structlog
    # This ensures logs from 'uvicorn' or 'sqlalchemy' also get JSON formatted if possible
    # (Optional, but good for consistency)
