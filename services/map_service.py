import json
import random
import os
from typing import List, Dict, Any, Optional

class MapService:

    def __init__(self, maps_dir: str = "data/maps"):
        self.maps_dir = maps_dir
        self.maps_cache : List[Dict[str, Any]] = []
        self._load_all_maps()

    def _load_all_maps(self):

        if not os.path.exists(self.maps_dir):
            os.makedirs(self.maps_dir)
            self._create_example_map()

        self.maps_cache = []
        for filename in os.listdir(self.maps_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(self.maps_dir, filename)
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                        self.maps_cache.append(data)
                except Exception as e:
                    print(f"Error cargando mapa {filename}: {e}")

        if not self.maps_cache:
            self._create_example_map()
            self._load_all_maps()

    def _create_example_map(self):
        """Crea un mapa de ejemplo si el directorio está vacío."""
        example : Dict[str, Any] = {
            "name": "Arena Básica",
            "width": 20,
            "height": 20,
            "obstacles": [
                [5, 5], [5, 6], [6, 5],
                [10, 10], [10, 11], [11, 10],
                [15, 3], [15, 4], [16, 3]
            ],
            "spawn_points": [
                {"x": 2, "y": 2, "direction": "S"},
                {"x": 17, "y": 17, "direction": "N"}
            ]
        }
        filepath = os.path.join(self.maps_dir, "map_example.json")
        with open(filepath, 'w') as f:
            json.dump(example, f, indent=2)
        print(f"mapa de ejemplo creado en {filepath}")

    def get_map_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        for map_data in self.maps_cache:
            if map_data.get('name') == name:
                return map_data

        return None

    def get_map_count(self) -> int:
        return len(self.maps_cache)

    def get_random_map(self) -> Dict[str, Any]:
        if not self.maps_cache:
            raise ValueError("No hay mapas disponibles")
        return random.choice(self.maps_cache)