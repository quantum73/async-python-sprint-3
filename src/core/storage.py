from datetime import datetime

from config import SHOW_LAST_MESSAGES_COUNT
from core.schemas import User, Message
from core.utils import DummyStorageProtocol, Singleton

__all__ = ("DummyDatabase",)


class DummyUsersStorage(DummyStorageProtocol, Singleton):
    def __init__(self) -> None:
        self._data: dict[str, User] = {}

    def __len__(self) -> int:
        return len(self._data)

    def _object_as_string(self) -> str:
        return "<DummyUsersStorage> %s" % len(self._data)

    def __str__(self) -> str:
        return self._object_as_string()

    def __repr__(self) -> str:
        return self._object_as_string()

    def get_by_id(self, idx: str) -> User | None:
        return self._data.get(idx)

    def add(self, user: User) -> None:
        self._data[user.idx] = user

    def bulk_add(self, users: list[User]) -> None:
        for user in users:
            self._data[user.idx] = user

    def delete(self, idx: str) -> None:
        if idx in self._data:
            del self._data[idx]

    def clear(self) -> None:
        for user in self._data.values():
            user.writer.close()
        self._data = {}


class DummyMessagesStorage(DummyStorageProtocol, Singleton):
    def __init__(self) -> None:
        self._data: list[Message] = []

    def __len__(self) -> int:
        return len(self._data)

    def __str__(self) -> str:
        return "<MessagesStorage> %s" % len(self._data)

    def __repr__(self) -> str:
        return "<MessagesStorage> %s" % len(self._data)

    def get_by_id(self, idx: str) -> Message | None:
        for message in self._data:
            if idx == message.idx:
                return message
        return None

    def get_all(self, limit: int | None = SHOW_LAST_MESSAGES_COUNT) -> list[Message]:
        if limit is None:
            return self._data
        return self._data[-limit:]

    def get_all_from_date(self, date_filter: datetime) -> list[Message]:
        messages = list(filter(lambda x: x.created_at > date_filter, self._data))
        return messages

    def add(self, message: Message) -> None:
        self._data.append(message)

    def bulk_add(self, messages: list[Message]) -> None:
        self._data.extend(messages)

    def delete(self, message: Message) -> None:
        self._data.remove(message)

    def bulk_delete(self, messages: list[Message]) -> None:
        for message in messages:
            self._data.remove(message)

    def clear(self) -> None:
        self._data = []


class DummyDatabase(Singleton):
    def __init__(self) -> None:
        self._users: DummyUsersStorage = DummyUsersStorage()
        self._messages: DummyMessagesStorage = DummyMessagesStorage()

    @property
    def users(self) -> DummyUsersStorage:
        return self._users

    @property
    def messages(self) -> DummyMessagesStorage:
        return self._messages

    def clear(self) -> None:
        self._users.clear()
        self._messages.clear()
