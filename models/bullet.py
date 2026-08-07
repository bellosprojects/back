from typing import Any

class Bullet:
    def __init__(self, owner_id: str, x: float, y: float, dx: float, dy: float,
                 speed: float, damage: float, hits: int = 1, splash: float = 0):
        self.owner_id = owner_id
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.speed = speed
        self.damage = damage
        self.hits = hits
        self.splash = splash
        self.active = True
        self.hit_targets : set[str] = set()

    def update(self):
        self.x += self.dx * self.speed
        self.y += self.dy * self.speed

    def to_dict(self) -> dict[str, Any]:
        return {
            "ownerId": self.owner_id,
            "x": self.x,
            "y": self.y,
            "dx": self.dx,
            "dy": self.dy,
            "active": self.active,
            "hits": self.hits,
            "splash": self.splash,
        }