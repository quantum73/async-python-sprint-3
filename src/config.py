import logging
import sys
from pathlib import Path

import yaml
from yaml import Loader

BASE_DIR = Path(__file__).parent
config_path = BASE_DIR / "config.yml"
with config_path.open("r", encoding="utf8") as f:
    config = yaml.load(f, Loader=Loader)

logging.basicConfig(**config["logging"], stream=sys.stdout)

ALREADY_CONNECTED_MESSAGE_TEMPLATE = "[*] You are already connected."
NO_MESSAGE_TEMPLATE = "[*] No messages yet."
ERROR_REQUEST_MESSAGE_TEMPLATE = "[*] Invalid request. Try again."
NOT_CONNECTED_MESSAGE_TEMPLATE = "[*] You are not connected. Please, request /connect command."
BAN_MESSAGE_TEMPLATE = "[*] You banned to {banned_to}."
BLOCK_CHATING_MESSAGE_TEMPLATE = "[*] You have no message limit. Try again at {block_to}."
USER_NO_FOUND_MESSAGE_TEMPLATE = "[*] User with {user_id} id does not exists."

DATE_FORMAT = config["logging"]["datefmt"]

server_config = config["server"]

SERVER_HOST = server_config.get("SERVER_HOST", "127.0.0.1")
SERVER_PORT = server_config.get("SERVER_PORT", 8000)

SHOW_LAST_MESSAGES_COUNT = server_config.get("show_last_messages_count", 20)
MESSAGE_LIFETIME_SECONDS = server_config.get("message_lifetime_seconds", 3600)
USER_MESSAGE_LIMIT = server_config.get("user_message_limit", 20)
CHATING_BLOCK_LIFETIME_SECONDS = server_config.get("chating_block_lifetime_seconds", 3600)
MAX_REPORTS_COUNT = server_config.get("max_reports_count", 3)
BAN_LIFETIME_SECONDS = server_config.get("ban_lifetime_seconds", 14400)
