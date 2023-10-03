import asyncio
import functools
import logging
import signal
import sys
from asyncio.streams import StreamReader, StreamWriter
from dataclasses import dataclass, field
from logging.config import dictConfig

import handlers
from config import LOGGING_CONFIG
from core import DummyDatabase
from core.schemas import Command
from services import (
    get_or_create_user_by_peer_name,
    send_start_message,
    create_message,
    user_can_send_message,
)

dictConfig(LOGGING_CONFIG)
logger = logging.getLogger()


@dataclass(eq=False, order=False)
class Server:
    host: str = "127.0.0.1"
    port: int = 8000
    dummy_db: DummyDatabase = field(init=False, repr=False)

    def __post_init__(self):
        self.dummy_db = DummyDatabase()

    def _stop_server(self, loop: asyncio.AbstractEventLoop):
        self.dummy_db.clear()
        logger.info("Closing server...")
        loop.stop()
        logger.info("Server is closed!")
        sys.exit(0)

    @staticmethod
    def request_to_command(raw_request: bytes) -> Command:
        decode_request = raw_request.decode()
        request_elements = list(filter(lambda x: x.strip(), decode_request.strip().split()))
        command_name, *command_args = request_elements
        return Command(name=command_name, arguments=command_args, request=decode_request)

    async def connect(self, reader: StreamReader, writer: StreamWriter):
        peer_name = writer.get_extra_info("peername")
        user = get_or_create_user_by_peer_name(peer_name=peer_name, reader=reader, writer=writer)
        logger.info("Start serving %s", user)
        await send_start_message(user_to=user)

        while True:
            request = await reader.read(1024)
            if not request:
                break
            if not await user_can_send_message(user):
                logger.info("%s banned or blocked for sending messages" % user)
                continue

            command = self.request_to_command(request)
            if command.name == "/report":
                await handlers.report(initiator=user, target_user_id=command.arguments[0])
            else:
                message = await create_message(sender=user, content=command.request)
                logger.info("Created Message[%s]" % message.idx)

        logger.info("Stop serving %s and close connection" % user)
        await user.disconnect()

    async def run(self) -> None:
        loop = asyncio.get_event_loop()
        # Signal handlers
        loop.add_signal_handler(signal.SIGINT, functools.partial(self._stop_server, loop=loop))
        loop.add_signal_handler(signal.SIGTERM, functools.partial(self._stop_server, loop=loop))
        # Run server
        srv = await asyncio.start_server(self.connect, host=self.host, port=self.port)
        logger.info("Server is running on %s:%s" % (self.host, self.port))
        async with srv:
            await srv.serve_forever()


async def main() -> None:
    server = Server(host="127.0.0.1", port=8000)
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
