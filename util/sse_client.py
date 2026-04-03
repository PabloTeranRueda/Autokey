from dataclasses import dataclass
import threading
import urllib3

@dataclass
class Event:
    id: str | None
    event: str
    data: str

class SSEClient:
    def __init__(self, url:str, pool:urllib3.PoolManager, auth:str, id_slave:str):
        self.url = url
        self.http = pool
        self.auth = auth
        self.id_slave = id_slave
        self.stop_event = threading.Event()
        self.response = None
        self.thread = None
        self.exception:Exception|None = None

    def _stream(self, on_event, on_connect, on_closed):
        try:
            self.response = self.http.request(
                "GET",
                self.url,
                preload_content=False,
                headers={"Accept": "text/event-stream", "Authorization":self.auth}
            )

            if(not on_connect(self.id_slave, self.response)):
                if self.response:
                    self.response.close()
                return

            # Buffers to accumulate a full SSE event
            event: Event = Event(id=None, event="message", data="")
            buffer = ""
            for chunk in self.response.stream(amt=1024):
                if self.stop_event.is_set():
                    break
                if not chunk:
                    continue

                # Split chunk into lines
                buffer += chunk.decode("utf-8")

                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    if not line:  # empty line signals end of event
                        if event.data:
                            # Yield or print complete event
                            if (not on_event(self.id_slave, event)):
                                if self.response:
                                    self.response.close()
                                return
                            #print(f"Event: {event['event']}, ID: {event['id']}, Data: {event['data']}")
                        # Reset for next event
                        event = Event(id=None, event="message", data="")
                        continue

                    if line.startswith("id:"):
                        event.id = line[3:].strip()
                    elif line.startswith("event:"):
                        event.event = line[6:].strip()
                    elif line.startswith("data:"):
                        # Multiple data lines are joined with newline
                        if event.data:
                            event.data += "\n"
                        event.data += line[5:].strip()
                    elif line.startswith("retry:"):
                        pass

        except Exception as e:
            if not self.stop_event.is_set():
                self.exception = e
        finally:
            if self.response:
                self.response.close()
            on_closed(self.id_slave, self.exception)

    def start(self, on_event, on_connect, on_closed):
        self.thread = threading.Thread(target=self._stream, kwargs={"on_event": on_event, "on_connect": on_connect, "on_closed":on_closed}, daemon=True)
        self.thread.start()

    def stop(self):
        self.stop_event.set()
        if self.response:
            self.response.close()
        if self.thread:
            self.thread.join()
            self.thread = None