from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from message.AbstractUpdateMessage import AbstractUpdateMessage


@dataclass
class RemoteMessage(ABC):
    slave_id:str
    message:AbstractUpdateMessage