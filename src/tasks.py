import asyncio
import logging
from datetime import datetime, timedelta
from logging.config import dictConfig

from config import LOGGING_CONFIG, MESSAGE_LIFETIME_SECONDS
from core import DummyDatabase

dictConfig(LOGGING_CONFIG)
logger = logging.getLogger()

dummy_db = DummyDatabase()


async def check_messages_lifetime():
    logger.info("Starting check_messages_lifetime task...")
    loop = asyncio.get_running_loop()
    while loop.is_running():
        now = datetime.now()
        all_messages = dummy_db.messages.get_all(limit=None)
        expired_messages = list(
            filter(lambda x: now >= x.created_at + timedelta(seconds=MESSAGE_LIFETIME_SECONDS), all_messages)
        )
        if expired_messages:
            logger.info("Remove %s expired messages" % len(expired_messages))
            for msg in expired_messages:
                dummy_db.messages.delete(msg)

        await asyncio.sleep(1)
