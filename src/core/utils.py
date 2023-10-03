import logging
import typing as tp
from datetime import datetime, timedelta
from logging.config import dictConfig

from config import LOGGING_CONFIG

__all__ = ("DummyStorageProtocol", "Singleton", "get_now_with_delta")

dictConfig(LOGGING_CONFIG)
logger = logging.getLogger()


def get_now_with_delta(seconds: int) -> datetime:
    return datetime.now() + timedelta(seconds=seconds)


class Singleton:
    __instance = None

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls, *args, **kwargs)
        return cls.__instance


class DummyStorageProtocol(tp.Protocol):
    def get_by_id(self, idx: tp.Any) -> tp.Any:
        raise NotImplementedError

    def add(self, item: tp.Any) -> None:
        raise NotImplementedError

    def bulk_add(self, items: tp.Any) -> None:
        raise NotImplementedError

    def delete(self, item: tp.Any) -> None:
        raise NotImplementedError

    def clear(self) -> None:
        raise NotImplementedError
