import builtins
from dataclasses import dataclass
from datetime import datetime
import json
from typing import Any, Self, override
from message.AbstractUpdateMessage import AbstractUpdateMessage


@dataclass
class ErrorMessage(AbstractUpdateMessage):
    error:str


    @override
    def jsonify(self) -> dict[str, str]:
        base_dict: dict[str, str] =  super().jsonify()
        base_dict["error"] = self.error

        return base_dict

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

            recovered_error_message = json_object.get("error_message")
            
            if recovered_error_message is None:
                return
        
            instance = cls(
                event_time = event_time,
                error= recovered_error_message
            )

        except Exception:
            return
            
        return instance