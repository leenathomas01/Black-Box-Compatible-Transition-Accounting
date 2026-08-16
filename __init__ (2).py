"""
Minimal model backend interface.

Everything in the experiment only needs one method:
    backend.generate(system: str, messages: list[dict]) -> str

messages: [{"role": "user"|"assistant", "content": "..."}]
Returns the raw text of the model's reply.
"""
from abc import ABC, abstractmethod


class Backend(ABC):
    @abstractmethod
    def generate(self, system: str, messages: list) -> str:
        ...
