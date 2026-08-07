from typing import List, Dict
from models.bullet import Bullet
from models.map import Map
from models.tank import Tank
from .collision import CollisionDetector

class BulletManager:
    def __init__(self):
        self.collision = CollisionDetector()

    def update_bullets(self, bullets: List[Bullet], game_map: Map, tanks: Dict[str, Tank]):
        alive_tanks = [t for t in tanks.values() if t.alive]
        for bullet in bullets:
            if not bullet.active:
                continue
            # Movimiento por pasos para evitar colisiones rápidas
            total_dx = bullet.dx * bullet.speed
            total_dy = bullet.dy * bullet.speed
            total_dist = (total_dx ** 2 + total_dy ** 2) ** 0.5
            steps = max(1, int(total_dist / 0.25) + 1)
            step_x = total_dx / steps
            step_y = total_dy / steps
            for _ in range(steps):
                bullet.x += step_x
                bullet.y += step_y
                # Colisión con tanques
                self.collision.check_single_bullet_tank_collision(bullet, alive_tanks)
                if not bullet.active:
                    break
                # Colisión con mapa
                grid_x = int(bullet.x)
                grid_y = int(bullet.y)
                if not game_map.is_within_bounds(grid_x, grid_y) or game_map.is_obstacle(grid_x, grid_y):
                    if bullet.splash > 0:
                        self.collision.apply_splash_damage(bullet.x, bullet.y, bullet, alive_tanks)
                    bullet.active = False
                    break