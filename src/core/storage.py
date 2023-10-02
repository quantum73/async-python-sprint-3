from config import SHOW_LAST_MESSAGES_COUNT
from core.schemas import User, Message
from core.utils import DummyStorageProtocol, Singleton


class DummyUsersStorage(DummyStorageProtocol, Singleton):
    def __init__(self):
        self._data: dict[str, User] = {}

    def __len__(self):
        return len(self._data)

    def __str__(self):
        return "<DummyUsersStorage> %s" % len(self._data)

    def __repr__(self):
        return "<DummyUsersStorage> %s" % len(self._data)

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
            writer = user.writer
            if writer is None:
                continue
            writer.close()
        self._data = {}


class DummyMessagesStorage(DummyStorageProtocol, Singleton):
    def __init__(self):
        self._data: list[Message] = []

    def __len__(self):
        return len(self._data)

    def __str__(self):
        return "<MessagesStorage> %s" % len(self._data)

    def __repr__(self):
        return "<MessagesStorage> %s" % len(self._data)

    def get_by_id(self, idx: str) -> Message | None:
        target = list(filter(lambda x: x.idx, self._data))
        if len(target) != 0:
            return target[0]

    def get_all(self, limit: int | None = SHOW_LAST_MESSAGES_COUNT) -> list[Message]:
        if limit is None:
            return self._data
        return self._data[-limit:]

    def add(self, message: Message) -> None:
        self._data.append(message)

    def bulk_add(self, messages: list[Message]) -> None:
        self._data.extend(messages)

    def delete(self, message: Message) -> None:
        self._data.remove(message)

    def clear(self) -> None:
        self._data = []


class DummyDatabase(Singleton):
    def __init__(self):
        self._users: DummyUsersStorage = DummyUsersStorage()
        self._messages: DummyMessagesStorage = DummyMessagesStorage()

    @property
    def users(self):
        return self._users

    @property
    def messages(self):
        return self._messages

    def clear(self):
        self._users.clear()
        self._messages.clear()
