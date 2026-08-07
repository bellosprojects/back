from .game_manager import GameManager
from .websocket_manager import WebsocketManager
from .map_service import MapService

ws_manager = WebsocketManager()
map_service = MapService()
game_manager = GameManager(ws_manager, map_service)