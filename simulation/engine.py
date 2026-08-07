import asyncio
import math
from typing import Dict, List, Optional, Callable, Any
from models.tank import Tank
from models.bullet import Bullet
from models.map import Map
from models.direction import Direction
from models.power import DEFAULT_FIRE_RATE, DEFAULT_SPEED
from .bullet_manager import BulletManager

class SimulationEngine:
    def __init__(self, game_map: Map, tanks: Dict[str, Tank], player_codes: Dict[str, Any]):
        from .interpreter import ASTInterpreter
        self.game_map = game_map
        self.tanks = tanks
        self.bullets: List[Bullet] = []
        self.tick = 0
        self.running = False
        self.bullet_manager = BulletManager()
        self.interpreters: Dict[str, ASTInterpreter] = {}
        for uid, code in player_codes.items():
            if uid in tanks:
                self.interpreters[uid] = ASTInterpreter(code, uid, self)
        self.on_state_update: Optional[Callable[[Dict[str, Any]], None]] = None
        self.on_game_over: Optional[Callable[[Optional[str]], None]] = None

    async def run(self, tick_rate: float = 30, max_ticks: int = 3000):
        self.running = True
        action_interval = 3  # ejecutar acciones cada 3 ticks (equivalente a actionTickRate)
        action_counter = 0
        while self.running and self.tick < max_ticks:
            start = asyncio.get_event_loop().time()
            self._update_physics()
            action_counter += 1
            if action_counter % action_interval == 0:
                self._update_actions()
            self.tick += 1
            if self.on_state_update:
                self.on_state_update(self.get_state())
            # Verificar fin de partida
            alive = [t for t in self.tanks.values() if t.alive]
            if len(alive) <= 1:
                winner = alive[0].id if alive else None
                if self.on_game_over:
                    self.on_game_over(winner)
                break
            elapsed = asyncio.get_event_loop().time() - start
            sleep_time = max(0, (1.0 / tick_rate) - elapsed)
            await asyncio.sleep(sleep_time)
        self.running = False

    def _update_physics(self):
        self.bullet_manager.update_bullets(self.bullets, self.game_map, self.tanks)
        self.bullets = [b for b in self.bullets if b.active]
        for tank in self.tanks.values():
            # Interpolación suave hacia destino
            tank.x += (tank.target_x - tank.x) * 0.12
            tank.y += (tank.target_y - tank.y) * 0.12
            if abs(tank.target_x - tank.x) < 0.005:
                tank.x = tank.target_x
            if abs(tank.target_y - tank.y) < 0.005:
                tank.y = tank.target_y
            # Lerp de ángulos
            tank.angle = self._lerp_angle(tank.angle, tank.target_angle, 0.3)
            tank.cannon_angle = self._lerp_angle(tank.cannon_angle, tank.target_cannon_angle, 0.3)

    def _lerp_angle(self, current: float, target: float, t: float) -> float:
        diff = target - current
        while diff < -math.pi:
            diff += 2*math.pi
        while diff > math.pi:
            diff -= 2*math.pi
        return current + diff * t

    def _update_actions(self):
        for interpreter in self.interpreters.values():
            interpreter.step()
        for tank in self.tanks.values():
            if tank.fire_cooldown > 0:
                tank.fire_cooldown -= 1
            if tank.alive and tank.healing > 0:
                tank.hp = min(tank.max_hp, tank.hp + tank.healing)
            self._process_actions(tank)

    def _process_actions(self, tank: Tank):
        if not tank.actions_queue or not tank.alive:
            return
        action = tank.actions_queue.pop(0)
        cmd = action.get("type")
        if cmd == "mover":
            self._execute_move(tank, action.get("direction", "adelante"))
        elif cmd == "girar_tanque":
            self._execute_turn_tank(tank, action.get("direction"))
        elif cmd == "girar_cañon":
            self._execute_turn_cannon(tank, action.get("direction"))
        elif cmd == "disparar":
            self._execute_fire(tank)
        elif cmd == "apuntar_enemigo":
            self._execute_aim(tank)
        elif cmd == "saltar":
            self._execute_jump(tank)
        elif cmd == "set_message":
            # ya se asignó en el intérprete
            pass

    def _execute_move(self, tank: Tank, direction: str):
        target_dir = self._resolve_direction(tank.direction, direction)
        dx = target_dir.dx()
        dy = target_dir.dy()
        steps = max(1, int(tank.speed / DEFAULT_SPEED))
        new_x = int(tank.target_x)
        new_y = int(tank.target_y)
        for _ in range(steps):
            nx = new_x + dx
            ny = new_y + dy
            if not self.game_map.is_within_bounds(nx, ny):
                break
            if self.game_map.is_obstacle(nx, ny):
                tank.take_damage(10)
                break
            blocked = False
            for other in self.tanks.values():
                if other.id == tank.id: continue
                if int(other.target_x) == nx and int(other.target_y) == ny:
                    blocked = True
                    break
            if blocked:
                break
            new_x = nx
            new_y = ny
        tank.direction = target_dir
        tank.target_angle = target_dir.angle()
        tank.target_x = float(new_x)
        tank.target_y = float(new_y)

    def _resolve_direction(self, current: Direction, direction: str) -> Direction:
        dirs = [Direction.NORTH, Direction.EAST, Direction.SOUTH, Direction.WEST]
        idx = dirs.index(current)
        if direction == "adelante":
            return current
        elif direction == "atras":
            return dirs[(idx + 2) % 4]
        elif direction == "izquierda":
            return dirs[(idx + 3) % 4]
        elif direction == "derecha":
            return dirs[(idx + 1) % 4]
        else:
            # Si es cardinal directo
            try:
                return Direction.from_string(direction)
            except:
                return current

    def _execute_turn_tank(self, tank: Tank, direction: str):
        dirs = [Direction.NORTH, Direction.EAST, Direction.SOUTH, Direction.WEST]
        idx = dirs.index(tank.direction)
        if direction == "izquierda":
            new_idx = (idx + 3) % 4
        elif direction == "derecha":
            new_idx = (idx + 1) % 4
        else:
            return
        new_dir = dirs[new_idx]
        # Ajustar cañón relativo
        cannon_idx = dirs.index(tank.cannon_direction)
        rel = (cannon_idx - idx) % 4
        tank.direction = new_dir
        tank.target_angle = new_dir.angle()
        tank.cannon_direction = dirs[(new_idx + rel) % 4]
        tank.target_cannon_angle = tank.cannon_direction.angle()

    def _execute_turn_cannon(self, tank: Tank, direction: str):
        dirs = [Direction.NORTH, Direction.EAST, Direction.SOUTH, Direction.WEST]
        tank_idx = dirs.index(tank.direction)
        cannon_idx = dirs.index(tank.cannon_direction)
        rel = (cannon_idx - tank_idx) % 4
        if direction == "izquierda":
            rel = (rel + 3) % 4
        elif direction == "derecha":
            rel = (rel + 1) % 4
        elif direction == "atras":
            rel = (rel + 2) % 4
        elif direction == "adelante":
            rel = 0
        else:
            # intentar cardinal directo
            try:
                target = Direction.from_string(direction)
                target_idx = dirs.index(target)
                rel = (target_idx - tank_idx) % 4
            except:
                return
        tank.cannon_direction = dirs[(tank_idx + rel) % 4]
        tank.target_cannon_angle = tank.cannon_direction.angle()

    def _execute_fire(self, tank: Tank):
        if not tank.alive or tank.fire_cooldown > 0:
            return
        dx = tank.cannon_direction.dx()
        dy = tank.cannon_direction.dy()
        bullet = Bullet(
            owner_id=tank.id,
            x=tank.x + 0.5 + dx * 0.5,
            y=tank.y + 0.5 + dy * 0.5,
            dx=dx,
            dy=dy,
            speed=tank.bullet_speed,
            damage=tank.bullet_damage,
            hits=int(tank.bullet_hits),
            splash=tank.bullet_splash
        )
        self.bullets.append(bullet)
        tank.fire_cooldown = max(1, int(DEFAULT_FIRE_RATE / tank.fire_rate))

    def _execute_aim(self, tank: Tank):
        other_tanks = [t for t in self.tanks.values() if t.id != tank.id and t.alive]
        if not other_tanks:
            return
        closest = min(other_tanks, key=lambda t: abs(t.x - tank.x) + abs(t.y - tank.y))
        dx = closest.x - tank.x
        dy = closest.y - tank.y
        if abs(dx) > abs(dy):
            tank.cannon_direction = Direction.EAST if dx > 0 else Direction.WEST
        else:
            tank.cannon_direction = Direction.SOUTH if dy > 0 else Direction.NORTH
        tank.target_cannon_angle = tank.cannon_direction.angle()

    def _execute_jump(self, tank: Tank):
        dx = tank.direction.dx()
        dy = tank.direction.dy()
        nx = int(tank.target_x) + dx * 2
        ny = int(tank.target_y) + dy * 2
        if not self.game_map.is_within_bounds(nx, ny) or self.game_map.is_obstacle(nx, ny):
            return
        for other in self.tanks.values():
            if other.id == tank.id: continue
            if int(other.target_x) == nx and int(other.target_y) == ny:
                return
        tank.target_x = float(nx)
        tank.target_y = float(ny)

    def get_state(self) -> Any:
        return {
            "tick": self.tick,
            "tanks": [t.to_dict() for t in self.tanks.values()],
            "bullets": [b.to_dict() for b in self.bullets if b.active],
            "mapWidth": self.game_map.width,
            "mapHeight": self.game_map.height,
            "obstacles": self.game_map.obstacles,
        }