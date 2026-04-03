from bson import ObjectId


from model import Macro


from mongita import Database


import sys
# setting path
sys.path.append('../util')
sys.path.append('../controller')
sys.path.append('../model')

from util import parse_ini
from controller import DBRequestsController
from util import DBConnection
from core import Recorder


bbdd: str = parse_ini()
connection: Database | None = DBConnection.get_connection(bbdd)
controller: DBRequestsController = DBRequestsController()
recorder: Recorder = Recorder()

def print_all_macros() -> list[Macro]:
    print("All Macros:")
    macros_list: list[Macro] = controller.get_all_macros()
    for i in macros_list:
        print(i._id,i.name)
    print("________\n\n")
    return macros_list

def record_new_macro(name:str) -> Macro | None:
    result: bool = False
    try:
        print("Listening...")
        macro: Macro | None = recorder.start(name)
        print("Done!")
        if macro is not None:
            result: bool = controller.save_macro(obj=macro)
        else:
            return None
    except Exception as e:
        print(e)
    
    else:
        return macro if result else None

def update_macro(macro_id: ObjectId) -> bool:
    update: bool
    result: bool = False
    
    try:
        macro_to_update: Macro | None = controller.get_macro_by_id(macro_id)
        if macro_to_update is None:
            return False
        print("Listening...")
        tmp_macro: Macro | None = recorder.start(name="update")
        print("Done!")
        if tmp_macro is None:
            return False
        macro_to_update.steps = tmp_macro.steps
        macro_to_update.screens = tmp_macro.screens
        result: bool = controller.update_macro(obj=macro_to_update)
    except Exception as e:
        print(e)

    
    return result

def delete_macro(_id:ObjectId) -> bool:
    try:
        result: bool = controller.delete_macro(_id=_id)
    except Exception as e:
        print(e)
        return False
    else:
        return result

if __name__ == "__main__":
    # Player:104. Do not delete macro 0, since we can replicate the bug with it
    # for i in controller.get_all_macros()[1:]:
    #     controller.delete_macro(id=i._id)
    print_all_macros()
    new_macro: Macro | None = record_new_macro(name="test8")
    print_all_macros()
    # last_macro: Macro = controller.get_all_macros()[-1]
    # update_macro(macro_id=last_macro.id)
    # print_all_macros()
    # delete_macro(_id=last_macro.id)
    # print_all_macros()

