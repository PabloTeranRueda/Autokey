from mongita.database import Database
from typing import cast
from mongita import MongitaClientDisk



class DBConnection():
    _connection: Database|None = None
    
    @classmethod
    def _build_connection(cls, db:str) -> None:
        try:
            client: MongitaClientDisk = MongitaClientDisk()
            cls._connection = cast(Database,client[db])
        except Exception as e:
            #TODO: Create Error Event and send it to Dispatcher
            raise RuntimeError("Failed to initialize DB connection") from e

    @classmethod
    def get_connection(cls, db:str|None=None) -> Database | None:
        if cls._connection is None and db is None:
            raise RuntimeError("Missing initial BBDD configuration")
        elif cls._connection is None and db is not None:
            cls._build_connection(db)
        
        return cls._connection
    
    @classmethod
    def close_connection(cls) -> None:
        if cls._connection is not None:
            cls._connection.client.close()
            cls._connection = None