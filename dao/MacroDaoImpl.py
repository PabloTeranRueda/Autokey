from typing import Any, override
from mongita.cursor import Cursor
from mongita.database import Database
from mongita.collection import Collection, InsertOneResult, UpdateResult
from mongita.results import DeleteResult
from bson import ObjectId
from model.Macro import Macro
from util.DBConnection import DBConnection
from dao.GenericDaoInterface import GenericDAO


class MacroDaoImpl(GenericDAO[Macro]):
    def __init__(self) -> None:
        self._connection: Database | None = DBConnection.get_connection()
        self._collection: Collection | None= self._connection["macros"] if self._connection else None
    
    @override
    def get_by_id(self, _id:ObjectId) -> Macro | None:
        if self._collection is None:
            return None
        elif not isinstance(_id,ObjectId):
            return None

        document: Any | None = self._collection.find_one(filter={"_id": _id})

        macro: Macro | None = Macro.from_mongitaDB(data=document)

        return macro
    
    @override
    def get_all(self) -> list[Macro]:
        macro_list: list[Macro] = []

        if self._collection is None:
            return []
        
        try:
            cursor: Cursor = self._collection.find()
            for document in cursor:
                macro:Macro | None = Macro.from_mongitaDB(data=document)
                if macro is not None:
                    macro_list.append(macro)
                else:
                    return []

        except TypeError as e:
            print(e)
            return []
        
        else:
            return macro_list
    
    @override
    def save(self, obj: Macro) -> bool:
        """
        Saves a Macro in the BBDD. True = successful, False = unsuccessful
        """
        if not isinstance(obj,Macro):
            return False

        result: InsertOneResult = self._collection.insert_one(document=obj.to_dict())
        
        return result.acknowledged

    
    @override
    def update(self, obj: Macro) -> bool:
        """
        Updates a Macro in the BBDD. True = successful, False = unsuccessful
        """
        if not isinstance(obj,Macro):
            return False

        result: UpdateResult = self._collection.replace_one(filter={"_id":obj.id},replacement=obj.to_dict())
        
        return result.acknowledged
    
    @override
    def delete(self, _id: ObjectId) -> bool:
        """
        Deletes a Macro in the BBDD. True = successful, False = unsuccessful
        """
        if not isinstance(_id,ObjectId):
            return False

        result: DeleteResult =self._collection.delete_one(filter={"_id" : _id})
        
        return result.acknowledged