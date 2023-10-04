import typing as tp
import uuid
from asyncio import StreamWriter, StreamReader
from dataclasses import dataclass, field
from datetime import datetime

from config import DATE_FORMAT, USER_MESSAGE_LIMIT

__all__ = ("User", "Message", "Command", "Route")


def _set_idx() -> str:
    return str(uuid.uuid4())


def _now_datetime() -> datetime:
    return datetime.now()


@dataclass(frozen=True, slots=True, order=False, eq=False)
class Route:
    name: str
    handler: tp.Callable


@dataclass(slots=True)
class Command:
    request: bytes = field(repr=False)
    name: str = field(init=False)
    arguments: tp.Sequence[tp.Any] = field(init=False, repr=False)

    def __post_init__(self):
        self.name, self.arguments = self.parse_request(raw_request=self.request)

    def arguments_to_string(self) -> str:
        return " ".join(self.arguments)

    @staticmethod
    def parse_request(raw_request: bytes) -> tuple[str, list[str]]:
        decode_request = raw_request.decode()
        strip_request = decode_request.strip()
        request_elements = list(filter(lambda x: x.strip(), strip_request.split()))
        if len(request_elements) > 1:
            command_name, *command_args = request_elements
        else:
            command_name, command_args = request_elements[0], []

        return command_name, command_args


@dataclass(slots=True)
class User:
    idx: str
    host: str
    port: int
    reader: StreamReader
    writer: StreamWriter

    is_connected: bool = field(init=False, default=False)

    reports_count: int = 0
    is_banned: bool = field(init=False, default=False)
    banned_to: datetime | None = field(init=False, default=None)

    message_limit: int = USER_MESSAGE_LIMIT
    is_chating_blocked: bool = field(init=False, default=False)
    chating_blocked_to: datetime | None = field(init=False, default=None)

    last_status_request_at: datetime | None = field(init=False, default=None)

    def _object_as_string(self) -> str:
        return "User[%s]" % self.idx

    def __str__(self) -> str:
        return self._object_as_string()

    def __repr__(self) -> str:
        return self._object_as_string()

    async def disconnect(self) -> None:
        if not self.writer.is_closing():
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
    created_at_as_string: str = field(init=False)

    def __post_init__(self):
        self.created_at_as_string = self.created_at.strftime(DATE_FORMAT)

    def _object_as_string(self) -> str:
        return "[%s] <%s> %s" % (self.created_at_as_string, self.sender, self.content)

    def __str__(self) -> str:
        return self._object_as_string()

    def __repr__(self) -> str:
        return self._object_as_string()

    def to_dict(self) -> dict:
        return {
            "id": self.idx,
            "sender": self.sender.to_dict(),
            "content": self.content,
            "created_at": self.created_at_as_string,
        }
