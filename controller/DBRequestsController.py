from bson import ObjectId
from dao.MacroCollectionDaoImpl import MacroCollectionDaoImpl
from dao.MacroDaoImpl import MacroDaoImpl
from model.Macro import Macro
from model.MacroCollection import MacroCollection


class DBRequestsController():
    def __init__(self) -> None:
        self.mc_impl: MacroCollectionDaoImpl = MacroCollectionDaoImpl()
        self.m_impl: MacroDaoImpl = MacroDaoImpl()

# MACROCOLLECTIONS
    def get_macro_collection_by_id(self, _id: ObjectId) -> MacroCollection | None:
        try:
            macro_collection: MacroCollection | None = self.mc_impl.get_by_id(_id)
        except Exception as e:
            print(e)
            return None
        else:
            return macro_collection
            


    def get_all_macro_collections(self) -> list[MacroCollection] | None:
        try:
            macro_collection_list: list[MacroCollection] | None = self.mc_impl.get_all()
        except Exception as e:
            print(e)
            return None
        else:
            return macro_collection_list


    def save_macro_collection(self, obj: MacroCollection) -> bool:
        try:
            result: bool = self.mc_impl.save(obj)
        except Exception as e:
            print(e)
            return False
        else:
            return result


    def update_macro_collection(self, obj: MacroCollection) -> bool:
        try:
            result: bool = self.mc_impl.update(obj)
        except Exception as e:
            print(e)
            return False
        else:
            return result


    def delete_macro_collection(self, _id: ObjectId) -> bool:
        try:
            result: bool = self.mc_impl.delete(_id)
        except Exception as e:
            print(e)
            return False
        else:
            return result
# MACROS
    def get_macro_by_id(self, _id: ObjectId) -> Macro | None:
        try:
            macro: Macro | None = self.m_impl.get_by_id(_id)
        except Exception as e:
            print(e)
            return None
        else:
            return macro
            
    def get_all_macros(self) -> list[Macro]:
        try:
            macro_list: list[Macro] = self.m_impl.get_all()
        except Exception as e:
            print(e)
            return []
        else:
            return macro_list


    def save_macro(self, obj: Macro) -> bool:
        try:
            result: bool = self.m_impl.save(obj)
        except Exception as e:
            print(e)
            return False
        else:
            return result


    def update_macro(self, obj: Macro) -> bool:
        try:
            result: bool = self.m_impl.update(obj)
        except Exception as e:
            print(e)
            return False
        else:
            return result


    def delete_macro(self, _id: ObjectId) -> bool:
        try:
            result: bool = self.m_impl.delete(_id)
        except Exception as e:
            print(e)
            return False
        else:
            return result