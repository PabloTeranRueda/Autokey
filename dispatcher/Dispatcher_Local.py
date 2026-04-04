from abc import ABC
from message.MacroMessage import MacroMessage
from model.Screen import Screen
from model.Macro import Macro
from messenger.messenger import Messenger
from typing import override
from dispatcher.Abstract_Dispatcher import Abstract_Dispatcher
from core.Recorder import Recorder
from core.Player import Player
from datetime import datetime
from util.Target import Target
from util.State_Enum import State
from util.Event_Enum import DispatcherEvent, MacroEvent
from message.DispatcherMessage import DispatcherMessage

class Dispatcher_Local(Abstract_Dispatcher,ABC):
    def __init__(self, messenger:Messenger, available_screens:list[Screen]) -> None:
        super().__init__(messenger, available_screens) 

        self.recorder: Recorder = Recorder(messenger=messenger,available_screens=available_screens)
        self.player: Player = Player(messenger=messenger,available_screens=available_screens)


    @override
    def run(self,macro:Macro,reps:int,speed:float,target:Target|None=None) -> None:
        self.player.start(macro=macro,speed=speed,reps=reps)
        self.messenger.send_event(event=DispatcherMessage(event_time=datetime.now(),event=DispatcherEvent.ON_RUN))
        self.messenger.send_event(event=MacroMessage(event_time=datetime.now(),event=MacroEvent.STARTED,macro=macro))


    
    @override
    def record(self, macro:Macro) -> None:
        macro: Macro | None = self.recorder.start(provided_macro=macro)
        self.messenger.send_event(event=DispatcherMessage(event_time=datetime.now(),event=DispatcherEvent.ON_CREATE))

    def update(self, macro:Macro) -> None:
        macro: Macro | None = self.recorder.start(provided_macro=macro)
        self.messenger.send_event(event=DispatcherMessage(event_time=datetime.now(),event=DispatcherEvent.ON_UPDATE))

    @override
    def connect(self, target: Target) -> None:
        return

    @override
    def disconnect(self,target:Target) -> bool:
        return False

    @override
    def dummy(self,screen:Screen, target: Target|None) -> None:
        return

    @override    
    def toggle_pause(self, target:Target|None = None) -> None:
        #toogle_play()
        if self.recorder.estado != State.OFF:
            self.recorder.toggle_play()
        if self.player.estado != State.OFF:
            self.player.toggle_play()
    
    @override
    def stop(self, target:Target|None = None) -> None:
        # stop()
        if self.recorder.estado != State.OFF:
            self.recorder.stop()
        
        if self.player.estado != State.OFF:
            self.player.stop()

        
    @override
    def clean_up(self) -> None:
        self.stop()


    
