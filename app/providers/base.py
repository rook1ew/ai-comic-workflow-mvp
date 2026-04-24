from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from pydantic import BaseModel

RequestT = TypeVar("RequestT", bound=BaseModel)
ResponseT = TypeVar("ResponseT", bound=BaseModel)


class ProviderExecutionError(Exception):
    """Raised when a provider cannot complete a generation task."""


class BaseProvider(ABC, Generic[RequestT, ResponseT]):
    name: str

    @abstractmethod
    def generate(self, payload: RequestT) -> ResponseT:
        raise NotImplementedError
