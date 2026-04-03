from dataclasses import dataclass
from datetime import datetime
from util.Event_Enum import ExampleEvent
from pydoc import text
from typing import Any, Self, override
from message.AbstractUpdateMessage import AbstractUpdateMessage

@dataclass
class ExampleMessage(AbstractUpdateMessage):
    text : str
    event:ExampleEvent    

    @override
    def jsonify(self) -> dict[str, str]:
        base_dict: dict[str, str] =  super().jsonify()
        base_dict["event"] = self.event.name
        base_dict["text"] = self.text
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

            recovered_text = json_object.get("text")
            recovered_event = json_object.get("event")
            if recovered_text is None:
                return
            if recovered_event is None:
                return

            instance = cls(
                event_time = event_time,
                text = str(recovered_text),
                event=ExampleEvent[recovered_event]
            )
            
        except Exception:
            return
        return instance
        