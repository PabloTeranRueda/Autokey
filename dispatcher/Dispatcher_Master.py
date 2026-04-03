from requests.models import Response
import random
import string
from abc import ABC
from datetime import datetime
import json

import urllib3
from urllib3.response import BaseHTTPResponse
from message.AbstractUpdateMessage import AbstractUpdateMessage
from message.ConnectedMessage import ConnectedMessage
from message.DisconnectedMessage import DisconnectedMessage
from message.DispatcherMessage import DispatcherMessage
from message.ExampleMessage import ExampleMessage
from message.MacroMessage import MacroMessage
from message.PlayerMessage import PlayerMessage
from typing import override

from message.ErrorMessage import ErrorMessage
from message.RemoteMessage import RemoteMessage
from messenger.messenger import Messenger
from dispatcher.Abstract_Dispatcher import Abstract_Dispatcher
from model.Coordinates import Coordinates
from model.Macro import Macro
from model.Screen import Screen
import requests
from model.Target import Target
from util.Event_Enum import DispatcherEvent
from util.Message_Enum import MessageEnum
from util.sse_client import Event, SSEClient


class Dispatcher_Master(Abstract_Dispatcher, ABC):
    def __init__(self, messenger: Messenger, available_screens: list[Screen]) -> None:
        super().__init__(messenger, available_screens)
        self.slaves_dict: dict[str, SSEClient] = {}
        self.master_id: str = ''.join(random.choices(
            population=string.ascii_letters + string.digits, k=32))
        self.connection_pool = urllib3.PoolManager()

    @override
    def record(self, macro: Macro) -> None:
        return

    @override
    def update(self, macro: Macro) -> None:
        return

    @override
    def run(self, macro: Macro, reps: int, speed: float, target: Target | None) -> None:
        if target is None:
            return
        if self.slaves_dict.get(target.url, None) is None:
            self.messenger.send_event(event=ErrorMessage(
                event_time=datetime.now(), error=str(f"Slave is not connected")))
            return
        url: str = f"{target.url}/run"
        response = requests.post(url=url,
                                 json={
                                     "macro": macro.model_dump(mode="json"),
                                     "reps": reps,
                                     "speed": speed},
                                 headers={
                                     "Authorization": self.master_id},
                                 timeout=10)
        if response.status_code == 200:
            self.messenger.send_event(event=DispatcherMessage(
                event_time=datetime.now(), event=DispatcherEvent.RESPONSE_OK))
        else:
            self.messenger.send_event(event=ErrorMessage(event_time=datetime.now(
            ), error=str(f"Response: {response.status_code}{response.text}")))

    def on_sse_event(self, slave_id: str, event: Event):

        if event.data is None or event.data.strip() == "":
            return True
        content = json.loads(event.data)
        message: AbstractUpdateMessage | None
        event_type: str | None = content.get("event_type")
        if event_type is None:
            self.messenger.send_event(event=ErrorMessage(
                event_time=datetime.now(), error=str("Failed to parse message from Slave")))
            return True

        match event_type:
            case MessageEnum.DISPATCHER_MESSAGE.value:
                message = DispatcherMessage.from_json(json_object=content)
            case MessageEnum.ERROR_MESSAGE.value:
                message = ErrorMessage.from_json(json_object=content)
            case MessageEnum.MACRO_MESSAGE.value:
                message = MacroMessage.from_json(json_object=content)
            case MessageEnum.PLAYER_MESSAGE.value:
                message = PlayerMessage.from_json(json_object=content)
            case MessageEnum.EXAMPLE_MESSAGE.value:
                message = ExampleMessage.from_json(json_object=content)
            case MessageEnum.STOP_SSE_MESSAGE.value:
                self.messenger.send_event(event=RemoteMessage(slave_id=slave_id,message=DispatcherMessage(event_time=datetime.now(),event=DispatcherEvent.SERVER_DOWN)))
                return False
            case _:
                message = None

        if message is None:
            self.messenger.send_event(event=ErrorMessage(event_time=datetime.now(
            ), error=str(f"Failed to parse '{event_type}' message from Slave {slave_id}")))
        else:
            self.messenger.send_event(event=RemoteMessage(slave_id=slave_id,message=message))
        return True

    def on_sse_closed(self, slave_id: str,  e: Exception):
        self.messenger.send_event(event=DisconnectedMessage(
            event_time=datetime.now(), slave_id=slave_id))
        self.messenger.send_event(ErrorMessage(event_time=datetime.now(),error=str(e)))

    def on_sse_connect(self, slave_id: str, resp: BaseHTTPResponse) -> bool:
        result: bool = resp.status == 200

        if result:
            self.messenger.send_event(event=ConnectedMessage(
            event_time=datetime.now(), slave_id=slave_id))
        return result

    @override
    def connect(self, target: Target) -> None:
        slave_id: str = target.url

        if self.slaves_dict.get(slave_id) is not None:
            return

        client = SSEClient(f"{target.url}/events",
                           self.connection_pool, self.master_id, slave_id)

        self.slaves_dict[slave_id] = client

        client.start(self.on_sse_event, self.on_sse_connect, self.on_sse_closed)

    @override
    def disconnect(self, target: Target) -> bool:
        try:
            url: str = f"{target.url}/disconnect"
            response = requests.post(url=url,
                                    headers={
                                        "Authorization": self.master_id},
                                    timeout=10)
            if response.status_code == 200:
                self.messenger.send_event(event=DispatcherMessage(
                    event_time=datetime.now(), event=DispatcherEvent.RESPONSE_OK))
            else:
                self.messenger.send_event(event=ErrorMessage(event_time=datetime.now(
                ), error=str(f"Response: {response.status_code}{response.text}")))
            
            self.clean_disconnected_slave(target.url)
        
        except Exception as response_attempt_error:
            self.messenger.send_event(event=ErrorMessage(event_time=datetime.now(
                ), error=str(response_attempt_error)))
            try:
                self.clean_disconnected_slave(target.url)
            except Exception as clean_attempt_error:
                self.messenger.send_event(event=ErrorMessage(event_time=datetime.now(
                ), error=str(clean_attempt_error)))

                return False
        return True

    @override
    def dummy(self, screen: Screen, target: Target | None) -> None:
        try:
            if target is None:
                return
            url = f"{target.url}/dummy"

            screen = Screen(id=1, resolution=Coordinates(
                x=1, y=2), top_left=Coordinates(x=3, y=4))
            response = requests.post(url=url, json=screen.model_dump(mode="json"), headers={
                                     "Authorization": self.master_id}, timeout=10)

            # print(response.status_code)
            # print(screen.model_dump(mode="json"))

            if response.status_code == 200:
                print("ok")
            else:
                print("error")
        except (requests.exceptions.ConnectionError) as e:
            self.messenger.send_event(event=ErrorMessage(
                event_time=datetime.now(), error=str(e)))
        except Exception as e:
            self.messenger.send_event(event=ErrorMessage(
                event_time=datetime.now(), error=str(e)))

    @override
    def toggle_pause(self, target: Target | None) -> None:
        if target is None:
            return
        _: Response = requests.post(
            url=f"{target.url}/pause", headers={"Authorization": self.master_id}, timeout=10)

    @override
    def stop(self, target: Target | None) -> None:
        if target is None:
            return

        _: Response = requests.post(
            url=f"{target.url}/stop", headers={"Authorization": self.master_id}, timeout=10)

    @override
    def clean_up(self) -> None:
        for i in self.slaves_dict.values():
            i.stop()
        self.slaves_dict = {}

    def clean_disconnected_slave(self, slave_id: str) -> None:
        slave: SSEClient | None = self.slaves_dict.pop(slave_id, None)
        if slave:
            slave.stop()


# if __name__ == "__main__":
    # ip = "http://127.0.0.1"
    # port = 3000
    # master = Master()
    # master.ip = ip
    # master.port = port
