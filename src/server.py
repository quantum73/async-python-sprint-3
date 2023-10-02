import asyncio
import functools
import logging
import signal
import sys
import typing as tp
from asyncio.streams import StreamReader, StreamWriter
from dataclasses import dataclass, field
from logging.config import dictConfig

import handlers
import tasks
from config import LOGGING_CONFIG
from core import DummyDatabase
from core.schemas import Command
from services import get_or_create_user_by_peer_name, send_start_message

dictConfig(LOGGING_CONFIG)
logger = logging.getLogger()


@dataclass(eq=False, order=False)
class Server:
    host: str = "127.0.0.1"
    port: int = 8000
    on_startup_tasks: list[tp.Coroutine] = field(init=False, repr=False, default_factory=list)
    routes: dict[str, tp.Callable] = field(init=False, repr=False, default_factory=dict)
    dummy_db: DummyDatabase = field(init=False, repr=False)

    def __post_init__(self):
        self.dummy_db = DummyDatabase()

    def _stop_server(self, loop: asyncio.AbstractEventLoop):
        self.dummy_db.clear()
        logger.info("Handle SIGINT or SIGTERM signal.")
        loop.stop()
        logger.info("Close server!")
        sys.exit(0)

    @staticmethod
    def request_to_command(request: bytes) -> Command:
        decode_request = request.decode()
        request_elements = list(filter(lambda x: x.strip(), decode_request.strip().split()))
        command_name, *command_args = request_elements
        return Command(name=command_name, arguments=command_args)

    async def connect(self, reader: StreamReader, writer: StreamWriter):
        peer_name = writer.get_extra_info("peername")
        user = get_or_create_user_by_peer_name(peer_name=peer_name, reader=reader, writer=writer)
        logger.info("Start serving %s", user)
        await send_start_message(user_to=user)

        while True:
            request = await reader.read(1024)
            if not request:
                break

            command = self.request_to_command(request)
            handler = self.routes.get(command.name)
            logger.info("handler: %s" % handler)
            if handler:
                await handler(user, *command.arguments)

        logger.info("Stop serving %s and close connection", user)
        await user.disconnect()

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
    server.routes = {
        "/report": handlers.report,
    }
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
