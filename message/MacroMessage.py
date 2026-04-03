from dataclasses import dataclass
import json
from typing import Any, Self, override
from message.AbstractUpdateMessage import AbstractUpdateMessage
from model.Macro import Macro
from util.Event_Enum import MacroEvent
from datetime import timedelta, datetime
from decimal import Decimal

@dataclass
class MacroMessage(AbstractUpdateMessage):
    macro:Macro|None
    event:MacroEvent

    @override
    def jsonify(self) -> dict[str, str]:
        base_dict: dict[str, str] =  super().jsonify()
        base_dict["event"] = self.event.name
        if isinstance(self.macro,Macro):
            base_dict["macro"] = json.dumps(self.macro.model_dump(),default=self._json_encoder)
        else:
            base_dict["macro"] = json.dumps("")

        return base_dict

    def _json_encoder(self, obj: Any) -> float | str | list[Any]:
        if isinstance(obj, timedelta):
            return obj.total_seconds()
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, tuple):
            return list[Any](obj)

        return obj

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

            recovered_macro = json_object.get("macro")
            recovered_event = json_object.get("event")

            if recovered_macro is None:
                return
            if recovered_event is None:
                return

            tmp_macro =  json.loads(recovered_macro)
            macro_dict = _convert_timedelta_fields(tmp_macro)

            instance = cls(
                event_time = event_time,
                event=MacroEvent[recovered_event],
                macro = Macro.model_validate(macro_dict)
            )

        except Exception as e:
            print(e)
            return
            
        return instance

def _convert_timedelta_fields(obj: Any) -> Any:

    if isinstance(obj, dict):
        return {k: (_convert_timedelta_fields(v) if not k.endswith("_time") else timedelta(seconds=v))
                for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_convert_timedelta_fields(v) for v in obj]
    else:
        return obj