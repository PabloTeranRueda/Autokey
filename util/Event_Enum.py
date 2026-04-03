from enum import Enum

class DispatcherEvent(Enum):
    ON_CREATE = 1
    ON_UPDATE = 2
    ON_RUN = 3
    CONNECTED = 4
    DISCONNECTED = 5
    RESPONSE_OK = 6
    SERVER_UP = 7
    SERVER_DOWN = 8
    TEST = 9

class ExampleEvent(Enum):
    TEST1 = 1
    TEST2 = 2

class MacroEvent(Enum):
    CREATED = 1
    UPDATED = 2
    DELETED = 3
    SAVED = 4
    STARTED = 5

class PlayerEvent(Enum):
    STARTED = 1
    STOPPED = 2
    TOGGLED_PAUSE = 3
    FINISHED = 4
    ADVANCED = 5
    END_OF_MACRO = 6

class RecorderEvent(Enum):
    STARTED = 1
    STOPPED = 2
    TOGGLED_PAUSE = 3
    FINISHED = 4