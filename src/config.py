from pathlib import Path

import yaml

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

BASE_DIR = Path(__file__).parent
config_path = BASE_DIR / "config.yml"
with config_path.open("r", encoding="utf8") as f:
    config = yaml.load(f, Loader=Loader)

LOGGING_CONFIG = config["logging"]
DATE_FORMAT = "%H:%M:%S %d-%m-%Y"

server_config = config["server"]
SHOW_LAST_MESSAGES_COUNT = server_config.get("show_last_messages_count", 20)
MESSAGE_LIFETIME_SECONDS = server_config.get("message_lifetime_seconds", 3600)
MAX_REPORTS_COUNT = server_config.get("max_reports_count", 3)
BAN_LIFETIME_SECONDS = server_config.get("ban_lifetime_seconds", 14400)
