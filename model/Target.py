from dataclasses import dataclass
from typing import Self


@dataclass
class Target():
    host:str
    port:int

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}"

    @classmethod
    def from_string(cls,url:str) -> Self|None:
        try:
            host, raw_port = url.removeprefix("http://").split(":")
            port = int(raw_port)
        except Exception:
            return None
        else:
            return cls(host=host, port=int(port))
