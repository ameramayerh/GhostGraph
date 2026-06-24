import logging
import asyncio
from typing import List
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str, level: str = "info"):
        payload = {"level": level, "message": message}
        for connection in list(self.active_connections):
            try:
                await connection.send_json(payload)
            except Exception:
                pass

# Global instance
ws_manager = ConnectionManager()

class WebsocketLogHandler(logging.Handler):
    def emit(self, record):
        try:
            log_entry = self.format(record)
            level = "info"
            if record.levelno >= logging.ERROR:
                level = "error"
            elif record.levelno >= logging.WARNING:
                level = "warning"
            
            # Fire and forget the broadcast in the current asyncio event loop
            loop = asyncio.get_running_loop()
            loop.create_task(ws_manager.broadcast(log_entry, level))
        except RuntimeError:
            # If no event loop is running (e.g. during startup), skip
            pass
        except Exception:
            pass

# Attach to standard loggers so the frontend terminal sees REAL traffic
ws_handler = WebsocketLogHandler()
ws_handler.setFormatter(logging.Formatter('%(name)s: %(message)s'))

# Set up root logger to capture our app logs
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(ws_handler)

# Capture SQLAlchemy (Database queries) for that authentic hacker feel
sqlalchemy_logger = logging.getLogger("sqlalchemy.engine.Engine")
sqlalchemy_logger.setLevel(logging.INFO)
sqlalchemy_logger.addHandler(ws_handler)

# Capture FastAPI/Uvicorn requests
uvicorn_logger = logging.getLogger("uvicorn.access")
uvicorn_logger.addHandler(ws_handler)
