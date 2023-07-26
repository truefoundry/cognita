import logging
import sys

logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler = logging.StreamHandler(stream=sys.stdout)
handler.setLevel(logging.INFO)
handler.setFormatter(formatter)
logger.addHandler(handler)
