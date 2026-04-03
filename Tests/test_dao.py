from util.parse_ini import parse_ini
from controller.DBRequestsController import DBRequestsController
from util.DBConnection import DBConnection

bbdd = parse_ini()
connection = DBConnection.get_connection(bbdd)
controller = DBRequestsController()