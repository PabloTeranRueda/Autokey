from mongita.cursor import Cursor
from mongita.database import Database
from mongita.collection import Collection, InsertOneResult, UpdateResult
from mongita.results import DeleteResult
from dao.GenericDaoInterface import GenericDAO
from model.MacroCollection import MacroCollection
from util.DBConnection import DBConnection
from typing import Any, override
from bson import ObjectId

class MacroCollectionDaoImpl(GenericDAO[MacroCollection]):
    def __init__(self) -> None:
        self._connection: Database | None = DBConnection.get_connection()
        self._collection: Collection | None= self._connection["macroCollections"] if self._connection else None
    
    @override
    def get_by_id(self, _id:ObjectId) -> MacroCollection | None:
        if self._collection is None:
            return None

        document: Any | None = self._collection.find_one(filter={"_id": _id})

        macroCollection: MacroCollection | None = MacroCollection.from_mongitaDB(data=document)

        return macroCollection
    
    @override
    def get_all(self) -> list[MacroCollection]:
        macroCollection_list: list[MacroCollection] = []

        if self._collection is None:
            return []
        
        try:
            with self._collection.find() as cursor:
                if cursor is None:
                    return []
                elif isinstance(cursor,Cursor):
                    for document in cursor:
                        macroCollection:MacroCollection | None = MacroCollection.from_mongitaDB(data=document)
                        if macroCollection is not None:
                            macroCollection_list.append(macroCollection)
                else:
                    return []

        except TypeError:
            return []
        
        else:
            return macroCollection_list
    
    @override
    def save(self, obj: MacroCollection) -> bool:
        """
        Saves a MacroCollection in the BBDD. True = successful, False = unsuccessful
        """
        if not isinstance(obj,MacroCollection) or not isinstance(obj.id,ObjectId):
            return False

        result: InsertOneResult = self._collection.insert_one(document=obj.to_dict())
        
        return result.acknowledged

    
    @override
    def update(self, obj: MacroCollection) -> bool:
        """
        Updates a MacroCollection in the BBDD. True = successful, False = unsuccessful
        """
        if not isinstance(obj,MacroCollection) or not isinstance(obj.id,ObjectId):
            return False

        result: UpdateResult = self._collection.replace_one(filter={"_id":obj.id},replacement=obj.to_dict())
        
        return result.acknowledged
    
    @override
    def delete(self, _id: ObjectId) -> bool:
        """
        Deletes a MacroCollection in the BBDD. True = successful, False = unsuccessful
        """
        if not isinstance(_id,ObjectId):
            return False

        result: DeleteResult =self._collection.delete_one(filter={"_id" : _id})
        
        return result.acknowledged