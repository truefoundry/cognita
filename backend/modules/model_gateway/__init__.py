# When using locally, you can create your own models_config.json file before running docker-compose.
# The following code is used for tf-deployments
import json
import os

from backend.logger import logger

# Check if models_config.sample.json exists but not models_config.json
# If models_config.sample.json exists, copy it to models_config.json
if os.path.exists("./models_config.sample.json") and not os.path.exists(
    "./models_config.json"
):
    logger.info(
        "models_config.json not found. Creating models_config.json from models_config.sample.json"
    )
    with open("./models_config.sample.json") as f:
        data = json.load(f)
        with open("./models_config.json", "w") as f:
            json.dump(data, f, indent=4)
