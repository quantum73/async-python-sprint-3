import asyncio
import functools
import logging
import signal
import sys
import typing as tp
from asyncio.streams import StreamReader, StreamWriter
from dataclasses import dataclass, field

import handlers
import services
from config import SERVER_PORT, SERVER_HOST
from core import DummyDatabase
from core.schemas import Command, User, Route
from core.utils import prepare_message


@dataclass(eq=False, order=False)
class Server:
    host: str = SERVER_HOST
    port: int = SERVER_PORT
    routes: tp.MutableSequence[Route] = field(init=False, repr=False, default_factory=list)

    _dummy_db: DummyDatabase = field(init=False, repr=False)
    _logger: logging.Logger = field(init=False, repr=False)

    def __post_init__(self):
        self._dummy_db = DummyDatabase()
        self._logger = logging.getLogger(self.__class__.__name__)

    def _stop_server(self, loop: asyncio.AbstractEventLoop):
        self._dummy_db.clear()
        self._logger.info("Closing server...")
        loop.stop()
        self._logger.info("Server is closed!")
        sys.exit(0)

    def get_handler(self, command_name: str) -> tp.Callable:
        for route in self.routes:
            if route.name == command_name:
                self._logger.info("Execute %s handler" % route.name)
                return route.handler
        else:
            self._logger.info("Execute default handler")
            return handlers.default

    async def send_message_to_user(self, receiver: User, message: str) -> None:
        message = prepare_message(message)
        receiver.writer.write(message.encode())
        await receiver.writer.drain()

    async def close_connection(self, user: User) -> None:
        if not user.writer.is_closing():
            user.writer.close()
            await user.writer.wait_closed()

    async def entrypoint(self, reader: StreamReader, writer: StreamWriter):
        user = services.get_or_create_user(reader=reader, writer=writer)
        while True:
            try:
                request = await reader.read(1024)
            except Exception as err:
                self._logger.error(err)
                break

            if not request:
                break

            if user.is_banned or user.is_chating_blocked:
                self._logger.info("%s banned or blocked" % user)
                await services.send_block_or_ban_message(user)
                continue

            command = Command(request=request)
            if not user.is_connected and command.name != "/connect":
                self._logger.info("%s is not connected" % user)
                await services.send_not_connected_message(user)
                continue

            handler = self.get_handler(command_name=command.name)
            await handler(user, command)

        self._logger.info("Stop serving %s" % user)
        await self.close_connection(user)

    async def run(self) -> None:
        loop = asyncio.get_event_loop()
        # Signal handlers
        for signal_ in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(signal_, functools.partial(self._stop_server, loop=loop))
        # Run server
        srv = await asyncio.start_server(self.entrypoint, host=self.host, port=self.port)
        self._logger.info("Server is running on %s:%s" % (self.host, self.port))
        async with srv:
            await srv.serve_forever()


async def main() -> None:
    server = Server(host="127.0.0.1", port=8000)
    server.routes = [
        Route(name="/connect", handler=handlers.connect),
        Route(name="/disconnect", handler=handlers.disconnect),
        Route(name="/status", handler=handlers.status),
        Route(name="/report", handler=handlers.report),
        Route(name="/send", handler=handlers.send),
    ]
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
