import json
from typing import Dict, Set, List, Any
from fastapi import WebSocket
from models.user import User

class WebsocketManager:
    def __init__(self):
        self.connections: Set[WebSocket] = set()
        self.users: Dict[str, User] = {}  # id -> User

    async def connect_socket(self, ws: WebSocket):
        await ws.accept()
        self.connections.add(ws)

    async def disconnect_socket(self, ws: WebSocket):
        if ws in self.connections:
            self.connections.remove(ws)
        # Eliminar de users si existe
        to_remove = None
        for uid, user in self.users.items():
            if user.ws == ws:
                to_remove = uid
                break
        if to_remove:
            del self.users[to_remove]

    async def register_user(self, ws: WebSocket, user_id: str, user_name: str):
        user = User(id=user_id, name=user_name, ws=ws)
        self.users[user_id] = user
        return user

    async def broadcast(self, message: Any):
        for ws in self.connections:
            try:
                await ws.send_text(json.dumps(message))
            except Exception:
                pass

    def get_all_users(self) -> List[User]:
        return list(self.users.values())