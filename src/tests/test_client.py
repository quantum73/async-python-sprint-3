import asyncio

from client import Client
from config import (
    NO_MESSAGE_TEMPLATE,
    SHOW_LAST_MESSAGES_COUNT,
    NOT_CONNECTED_MESSAGE_TEMPLATE,
    ALREADY_CONNECTED_MESSAGE_TEMPLATE,
)


async def report_case_with_expire_ban():
    """
    Кейс с отправкой жалобы на юзера.
    Во время бана на любой запрос забанненный юзер будет получать сообщения типа [*] You banned to {banned_to}.
    Когда бан кончается, пользователь снова может отправлять запросы.
    """
    async with Client() as client1, Client() as client2:
        await client1.connect()
        await asyncio.sleep(0.25)
        _ = await client1.read()
        await asyncio.sleep(0.25)

        await client2.connect()
        await asyncio.sleep(0.25)
        _ = await client2.read()
        await asyncio.sleep(0.25)

        await client1.send(message="Message 1")
        await asyncio.sleep(0.25)

        await client2.status()
        await asyncio.sleep(0.25)

        answer = await client2.read()
        _, _, user_obj, *_ = answer.split()
        user_id = user_obj.strip("<User[]>")
        await asyncio.sleep(0.25)

        await client2.report(user_id)
        await asyncio.sleep(0.25)

        await client1.send(message="Some Message")
        await asyncio.sleep(0.25)

        answer = await client1.read()
        assert answer.startswith("[*] You banned")

        await asyncio.sleep(3.1)

        await client1.status()
        await asyncio.sleep(0.25)
        answer = await client1.read()
        assert not answer.startswith("[*] You banned")


async def message_block_case():
    """
    Кейс с блокировкой отправки сообщения по истечению лимита.
    Когда лимит исчерпан, то юзе будет получать сообщения типа [*] You have no message limit. Try again at {block_to}.
    """
    async with Client() as client1:
        await client1.connect()
        await asyncio.sleep(0.25)
        _ = await client1.read()
        await asyncio.sleep(0.25)

        await client1.send(message="Message 1")
        await asyncio.sleep(0.25)

        await client1.send(message="Message 1")
        await asyncio.sleep(0.25)

        answer = await client1.read()
        assert answer.startswith("[*] You have no message limit.")


async def unconnected_case():
    """
    Кейс при попытке юзера отправлять запросы до вызова команды /connect.
    В таком случае на любой запрос будет приходить сообщение типа
    "[*] You are not connected. Please, request /connect command."
    """
    async with Client() as client1:
        await client1.send(message="Message 1")
        await asyncio.sleep(0.25)

        answer = await client1.read()
        assert answer == NOT_CONNECTED_MESSAGE_TEMPLATE


async def multiple_connect_command_case():
    """
    Кейс при повторного вызова команды /connect.
    В таком случае на повторный запрос /connect будет приходить сообщение "[*] You are already connected."
    """
    async with Client() as client1:
        await client1.connect()
        await asyncio.sleep(0.25)
        _ = await client1.read()
        await asyncio.sleep(0.25)

        await client1.connect()
        await asyncio.sleep(0.25)
        answer = await client1.read()
        assert answer == ALREADY_CONNECTED_MESSAGE_TEMPLATE


async def expired_message_case():
    """
    Кейс проверки времени жизни сообщения.
    """
    async with Client() as client1:
        await client1.connect()
        await asyncio.sleep(0.25)
        _ = await client1.read()
        await asyncio.sleep(0.25)

        await client1.send(message="Some message")
        await asyncio.sleep(0.25)

        await asyncio.sleep(3.1)

        await client1.status()
        await asyncio.sleep(0.25)
        answer = await client1.read()
        assert answer == NO_MESSAGE_TEMPLATE


async def first_connect_case():
    """
    Кейс первого запроса команды /connect, когда какие-то сообщения уже есть.
    В ответ пользователю придут сообщения в количестве,
    указанном в переменной show_last_messages_count в конфиге.
    """
    async with Client() as client1, Client() as client2:
        await client1.connect()
        await asyncio.sleep(0.25)
        _ = await client1.read()
        await asyncio.sleep(0.25)

        await client1.send(message="message 1")
        await asyncio.sleep(0.25)
        await client1.send(message="message 2")
        await asyncio.sleep(0.25)
        await client1.send(message="message 3")
        await asyncio.sleep(0.25)
        await client1.send(message="message 4")
        await asyncio.sleep(0.25)

        await client2.connect()
        await asyncio.sleep(0.25)
        answer = await client2.read()
        assert len(answer) == SHOW_LAST_MESSAGES_COUNT


async def first_connect_case_with_no_message():
    """
    Кейс первого запроса команды /connect, когда нет ни одного сообщения.
    В ответ пользователю придет сообщение "[*] No messages yet."
    """
    async with Client() as client:
        await client.connect()
        await asyncio.sleep(0.25)
        answer = await client.read()
        assert len(answer) == NO_MESSAGE_TEMPLATE


if __name__ == "__main__":
    asyncio.run(first_connect_case())
    # asyncio.run(first_connect_case_with_no_message())
    # asyncio.run(expired_message_case())
    # asyncio.run(multiple_connect_command_case())
    # asyncio.run(unconnected_case())
    # asyncio.run(message_block_case())
    # asyncio.run(report_case_with_expire_ban())
