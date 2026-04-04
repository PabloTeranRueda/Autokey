from fastapi.responses import JSONResponse
from uvicorn.server import Server


import queue
from anyio import from_thread


from abc import ABC
from typing import override
from datetime import datetime
import json
from threading import Thread
import uvicorn
from fastapi import Body, FastAPI, Request, Header, Response
from starlette.responses import StreamingResponse
from message.MacroMessage import MacroMessage
from message.StopSSEMessage import StopSSEMessage
from message.AbstractUpdateMessage import AbstractUpdateMessage
from message.DispatcherMessage import DispatcherMessage
from message.ErrorMessage import ErrorMessage
from message.ExampleMessage import ExampleMessage
from message.PlayerMessage import PlayerMessage
from messenger.messenger import Messenger
from dispatcher.Abstract_Dispatcher import Abstract_Dispatcher
from core.Player import Player
from model.Macro import Macro
from model.Screen import Screen
from util.Target import Target
from util.Event_Enum import DispatcherEvent, ExampleEvent, MacroEvent, PlayerEvent
from util.State_Enum import State


class Dispatcher_Slave(Abstract_Dispatcher,ABC):
    def __init__(self, messenger:Messenger, available_screens:list[Screen]) -> None:
        super().__init__(messenger, available_screens) 
        self.app: FastAPI = FastAPI()
        self.player: Player = Player(messenger=messenger,available_screens=available_screens)
        self.master:queue.SimpleQueue[AbstractUpdateMessage|None]|None = None
        self.master_id : str | None = None
        self.server_thread: Thread|None = None
        self.server: Server|None = None
        

        self._register_routes_in_app()


    
    def _register_routes_in_app(self) -> None:
        
        @self.app.post("/run")
        def start_api(
            speed:float=Body(...),
            reps:int=Body(...),
            macro:Macro=Body(...),
            authorization: str | None = Header(default=None),
            ) -> Response:
            try:
                if(self.master_id is None or authorization is None or self.master_id != authorization):
                    return  Response(content='{"status":"401"}', status_code=401, media_type="application/json")
                print("Process started")
                self.player.start(macro=macro,speed=speed,reps=reps)
                self.messenger.send_event(event=DispatcherMessage(event_time=datetime.now(),event=DispatcherEvent.ON_RUN))
                self.messenger.send_event(event=MacroMessage(event_time=datetime.now(),event=MacroEvent.STARTED,macro=macro))

            except Exception as e:
                self.messenger.send_event(event=ErrorMessage(event_time=datetime.now(),error=str(e)))
                return Response(content='{"status":"400"}', status_code=400, media_type="application/json")
            return  Response(content='{"status":"200"}', status_code=200, media_type="application/json")

        @self.app.post("/disconnect")
        def disconnect(authorization: str | None = Header(default=None)) -> Response:
            try:
                if(self.master_id is None or authorization is None or self.master_id != authorization):
                    return  Response(content='{"status":"401"}', status_code=401, media_type="application/json")
                if self.master is not None:
                    self.master.put_nowait(StopSSEMessage(event_time=datetime.now()))
                    # self.messenger.send_event(event=DispatcherMessage(event_time=datetime.now(),event=DispatcherEvent.DISCONNECTED))
                self.master = None
                self.master_id = None
                self.messenger.master = None
            except Exception as e:
                self.messenger.send_event(event=ErrorMessage(event_time=datetime.now(),error=str(e)))
                return Response(content='{"status":"400"}', status_code=400, media_type="application/json")
            return  Response(content='{"status":"200"}', status_code=200, media_type="application/json")
                
        @self.app.post("/pause")
        def toggle_pause(authorization: str | None = Header(default=None)) -> Response:
            try:
                if(self.master_id is None or authorization is None or self.master_id != authorization):
                    return  Response(content='{"status":"401"}', status_code=401, media_type="application/json")
                print("Process paused")
                if self.player.estado != State.OFF:
                    self.player.toggle_play()
            except Exception as e:
                self.messenger.send_event(event=ErrorMessage(event_time=datetime.now(),error=str(e)))
                return Response(content='{"status":"400"}', status_code=400, media_type="application/json")
            return  Response(content='{"status":"200"}', status_code=200, media_type="application/json")
                
        @self.app.post("/stop")
        def stop(authorization: str | None = Header(default=None)) -> Response:
            if(self.master_id is None or authorization is None or self.master_id != authorization):
                return  Response(content='{"status":"401"}', status_code=401, media_type="application/json")
            if self.master is None:
                return  Response(content='{"status":"400"}', status_code=400, media_type="application/json")
            try:
                print("Process stopped")
                if self.player.estado != State.OFF:
                    self.player.stop()
            except Exception as e:
                self.messenger.send_event(event=ErrorMessage(event_time=datetime.now(),error=str(e)))
                return Response(content='{"status":"400"}', status_code=400, media_type="application/json")
            return  Response(content='{"status":"200"}', status_code=200, media_type="application/json")

        @self.app.post("/dummy")
        def dummy_api(screen: Screen = Body(...),authorization: str | None = Header(default=None)) -> Response:
            try:
                if(self.master_id is None or authorization is None or self.master_id != authorization):
                    return  Response(content='{"status":"401"}', status_code=401, media_type="application/json")
                print(screen.to_dict())
                print(screen.model_dump())
                if self.master is None:
                    return Response(content='{"status":"404"}', status_code=404, media_type="application/json")
                
                self.master.put_nowait(item=PlayerMessage(event_time=datetime.now(),event=PlayerEvent.STOPPED,state=State.ON,current_step=1))
                self.dummy(target=None,screen=screen)
            except Exception as e:
                self.messenger.send_event(event=ErrorMessage(event_time=datetime.now(),error=str(e)))
                return Response(content='{"status":"400"}', status_code=400, media_type="application/json")
            return  Response(content='{"status":"200"}', status_code=200, media_type="application/json")
        
        @self.app.get("/events")
        def sse_connection(request:Request,authorization: str | None = Header(default=None),):

            if self.master is not None or self.master_id is not None:
                return Response(
                    status_code=400, content="Connection is already in use."
                )
            elif authorization is None:
                return Response(
                    status_code=401, content="Authorization failed: no valid credentials provided."
                )

            self.master = queue.SimpleQueue[AbstractUpdateMessage|None]()

            self.messenger.master = self.master
            self.master_id = authorization
            self.messenger.send_event(event=DispatcherMessage(event_time=datetime.now(),event=DispatcherEvent.CONNECTED))
            # self.master.put_nowait(item=DispatcherMessage(event_time=datetime.now(),event=DispatcherEvent.CONNECTED))

            def event_generator():
                try:
                    while True:
                        if self.master is None or self.master_id == None:
                            self.messenger.send_event(event=DispatcherMessage(event_time=datetime.now(),event=DispatcherEvent.DISCONNECTED))
                            break
                        if from_thread.run(request.is_disconnected):
                            break

                        try:
                            value: AbstractUpdateMessage|None = self.master.get(timeout=0.2)
                            
                            if value is None:
                                stop = StopSSEMessage(event_time=datetime.now())
                                yield f"event: {stop.event_type}\ndata: {json.dumps(stop.jsonify())}\n\n"
                                break
                            if from_thread.run(request.is_disconnected):
                                self.messenger.send_event(event=DispatcherMessage(event_time=datetime.now(),event=DispatcherEvent.DISCONNECTED))
                                break

                            yield f"event: {value.event_type}\ndata: {json.dumps(value.jsonify())}\n\n"
                        except queue.Empty:
                            yield ": keep-alive\n\n"
                            if from_thread.run(request.is_disconnected):
                                # if we do not receive events and request is disconnected, this means we disconnected abruptly
                                self.messenger.send_event(ErrorMessage(event_time=datetime.now(),error=str("Abrupt disconnection")))
                                break
                            if self.server is not None: 
                                if (self.server.force_exit or self.server.should_exit):
                                    self.messenger.send_event(ErrorMessage(event_time=datetime.now(),error=str("Server disconnected")))
                                    break

                except Exception as e:
                    self.messenger.send_event(event=ErrorMessage(event_time=datetime.now(),error=str(e)))
                finally:
                    if not self.player.estado == State.OFF:
                        self.messenger.send_event(
                                event=PlayerMessage(event=PlayerEvent.END_OF_MACRO, state=self.player.estado, event_time=datetime.now(), current_step=self.player.current_step))

                    self.master = None
                    self.master_id = None
                    self.messenger.master = None
        
            return StreamingResponse(event_generator(), media_type="text/event-stream")
    
    def run_server(self,port:int) -> bool:
        try:
            if self.server_thread is not None and self.server_thread.is_alive():
                return False
            
            config: uvicorn.Config = uvicorn.Config(
                self.app,
                host="0.0.0.0",
                port=port
            )
            self.server = uvicorn.Server(config)

            self.server_thread = Thread(target=self.server.run, daemon=True)
            self.server_thread.start()
            self.messenger.send_event(event=DispatcherMessage(event_time=datetime.now(),event=DispatcherEvent.SERVER_UP))
        except Exception:
            self.clean_up()
            return False
        else:
            return True
    @override
    def record(self, macro:Macro) -> None:
        return

    @override
    def update(self, macro:Macro) -> None:
        return
    @override
    def run(self,macro:Macro,reps:int,speed:float,target:Target|None) -> None:
        return
    @override            
    def toggle_pause(self,target:Target|None) -> None:
        if self.player.estado != State.OFF:
            self.player.toggle_play()
    @override
    def stop(self,target:Target|None=None) -> None:
        if self.player.estado != State.OFF:
            self.player.stop()
    @override
    def connect(self,target:Target) -> None:
        return
    @override
    def disconnect(self,target:Target) -> bool:
        try:
            if self.master is not None:
                self.master.put_nowait(item=None)
            
            self.clean_up()
        except Exception:
            return False        
        return True
    @override
    def dummy(self,screen:Screen,target:Target|None=None) -> None:
        self.messenger.send_event(ExampleMessage(event_time=datetime.now(),event= ExampleEvent.TEST1,text="Running process..."))
        return

    @override
    def clean_up(self) -> None:
        self.stop()

        if self.server_thread and self.server:
            self.server.force_exit = True
            self.server.should_exit = True
            self.server_thread.join()
            self.server_thread = None
            self.server = None
        
        if self.master is not None:
            self.master.put_nowait(StopSSEMessage(event_time=datetime.now()))
            self.messenger.send_event(event=DispatcherMessage(event_time=datetime.now(),event=DispatcherEvent.SERVER_DOWN))
        
        self.master = None
        self.master_id = None
    
# if __name__ == "__main__":
#     import uvicorn
#     dispatcher = Dispatcher_Slave()
#     app = dispatcher.app
#     uvicorn.run(app,reload=True, host ="127.0.0.1", port=3000)