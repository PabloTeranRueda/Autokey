from datetime import datetime, timedelta
from pynput.keyboard._base import Key, KeyCode
from pynput import keyboard, mouse
from message.MacroMessage import MacroMessage
from messenger.messenger import Messenger
from model.Macro import Macro
from model.Step import Step
from model.Screen import Screen
from util.State_Enum import State
from util.Event_Enum import MacroEvent, RecorderEvent
from message.RecorderMessage import RecorderMessage
from message.ErrorMessage import ErrorMessage


class Recorder():
    def __init__(self, messenger: Messenger, available_screens: list[Screen]) -> None:
        self.estado: State = State.OFF

        self.mouse_listener: mouse.Listener | None = None
        self.keyboard_listener: keyboard.Listener | None = None
        self.steps_on_flight_key: dict[str, Step] = {}
        self.steps_on_flight_mouse: dict[str, Step] = {}
        
        self.macro_start:datetime = datetime.now()
        self.pause_start:datetime =  datetime.now()
        self.pause_drift:timedelta = timedelta(0)
        
        self.macro: Macro = Macro()
        self.shift_is_pressed: bool = False

        self.messenger: Messenger = messenger
        self.available_screens: list[Screen] = available_screens

    def start(self, provided_macro: Macro) -> None:
        if (self.estado != State.OFF):
            self.messenger.send_event(ErrorMessage(event_time=datetime.now(
            ), error=str("Recorder was already recording")))
            return

        self.estado = State.ON

        self.steps_on_flight_key = {}
        self.steps_on_flight_mouse = {}
        self.pause_drift = timedelta(0)
        self.macro = provided_macro
        self.macro_start = datetime.now()
        self.shift_is_pressed = False

        

        self.mouse_listener = mouse.Listener(on_move=self.on_move,
                                             on_click=self.on_click,
                                             on_scroll=self.on_scroll,)
        self.keyboard_listener = keyboard.Listener(on_press=self.on_press,
                                                   on_release=self.on_release)

        self.macro.screens = self.available_screens

        self.keyboard_listener.start()
        self.mouse_listener.start()

        self.messenger.send_event(
            event=RecorderMessage(event=RecorderEvent.STARTED, state=self.estado, event_time=datetime.now()))

    def toggle_play(self) -> None:
        if self.estado == State.PAUSED:
            self.pause_drift = self.pause_drift + (datetime.now()-self.pause_start)
            self.estado = State.ON
        elif self.estado == State.ON:
            self.pause_start = datetime.now()
            self.estado = State.PAUSED
            _ = self.steps_on_flight_key.pop(keyboard.Key.shift.name, None)

        self.messenger.send_event(
            event=RecorderMessage(event=RecorderEvent.TOGGLED_PAUSE, state=self.estado, event_time=datetime.now()))

    def stop(self) -> None:
        if self.estado == State.OFF:
            return
        self.estado = State.OFF

        if self.keyboard_listener is None or self.mouse_listener is None:
            return

        self.keyboard_listener.stop()
        self.mouse_listener.stop()
        
        self.macro.steps.sort(key=lambda s: s.key_press_time or datetime.min)
        
        for index, step in enumerate(self.macro.steps):
            step.id = index

        self.messenger.send_event(event=MacroMessage(event=MacroEvent.CREATED, event_time=datetime.now(),macro=self.macro))
        self.messenger.send_event(event=RecorderMessage(event=RecorderEvent.STOPPED, state=self.estado, event_time=datetime.now()))

    def on_move(self, x: int, y: int) -> None:
        if self.estado == State.PAUSED:
            return
        
        screen: Screen | None = self.macro.find_screen_by_coordinates(x, y)
        if(screen is None):
            return

        step: Step = Step()
        step.type = "movement"
        step.coordinate = (x, y)
        step.key_press_time = self.get_corrected_now()
        step.key_release_time = step.key_press_time
        step.screen_number = screen.id
        self.macro.steps.append(step)

    def on_click(self, x: int, y: int, button: mouse.Button, pressed: bool) -> None:
        if self.estado == State.PAUSED:
            if (not pressed and button.name == 'left'):
                past_click = self.steps_on_flight_mouse.get(button.name)
                if(past_click is not None and past_click.type == "click"):
                    _ = self.steps_on_flight_mouse.pop(button.name, None)
            return

        if pressed:
            screen: Screen | None = self.macro.find_screen_by_coordinates(x, y)
            if(screen is None):
                return
            
            if(button.name not in self.steps_on_flight_mouse):
                self.steps_on_flight_mouse[button.name] = Step()
            current_click = self.steps_on_flight_mouse[button.name]
            current_click.type = "click"
            current_click.key = button.name
            current_click.coordinate = (x-screen.top_left.x,y-screen.top_left.y)
            current_click.key_press_time = self.get_corrected_now()
            current_click.screen_number = screen.id
        else:
            past_click = self.steps_on_flight_mouse.get(button.name)
            if(past_click is None):
                return
            
            past_click.key_release_time = self.get_corrected_now()
            _ = self.steps_on_flight_mouse.pop(button.name, None)
            
            self.macro.steps.append(past_click)

    def on_scroll(self, x: int, y: int, dx: int, dy: int) -> None:
        if self.estado == State.PAUSED:
            return

        screen: Screen | None = self.macro.find_screen_by_coordinates(x, y)
        if(screen is None):
            return

        step: Step = Step()
        step.type = "scroll"
        step.coordinate = (dx, dy)
        step.key_press_time = self.get_corrected_now()
        step.screen_number = screen.id
        step.key_release_time = step.key_press_time
        self.macro.steps.append(step)

    def key_as_str (self, k: Key | KeyCode|None)->str|None:
        key: str | None
        if hasattr(k, "char"):  # KeyCode
            key = k.char if k.char is not None else None
        elif hasattr(k, "name"):  # Key
            # Literal['shift', 'alt', 'alt_l', 'alt_r', 'alt_gr', 'backspace', 'caps_lock', 'cmd', 'cmd_l', 'cmd_r', 'ctrl', 'ctrl_l', 'ctrl_r', 'delete', 'down', 'enter', 'esc', 'f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9', 'f10', 'f11', 'f12', 'f13', 'f14', 'f15', 'f16', 'f17', 'f18', 'f19', 'f20', 'f21', 'f22', 'f23', 'f24', 'home', 'left', 'page_down', 'page_up', 'right', 'shift_l', 'shift_r', 'space', 'tab', 'up', 'media_play_pause', 'media_stop', 'media_volume_mute', 'media_volume_down', 'media_volume_up', 'media_previous', 'media_next', 'media_eject', 'insert', 'menu', 'num_lock', 'pause', 'print_screen', 'scroll_lock', 'end'] | None
            key = k.name if k.name else None
        else:
            key = str(k)
        return key

    def on_press(self, received_key: Key | KeyCode | None) -> None:
        if received_key is None:
            return
        key = self.key_as_str(received_key)

        if (key is None):
            return
        
        if(received_key == keyboard.Key.shift):
            self.shift_is_pressed = True
        
        if (received_key == keyboard.Key.end and self.shift_is_pressed):
            self.stop()
            return

        if (received_key == keyboard.Key.home and self.shift_is_pressed):
            self.toggle_play()
            return

        if self.estado == State.PAUSED:
            return


        if(key not in self.steps_on_flight_key):
            self.steps_on_flight_key[key] = Step()
        new_step = self.steps_on_flight_key[key]
        new_step.type = f"keyboard"
        new_step.key = key
        new_step.key_press_time = self.get_corrected_now()

    def on_release(self, received_key: Key | KeyCode | None) -> None:
        if(received_key == keyboard.Key.shift):
            self.shift_is_pressed = False
        if self.estado == State.PAUSED:
            return

        key_str = self.key_as_str(received_key)
        if(key_str is None):
            return
        
        released_key = self.steps_on_flight_key.get(key_str)
        
        if(released_key is None):
            return
        
        released_key.key_release_time = self.get_corrected_now()
        self.macro.steps.append(released_key)
        
        _ = self.steps_on_flight_key.pop(key_str, None)
        
    def get_corrected_now(self)->timedelta:
        return (datetime.now()-self.macro_start)-self.pause_drift
        