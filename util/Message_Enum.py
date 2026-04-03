from enum import Enum

# from message.DispatcherMessage import DispatcherMessage
# from message.AbstractUpdateMessage import AbstractUpdateMessage
# from message.ErrorMessage import ErrorMessage
# from message.ExampleMessage import ExampleMessage
# from message.MacroMessage import MacroMessage
# from message.PlayerMessage import PlayerMessage
# from message.RecorderMessage import RecorderMessage

class MessageEnum(Enum):
    CONNECTED_MESSAGE = "ConnectedMessage"
    DISCONNECTED_MESSAGE = "DisconnectedMessage"
    DISPATCHER_MESSAGE = "DispatcherMessage"
    ERROR_MESSAGE = "ErrorMessage"
    EXAMPLE_MESSAGE = "ExampleMessage"
    MACRO_MESSAGE = "MacroMessage"
    PLAYER_MESSAGE = "PlayerMessage"
    RECORDER_MESSAGE = "RecorderMessage"
    STOP_SSE_MESSAGE = "StopSSEMessage"

    # def create(self, **kwars) -> AbstractUpdateMessage:
    #     return self.value(**kwars)