from enum import Enum
import math

class Direction(Enum):
    NORTH = "N"
    SOUTH = "S"
    EAST = "E"
    WEST = "O"

    @staticmethod
    def from_string(value: str):
        mapping = {"N": Direction.NORTH, "S": Direction.SOUTH, "E": Direction.EAST, "O": Direction.WEST}
        return mapping.get(value, Direction.NORTH)

    def dx(self) -> int:
        return {Direction.NORTH: 0, Direction.SOUTH: 0, Direction.EAST: 1, Direction.WEST: -1}.get(self, 0)

    def dy(self) -> int:
        return {Direction.NORTH: -1, Direction.SOUTH: 1, Direction.EAST: 0, Direction.WEST: 0}.get(self, 0)

    def angle(self) -> float:
        return {Direction.NORTH: 0.0, Direction.EAST: math.pi/2, Direction.SOUTH: math.pi, Direction.WEST: 3*math.pi/2}.get(self, 0.0)