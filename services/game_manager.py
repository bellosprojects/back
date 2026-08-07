import asyncio
from typing import Optional, List, Dict, Any
from services.websocket_manager import WebsocketManager
from models import User
from fastapi import WebSocket
import json, random
from .map_service import MapService
from simulation.engine import SimulationEngine
from models.tank import Tank
from models.map import Map
from models.direction import Direction

class GameManager:
    def __init__(self, ws_manager: WebsocketManager, map_service: MapService):
        self.ws_manager = ws_manager
        self.map_service = map_service
        self.current_map: Optional[Dict[str, Any]] = None
        self.state: Optional[str] = None
        self.playing_users: Dict[str, User] = {}
        self.timer_task: Optional[asyncio.Task[Any]] = None
        self.current_time: float = 0.0
        self.ronda_actual: int = 0
        self.cards: List[int] = []

        self.sim_engine: Optional[SimulationEngine] = None
        self.sim_task: Optional[asyncio.Task[Any]] = None

        # Parámetros
        self.WAITING_TIME = 40.0
        self.SELECTION_ROUNDS = 3
        self.SELECTION_TIME = 8.0
        self.CODING_TIME = 180.0
        self.PLAYING_TIME = 300.0
        self.ENDING_TIME = 1.0

    # ---------- Métodos públicos ----------
    def get_lobby_users(self) -> List[User]:
        if self.state is None:
            return self.ws_manager.get_all_users()
        else:
            playing_ids = set(self.playing_users.keys())
            return [u for u in self.ws_manager.get_all_users() if u.id not in playing_ids]

    def get_active_players(self) -> List[User]:
        return list(self.playing_users.values()) 

    async def start_game_cycle(self):
        if self.timer_task and not self.timer_task.done():
            return
        if self.state is not None:
            return
        if len(self.ws_manager.users) < 2:
            return

        self.current_map = self.map_service.get_random_map()
        print(f"Mapa seleccionado: {self.current_map.get('name')}")

        self.state = "waiting"
        self.current_time = self.WAITING_TIME
        self.playing_users = {uid: user for uid, user in self.ws_manager.users.items()}
        await self.broadcast_state()

        self.timer_task = asyncio.create_task(self._run_timer_loop())

    async def register_player_for_game(self, user_id: str):
        user = self.ws_manager.users.get(user_id)
        if not user:
            return

        if self.state is None:
            self.playing_users[user_id] = user
            if len(self.ws_manager.users) >= 2:
                await self.start_game_cycle()
        elif self.state == "waiting":
            if user_id not in self.playing_users:
                self.playing_users[user_id] = user
                await self.broadcast_state()
        # En otros estados, no se añade a playing_users

    async def broadcast_state(self, extra: Optional[Any] = None):
        payload : Any = {
            "tipo": "game_state",
            "state": self.state,
            "tiempo_restante": round(self.current_time, 1),
            "ronda_actual": self.ronda_actual if self.state == "selecting" else 0,
            "jugadores_lobby": [{"id": u.id, "name": u.name} for u in self.get_lobby_users()],
            "jugadores_partida": [{"id": u.id, "name": u.name} for u in self.get_active_players()],
            "total_conectados": len(self.ws_manager.connections)
        }
        if self.state == "selecting":
            payload["cartas"] = self.cards

        if self.state in ["waiting", "coding"] and self.current_map:
            payload["map"] = {
                "name": self.current_map.get("name"),
                "width": self.current_map.get("width"),
                "height": self.current_map.get("height"),
                "obstacles": self.current_map.get("obstacles", []),
                "spawn_points": self.current_map.get("spawn_points", [])
            }

        if extra:
            payload.update(extra)
        await self.ws_manager.broadcast(payload)

    def get_full_state(self) -> Any:
        return {
            "state": self.state,
            "tiempo_restante": round(self.current_time, 1),
            "ronda_actual": self.ronda_actual,
            "total_conectados": len(self.ws_manager.connections),
            "usuarios_lobby": [{"id": u.id, "name": u.name} for u in self.get_lobby_users()],
            "usuarios_partida": [{"id": u.id, "name": u.name} for u in self.get_active_players()],
            "jugadores": {uid: {"name": u.name} for uid, u in self.ws_manager.users.items()},
            "cartas": self.cards
        }

    # ---------- Verificación de jugadores ----------
    async def check_players_count(self):
        """Verifica que haya al menos 2 jugadores activos. Si no, actúa según el estado."""
        if self.state is None or self.state == "ending":
            return

        if len(self.playing_users) < 2:
            if self.state in ["waiting", "selecting", "coding"]:
                # Cancelar partida y volver al lobby (el bucle se encargará de reiniciar si hay suficientes)
                self.state = None
                self.playing_users.clear()
                self.current_time = 0.0
                if self.sim_task and not self.sim_task.done():
                    self.sim_task.cancel()
                    self.sim_task = None
                    self.sim_engine = None
                await self.broadcast_state()
                # No llamamos a start_game_cycle aquí; el finally del loop lo hará
            elif self.state == "playing":
                # Pasar a ending
                if self.sim_task and not self.sim_task.done():
                    self.sim_task.cancel()
                    self.sim_task = None
                    self.sim_engine = None
                self.state = "ending"
                self.current_time = self.ENDING_TIME
                ganador = self._determine_winner()
                await self.broadcast_state(extra={"ganador": ganador})

    # ---------- Bucle principal ----------
    async def _run_timer_loop(self):
        try:
            while True:
                if self.state is None:
                    break

                await self.check_players_count()
                await self.broadcast_state()
                await asyncio.sleep(0.1)
                self.current_time -= 0.1

                if self.current_time <= 0:
                    await self._transition_next_state()
        except asyncio.CancelledError:
            pass
        finally:
            self.timer_task = None
            # Si el estado es None y hay suficientes jugadores, iniciar nuevo ciclo
            if self.state is None and len(self.ws_manager.users) >= 2:
                await self.start_game_cycle()

    # ---------- Transiciones ----------
    async def _transition_next_state(self):
        if self.state == "waiting":
            self.state = "selecting"
            self.current_time = self.SELECTION_TIME
            self.ronda_actual = 0
            self.cards = random.sample(range(12), 9)
            await self.broadcast_state()
        elif self.state == "selecting":
            self.ronda_actual += 1
            if self.ronda_actual < self.SELECTION_ROUNDS:
                self.current_time = self.SELECTION_TIME
                await self.broadcast_state()
            else:
                self.state = "coding"
                self.current_time = self.CODING_TIME
                await self.broadcast_state()
        elif self.state == "coding":
            self.state = "playing"
            self.current_time = self.PLAYING_TIME
            await self.broadcast_state()
            asyncio.create_task(self.start_playing_phase())
        elif self.state == "playing":
            if self.sim_task:
                await self.sim_task
            self.state = "ending"
            self.current_time = self.ENDING_TIME
            ganador = self._determine_winner()
            await self.broadcast_state(extra={"ganador": ganador})
        elif self.state == "ending":
            self.state = None
            self.playing_users.clear()
            self.current_time = 0.0
            await self.broadcast_state()
            # No llamamos a start_game_cycle aquí; el finally del loop lo hará

    # ---------- Auxiliares ----------
    def _determine_winner(self) -> Optional[str]:
        alive = [u for u in self.playing_users.values()]
        if len(alive) == 1:
            return alive[0].name
        return None

    async def send_state_to_client(self, ws: WebSocket):
        """Envía el estado actual a un cliente específico."""
        payload : Dict[str, Any] = {
            "tipo": "game_state",
            "state": self.state,
            "tiempo_restante": round(self.current_time, 1),
            "ronda_actual": self.ronda_actual if self.state == "selecting" else 0,
            "jugadores_lobby": [{"id": u.id, "name": u.name} for u in self.get_lobby_users()],
            "jugadores_partida": [{"id": u.id, "name": u.name} for u in self.get_active_players()],
            "total_conectados": len(self.ws_manager.connections)
        }
        try:
            await ws.send_text(json.dumps(payload))
        except Exception:
            pass

    def set_user_powers(self, user_id: str, powers: List[int | None]):
        if user_id in self.playing_users:
            valid_powers = [p for p in powers if p != -1 and p is not None]
            self.playing_users[user_id].powers = valid_powers

    def all_codes_received(self) -> bool:
        for user in self.playing_users.values():
            if not hasattr(user, 'code') or user.code is None:
                return False
        return True

    async def start_playing_phase(self):
        if self.state != "playing":
            return

        if not self.current_map:
            return

        game_map = Map(
            width=self.current_map['width'],
            height=self.current_map['height'],
            obstacles=[tuple(ob) for ob in self.current_map.get('obstacles', [])]
        )

        spawns = self.current_map.get('spawn_points', [])

        tanks   : Dict[str, Tank] = {}
        spanw_index = 0

        for uid, user in self.playing_users.items():
            if spanw_index < len(spawns):
                sp = spawns[spanw_index]
                x = sp["x"]
                y = sp["y"]
                dir_str = sp.get("direction", "N")
                direction = Direction.from_string(dir_str)

            else:
                x = 2 + spanw_index * 3
                y = 2 + spanw_index * 3
                direction = Direction.NORTH

            tank = Tank(
                id=uid,
                name=user.name,
                x=x,
                y=y,
                direction=direction,
                cannon_direction=direction
            )

            if user.powers:
                tank.apply_powers(user.powers)
            tanks[uid] = tank
            spanw_index += 1

        codes = {uid: user.code for uid, user in self.playing_users.items() if user.code}

        self.sim_engine = SimulationEngine(game_map, tanks, codes)
        self.sim_engine.on_state_update = self._handle_state_update
        self.sim_engine.on_game_over = self._handle_game_over

        self.sim_task = asyncio.create_task(self.sim_engine.run(tick_rate=30, max_ticks=int(self.PLAYING_TIME * 30)))

    def _handle_state_update(self, state: Dict[str, Any]):
        asyncio.create_task(self._broadcast_state_async(state))

    async def _broadcast_state_async(self, state: Dict[str, Any]):
        payload : Dict[str, Any] = {
            "tipo": "game_state",
            "state": "playing",
            "tiempo_restante": self.current_time,
            "ronda_actual": self.ronda_actual,
            "jugadores_lobby": [{"id": u.id, "name": u.name} for u in self.get_lobby_users()],
            "jugadores_partida": [{"id": u.id, "name": u.name} for u in self.get_active_players()],
            "total_conectados": len(self.ws_manager.connections),
            "map": {
                "name": self.current_map.get("name") if self.current_map else "",
                "width": self.current_map.get("width") if self.current_map else 0,
                "height": self.current_map.get("height") if self.current_map else 0,
                "obstacles": self.current_map.get("obstacles", []) if self.current_map else [],
                "spawn_points": self.current_map.get("spawn_points", []) if self.current_map else []
            },
            "simulation": state
        }

        await self.ws_manager.broadcast(payload)

    def _handle_game_over(self, winner_id: Optional[str]):

        if self.sim_task and not self.sim_task.done():
            self.sim_task.cancel()
        self.sim_engine = None

        winner_name = self.playing_users[winner_id].name if winner_id and winner_id in self.playing_users else None
        self.state = "ending"
        self.current_time = self.ENDING_TIME
        asyncio.create_task(self.broadcast_state(extra={"ganador": winner_name}))