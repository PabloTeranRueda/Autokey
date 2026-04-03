from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class AbstractUpdateMessage(ABC):
    event_time:datetime

    @property
    def event_type(self) -> str:
        return self.__class__.__name__
    
    def _base_json(self) -> dict[str,str]:
        return{
            "event_type": self.event_type,
            "event_time": self.event_time.isoformat(timespec='minutes'),
        }

    @abstractmethod
    def jsonify(self) -> dict[str,str]:
        return self._base_json()

    # @abstractmethod
    # def from_json(self,json_object:dict[str,Any]) -> bool:
    #     received_event_time = json_object.get("event_time")
    #     if received_event_time is None:
    #         return False
        
    #     try:
    #         self.event_time = datetime.fromisoformat(received_event_time)
    #     except ValueError:
    #         return False
        
    #     return True