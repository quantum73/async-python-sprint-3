import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from logging.config import dictConfig

from config import LOGGING_CONFIG, MESSAGE_LIFETIME_SECONDS
from core import DummyDatabase
from core.schemas import Message, User

dictConfig(LOGGING_CONFIG)
logger = logging.getLogger()

dummy_db = DummyDatabase()


async def check_messages_lifetime():
    logger.info("Starting check_messages_lifetime task...")
    loop = asyncio.get_running_loop()
    while loop.is_running():
        now = datetime.utcnow()
        all_messages = dummy_db.messages.get_all(limit=None)
        expired_messages = list(
            filter(lambda x: now >= x.created_at + timedelta(seconds=MESSAGE_LIFETIME_SECONDS), all_messages)
        )
        if expired_messages:
            logger.info("Remove %s expired messages" % len(expired_messages))
            for msg in expired_messages:
                dummy_db.messages.delete(msg)

        await asyncio.sleep(1)


async def users_fixture():
    logger.info("Starting users_fixture task...")
    users = [
        User(
            idx=str(uuid.uuid4()),
            host="127.0.0.1",
            port=51500 + i,
        )
        for i in range(10)
    ]
    dummy_db.users.bulk_add(users)
    logger.info("Users fixture is done!")


async def messages_fixture():
    logger.info("Starting messages_fixture task...")
    messages = []
    for i in range(1, 31):
        msg = Message(
            sender=User(
                idx=str(uuid.uuid4()),
                host="127.0.0.1",
                port=i,
            ),
            content=f"Some message {i}",
        )
        messages.append(msg)
        await asyncio.sleep(1)

    dummy_db.messages.bulk_add(messages)
    logger.info("Messages fixture is done!")
