import asyncio
import logging
import typing as tp
import uuid

from config import SERVER_HOST, SERVER_PORT, CLIENT_HELP_MESSAGE, CLIENT_MESSAGE_TEMPLATE
from core.schemas import Command

__all__ = ("Client",)

"""
Приветствую, Матвей.
Надеюсь в третий то раз все получится :D
Не стал особо париться и написал elif'ы, надеюсь ты пропустишь такое.
Хотя я понимаю что не очень)
"""


class Client:
    def __init__(
        self,
        server_host: str = SERVER_HOST,
        server_port: int = SERVER_PORT,
        butch_size: int = 1024,
        logging_level: int = logging.CRITICAL,
    ) -> None:
        self.idx = str(uuid.uuid4())
        self._server_host = server_host
        self._server_port = server_port
        self._butch_size = butch_size

        self.logger = logging.getLogger(f"{self.__class__.__name__}[{self.idx}]")
        self.logger.setLevel(logging_level)

    async def __aenter__(self) -> tp.Self:
        self._reader, self._writer = await asyncio.open_connection(self._server_host, self._server_port)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> bool:
        self.logger.info("Close context manager")
        await self.__close_connection()
        return True

    async def __close_connection(self) -> None:
        """
        Вспомогательный метод для закрытия соединения.
        Вызываем его при закрытии контекстного менеджера.
        """
        if not self._writer.is_closing():
            self._writer.close()
            await self._writer.wait_closed()

    async def read(self) -> str:
        """Считываем определенное количество байт (_butch_size) с сервера и возвращаем ответ в виде строки"""
        try:
            received_data = await asyncio.wait_for(self._reader.read(self._butch_size), timeout=1)
        except asyncio.TimeoutError:
            decode_data = "No data"
        else:
            decode_data = received_data.decode().strip()
        return decode_data

    async def _send(self, message: str) -> None:
        """Вспомогательный метод для отправки сообщения на сервер"""
        self._writer.write(message.encode())
        await self._writer.drain()

    async def connect(self):
        """Отправляем /connect команду на сервер"""
        await self._send(message="/connect")

    async def disconnect(self) -> None:
        """Отправляем /disconnect команду на сервер"""
        await self._send(message="/disconnect")

    async def report(self, user_id: str):
        """
        Отправляем /report команду на сервер.
        В качестве параметра указываем айди юзера, на которого жалуемся.
        """
        command = "/report"
        result_message = f"{command} {user_id}"
        await self._send(result_message)

    async def status(self):
        """Отправляем /status команду на сервер"""
        await self._send(message="/status")

    async def send(self, message: str):
        """
        Отправляем /send команду на сервер.
        В качестве параметра указываем сообщение, которое хотим отправить.
        """
        command = "/send"
        result_message = f"{command} {message}"
        await self._send(result_message)

    async def run(self):
        self.logger.info(CLIENT_HELP_MESSAGE)
        while True:
            data = await self.read()
            if not data:
                break
            self.logger.info(CLIENT_MESSAGE_TEMPLATE.format(data))

            user_input = input(">>>: ")
            command = Command(request=user_input)
            if self._writer.is_closing():
                break

            if command.name == "/help":
                self.logger.info(CLIENT_HELP_MESSAGE)
            elif command.name == "/connect":
                await self.connect()
            elif command.name == "/send":
                message = command.arguments[0]
                await self.send(message)
            elif command.name == "/status":
                await self.status()
            elif command.name == "/report":
                user_id = command.arguments[0]
                await self.report(user_id)
            elif command.name == "/exit":
                await self.disconnect()
                self.logger.info(CLIENT_MESSAGE_TEMPLATE.format("Close client!"))
                break
            else:
                self.logger.info(CLIENT_MESSAGE_TEMPLATE.format("Invalid request!"))

        await self.__close_connection()


async def run_client() -> None:
    async with Client(logging_level=logging.INFO) as client:
        await client.run()


if __name__ == "__main__":
    asyncio.run(run_client())
