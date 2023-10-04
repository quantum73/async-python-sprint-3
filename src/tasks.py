import logging

from config import USER_MESSAGE_LIMIT
from core import DummyDatabase
from core.schemas import Message, User

__all__ = ("remove_user_chating_block", "remove_user_ban", "remove_expired_message")

logger = logging.getLogger(__name__)

dummy_db = DummyDatabase()


def remove_user_chating_block(user: User) -> None:
    user.message_limit = USER_MESSAGE_LIMIT
    user.is_chating_blocked = False
    user.chating_blocked_to = None
    logger.info("Remove messaging block for %s" % user)


def remove_user_ban(user: User) -> None:
    user.is_banned = False
    user.banned_to = None
    logger.info("%s ban is expired" % user)


def remove_expired_message(message: Message) -> None:
    logger.info("Delete expired Message<%s>" % message.idx)
    dummy_db.messages.delete(message)
