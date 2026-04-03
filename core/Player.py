from threading import Thread, Event
from messenger.messenger import Messenger
from datetime import datetime, timedelta
from pynput.keyboard import Key, KeyCode
from pynput.mouse import Button
from pynput import keyboard, mouse
from model.Coordinates import Coordinates
from model.Macro import Macro
from model.Screen import Screen
from model.UnfoldedStep import UnfoldedStep
from message.PlayerMessage import PlayerMessage
from message.ErrorMessage import ErrorMessage
from util.Event_Enum import PlayerEvent
from util.State_Enum import State


class Player():
    def __init__(self, messenger: Messenger, available_screens: list[Screen]) -> None:
        self.estado: State = State.OFF
        self.current_step: int = 0
        self.mouse_controller: mouse.Controller = mouse.Controller()
        self.keyboard_controller: keyboard.Controller = keyboard.Controller()
        self.keyboard_listener: keyboard.Listener | None = None
        self.shift_is_pressed: bool = False
        self.messenger: Messenger = messenger
        self.available_screens: list[Screen] = available_screens
        self.player_thread: Thread | None = None
        self.unpaused: Event = Event()
        self.sleep_unstuck: Event = Event()

    def start(self, macro: Macro, speed: float, reps: int) -> None:
        self.estado = State.ON
        self.current_step = 0
        self.shift_is_pressed = False
        self.unpaused.set()
        self.sleep_unstuck.clear()
        
        self.keyboard_listener = keyboard.Listener(on_press=self.on_press)
        self.player_thread = Thread(target=self.player_loop, kwargs={
                                    "macro": macro, "speed": speed, "reps": reps}, daemon=True)

        self.keyboard_listener.start()
        self.player_thread.start()

        self.messenger.send_event(event=PlayerMessage(event=PlayerEvent.STARTED, state=self.estado, event_time=datetime.now(), current_step=self.current_step))

    def on_press(self, key: Key | KeyCode | None) -> None:
        if not isinstance(key, Key):
            return
        if key == keyboard.Key.shift:
            self.shift_is_pressed = True
        elif key == keyboard.Key.home and self.shift_is_pressed:
            self.shift_is_pressed = False
            self.toggle_play()
        elif key == keyboard.Key.end and self.shift_is_pressed:
            self.shift_is_pressed = False
            self.stop()
            return

    def stop(self) -> None:
        if self.estado == State.OFF:
            # already stopped
            return
        self.estado = State.OFF
        self.sleep_unstuck.set()
        self.unpaused.set()

        if self.keyboard_listener is None:
            self.messenger.send_event(event=ErrorMessage(event_time=datetime.now(
            ), error=str("Keyboard Listener was not correctly initialized")))
        else:
            self.keyboard_listener.stop()
        
        if self.player_thread is not None:
            self.player_thread.join()
            self.player_thread = None
        else:
            self.messenger.send_event(event=ErrorMessage(event_time=datetime.now(
            ), error=str("Player's Thread was not correctly initialized")))

        self.messenger.send_event(
                event=PlayerMessage(event=PlayerEvent.FINISHED, state=self.estado, event_time=datetime.now(), current_step=self.current_step))

    def toggle_play(self) -> None:
        if (self.estado != State.ON):
            return

        if (self.unpaused.is_set()):
            #Is not paused
            self.unpaused.clear()
        else:
            #Is paused
            self.unpaused.set()

        self.messenger.send_event(
            event=PlayerMessage(event=PlayerEvent.TOGGLED_PAUSE, state=self.estado, event_time=datetime.now(), current_step=self.current_step))

    def player_loop(self, macro: Macro, speed: float, reps: int) -> None:
        # Reps < 0 = INFINITE
        if (len(macro.screens) < 1):
            return
        
        unfolded_steps:list[UnfoldedStep] = [] 
        
        for step in macro.steps:
            match step.type:
                case "keyboard" | "click":
                    unfolded_steps.append(UnfoldedStep(step, True))
                    unfolded_steps.append(UnfoldedStep(step, False))
                case "scroll" | "movement":
                     unfolded_steps.append(UnfoldedStep(step, False))
                case _:
                    pass
                
        unfolded_steps.sort(key=lambda s: s.when or timedelta(0))
        
        
        last_time =timedelta(0)
        while (reps != 0 and self.estado == State.ON):
            self.current_step = 0
            for step in unfolded_steps:
                if(step.when is None):
                    continue
                
                sleep_time = (((step.when -last_time)* speed)).total_seconds()
                
                if(sleep_time>0):
                    if(self.sleep_unstuck.wait(sleep_time)):
                        break

                # Wait if paused
                self.unpaused.wait()

                # Check if still running and break the loop if not
                if (self.estado != State.ON):
                    break
                
                if step.release is False:
                    self.current_step += 1
                    self.messenger.send_event(event=PlayerMessage(event=PlayerEvent.ADVANCED, state=self.estado, event_time=datetime.now(), current_step=self.current_step))

                self.run_step(step, macro.screens[step.screen_number]if (
                    step.screen_number is not None)else None)
                last_time = step.when

            if (reps > 0):
                reps = reps-1

        self.messenger.send_event(
                event=PlayerMessage(event=PlayerEvent.END_OF_MACRO, state=self.estado, event_time=datetime.now(), current_step=self.current_step))
        # self.stop()

    def calcute_relative_coordinates(self, step: UnfoldedStep, source_screen: Screen) -> Coordinates | None:
        if (step.coordinate is None or len(self.available_screens) <= 0):
            return
        step_coordinate_x: int = step.coordinate[0]
        step_coordinate_y: int = step.coordinate[1]

        # Choose a screen (or clip if out of bounds)
        screen_index: int = 0

        if step.screen_number != None:
            if step.screen_number < len(self.available_screens):
                screen_index = step.screen_number
            else:
                screen_index = len(self.available_screens)-1

        target_screen = self.available_screens[screen_index]

        target_x: int = target_screen.resolution.x
        target_y: int = target_screen.resolution.y

        source_x: int = source_screen.resolution.x
        source_y: int = source_screen.resolution.y

        target_top_left_x: int = target_screen.top_left.x
        target_top_left_y: int = target_screen.top_left.y

        return Coordinates(
            x=round(number=(target_x/source_x) *
                    (step_coordinate_x + target_top_left_x)),
            y=round(number=(target_y/source_y) *
                    (step_coordinate_y + target_top_left_y))
        )

    def run_step(self, step: UnfoldedStep, source_screen: Screen | None) -> None:
        match step.type:
            case "keyboard":
                if step.key is None:
                    return
                try:
                    key_or_letter: str = getattr(Key, step.key)
                except AttributeError:
                    key_or_letter: str = step.key

                if(step.release):
                    self.keyboard_controller.release(key=key_or_letter)
                else:
                    self.keyboard_controller.press(key=key_or_letter)

            case "scroll":
                if (step.coordinate is None):
                    return

                self.mouse_controller.scroll(
                    dx=step.coordinate[0], dy=step.coordinate[1])
            case "click":
                if step.key is None or source_screen is None:
                    return

                rel = self.calcute_relative_coordinates(
                    step=step, source_screen=source_screen)
                if (rel is None):
                    return

                self.mouse_controller.position = (rel.x, rel.y)

                button: Button = Button[step.key]

                if(step.release):
                    self.mouse_controller.release(button)
                else:
                    self.mouse_controller.press(button)
            
            case "movement":
                if source_screen is None:
                    return
                rel = self.calcute_relative_coordinates(
                    step=step, source_screen=source_screen)
                if (rel is None):
                    return
                self.mouse_controller.position = (rel.x, rel.y)

            case _:
                pass

        return
