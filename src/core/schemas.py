import typing as tp
import uuid
from asyncio import StreamWriter, StreamReader
from dataclasses import dataclass, field
from datetime import datetime

from config import DATE_FORMAT, USER_MESSAGE_LIMIT

__all__ = ("User", "Message", "Command")


def _set_idx() -> str:
    return str(uuid.uuid4())


def _now_datetime() -> datetime:
    return datetime.now()


@dataclass(slots=True, frozen=True)
class Command:
    name: str
    request: str
    arguments: tp.Sequence[tp.Any] = field(default_factory=tuple)


@dataclass(slots=True)
class User:
    idx: str
    host: str
    port: int
    reader: StreamReader
    writer: StreamWriter

    reports_count: int = 0
    is_banned: bool = field(init=False, default=False)
    banned_to: datetime | None = field(init=False, default=None)

    message_limit: int = USER_MESSAGE_LIMIT
    is_chating_blocked: bool = field(init=False, default=False)
    chating_blocked_to: datetime | None = field(init=False, default=None)

    last_exit: datetime | None = field(init=False, default=None)

    def _object_as_string(self) -> str:
        return "User[<%s> (%s:%s)]" % (self.idx, self.host, self.port)

    def __str__(self) -> str:
        return self._object_as_string()

    def __repr__(self) -> str:
        return self._object_as_string()

    async def disconnect(self) -> None:
        self.last_exit = datetime.now()
        self.writer.close()

    def to_dict(self) -> tp.Mapping:
        data = {
            "id": self.idx,
            "host": self.host,
            "port": self.port,
        }
        return data


@dataclass(slots=True)
class Message:
    idx: str = field(init=False, default_factory=_set_idx)
    sender: User
    content: str
    created_at: datetime = field(init=False, default_factory=_now_datetime)

    def _object_as_string(self) -> str:
        return "<%s>[%s] %s" % (str(self.sender), self.created_at.strftime(DATE_FORMAT), self.content)

    def __str__(self) -> str:
        return self._object_as_string()

    def __repr__(self) -> str:
        return self._object_as_string()

    def to_dict(self) -> dict:
        return {
            "id": self.idx,
            "sender": self.sender.to_dict(),
            "content": self.content,
            "created_at": self.created_at.strftime(DATE_FORMAT),
        }
