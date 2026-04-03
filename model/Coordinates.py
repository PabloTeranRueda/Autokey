
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel


# @dataclass
class Coordinates(BaseModel):
    x:int
    y:int

    def to_json(self) -> dict[str,Any]:
        return{"x":self.x,"y":self.y}

    def from_json(self,json:dict[str,Any]) -> bool:
        if json["x"] is None:
            return False
        if json["y"] is None:
            return False
        
        self.x = int(json["x"])
        self.y = int(json["y"])

        return True