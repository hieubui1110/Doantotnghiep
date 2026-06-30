from fastapi import WebSocket
from typing import Dict, List
import json

class DashboardManager:
    def __init__(self):
        # Maps camera_id or "all" to active WebSocket connections
        self.connections: Dict[str, List[WebSocket]] = {"all": []}

    async def connect(self, websocket: WebSocket, camera_filter: str = None):
        await websocket.accept()
        self.connections["all"].append(websocket)
        if camera_filter:
            if camera_filter not in self.connections:
                self.connections[camera_filter] = []
            self.connections[camera_filter].append(websocket)

    def disconnect(self, websocket: WebSocket):
        for key in list(self.connections.keys()):
            if websocket in self.connections[key]:
                self.connections[key].remove(websocket)
            # Cleanup key if it has no connections (except "all")
            if key != "all" and not self.connections[key]:
                del self.connections[key]

    async def broadcast(self, message: dict):
        """Send message to all connected dashboards."""
        inactive_sockets = []
        for ws in self.connections.get("all", []):
            try:
                await ws.send_json(message)
            except Exception:
                inactive_sockets.append(ws)
                
        # Clean up dead sockets
        for ws in inactive_sockets:
            self.disconnect(ws)

    async def send_to_camera_subscribers(self, camera_id: str, message: dict):
        """Send message to dashboards watching a specific camera."""
        inactive_sockets = []
        for ws in self.connections.get(camera_id, []):
            try:
                await ws.send_json(message)
            except Exception:
                inactive_sockets.append(ws)
                
        # Clean up dead sockets
        for ws in inactive_sockets:
            self.disconnect(ws)

dashboard_manager = DashboardManager()
