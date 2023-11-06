"""
Logging configuration for the OGM.

Logging is controlled by two environment variables:
- : the log level to use (default: WARNING)
- PYNEO4J_OGM_ENABLE_LOGGING: whether to enable logging (default: True)
"""
import logging
from os import environ

# Get log level and whether to enable logging from environment variables
enable_logging = environ.get("PYNEO4J_OGM_ENABLE_LOGGING", "True").lower() == "true"
log_level = int(environ.get("PYNEO4J_OGM_LOG_LEVEL", logging.WARNING))

logger = logging.getLogger("pyneo4j-ogm")
logger.setLevel(log_level)

handler = logging.StreamHandler()
handler.setLevel(log_level)

formatter = logging.Formatter("[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

if not enable_logging:
    logger.disabled = True
