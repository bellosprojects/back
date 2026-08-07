from typing import Any, List, Optional, Dict, cast
from simulation.engine import SimulationEngine

class ASTInterpreter:
    def __init__(self, ast: Any, player_id: str, engine: SimulationEngine):
        self.ast = ast
        self.player_id = player_id
        self.engine = engine
        self.threads: List[Any] = []  # cada thread: {stack: [{"program": list, "pc": int, "loop": optional}], variables: Any, running: bool}
        self.last_closest_enemy_id: Optional[str] = None
        # Disparar evento init
        self.trigger_event("init")

    def trigger_event(self, event_name: str):
        if event_name == "keyInterrupt":
            tank = self.engine.tanks.get(self.player_id)
            if not tank or not tank.can_interrupt():
                return
            tank.use_interrupt()
        events = [e for e in self.ast.get("eventos", []) if e.get("trigger") == event_name]
        for ev in events:
            self.threads.append({
                "stack": [{"program": ev.get("entonces", []), "pc": 0, "loop": None}],
                "variables": {},
                "running": True
            })

    def check_enemy_entries(self):
        tank = self.engine.tanks.get(self.player_id)
        if not tank or not tank.alive:
            return
        other_tanks = [t for t in self.engine.tanks.values() if t.id != self.player_id and t.alive]
        # Filtrar por radar
        in_radar = [t for t in other_tanks if abs(t.x - tank.x) + abs(t.y - tank.y) <= tank.radar_range]
        in_radar.sort(key=lambda t: abs(t.x - tank.x) + abs(t.y - tank.y))
        current_closest = in_radar[0].id if in_radar else None
        if current_closest != self.last_closest_enemy_id:
            self.last_closest_enemy_id = current_closest
            if current_closest is not None:
                self.trigger_event("enemy_entries")

    def step(self):
        self.check_enemy_entries()
        for thread in self.threads:
            if not thread["running"]:
                continue
            action_executed = False
            safety = 0
            while thread["running"] and not action_executed and safety < 1000:
                action_executed = self._execute_next(thread)
                safety += 1
            if safety >= 1000:
                print(f"Bucle infinito en {self.player_id}")
                thread["running"] = False
        self.threads = [t for t in self.threads if t["running"]]

    def _execute_next(self, thread: Any) -> bool:
        stack = thread["stack"]
        if not stack:
            thread["running"] = False
            return False
        ctx = stack[-1]
        if ctx["pc"] >= len(ctx["program"]):
            # Fin del bloque
            if ctx["loop"] is not None:
                # Evaluar condición del while
                cond = self._evaluate_expression(thread, ctx["loop"]["condicion"])
                if cond:
                    ctx["pc"] = 0  # reiniciar
                    return False
            stack.pop()
            if not stack:
                thread["running"] = False
            return False
        instr = ctx["program"][ctx["pc"]]
        ctx["pc"] += 1
        tipo = instr.get("tipo")
        if tipo == "accion":
            return self._execute_action(thread, instr)
        elif tipo == "if":
            self._execute_if(thread, instr)
            return False
        elif tipo == "while":
            self._execute_while(thread, instr)
            return False
        elif tipo == "break":
            self._execute_break(thread)
            return False
        elif tipo == "asignacion":
            self._execute_assignment(thread, instr)
            return False
        else:
            print(f"Instrucción no soportada: {instr}")
            return False

    def _execute_action(self, thread: Any, instr: Any) -> bool:
        tank = self.engine.tanks.get(self.player_id)
        if not tank:
            return False
        action = {"type": instr.get("comando"), "direction": instr.get("direccion")}
        if instr.get("comando") == "set_message" and "valor" in instr:
            val = self._evaluate_expression(thread, instr["valor"])
            action["value"] = str(val) if val is not None else ""
            tank.message = action["value"]
        tank.actions_queue.append(action)
        return True

    def _execute_if(self, thread: Any, instr: Any):
        cond = self._evaluate_condition(thread, instr.get("condicion"))
        block = instr.get("entonces", []) if cond else instr.get("sino", [])
        if block:
            thread["stack"].append({"program": block, "pc": 0, "loop": None})

    def _execute_while(self, thread: Any, instr: Any):
        cond = self._evaluate_condition(thread, instr.get("condicion"))
        if cond and instr.get("hacer"):
            thread["stack"].append({"program": instr["hacer"], "pc": 0, "loop": {"condicion": instr["condicion"]}})

    def _execute_break(self, thread: Any):
        while thread["stack"]:
            ctx = thread["stack"].pop()
            if ctx.get("loop") is not None:
                break
        if not thread["stack"]:
            thread["running"] = False

    def _execute_assignment(self, thread: Any, instr: Any):
        name = instr.get("nombre", "")
        value = self._evaluate_expression(thread, instr.get("valor"))
        thread["variables"][name] = value

    def _evaluate_condition(self, thread: Any, cond: Any) -> bool:
        if cond is None:
            return False
        return bool(self._evaluate_expression(thread, cond))

    def _evaluate_expression(self, thread: Any, expr: Any) -> Any:
        if expr is None:
            return None
        tipo = expr.get("tipo")
        if tipo == "valor":
            return expr.get("valor")
        elif tipo == "variable":
            return thread["variables"].get(expr.get("nombre"))
        elif tipo == "operador":
            left = self._evaluate_expression(thread, expr.get("izquierda"))
            right = self._evaluate_expression(thread, expr.get("derecha")) if "derecha" in expr else None
            op = expr.get("operador")
            if op == "+":
                if isinstance(left, (int, float)) and isinstance(right, (int, float)):
                    return left + right
                return str(left) + str(right) if left is not None and right is not None else None
            elif op == "-":
                return left - right if isinstance(left, (int, float)) and isinstance(right, (int, float)) else None
            elif op == "*":
                return left * right if isinstance(left, (int, float)) and isinstance(right, (int, float)) else None
            elif op == "/":
                if right == 0: return None
                return left / right if isinstance(left, (int, float)) and isinstance(right, (int, float)) else None
            elif op == "==":
                return left == right
            elif op == "!=":
                return left != right
            elif op == ">":
                return left > right
            elif op == "<":
                return left < right
            elif op == ">=":
                return left >= right
            elif op == "<=":
                return left <= right
            elif op == "and":
                return left and right
            elif op == "or":
                return left or right
            elif op == "not":
                return not left
            else:
                return None
        elif tipo == "acceso_propiedad":
            obj = self._evaluate_expression(thread, expr.get("objeto"))
            if obj and isinstance(obj, dict) and "propiedad" in expr:
                prop = expr.get("propiedad")
                # cast obj to a typed dict to satisfy type checkers
                return cast(Dict[str, Any], obj).get(prop, None)
            return None
        elif tipo == "entorno":
            return self._evaluate_environment(expr, thread)
        else:
            return None

    def _evaluate_environment(self, env: Any, thread: Any) -> Any:
        tank = self.engine.tanks.get(self.player_id)
        if not tank:
            return None
        other_tanks = [t for t in self.engine.tanks.values() if t.id != self.player_id and t.alive]
        consulta = env.get("consulta")
        if consulta == "me":
            return {"x": tank.x, "y": tank.y, "hp": tank.hp, "name": tank.name, "message": tank.message}
        elif consulta == "enemigo_mas_cercano":
            if not other_tanks:
                return None
            closest = min(other_tanks, key=lambda t: abs(t.x - tank.x) + abs(t.y - tank.y))
            dist = abs(closest.x - tank.x) + abs(closest.y - tank.y)
            if dist > tank.radar_range:
                return None
            return {"x": closest.x, "y": closest.y, "hp": closest.hp, "name": closest.name, "message": closest.message}
        elif consulta == "pared_en_frente":
            dx = tank.direction.dx()
            dy = tank.direction.dy()
            nx = int(tank.x + dx)
            ny = int(tank.y + dy)
            return self.engine.game_map.is_wall(nx, ny)
        elif consulta == "obstaculo_en_frente":
            dx = tank.direction.dx()
            dy = tank.direction.dy()
            nx = int(tank.x + dx)
            ny = int(tank.y + dy)
            if self.engine.game_map.is_obstacle(nx, ny):
                return True
            for t in other_tanks:
                if int(t.x) == nx and int(t.y) == ny:
                    return True
            return False
        elif consulta == "enemigo_visible":
            if not other_tanks:
                return False
            closest = min(other_tanks, key=lambda t: abs(t.x - tank.x) + abs(t.y - tank.y))
            return (abs(closest.x - tank.x) + abs(closest.y - tank.y)) <= tank.radar_range
        elif consulta == "estoy_bajo_fuego":
            # Por ahora siempre False (se puede implementar si se guarda historial de daños)
            return False
        elif consulta == "cantidad_enemigos":
            return len([t for t in other_tanks if abs(t.x - tank.x) + abs(t.y - tank.y) <= tank.radar_range])
        return None