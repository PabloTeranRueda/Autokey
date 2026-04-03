from dataclasses import dataclass
from datetime import datetime
from typing import Any, Self, override

from message.AbstractUpdateMessage import AbstractUpdateMessage


@dataclass
class ConnectedMessage(AbstractUpdateMessage):
    slave_id:str
    
    @override
    def jsonify(self) -> dict[str, str]:
        base_dict: dict[str, str] =  super().jsonify()
        base_dict["slave_id"] = str(self.slave_id)
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
                
            slave_id: Any | None = json_object.get("slave_id")
            if slave_id is None:
                return

            instance = cls(
                event_time = event_time,
                slave_id=slave_id
            )

        except Exception:
            return
            
        return instance