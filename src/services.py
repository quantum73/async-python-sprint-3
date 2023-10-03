import asyncio
import hashlib
import logging
from asyncio import StreamWriter, StreamReader
from logging.config import dictConfig

from config import (
    LOGGING_CONFIG,
    SHOW_LAST_MESSAGES_COUNT,
    MAX_REPORTS_COUNT,
    CHATING_BLOCK_LIFETIME_SECONDS,
    BAN_MESSAGE_TEMPLATE,
    BLOCK_CHATING_MESSAGE_TEMPLATE,
    BAN_LIFETIME_SECONDS,
    MESSAGE_LIFETIME_SECONDS,
)
from core import DummyDatabase
from core.schemas import User, Message
from core.utils import get_now_with_delta
from tasks import remove_user_chating_block, remove_user_ban, remove_expired_message

dictConfig(LOGGING_CONFIG)
logger = logging.getLogger()

dummy_db = DummyDatabase()


async def send_message_to_user(user: User, message: str) -> None:
    user.writer.write(f"{message}\n".encode())
    await user.writer.drain()


async def user_can_send_message(user: User) -> bool:
    if user.is_banned:
        await send_message_to_user(
            user=user,
            message=BAN_MESSAGE_TEMPLATE.format(banned_to=user.banned_to),
        )
        return False
    if user.is_chating_blocked:
        await send_message_to_user(
            user=user,
            message=BLOCK_CHATING_MESSAGE_TEMPLATE.format(block_to=user.chating_blocked_to),
        )
        return False

    return True


def create_user_id_by_peer_name(peer_name: tuple[str, int]) -> str:
    logger.info("Create user id by peername")
    peer_name_to_bytes = str(peer_name).encode()
    user_id = hashlib.md5(peer_name_to_bytes).hexdigest()
    return user_id


def get_or_create_user_by_peer_name(*, peer_name: tuple[str, int], reader: StreamReader, writer: StreamWriter) -> User:
    logger.info("Create user id by peername")
    user_id = create_user_id_by_peer_name(peer_name)
    logger.info("Check user in db")
    user = dummy_db.users.get_by_id(idx=user_id)
    if not user:
        logger.info("Create new user")
        user = User(
            idx=user_id,
            host=peer_name[0],
            port=peer_name[1],
            reader=reader,
            writer=writer,
        )
        dummy_db.users.add(user)
    return user


async def send_start_message(*, user_to: User) -> None:
    last_exit = user_to.last_exit
    if last_exit:
        logger.info("Get last messages from %s" % last_exit)
        last_messages = dummy_db.messages.get_all_from_date(date_filter=last_exit)
    else:
        logger.info("Get last %s messages" % SHOW_LAST_MESSAGES_COUNT)
        last_messages = dummy_db.messages.get_all()

    for message in last_messages:
        await send_message_to_user(user_to, str(message))


async def decrease_user_messages_limit(user: User) -> None:
    user.message_limit -= 1
    if user.message_limit > 0:
        return

    logger.info("Blocking messaging for %s" % user)
    user.is_chating_blocked = True
    user.chating_blocked_to = get_now_with_delta(seconds=CHATING_BLOCK_LIFETIME_SECONDS)

    asyncio.get_running_loop().call_later(
        CHATING_BLOCK_LIFETIME_SECONDS,
        remove_user_chating_block,
        user,
    )


async def create_message(sender: User, content: str) -> Message:
    message = Message(sender=sender, content=content)
    dummy_db.messages.add(message)
    asyncio.get_running_loop().call_later(
        MESSAGE_LIFETIME_SECONDS,
        remove_expired_message,
        message,
    )

    await decrease_user_messages_limit(user=sender)
    return message


async def report_on_user(user: User) -> None:
    user.reports_count += 1
    if user.reports_count < MAX_REPORTS_COUNT:
        return

    logger.info("%s reports count is %s. Ban!" % (user, user.reports_count))
    user.is_banned = True
    user.banned_to = get_now_with_delta(seconds=BAN_LIFETIME_SECONDS)

    asyncio.get_running_loop().call_later(
        BAN_LIFETIME_SECONDS,
        remove_user_ban,
        user,
    )
