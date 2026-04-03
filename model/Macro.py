from bson.objectid import ObjectId


from pydantic import BaseModel, Field, field_serializer, field_validator
from pynput.keyboard._base import Key
from typing import Any, Self
from model.Step import Step
from model.Screen import Screen
from bson import ObjectId


class Macro(BaseModel):
    id: ObjectId | None = None
    name: str | None = None
    steps: list[Step] = []
    screens: list[Screen] = []

    model_config = {
        "arbitrary_types_allowed": True  # allow ObjectId
    }

    @field_serializer("id")
    def serialize_objectid(self, value: ObjectId) -> str:
        return str(value)

    @field_validator("id",mode="before")
    @classmethod
    def validate_id(cls, value:Any) -> ObjectId|None:
        if value is None:
            return None
        if isinstance(value, ObjectId):
            return value
        return ObjectId(value)


    def to_dict(self) -> dict[str, str | list[dict[str, int | str | list[int] | float | None]] | None | list[dict[str, int | list[int] | None]] | None]:

        return {
            "name": self.name,
            "steps": [step.to_dict() for step in self.steps] if self.steps else None,
            "screens": [screen.to_dict() for screen in self.screens] if self.screens else None
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
        data_name: Any | None
        data_steps: Any | None
        data_screens: Any | None

        (
            data_id,
            data_name,
            data_steps_raw,
            data_screens_raw
        ) = (
            data.get("_id"),
            data.get("name"),
            data.get("steps"),
            data.get("screens")
        )

        # Convert steps and screen items into objects
        data_steps = [Step.from_mongitaDB(
            data=item) for item in data_steps_raw] if data_steps_raw else []
        data_screens = [Screen.from_mongitaDB(
            data=item) for item in data_screens_raw] if data_screens_raw else []


        macro_id: ObjectId | None = data_id if isinstance(data_id, ObjectId) else None
        macro_name: str | None = data_name if isinstance(data_name, str) else None

        if (
            isinstance(data_steps, list)
            and len(data_steps) > 0
            and all(isinstance(x, Step) for x in data_steps)
        ):
            macro_steps: list[Step] = data_steps
        else:
            macro_steps: list[Step] = []

        if (
            isinstance(data_screens, list)
            and len(data_screens) > 0
            and all(isinstance(x, Screen) for x in data_screens)
        ):
            macro_screens: list[Screen] = data_screens
        else:
            macro_screens: list[Screen] = []


        return cls(
            id=macro_id,
            name=macro_name,
            steps=macro_steps,
            screens=macro_screens
        )

    def find_screen_by_coordinates(self, x: int, y: int) -> Screen | None:
        if self.screens is None:
            return None

        for screen in self.screens:
            if screen.top_left is None or screen.resolution is None:
                continue

            top_left_x, top_left_y = screen.top_left.x, screen.top_left.y
            monitor_width, monitor_height = screen.resolution.x, screen.resolution.y

            if (top_left_x <= x < (top_left_x + monitor_width)
                ) and (
                    top_left_y <= y < (top_left_y + monitor_height)):
                return screen

        return None
