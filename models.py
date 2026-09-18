from typing import Dict, List, Optional
import heapq


class Valid_List:

    valid_hubs = {"hub:", "start_hub:", "end_hub:"}

    valid_zones = {"normal", "blocked", "restricted", "priority"}

    zone_costs = {
        "priority": 1, "normal": 1, "restricted": 2, "blocked": 999999
                  }

    valid_colors = {
        "green": "\033[32m",
        "yellow": "\033[33m",
        "red": "\033[31m",
        "blue": "\033[34m",
        "cyan": "\033[36m",
        "magenta": "\033[35m",
        "white": "\033[37m",
        "purple": "\033[35;1m",
        "orange": "\033[38;5;208m",
        "brown": "\033[38;5;130m",
        "maroon": "\033[38;5;88m",
        "black": "\033[90m",
        "gold": "\033[33;1m",
        "violet": "\033[35;1m",
        "crimson": "\033[31;1m",
        "darkred": "\033[31m",
        "rainbow": "\033[36;1m",
        "lime": "\033[38;5;118m",
        "gray": "\033[38;5;244m",
        "marron": "\033[38;5;88m",
        "darked": "\033[38;5;52m"
    }

    @classmethod
    def check_zone(cls, zone: str) -> None:
        if zone not in cls.valid_zones:
            raise ValueError(f"Zona no válida: '{zone}'")


class Hub:
    def __init__(
            self, name: str, x: int, y: int, zo_type: str = "normal",
            color: str = "none", hub_type: str = "normal",
            max_drones: int = 1) -> None:

        self.name: str = name
        self.x: int = x
        self.y: int = y
        self.zo_type: str = zo_type
        self.color: str = color
        self.hub_type: str = hub_type
        self.max_drones: int = max_drones

    def __repr__(self) -> str:
        return f"Hub({self.name})"


class Connection:
    def __init__(
            self, name: str, zone1: Hub, zone2: Hub, capacity: int = 1
            ) -> None:

        self.name: str = name
        self.zone1: Hub = zone1
        self.zone2: Hub = zone2
        self.capacity: int = capacity

    def _key(self) -> frozenset:
        return frozenset({self.zone1.name, self.zone2.name})

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Connection):
            return NotImplemented
        return self._key() == other._key()

    def __hash__(self) -> int:
        return hash(self._key())


class Drone:
    def __init__(self, id_drone: str, curr_loc: Hub) -> None:
        self.id: str = id_drone
        self.location: Hub | Connection = curr_loc
        self.in_transit: bool = False
        self.turn: int = 0
        self.has_arrived: bool = False

    def get_drone_info(self) -> None:
        print(f"Drone_id: {self.id}")
        print(
            f"Drone location: "
            f"{self.location.name if self.location else 'None'}"
            )
        print(f"In transit: {self.in_transit}")
        print(f"Turn number: {self.turn}")
        print(f"Has arrived?: {self.has_arrived}")


class Drone_Map:
    def __init__(self) -> None:
        self.hubs: Dict[str, Hub] = {}
        self.connections: list[Connection] = []
        self.start_hub: Optional[Hub] = None
        self.end_hub: Optional[Hub] = None
        self.used_coords: set = set()

    def add_hub(self, hub: Hub) -> None:
        if hub.name in self.hubs:
            raise ValueError(f"Error: El Hub con nombre '{hub.name}' ya existe.")

        if (hub.x, hub.y) in self.used_coords:
            raise ValueError(f"Error: ya existe un hub en la coordenada ({hub.x}, {hub.y}).")

        if hub.hub_type == "start" and self.start_hub is not None:
            raise ValueError("Error: ya existe un start_hub.")

        if hub.hub_type == "end" and self.end_hub is not None:
            raise ValueError("Error: ya existe un end_hub.")

        self.hubs[hub.name] = hub
        self.used_coords.add((hub.x, hub.y))

        if hub.hub_type == "start":
            self.start_hub = hub
        elif hub.hub_type == "end":
            self.end_hub = hub

    def add_connection(self, connection: Connection) -> None:
        if connection not in self.connections:
            self.connections.append(connection)
        else:
            raise ValueError(f"Error: La conexion '{connection.name}' ya existe")

    def get_neightbors(self, hub: Hub) -> list[tuple[Hub, Connection]]:

        neightbors = []
        for conn in self.connections:
            if conn.zone1.name == hub.name:
                neightbors.append((conn.zone2, conn))

            elif conn.zone2.name == hub.name:
                neightbors.append((conn.zone1, conn))

        return neightbors


class Solver:
    def __init__(self, drone_map: Drone_Map, drones_number: int) -> None:
        self.map: Drone_Map = drone_map
        self.curr_turn: int = 0
        self.history: list = []
        self._reservaion_table = ReservationTable()

        self.drones: list[Drone] = [
            Drone(f"D{i}", self.map.start_hub)
            for i in range(1, drones_number + 1)
        ]

    def print_simulation_output(self, total_paths: list[tuple[Drone, list[tuple[Hub, int]]]]) -> None:
        """Imprime la simulación turno a turno con contador explícito."""
        moves_by_turn: dict[int, list[str]] = {}

        for drone, path in total_paths:
            for i in range(1, len(path)):
                hub, turn = path[i]
                prev_hub, _ = path[i - 1]

                if hub.name != prev_hub.name:
                    if turn not in moves_by_turn:
                        moves_by_turn[turn] = []
                    moves_by_turn[turn].append(f"{drone.id}-{hub.name}")

        if not moves_by_turn:
            return

        max_turn = max(moves_by_turn.keys())
        for turn in range(1, max_turn + 1):
            moves = moves_by_turn.get(turn, [])
            moves_str = " ".join(moves) if moves else "(Sin movimientos)"
            print(f"Turno {turn:02d}: \n {moves_str}\n")
        print(f"--- TOTAL TURNOS: {max_turn} ---\n")

    def get_drones_in_hub(self, hub: Hub) -> int:
        return sum(1 for d in self.drones if d.location == hub)

    def get_drones_in_con(self, conn: Connection) -> int:
        return sum(1 for d in self.drones if d.location == conn)

    def can_move_hub(self, hub: Hub) -> bool:
        return self.get_drones_in_hub(hub) < hub.max_drones

    def can_move_conn(self, conn: Connection) -> bool:
        return self.get_drones_in_con(conn) < conn.capacity

    def get_move_costs(
            self, from_hub: Hub, to_hub: Hub, conn: Connection
            ) -> int:
        if to_hub.zo_type == "blocked":
            return 999999
        return Valid_List.zone_costs.get(to_hub.zo_type, 1)

    def run(self) -> None:
        print(f"\n--- Iniciando simulación con {len(self.drones)} drones ---")
        self._reservaion_table.clear()
        total_paths = []

        for drone in self.drones:
            path = self.find_path(self.map.start_hub, self.map.end_hub)
            if path:
                self.add_path(path)
                total_paths.append((drone, path))

        self.print_simulation_output(total_paths)

    def find_path(self, start: Hub, end: Hub, start_turn: int = 0) -> Optional[List[tuple[Hub, int]]]:
    # Estrcutura en la cola de prioridad:
    # (coste_total, turno_actual, id(hub_actual), hub_actual, camino_recorrido)
    # Nota: id(curr_hub) evita errores de comparación entre objetos Hub en heapq.
        queue: List[tuple[float, int, int, Hub, List[tuple[Hub, int]]]] = [
            (0.0, start_turn, id(start), start, [(start, start_turn)])
        ]
        
        # Registro del menor costo encontrado para un (hub_name, turn)
        min_cost: Dict[tuple[str, int], float] = {(start.name, start_turn): 0.0}

        while queue:
            curr_cost, curr_turn, _, curr_hub, path = heapq.heappop(queue)

            # Meta alcanzada
            if curr_hub.name == end.name:
                return path

            # Si ya encontramos una ruta más barata para este mismo estado, ignoramos
            if curr_cost > min_cost.get((curr_hub.name, curr_turn), float('inf')):
                continue

            # 1. OPCIÓN A: Moverse a nodos vecinos (Prioridad máxima)
            for neighbor_hub, connection in self.map.get_neightbors(curr_hub):
                step_cost = self.get_move_costs(curr_hub, neighbor_hub, connection)
                if step_cost >= 999999:  # Nodo bloqueado o inalcanzable
                    continue

                next_turn = curr_turn + step_cost
                link_ok = self._reservaion_table.link_available(connection, curr_turn)
                hub_ok = self._reservaion_table.hub_available(neighbor_hub, next_turn)

                if link_ok and hub_ok:
                    new_cost = curr_cost + step_cost
                    if new_cost < min_cost.get((neighbor_hub.name, next_turn), float('inf')):
                        min_cost[(neighbor_hub.name, next_turn)] = new_cost
                        heapq.heappush(
                            queue, 
                            (new_cost, next_turn, id(neighbor_hub), neighbor_hub, path + [(neighbor_hub, next_turn)])
                        )

            if curr_hub.hub_type != "end":
                next_turn = curr_turn + 1
                if self._reservaion_table.hub_available(curr_hub, next_turn):
                    wait_cost = curr_cost + 1.0001
                    if wait_cost < min_cost.get((curr_hub.name, next_turn), float('inf')):
                        min_cost[(curr_hub.name, next_turn)] = wait_cost
                        heapq.heappush(
                            queue, 
                            (wait_cost, next_turn, id(curr_hub), curr_hub, path + [(curr_hub, next_turn)])
                        )

        return None

    def add_path(self, path: list[tuple[Hub, int]]) -> None:
        """Reserva correctamente el camino en la tabla de espacio-tiempo."""
        for i in range(len(path)):
            hub, turn = path[i]

            # Reservar Hub
            if hub.hub_type not in ("start", "end"):
                self._reservaion_table.reserve_hub(hub.name, turn)

            # Reservar Conexión
            if i > 0:
                prev_hub, prev_turn = path[i - 1]
                for conn in self.map.connections:
                    is_match = (
                        (conn.zone1.name == prev_hub.name and conn.zone2.name == hub.name) or
                        (conn.zone2.name == prev_hub.name and conn.zone1.name == hub.name)
                    )
                    if is_match:
                        for t in range(prev_turn, turn):
                            self._reservaion_table.reserve_link(conn, t)


class ReservationTable:

    def __init__(self) -> None:
        self._hub_occup: dict[tuple[str, int], int] = {}
        self._link_occup: dict[tuple[frozenset, int], int] = {}

    def hub_available(self, hub: Hub, turn: int) -> bool:
        if hub.hub_type in ("start", "end"):
            return True
        curr_drones = self._hub_occup.get((hub.name, turn), 0)
        return curr_drones < hub.max_drones

    def link_available(self, connection: Connection, turn: int) -> bool:
        key = (connection._key(), turn)
        curr_drones = self._link_occup.get(key, 0)
        return curr_drones < connection.capacity

    def reserve_hub(self, hub_name: str, turn: int) -> None:
        key = (hub_name, turn)
        self._hub_occup[key] = self._hub_occup.get(key, 0) + 1

    def reserve_link(self, connection: Connection, turn: int) -> None:
        key = (connection._key(), turn)
        self._link_occup[key] = self._link_occup.get(key, 0) + 1

    def clear(self):
        self._hub_occup.clear()
        self._link_occup.clear()
 