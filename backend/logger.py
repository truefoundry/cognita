import logging
import sys

from backend.settings import settings

LOG_LEVEL = logging.getLevelName(settings.LOG_LEVEL.upper())

logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)
formatter = logging.Formatter(
    "%(levelname)s:    %(asctime)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s"
)
handler = logging.StreamHandler(stream=sys.stdout)
handler.setLevel(LOG_LEVEL)
handler.setFormatter(formatter)
logger.addHandler(handler)
