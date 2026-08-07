from fastapi import APIRouter, HTTPException
from services import game_manager, map_service

router = APIRouter()

@router.get("/start_game")
async def start_game():
    # Solo por si quieres forzar, pero la lógica automática ya lo hace
    await game_manager.start_game_cycle()
    return {"status": "ok"}

@router.get("/end_game")
async def end_game():
    # Forzar fin de partida
    if game_manager.timer_task:
        game_manager.timer_task.cancel()
    game_manager.state = None
    game_manager.playing_users.clear()
    await game_manager.broadcast_state()
    return {"status": "ok"}

@router.get("/game_state")
async def get_game_state():
    """Devuelve el estado completo del juego."""
    return game_manager.get_full_state()

@router.get("/maps")
async def list_maps():
    return {"maps": [m.get('name') for m in map_service.maps_cache]}

@router.get("/maps/{name}")
async def get_map(name: str):
    """Devuelve un mapa específico."""
    map_data = map_service.get_map_by_name(name)
    if not map_data:
        raise HTTPException(404, "Mapa no encontrado")
    return map_data