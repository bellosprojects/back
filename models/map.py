from typing import List, Tuple

class Map:
    def __init__(self, width: int, height: int, obstacles: List[Tuple[int, int]]):
        self.width = width
        self.height = height
        self.obstacles = obstacles

    def is_obstacle(self, x: int, y: int) -> bool:
        return (x, y) in self.obstacles

    def is_wall(self, x: int, y: int) -> bool:
        return x < 0 or x >= self.width or y < 0 or y >= self.height

    def is_within_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height