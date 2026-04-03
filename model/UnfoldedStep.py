
from dataclasses import dataclass
from datetime import timedelta

from model.Step import Step


@dataclass
class UnfoldedStep:
    type: str | None
    key: str | None
    coordinate: tuple[int, int] | None
    when: timedelta | None
    screen_number: int | None
    release: bool

    def __init__(self, step: Step, release: bool):
        self.release = release
        self.type = step.type
        self.key = step.key
        self.coordinate = step.coordinate
        self.screen_number = step.screen_number
        self.when = step.key_release_time if (release) else step.key_press_time
