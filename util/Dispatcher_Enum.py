from enum import Enum
from dispatcher.Abstract_Dispatcher import Abstract_Dispatcher
from dispatcher.Dispatcher_Local import Dispatcher_Local
from dispatcher.Dispatcher_Master import Dispatcher_Master
from dispatcher.Dispatcher_Slave import Dispatcher_Slave

from messenger.messenger import Messenger
from model.Screen import Screen

class Dispatcher(Enum):
    Local = Dispatcher_Local
    Master = Dispatcher_Master
    Slave = Dispatcher_Slave