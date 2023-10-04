import logging
from datetime import datetime

import services
from config import (
    ERROR_REQUEST_MESSAGE_TEMPLATE,
    USER_NO_FOUND_MESSAGE_TEMPLATE,
    NO_MESSAGE_TEMPLATE,
    ALREADY_CONNECTED_MESSAGE_TEMPLATE,
)
from core import DummyDatabase
from core.schemas import User, Command

dummy_db = DummyDatabase()

logger = logging.getLogger(__name__)


async def connect(user: User, command: Command | None = None) -> None:
    if user.is_connected:
        await services.send_message_to_user(user=user, message=ALREADY_CONNECTED_MESSAGE_TEMPLATE)
        return

    user.is_connected = True
    logger.info("%s connected!" % user)
    await services.send_start_message(user_to=user)


async def disconnect(user: User, command: Command | None = None) -> None:
    logger.info("%s disconnect" % user)
    user.is_connected = False
    await user.disconnect()


async def send(user: User, command: Command | None = None) -> None:
    if command is None:
        logger.error('send handler must have "command" parameter')
        await services.send_message_to_user(user=user, message=ERROR_REQUEST_MESSAGE_TEMPLATE)
        return

    message_content = command.arguments_to_string()
    message = await services.create_message(sender=user, content=message_content)
    logger.info("Created Message[%s] by %s" % (message.idx, user))


async def status(user: User, command: Command | None = None) -> None:
    last_messages = dummy_db.messages.get_all(limit=None)
    logger.info("Show %s %s messages" % (user, len(last_messages)))
    user.last_status_request_at = datetime.now()
    if len(last_messages) == 0:
        await services.send_message_to_user(user, NO_MESSAGE_TEMPLATE)
        return

    for message_obj in last_messages:
        await services.send_message_to_user(user, repr(message_obj))


async def report(user: User, command: Command | None = None) -> None:
    if command is None:
        logger.error('report handler must have "command" parameter')
        await services.send_message_to_user(user=user, message=ERROR_REQUEST_MESSAGE_TEMPLATE)
        return

    command_arguments = command.arguments
    target_user_id = command_arguments[0] if len(command_arguments) != 0 else ""
    target_user = dummy_db.users.get_by_id(idx=target_user_id)

    if target_user and target_user.idx != user.idx:
        logger.info("Ban report on %s" % target_user)
        await services.report_on_user(target_user)
    else:
        await services.send_message_to_user(
            user=user,
            message=USER_NO_FOUND_MESSAGE_TEMPLATE.format(user_id=target_user_id),
        )


async def default(user: User, command: Command | None = None) -> None:
    logger.info("Invalid request. Send error to %s" % user)
    await services.send_message_to_user(user=user, message=ERROR_REQUEST_MESSAGE_TEMPLATE)
