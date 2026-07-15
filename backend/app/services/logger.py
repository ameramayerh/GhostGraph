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
                self.disconnect(connection)

# Only deliberate scan events are sent to the desktop activity panel. Application,
# database, and HTTP diagnostics remain in the backend console where developers can
# inspect them without overwhelming users or exposing query details in the UI.
ws_manager = ConnectionManager()
