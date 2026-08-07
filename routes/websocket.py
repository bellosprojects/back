from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
from services import ws_manager, game_manager

router = APIRouter()

@router.websocket("/ws/code")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect_socket(websocket)
    await game_manager.send_state_to_client(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            tipo = message.get("tipo")
            print(f"New message from user: {tipo}")

            if tipo == "registrar_jugador":
                user_id = message.get("id", "default_id")
                user_name = message.get("nombre", "Anónimo")
                await ws_manager.register_user(websocket, user_id, user_name)
                await game_manager.register_player_for_game(user_id)
                await game_manager.broadcast_state()
            elif tipo == "seleccion_completa":
                user_id = message.get("id")
                seleccion = message.get("seleccion", [])
                if len(seleccion) == 3:
                    game_manager.set_user_powers(user_id=user_id, powers=seleccion)
            elif tipo == "codigo_listo":
                user_id = message.get("id")
                codigo = message.get("codigo")
                if user_id in game_manager.playing_users:
                    game_manager.playing_users[user_id].code = codigo
                    await websocket.send_text(json.dumps({"tipo": "codigo_recibido", "id": user_id}))
                    if game_manager.all_codes_received():
                        game_manager.current_time = min(5, game_manager.current_time)

            elif tipo == "key_interrupt":
                user_id = message.get("id")
                if user_id and game_manager.sim_engine:
                    tank = game_manager.sim_engine.tanks.get(user_id)
                    if tank and tank.can_interrupt():
                        tank.use_interrupt()

                        interpreter = game_manager.sim_engine.interpreters.get(user_id)
                        if interpreter:
                            interpreter.trigger_event("keyInterrupt")
                        await websocket.send_text(json.dumps({"tipo": "interrupt_accepted", "id": user_id}))
                    else:
                        await websocket.send_text(json.dumps({"tipo": "interrupt_denied", "id": user_id}))

    except WebSocketDisconnect:
        await ws_manager.disconnect_socket(websocket)
        for uid, user in list(game_manager.playing_users.items()):
            if user.ws == websocket:
                del game_manager.playing_users[uid]
                break
        await game_manager.check_players_count()
        await game_manager.broadcast_state()