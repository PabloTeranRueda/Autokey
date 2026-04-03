from abc import ABC, abstractmethod
from messenger.messenger import Messenger
from model.Macro import Macro
from model.Screen import Screen
from model.Target import Target

class Abstract_Dispatcher(ABC):
    def __init__(self,messenger:Messenger, available_screens:list[Screen]) -> None:
        self.messenger: Messenger = messenger
        self.available_screens: list[Screen] = available_screens


    @abstractmethod
    def record(self, macro:Macro) -> None:
        ...

    @abstractmethod
    def update(self, macro:Macro) -> None:
        ...
    
    @abstractmethod
    def run(self,macro:Macro,reps:int,speed:float,target:Target|None) -> None:
        ...
            
    @abstractmethod
    def toggle_pause(self,target:Target|None) -> None:
        ...

    @abstractmethod
    def stop(self,target:Target|None) -> None:
        ...

    @abstractmethod
    def connect(self,target:Target) -> None:
        ...

    @abstractmethod
    def dummy(self,screen:Screen,target:Target|None) -> None:
        ...

    @abstractmethod
    def disconnect(self,target:Target) -> bool:
        ...

    @abstractmethod
    def clean_up(self) -> None:
        ...