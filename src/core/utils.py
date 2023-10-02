import asyncio
import functools
import logging
import typing as tp
from concurrent.futures import ThreadPoolExecutor
from logging.config import dictConfig

from config import LOGGING_CONFIG

dictConfig(LOGGING_CONFIG)
logger = logging.getLogger()


def sync_to_async(func: tp.Callable) -> tp.Callable:
    @functools.wraps(func)
    def wrapped(*args, **kwargs) -> asyncio.Future:
        loop = asyncio.get_running_loop()
        func_with_kwargs = func
        for key, val in kwargs.items():
            func_with_kwargs = functools.partial(func_with_kwargs, key=val)
        return loop.run_in_executor(ThreadPoolExecutor, func_with_kwargs, *args)

    return wrapped


class Singleton:
    __instance = None

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls, *args, **kwargs)
        return cls.__instance


class DummyStorageProtocol(tp.Protocol):
    def get_by_id(self, idx: tp.Any) -> None:
        raise NotImplementedError

    def add(self, item: tp.Any) -> None:
        raise NotImplementedError

    def bulk_add(self, items: tp.Any) -> None:
        raise NotImplementedError

    def delete(self, item: tp.Any) -> None:
        raise NotImplementedError

    def clear(self) -> None:
        raise NotImplementedError
