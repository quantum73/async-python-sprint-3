import asyncio
import hashlib
import logging
from asyncio import StreamWriter, StreamReader

from config import (
    SHOW_LAST_MESSAGES_COUNT,
    MAX_REPORTS_COUNT,
    CHATING_BLOCK_LIFETIME_SECONDS,
    BAN_MESSAGE_TEMPLATE,
    BLOCK_CHATING_MESSAGE_TEMPLATE,
    BAN_LIFETIME_SECONDS,
    MESSAGE_LIFETIME_SECONDS,
    NOT_CONNECTED_MESSAGE_TEMPLATE,
    NO_MESSAGE_TEMPLATE,
)
from core import DummyDatabase
from core.schemas import User, Message
from core.utils import get_now_with_delta, prepare_message
from tasks import remove_user_chating_block, remove_user_ban, remove_expired_message

logger = logging.getLogger(__name__)

dummy_db = DummyDatabase()


async def send_message_to_user(user: User, message: str) -> None:
    message = prepare_message(message)
    user.writer.write(message.encode())
    await user.writer.drain()


async def send_block_or_ban_message(user: User) -> None:
    if user.is_banned:
        await send_message_to_user(
            user=user,
            message=BAN_MESSAGE_TEMPLATE.format(banned_to=user.banned_to),
        )
    elif user.is_chating_blocked:
        await send_message_to_user(
            user=user,
            message=BLOCK_CHATING_MESSAGE_TEMPLATE.format(block_to=user.chating_blocked_to),
        )


async def send_not_connected_message(user: User) -> None:
    if not user.is_connected:
        await send_message_to_user(user=user, message=NOT_CONNECTED_MESSAGE_TEMPLATE)


def create_user_id_by_peer_name(peer_name: tuple[str, int]) -> str:
    peer_name_to_bytes = str(peer_name).encode()
    user_id = hashlib.md5(peer_name_to_bytes).hexdigest()
    return user_id


def get_or_create_user(*, reader: StreamReader, writer: StreamWriter) -> User:
    peer_name = writer.get_extra_info("peername")
    logger.info("Create user id by peername (%s)" % str(peer_name))
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
    last_status_request = user_to.last_status_request_at
    if last_status_request:
        logger.info("Get last messages from %s" % last_status_request)
        last_messages = dummy_db.messages.get_all_from_date(date_filter=last_status_request)
    else:
        logger.info("Get last %s messages" % SHOW_LAST_MESSAGES_COUNT)
        last_messages = dummy_db.messages.get_all()

    if len(last_messages) == 0:
        await send_message_to_user(user_to, NO_MESSAGE_TEMPLATE)
        return

    for message_obj in last_messages:
        await send_message_to_user(user_to, repr(message_obj))


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
