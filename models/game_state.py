from typing import List, Tuple, Any
from .tank import Tank
from .bullet import Bullet

class GameState:

    def __init__(
        self,
        tick: int,
        tanks: List[Tank],
        bullets: List[Bullet],
        map_width: int,
        map_height: int,
        obstacles: List[Tuple[int]]
    ):
        self.tick = tick
        self.tanks = tanks
        self.bullets = bullets
        self.map_width = map_width
        self.map_height = map_height
        self.obstacles = obstacles

    def to_dict(self) -> dict[str, Any]:

        return {
            "tick": self.tick,
            "tanks": [
                {
                    "id": t.id,
                    "name": t.name,
                    "x": t.x,
                    "y": t.y,
                    "direction": t.direction.value,
                    "cannon_direction": t.cannon_direction.value,
                    "hp": t.hp,
                    "max_hp": t.max_hp,
                    "alive": t.alive,
                    "speed": t.speed,
                    "radar_range": t.radar_range,
                    "interrupts_used": t.interrupts_used,
                    "max_interrupts": t.max_interrupts
                }
                for t in self.tanks
            ],
            "bullets": [
                {
                    "owner_id": b.owner_id,
                    "x": b.x,
                    "y": b.y,
                    "dx": b.dx,
                    "dy": b.dy,
                    "active": b.active,
                    "speed": b.speed
                }
                for b in self.bullets
            ],
            "map": {
                "width": self.map_width,
                "height": self.map_height,
                "obstacles": self.obstacles 
            }
        }