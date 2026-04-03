from typing import Self, Any

from model.Coordinates import Coordinates
from pydantic import BaseModel

class Screen(BaseModel):

    id: int
    resolution: Coordinates
    top_left: Coordinates

    def to_dict(self) -> dict[str, int | list[int] | None]:
        return {
            "_id": self.id,
            "resolution":  [self.resolution.x, self.resolution.y],
            "top_left": [self.top_left.x, self.top_left.y]
        }

    @classmethod
    def from_mongitaDB(cls, data: Any) -> Self | None:
        # Check that data is a dict
        if not isinstance(data, dict):
            return None
        # Check all class attributes are in data keys
        # missing_attr_list: list[Any] = [
        #     attr for attr in cls.__annotations__ if attr not in data]
        # if missing_attr_list:
        #     return None

        # Declare and assign variables for data elements
        data_id: Any | None
        data_resolution: Any | None
        data_top_left: Any | None

        (
            data_id,
            data_resolution,
            data_top_left
        ) = (
            data.get("_id"),
            data.get("resolution"),
            data.get("top_left")
        )

        # Create a Screen and fill it with data elements
        screen = cls.__new__(cls)
        if not isinstance(data_id, int):
            return
        
        screen_id: int = data_id

        if (
        isinstance(data_resolution,list)
        and len(data_resolution)>0
        and all(isinstance(x,int) for x in data_resolution)
        ):
            screen_resolution: Coordinates = Coordinates(x=data_resolution[0], y=data_resolution[1])
        else:
            return

        if (
            isinstance(data_top_left, list)
            and len(data_top_left) > 0
            and all(isinstance(x, int) for x in data_top_left)
        ):
            screen_top_left = Coordinates(x=data_top_left[0], y=data_top_left[1])
            
        else:
            return

        return cls(
            id=screen_id,
            resolution=screen_resolution,
            top_left=screen_top_left
        )
