from datetime import datetime
from util.Event_Enum import PlayerEvent
from dataclasses import dataclass
from typing import Any, Self, override
from message.AbstractUpdateMessage import AbstractUpdateMessage
from util.State_Enum import State

@dataclass
class PlayerMessage(AbstractUpdateMessage):
    state: State
    event:PlayerEvent
    current_step:int
    
    @override
    def jsonify(self) -> dict[str, str]:
        base_dict: dict[str, str] =  super().jsonify()
        base_dict["state"] = self.state.name
        base_dict["event"] = self.event.name
        base_dict["current_step"] = str(self.current_step)

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

            recovered_state = json_object.get("state")
            recovered_event = json_object.get("event")
            recovered_current_step = json_object.get("current_step")
    
            if recovered_state is None:
                return
            if recovered_event is None:
                return
            if recovered_current_step is None:
                return

            instance = cls(
                event_time = event_time,
                state = State[recovered_state],
                event = PlayerEvent[recovered_event],
                current_step = int(recovered_current_step)
            )
        
        except Exception:
            return

        return instance