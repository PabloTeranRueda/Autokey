from datetime import datetime
from util.Event_Enum import RecorderEvent
from dataclasses import dataclass
from typing import Any, Self, override
from message.AbstractUpdateMessage import AbstractUpdateMessage
from util.State_Enum import State

@dataclass
class StopSSEMessage(AbstractUpdateMessage):
    
    @override
    def jsonify(self) -> dict[str, str]:
        return  super().jsonify()

    @classmethod
    def from_json(cls,json_object:dict[str,Any]) -> Self|None:
        try:

            received_event_time = json_object.get("event_time")
            if received_event_time is None:
                return
            
            try:
                event_time: datetime = datetime.fromisoformat(received_event_time)
            except ValueError:
                return
           
            instance = cls(
                event_time = event_time,
            )
        except Exception:
            return
            
        return instance