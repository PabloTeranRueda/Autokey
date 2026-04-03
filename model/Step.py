from datetime import datetime, timedelta
from typing import Any, Self

from pydantic import BaseModel


class Step(BaseModel):
    id: int | None = None
    type:str|None = None
    key:str|None = None
    coordinate:tuple[int,int]|None = None
    key_press_time:timedelta|None = None
    key_release_time:timedelta|None = None
    screen_number:int|None = None

    @property
    def key_duration(self) -> float|None:
        if self.key_press_time and self.key_release_time:
            return (self.key_release_time - self.key_press_time).total_seconds()
        return None

    
    def to_dict(self) -> dict[str, int | str | list[int] | float | None]:
        return {
            "_id" : self.id,
            "type" : self.type,
            "key" : self.key,
            "coordinate" : list[int](self.coordinate) if self.coordinate is not None else None,
            "key_press_time" : self.key_press_time.total_seconds() if self.key_press_time is not None else None,
            "key_release_time" : self.key_release_time.total_seconds() if self.key_release_time is not None else None,
            "screen_number" : self.screen_number
        }

    @classmethod
    def from_mongitaDB(cls, data:Any) -> Self|None:
        # Check that data is a dict
        if not isinstance(data,dict):
            return None
        # Check all class attributes are in data keys 
        # missing_attr_list: list[Any] = [attr for attr in cls.__annotations__ if attr not in data]
        # if missing_attr_list:
        #     return None

        # Declare and assign variables for data elements
        data_id:Any | None
        data_type:Any | None
        data_key:Any | None
        data_coordinate:Any | None
        data_key_press_time:Any | None
        data_key_release_time:Any | None
        data_screen_number:Any | None

        (
            data_id,
            data_type,
            data_key,
            data_coordinate,
            data_key_press_time,
            data_key_release_time,
            data_screen_number
        ) = (
            data.get("_id"),
            data.get("type"),
            data.get("key"),
            data.get("coordinate"),
            data.get("key_press_time"),
            data.get("key_release_time"),
            data.get("screen_number")
        )

        step_id: int | None = data_id if isinstance(data_id,int) else None
        step_type: str | None = data_type if isinstance(data_type,str) else None
        step_key: str | None = data_key if isinstance(data_key,str) else None

        step_coordinate: tuple[int, int]|None
        if (
        isinstance(data_coordinate,list)
        and len(data_coordinate)>0
        and all(isinstance(x,int) for x in data_coordinate)
        ):
            step_coordinate = tuple[int, int](data_coordinate)
        else:
            step_coordinate = None

        step_key_press_time: timedelta | None = timedelta(seconds=data_key_press_time) if isinstance(data_key_press_time,float) else None
        step_key_release_time: timedelta | None = timedelta(seconds=data_key_release_time) if isinstance(data_key_release_time,float) else None

        step_screen_number: int | None = data_screen_number if isinstance(data_screen_number,int) else None

        # Create Step instance
        return cls(
            id=step_id,
            type=step_type,
            key=step_key,
            coordinate=step_coordinate,
            key_press_time=step_key_press_time,
            key_release_time=step_key_release_time,
            screen_number=step_screen_number
        )

