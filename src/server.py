import asyncio
import functools
import logging
import signal
import sys
import typing as tp
from asyncio.streams import StreamReader, StreamWriter
from dataclasses import dataclass, field
from datetime import datetime
from logging.config import dictConfig

import tasks
from config import (
    LOGGING_CONFIG,
    BAN_MESSAGE_TEMPLATE,
    BLOCK_CHATING_MESSAGE_TEMPLATE,
    DATE_FORMAT,
    SERVER_MESSAGE_TEMPLATE,
)
from core import DummyDatabase
from core.schemas import Command, User
from services import (
    get_or_create_user_by_peer_name,
    send_start_message,
    create_message,
)

dictConfig(LOGGING_CONFIG)
logger = logging.getLogger()


@dataclass(eq=False, order=False)
class Server:
    host: str = "127.0.0.1"
    port: int = 8000
    on_startup_tasks: list[tp.Coroutine] = field(init=False, repr=False, default_factory=list)
    dummy_db: DummyDatabase = field(init=False, repr=False)

    def _object_as_string(self) -> str:
        now = datetime.now().strftime(DATE_FORMAT)
        return "<Server(%s:%s)>[%s]" % (self.host, self.port, now)

    def __str__(self) -> str:
        return self._object_as_string()

    def __repr__(self) -> str:
        return self._object_as_string()

    def __post_init__(self):
        self.dummy_db = DummyDatabase()

    def _stop_server(self, loop: asyncio.AbstractEventLoop):
        self.dummy_db.clear()
        logger.info("Handle SIGINT or SIGTERM signal.")
        loop.stop()
        logger.info("Close server!")
        sys.exit(0)

    @staticmethod
    def request_to_command(raw_request: bytes) -> Command:
        decode_request = raw_request.decode()
        request_elements = list(filter(lambda x: x.strip(), decode_request.strip().split()))
        command_name, *command_args = request_elements
        return Command(name=command_name, arguments=command_args, request=decode_request)

    async def send_message_to_user(self, user: User, message: str) -> None:
        server_message = SERVER_MESSAGE_TEMPLATE.foramt(server_obj=self, message=message)
        user.writer.write(server_message.encode())
        await user.writer.drain()

    async def disconnect_user(self, user: User) -> None:
        user.last_exit = datetime.now()
        user.writer.close()

    async def _user_can_send_message(self, user: User) -> bool:
        if user.is_banned:
            await self.send_message_to_user(
                user=user,
                message=BAN_MESSAGE_TEMPLATE.format(banned_to=user.banned_to),
            )
            return False
        if user.is_chating_blocked:
            await self.send_message_to_user(
                user=user,
                message=BLOCK_CHATING_MESSAGE_TEMPLATE.format(block_to=user.chating_blocked_to),
            )
            return False

        return True

    async def connect(self, reader: StreamReader, writer: StreamWriter):
        peer_name = writer.get_extra_info("peername")
        user = get_or_create_user_by_peer_name(peer_name=peer_name, reader=reader, writer=writer)
        logger.info("Start serving %s", user)
        await send_start_message(user_to=user)

        while True:
            request = await reader.read(1024)
            if not request:
                break

            # Command logic
            command = self.request_to_command(request)
            if command.name.startswith("/"):
                logger.info("command: %s" % command)
                continue

            # Messages logic
            if not await self._user_can_send_message(user):
                logger.info("%s banned or blocked sending messages" % user)
                continue

            await create_message(sender=user, content=command.request)

        logger.info("Stop serving %s and close connection", user)
        await self.disconnect_user(user)

    async def run(self) -> None:
        loop = asyncio.get_event_loop()
        # Signal handlers
        logger.info("Init signal handlers...")
        loop.add_signal_handler(signal.SIGINT, functools.partial(self._stop_server, loop=loop))
        loop.add_signal_handler(signal.SIGTERM, functools.partial(self._stop_server, loop=loop))
        # Init on startup tasks
        logger.info("Init startup tasks...")
        for on_startup_coro in self.on_startup_tasks:
            loop.create_task(on_startup_coro)
        # Run server
        logger.info("Run server...")
        srv = await asyncio.start_server(self.connect, host=self.host, port=self.port)
        logger.info("Server is running on %s:%s" % (self.host, self.port))
        async with srv:
            await srv.serve_forever()


async def main() -> None:
    server = Server(host="127.0.0.1", port=8000)
    server.on_startup_tasks = [
        tasks.check_messages_lifetime(),
    ]
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
