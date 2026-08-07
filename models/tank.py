from typing import List, Any
from .direction import Direction
from .power import get_powers_modifier, DEFAULT_MAX_HP, DEFAULT_SPEED, DEFAULT_BULLET_DAMAGE, DEFAULT_BULLET_SPEED, DEFAULT_BULLET_HITS, DEFAULT_BULLET_SPLASH, DEFAULT_FIRE_RATE, DEFAULT_RADAR_RANGE, DEFAULT_MAX_INTERRUPTS, DEFAULT_DAMAGE_RECEIVED, DEFAULT_HEALING

class Tank:
    def __init__(self, id: str, name: str, x: int = 0, y: int = 0,
                 direction: Direction = Direction.NORTH,
                 cannon_direction: Direction = Direction.NORTH):
        self.id = id
        self.name = name
        self.x = float(x)
        self.y = float(y)
        self.target_x = float(x)
        self.target_y = float(y)
        self.direction = direction
        self.cannon_direction = cannon_direction

        # Ángulos para interpolación
        self.angle = direction.angle()
        self.target_angle = self.angle
        self.cannon_angle = cannon_direction.angle()
        self.target_cannon_angle = self.cannon_angle

        # Stats base
        self.base_max_hp = DEFAULT_MAX_HP
        self.base_speed = DEFAULT_SPEED
        self.base_bullet_damage = DEFAULT_BULLET_DAMAGE
        self.base_bullet_speed = DEFAULT_BULLET_SPEED
        self.base_bullet_hits = DEFAULT_BULLET_HITS
        self.base_bullet_splash = DEFAULT_BULLET_SPLASH
        self.base_fire_rate = DEFAULT_FIRE_RATE
        self.base_radar_range = DEFAULT_RADAR_RANGE
        self.base_max_interrupts = DEFAULT_MAX_INTERRUPTS
        self.base_damage_received = DEFAULT_DAMAGE_RECEIVED
        self.base_healing = DEFAULT_HEALING

        # Stats actuales (serán modificados por poderes)
        self.max_hp = self.base_max_hp
        self.hp = self.max_hp
        self.speed = self.base_speed
        self.bullet_damage = self.base_bullet_damage
        self.bullet_speed = self.base_bullet_speed
        self.bullet_hits = self.base_bullet_hits
        self.bullet_splash = self.base_bullet_splash
        self.fire_rate = self.base_fire_rate
        self.radar_range = self.base_radar_range
        self.max_interrupts = self.base_max_interrupts
        self.damage_received = self.base_damage_received
        self.healing = self.base_healing

        self.interrupts_used = 0
        self.alive = True
        self.fire_cooldown = 0
        self.actions_queue: List[Any] = []
        self.message: str = ""

    def apply_powers(self, power_ids: List[int]):
        modifier = get_powers_modifier(power_ids)
        self.max_hp *= modifier.get("maxHpMultiplier", 1.0)
        self.speed *= modifier.get("speedMultiplier", 1.0)
        self.bullet_damage = max(1, self.bullet_damage + modifier.get("bulletDamageBoost", 0))
        self.bullet_speed *= modifier.get("bulletSpeedMultiplier", 1.0)
        self.bullet_hits += modifier.get("bulletHitsBoost", 0)
        self.bullet_splash += modifier.get("bulletSplashBoost", 0)
        self.fire_rate = max(1, self.fire_rate + modifier.get("fireRateBoost", 0))
        self.radar_range += modifier.get("radarRangeBoost", 0)
        self.max_interrupts += modifier.get("maxInterruptsBoost", 0)
        self.damage_received *= modifier.get("damageReceivedMultiplier", 1.0)
        self.healing += modifier.get("healingBoost", 0)
        self.hp = self.max_hp  # cura completa al aplicar

    def take_damage(self, damage: float):
        self.hp -= damage * self.damage_received
        if self.hp <= 0:
            self.hp = 0
            self.alive = False

    def can_interrupt(self) -> bool:
        return self.interrupts_used < self.max_interrupts

    def use_interrupt(self):
        self.interrupts_used += 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "x": self.x,
            "y": self.y,
            "targetX": self.target_x,
            "targetY": self.target_y,
            "direction": self.direction.value,
            "cannonDirection": self.cannon_direction.value,
            "angle": self.angle,
            "cannonAngle": self.cannon_angle,
            "hp": self.hp,
            "maxHp": self.max_hp,
            "alive": self.alive,
            "speed": self.speed,
            "radarRange": self.radar_range,
            "interruptsUsed": self.interrupts_used,
            "maxInterrupts": self.max_interrupts,
            "message": self.message
        }