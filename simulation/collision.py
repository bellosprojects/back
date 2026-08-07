from typing import List
from models.bullet import Bullet
from models.tank import Tank

class CollisionDetector:
    @staticmethod
    def check_single_bullet_tank_collision(bullet: Bullet, tanks: List[Tank]):
        if not bullet.active:
            return
        for tank in tanks:
            if not tank.alive:
                continue
            if bullet.owner_id == tank.id:
                continue
            if tank.id in bullet.hit_targets:
                continue
            # Hitbox AABB de 1x1
            if bullet.x >= tank.x and bullet.x <= tank.x + 1 and bullet.y >= tank.y and bullet.y <= tank.y + 1:
                tank.take_damage(bullet.damage)
                bullet.hit_targets.add(tank.id)
                bullet.hits -= 1
                if bullet.splash > 0:
                    CollisionDetector.apply_splash_damage(bullet.x, bullet.y, bullet, tanks)
                if bullet.hits <= 0:
                    bullet.active = False
                    break

    @staticmethod
    def apply_splash_damage(impact_x: float, impact_y: float, bullet: Bullet, tanks: List[Tank]):
        for tank in tanks:
            if tank.id == bullet.owner_id or not tank.alive:
                continue
            center_x = tank.x + 0.5
            center_y = tank.y + 0.5
            dist = ((center_x - impact_x) ** 2 + (center_y - impact_y) ** 2) ** 0.5
            if dist <= bullet.splash:
                tank.take_damage(bullet.damage)