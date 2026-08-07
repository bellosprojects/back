from typing import List, Dict, Any

PowerModifier = Dict[str, int | float]
PowerDefinition = Dict[str, Any]

DEFAULT_MAX_HP = 100
DEFAULT_SPEED = 100
DEFAULT_BULLET_DAMAGE = 20
DEFAULT_BULLET_SPEED = 0.166
DEFAULT_BULLET_HITS : int = 1
DEFAULT_BULLET_SPLASH = 0
DEFAULT_FIRE_RATE = 10
DEFAULT_RADAR_RANGE = 5
DEFAULT_MAX_INTERRUPTS = 3
DEFAULT_DAMAGE_RECEIVED = 1.0
DEFAULT_HEALING = 0

def get_default_power_modifier() -> PowerModifier:
    """Devuelve un diccionario con los modificadores por defecto (sin poderes)."""
    return {
        "maxHpMultiplier": 1.0,
        "speedMultiplier": 1.0,
        "bulletDamageBoost": 0,
        "bulletSpeedMultiplier": 1.0,
        "bulletHitsBoost": 0,
        "bulletSplashBoost": 0,
        "fireRateBoost": 0,
        "radarRangeBoost": 0,
        "maxInterruptsBoost": 0,
        "damageReceivedMultiplier": 1.0,
        "healingBoost": 0
    }

ALL_POWERS: List[PowerDefinition] = [
    {
        "id": 0,
        "name": "Blindaje Juggernaut",
        "description": "Refuerza el chasis aumentando la Integridad Estructural (HP) inicial en un 50%.",
        "modifier": { "maxHpMultiplier": 1.5 }
    },
    {
        "id": 1,
        "name": "Motor Sobrealimentado",
        "description": "Inyecta óxido nitroso en las orugas, aumentando la velocidad de movimiento un 50%.",
        "modifier": { "speedMultiplier": 1.5 }
    },
    {
        "id": 2,
        "name": "Calibre Magnum",
        "description": "Cambia a munición de alto impacto. Tus proyectiles infligen +10 de daño base.",
        "modifier": { "bulletDamageBoost": 10 }
    },
    {
        "id": 3,
        "name": "Cañón de Riel (Railgun)",
        "description": "Acelera electromagnéticamente los proyectiles. Tus balas viajan al doble de velocidad.",
        "modifier": { "bulletSpeedMultiplier": 2 }
    },
    {
        "id": 4,
        "name": "Auto-Cargador Ligero",
        "description": "Optimiza los engranajes del cañón para disparar más rápido.",
        "modifier": { "fireRateBoost": 2 }
    },
    {
        "id": 5,
        "name": "Radar Doppler",
        "description": "Despeja la niebla de guerra aumentando el radio de escaneo en +3 casillas.",
        "modifier": { "radarRangeBoost": 3 }
    },
    {
        "id": 6,
        "name": "Reflejos Cibernéticos",
        "description": "Otorga 2 hilos de procesamiento extra para Interrupciones de Usuario (Eventos).",
        "modifier": { "maxInterruptsBoost": 2 }
    },
    {
        "id": 7,
        "name": "Matriz Defensiva",
        "description": "Despliega un escudo de energía pasivo que mitiga el 25% de todo el daño recibido.",
        "modifier": { "damageReceivedMultiplier": 0.75 }
    },
    {
        "id": 8,
        "name": "Nanobots de Reparación",
        "description": "Sistemas biotecnológicos reparan pasivamente +1 HP por cada Tick de acción.",
        "modifier": { "healingBoost": 1 }
    },
    {
        "id": 9,
        "name": "Proyectiles Perforantes (AP)",
        "description": "Balas con punta de tungsteno capaces de atravesar al primer objetivo impactado.",
        "modifier": { "bulletHitsBoost": 1 }
    },
    {
        "id": 10,
        "name": "Ojivas Explosivas (AoE)",
        "description": "Los proyectiles detonan al impactar, causando daño en área (+1 casilla) y +5 de daño directo.",
        "modifier": { "bulletDamageBoost": 5, "bulletSplashBoost": 1 }
    },
    {
        "id": 11,
        "name": "Modo Artillería",
        "description": "Sacrifica cadencia de tiro por potencia bruta. Daño masivo (+20) pero ataques lentos.",
        "modifier": { "fireRateBoost": -5, "bulletDamageBoost": 20 }
    },
    {
        "id": 12,
        "name": "Cañón Gatling",
        "description": "Lluvia de balas. Aumenta drásticamente la cadencia de fuego a cambio de menor daño por impacto.",
        "modifier": { "fireRateBoost": 5, "bulletDamageBoost": -5 }
    }
]

def get_powers_modifier(powersIds: List[int]) -> PowerModifier:
    """Dado un listado de IDs de poderes, devuelve un diccionario con los modificadores combinados."""
    combined_modifier: PowerModifier = get_default_power_modifier()
    for power_id in powersIds:
        power = next((p for p in ALL_POWERS if p["id"] == power_id), None)
        if power:
            modifier = power["modifier"]
            combined_modifier["maxHpMultiplier"] *= modifier.get("maxHpMultiplier", 1.0)
            combined_modifier["speedMultiplier"] *= modifier.get("speedMultiplier", 1.0)
            combined_modifier["bulletDamageBoost"] += modifier.get("bulletDamageBoost", 0)
            combined_modifier["bulletSpeedMultiplier"] *= modifier.get("bulletSpeedMultiplier", 1.0)
            combined_modifier["bulletHitsBoost"] += modifier.get("bulletHitsBoost", 0)
            combined_modifier["bulletSplashBoost"] += modifier.get("bulletSplashBoost", 0)
            combined_modifier["fireRateBoost"] += modifier.get("fireRateBoost", 0)
            combined_modifier["radarRangeBoost"] += modifier.get("radarRangeBoost", 0)
            combined_modifier["maxInterruptsBoost"] += modifier.get("maxInterruptsBoost", 0)
            combined_modifier["damageReceivedMultiplier"] *= modifier.get("damageReceivedMultiplier", 1.0)
            combined_modifier["healingBoost"] += modifier.get("healingBoost", 0)

    return combined_modifier