from PySide6.QtCore import QObject, Signal, Slot
from message.AbstractUpdateMessage import AbstractUpdateMessage
import queue

from message.RemoteMessage import RemoteMessage

class Messenger(QObject):

    signal = Signal(object)

    def __init__(self) -> None:
        super().__init__()
        self.master:queue.SimpleQueue[AbstractUpdateMessage|None]|None = None

    def send_event(self, event:AbstractUpdateMessage|RemoteMessage) -> None:
        self.signal.emit(event)
        # if self.master is not None:
        if self.master is not None and not isinstance(event,RemoteMessage):
            self.master.put(item=event)


    @Slot(object)
    def recibir_valor(self, event:AbstractUpdateMessage|RemoteMessage) -> None:
        print(f"Recibido valor: {event}")
