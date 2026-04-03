from bson.objectid import ObjectId


from typing import Self, Any
from bson import ObjectId
from pydantic import BaseModel, field_serializer, field_validator

class MacroCollection(BaseModel):
    id: ObjectId | None = None
    name:str|None = None
    macros:list[ObjectId] = []

    model_config = {
        "arbitrary_types_allowed": True  # <-- allow ObjectId
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
    
    def to_dict(self) -> dict[str, str | list[ObjectId] | None]:
        return {
            "name" : self.name,
            "macros" : self.macros
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
        data_name:Any | None
        data_macros:Any | None

        (
            data_id,
            data_name,
            data_macros_raw
        ) = (
            data.get("_id"),
            data.get("name"),
            data.get("macros")
        )

        data_macros = [ObjectId(oid=item) for item in data_macros_raw] if data_macros_raw else []
        
        macro_collection_id: ObjectId | None = data_id if isinstance(data_id,ObjectId) else None
        macro_collection_name: str | None = data_name if isinstance(data_name,str) else None

        if (
        isinstance(data_macros,list)
        and len(data_macros)>0
        and all(isinstance(x, ObjectId) for x in data_macros)
        ):
            macro_collection_macros: list[ObjectId] = data_macros
        else:
            macro_collection_macros: list[ObjectId] = []

        # Create MacroCollection instance (Pydantic-compliant)
        return cls(
            id=macro_collection_id,
            name=macro_collection_name,
            macros=macro_collection_macros
        )