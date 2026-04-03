from bson import ObjectId
from model import Macro


from mongita import Database


import sys
# setting path
sys.path.append('../util')
sys.path.append('../controller')
sys.path.append('../model')

from util.parse_ini import parse_ini
from controller import DBRequestsController
from util.DBConnection import DBConnection
from core import Player

if __name__ == "__main__":
    bbdd: str = parse_ini()
    connection: Database | None = DBConnection.get_connection(db=bbdd)
    controller: DBRequestsController = DBRequestsController()

    player: Player = Player()
    macros: list[Macro] = controller.get_all_macros()
    # macro: Macro | None = controller.get_macro_by_id(ObjectId("69b597af58d5fbe74cfd3155"))
    macro: Macro = macros[-1]
    if macro is not None:
        player.start(macro=macro)
    print("Done")