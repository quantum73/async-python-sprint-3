import hashlib
import logging
from datetime import datetime, timedelta
from logging.config import dictConfig

from config import LOGGING_CONFIG, SHOW_LAST_MESSAGES_COUNT, MAX_REPORTS_COUNT, BAN_LIFETIME_SECONDS, DATE_FORMAT
from core import DummyDatabase
from core.schemas import User

dictConfig(LOGGING_CONFIG)
logger = logging.getLogger()

dummy_db = DummyDatabase()


def create_user_id_by_peer_name(peer_name: tuple[str, int]) -> str:
    logger.info("Create user id by peername")
    peer_name_to_bytes = str(peer_name).encode()
    user_id = hashlib.md5(peer_name_to_bytes).hexdigest()
    return user_id


def get_or_create_user_by_peer_name(*, peer_name: tuple[str, int], **kwargs) -> User:
    logger.info("Create user id by peername")
    user_id = create_user_id_by_peer_name(peer_name)
    logger.info("Check user in db")
    user = dummy_db.users.get_by_id(idx=user_id)
    if user:
        logger.info("User already exists")
        return user

    logger.info("Create new user")
    user = User(
        idx=user_id,
        host=peer_name[0],
        port=peer_name[1],
        reader=kwargs["reader"],
        writer=kwargs["writer"],
    )
    dummy_db.users.add(user)
    return user


async def send_start_message(*, user_to: User) -> None:
    logger.info("Get last %s messages" % SHOW_LAST_MESSAGES_COUNT)
    last_messages = dummy_db.messages.get_all()
    logger.info("Send to %s" % user_to)
    for message in last_messages:
        message_as_str = f"{message}\n"
        user_to.writer.write(message_as_str.encode())
        await user_to.writer.drain()


def report_on_user(user: User):
    logger.info("Increase %s reports_count" % user)
    user.reports_count += 1
    if user.reports_count >= MAX_REPORTS_COUNT:
        banned_to = datetime.utcnow() + timedelta(seconds=BAN_LIFETIME_SECONDS)
        user.is_banned = True
        user.banned_to = banned_to
        logger.info("Ban %s user to %s" % user, banned_to.strftime(DATE_FORMAT))
