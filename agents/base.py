from abc import ABC, abstractmethod
from datetime import datetime


class Agent(ABC):
    name: str

    def __init__(self, name: str):
        self.name = name
        self._log: list[dict] = []

    @abstractmethod
    def run(self, context: dict) -> dict: ...

    def log(self, msg: str, level: str = "info") -> None:
        self._log.append({
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "agent": self.name,
            "level": level,
            "message": msg,
        })

    @property
    def log_entries(self) -> list[dict]:
        return list(self._log)
