from typing import Dict, List, Optional
import heapq
import sys


class ValidList:
    """Registry of valid zone types, costs, and ANSI color codes.

    Attributes:
        valid_hubs: Set of valid hub type prefixes.
        valid_zones: Set of valid zone types.
        zone_costs: Mapping from zone type to movement cost.
        valid_colors: Mapping from color name to ANSI escape code.
        ansi_colors: Extended color mapping including RESET code.
    """

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
        "darked": "\033[38;5;52m",
        "RESET": "\033[0m"
    }

    @classmethod
    def check_zone(cls, zone: str) -> None:
        """Validate that a zone type is recognized.

        Args:
            zone: The zone type string to validate.

        Raises:
            ValueError: If the zone type is not in valid_zones.
        """
        if zone not in cls.valid_zones:
            raise ValueError(f"Invalid zone type: '{zone}'")


class Hub:
    """Represents a zone in the drone network.

    Attributes:
        name: Unique identifier for the hub.
        x: X-coordinate on the map grid.
        y: Y-coordinate on the map grid.
        zone_type: Zone type (normal, blocked, restricted, priority).
        color: Optional color name for terminal display.
        hub_type: Hub role (start, end, or normal).
        max_drones: Maximum simultaneous drone occupancy.
    """

    def __init__(
            self, name: str, x: int, y: int, zone_type: str = "normal",
            color: str = "none", hub_type: str = "normal",
            max_drones: int = 1) -> None:
        """Initialize a Hub instance.

        Args:
            name: Unique identifier for the hub.
            x: X-coordinate on the map grid.
            y: Y-coordinate on the map grid.
            zone_type: Zone type, defaults to "normal".
            color: Color name for display, defaults to "none".
            hub_type: Role of the hub, defaults to "normal".
            max_drones: Maximum drone capacity, defaults to 1.
        """
        self.name: str = name
        self.x: int = x
        self.y: int = y
        self.zone_type: str = zone_type
        self.color: str = color
        self.hub_type: str = hub_type
        self.max_drones: int = max_drones

    def __repr__(self) -> str:
        """Return a string representation of the hub.

        Returns:
            String in the format Hub(name).
        """
        return f"Hub({self.name})"


class Connection:
    """Represents a bidirectional link between two hubs.

    Attributes:
        name: Internal identifier (Conn1, Conn2, ...).
        zone1: First hub of the connection.
        zone2: Second hub of the connection.
        capacity: Maximum simultaneous drone traversal.
    """

    def __init__(
            self, name: str, zone1: Hub, zone2: Hub, capacity: int = 1
            ) -> None:
        """Initialize a Connection instance.

        Args:
            name: Internal identifier for the connection.
            zone1: First hub endpoint.
            zone2: Second hub endpoint.
            capacity: Maximum drones that can traverse simultaneously.
        """
        self.name: str = name
        self.zone1: Hub = zone1
        self.zone2: Hub = zone2
        self.capacity: int = capacity

    def _key(self) -> frozenset:
        """Return an unordered key for connection comparison.

        Returns:
            A frozenset containing both hub names.
        """
        return frozenset({self.zone1.name, self.zone2.name})

    def __eq__(self, other: object) -> bool:
        """Check equality based on hub endpoints.

        Args:
            other: Object to compare against.

        Returns:
            True if the other is a Connection with the same endpoints.
        """
        if not isinstance(other, Connection):
            return NotImplemented
        return self._key() == other._key()

    def __hash__(self) -> int:
        """Return hash based on connection endpoints.

        Returns:
            Hash value for the connection.
        """
        return hash(self._key())


class Drone:
    """Represents a single drone in the simulation.

    Attributes:
        id: Unique drone identifier (D1, D2, ...).
        location: Current hub or connection.
        in_transit: Whether the drone is between hubs.
        turn: Current turn number.
        has_arrived: Whether the drone has reached the end zone.
    """

    def __init__(self, id_drone: str, curr_loc: Hub) -> None:
        """Initialize a Drone instance.

        Args:
            id_drone: Unique identifier string for the drone.
            curr_loc: Starting hub location.
        """
        self.id: str = id_drone
        self.location: Hub | Connection = curr_loc


class DroneMap:
    """Container for all hubs and connections in the network.

    Attributes:
        hubs: Dictionary mapping hub names to Hub objects.
        connections: List of all Connection objects.
        start_hub: The designated starting zone.
        end_hub: The designated target zone.
        used_coords: Set of (x, y) coordinates already occupied.
    """

    def __init__(self) -> None:
        """Initialize an empty DroneMap."""
        self.hubs: Dict[str, Hub] = {}
        self.connections: list[Connection] = []
        self.start_hub: Optional[Hub] = None
        self.end_hub: Optional[Hub] = None

    def add_hub(self, hub: Hub) -> None:
        """Add a hub to the map after validating uniqueness.

        Args:
            hub: The Hub instance to add.

        Raises:
            ValueError: If hub name is duplicated, if start/end already exists.
        """
        if hub.name in self.hubs:
            raise ValueError(
                f"Error: Hub with name '{hub.name}' already exists."
            )

        if hub.hub_type == "start" and self.start_hub is not None:
            raise ValueError("Error: start_hub already exists.")

        if hub.hub_type == "end" and self.end_hub is not None:
            raise ValueError("Error: end_hub already exists.")

        self.hubs[hub.name] = hub

        if hub.hub_type == "start":
            self.start_hub = hub
        elif hub.hub_type == "end":
            self.end_hub = hub

    def add_connection(self, connection: Connection) -> None:
        """Add a connection to the map after checking for duplicates.

        Args:
            connection: The Connection instance to add.

        Raises:
            ValueError: If an equivalent connection already exists.
        """
        if connection not in self.connections:
            self.connections.append(connection)
        else:
            raise ValueError(
                f"Error: Connection between '{connection.zone1.name}' and "
                f"'{connection.zone2.name}' already exists."
            )

    def get_neighbors(self, hub: Hub) -> list[tuple[Hub, Connection]]:
        """Find all adjacent hubs and their connecting connections.

        Args:
            hub: The hub to find neighbors for.

        Returns:
            List of (neighbor_hub, connection) tuples.
        """
        neighbors = []
        for conn in self.connections:
            if conn.zone1.name == hub.name:
                neighbors.append((conn.zone2, conn))

            elif conn.zone2.name == hub.name:
                neighbors.append((conn.zone1, conn))

        return neighbors


class ReservationTable:
    """Tracks occupancy of hubs and connections across all turns.

    Uses dictionaries keyed by (name, turn) for efficient lookup.

    Attributes:
        _hub_occup: Mapping from (hub_name, turn) to drone count.
        _link_occup: Mapping from (connection_key, turn) to drone count.
    """

    def __init__(self) -> None:
        """Initialize an empty reservation table."""
        self._hub_occup: dict[tuple[str, int], int] = {}
        self._link_occup: dict[tuple[frozenset, int], int] = {}

    def hub_available(self, hub: Hub, turn: int) -> bool:
        """Check if a hub has capacity at a given turn.

        Args:
            hub: The hub to check.
            turn: The turn number to check.

        Returns:
            True if the hub can accept another drone, False otherwise.
        """
        if hub.hub_type in ("start", "end"):
            return True
        curr_drones = self._hub_occup.get((hub.name, turn), 0)
        return curr_drones < hub.max_drones

    def link_available(self, connection: Connection, turn: int) -> bool:
        """Check if a connection has capacity at a given turn.

        Args:
            connection: The connection to check.
            turn: The turn number to check.

        Returns:
            True if the connection can accept another drone, False otherwise.
        """
        key = (connection._key(), turn)
        curr_drones = self._link_occup.get(key, 0)
        return curr_drones < connection.capacity

    def reserve_hub(self, hub_name: str, turn: int) -> None:
        """Reserve a hub for a specific turn.

        Args:
            hub_name: Name of the hub to reserve.
            turn: The turn to reserve for.
        """
        key = (hub_name, turn)
        self._hub_occup[key] = self._hub_occup.get(key, 0) + 1

    def reserve_link(self, connection: Connection, turn: int) -> None:
        """Reserve a connection for a specific turn.

        Args:
            connection: The connection to reserve.
            turn: The turn to reserve for.
        """
        key = (connection._key(), turn)
        self._link_occup[key] = self._link_occup.get(key, 0) + 1

    def clear(self) -> None:
        """Clear all reservations from the table."""
        self._hub_occup.clear()
        self._link_occup.clear()


class Solver:
    """Pathfinding engine that schedules drone routes.

    Uses A* search in time-space with a reservation table to plan
    conflict-free paths for all drones.

    Attributes:
        map: The DroneMap representing the network.
        curr_turn: Current simulation turn.
        history: List of simulation events.
        _reservation_table: Internal reservation tracker.
        drones: List of Drone instances to route.
    """

    def __init__(self, dronemap: DroneMap, drones_number: int, show_capacity: bool = False) -> None:
        """Initialize the solver with a map and drone count.

        Args:
            dronemap: The DroneMap to solve.
            drones_number: Number of drones to route from start to end.
        """
        self.map: DroneMap = dronemap
        self.curr_turn: int = 0
        self.history: list = []
        self._reservation_table = ReservationTable()
        self.show_capacity: bool = show_capacity

        assert self.map.start_hub is not None, "start_hub must exist"
        self.drones: list[Drone] = [
            Drone(f"D{i}", self.map.start_hub)
            for i in range(1, drones_number + 1)
        ]

    def get_drones_in_hub(self, hub: Hub) -> int:
        """Count drones currently located at a hub.

        Args:
            hub: The hub to count drones in.

        Returns:
            Number of drones at the specified hub.
        """
        return sum(1 for d in self.drones if d.location == hub)

    def get_drones_in_con(self, conn: Connection) -> int:
        """Count drones currently on a connection.

        Args:
            conn: The connection to count drones on.

        Returns:
            Number of drones traversing the connection.
        """
        return sum(1 for d in self.drones if d.location == conn)

    def get_move_costs(self, to_hub: Hub) -> int:
        """Calculate the movement cost to enter a destination zone.

        Args:
            to_hub: The destination hub.

        Returns:
            The movement cost in turns based on zone type.
        """
        if to_hub.zone_type == "blocked":
            return 999999
        return ValidList.zone_costs.get(to_hub.zone_type, 1)

    def run(self) -> None:
        """Execute the full pathfinding and simulation output.

        Plans paths for all drones sequentially using A* in time-space,
        then prints the simulation output turn by turn.

        Raises:
            SystemExit: If the end hub is unreachable.
        """
        self._reservation_table.clear()
        total_paths = []

        assert self.map.start_hub is not None, "start_hub must exist"
        assert self.map.end_hub is not None, "end_hub must exist"
        for drone in self.drones:
            path = self.find_path(self.map.start_hub, self.map.end_hub)

            if not path:
                sys.stderr.write("End_hub unreachable")
                sys.exit(1)

            self.add_path(path)
            total_paths.append((drone, path))
        else:
            self.print_simulation_output(total_paths)

    def find_path(self, start: Hub, end: Hub, start_turn: int = 0
                  ) -> Optional[List[tuple[Hub, int]]]:
        """Find the optimal path from start to end using A* in time-space.

        Explores states as (hub, turn) pairs, using a reservation table
        to avoid conflicts with previously planned paths.

        Args:
            start: The starting hub.
            end: The destination hub.
            start_turn: The turn to begin planning from, defaults to 0.

        Returns:
            A list of (hub, turn) tuples representing the path, or None
            if no valid path exists.
        """
        queue: List[tuple[float, int, int, Hub, List[tuple[Hub, int]]]] = [
            (0.0, start_turn, id(start), start, [(start, start_turn)])
        ]

        # Lowest cost found
        min_cost: Dict[tuple[str, int], float] = {
            (start.name, start_turn): 0.0
        }

        while queue:
            curr_cost, curr_turn, _, curr_hub, path = heapq.heappop(queue)

            if curr_cost > 700:
                continue

            # Goal reached
            if curr_hub.name == end.name:
                return path

            # Already found a cheaper path
            prev_cost = min_cost.get((curr_hub.name, curr_turn), float('inf'))
            if curr_cost > prev_cost:
                continue

            # Move to neighbor nodes (highest priority)
            for neighbor_hub, connection in self.map.get_neighbors(curr_hub):

                # Avoid backtracking
                if len(path) > 1 and neighbor_hub.name == path[-2][0].name:
                    continue

                step_cost = self.get_move_costs(neighbor_hub)
                if step_cost >= 999999:  # Blocked node
                    continue

                next_turn = curr_turn + step_cost
                link_ok = all(
                    self._reservation_table.link_available(
                        connection, t
                    )
                    for t in range(curr_turn, next_turn)
                )

                hub_ok = self._reservation_table.hub_available(
                    neighbor_hub, next_turn
                )

                if link_ok and hub_ok:

                    if neighbor_hub.zone_type == "priority":
                        bonus = 0.01
                    else:
                        bonus = 0.00
                    new_cost = curr_cost + step_cost - bonus

                    key = (neighbor_hub.name, next_turn)
                    best = min_cost.get(key, float('inf'))
                    if new_cost < best:
                        min_cost[key] = new_cost
                        heapq.heappush(
                            queue,
                            (
                                new_cost,
                                next_turn,
                                id(neighbor_hub),
                                neighbor_hub,
                                path + [(neighbor_hub, next_turn)],
                            ),
                        )

            if curr_hub.hub_type != "end":
                next_turn = curr_turn + 1
                if self._reservation_table.hub_available(curr_hub, next_turn):
                    wait_cost = curr_cost + 1.0001
                    wait_key = (curr_hub.name, next_turn)
                    best = min_cost.get(wait_key, float('inf'))
                    if wait_cost < best:
                        min_cost[wait_key] = wait_cost
                        heapq.heappush(
                            queue,
                            (
                                wait_cost,
                                next_turn,
                                id(curr_hub),
                                curr_hub,
                                path + [(curr_hub, next_turn)],
                            ),
                        )

        return None

    def add_path(self, path: list[tuple[Hub, int]]) -> None:
        """Reserve all hubs and connections along a planned path.

        Iterates through the path and reserves each hub and connection
        for the appropriate turns in the reservation table.

        Args:
            path: List of (hub, turn) tuples representing the path.
        """
        # Reserve the path in the table
        for i in range(len(path)):
            hub, turn = path[i]

            # Reserve hub
            if hub.hub_type not in ("start", "end"):
                if i > 0:
                    prev_hub, prev_turn = path[i - 1]
                    for t in range(prev_turn + 1, turn + 1):
                        self._reservation_table.reserve_hub(hub.name, t)
                else:
                    self._reservation_table.reserve_hub(hub.name, turn)

            # Reserve connection

            if i > 0:
                prev_hub, prev_turn = path[i - 1]

                if prev_hub.name != hub.name:
                    curr_pair = frozenset({prev_hub.name, hub.name})

                    for conn in self.map.connections:
                        if conn._key() == curr_pair:
                            for t in range(prev_turn, turn):
                                self._reservation_table.reserve_link(conn, t)
                            break

    def print_simulation_output(
            self, total_paths: list[tuple[Drone, list[tuple[Hub, int]]]]
            ) -> None:
        """Print the simulation output turn by turn.

        For each turn, prints a space-separated list of drone movements
        in the format D<ID>-<zone> or D<ID>-<connection> for drones in flight.

        Args:
            total_paths: List of (drone, path) tuples for all drones.
        """
        turn_moves: dict[int, list[str]] = {}

        for drone, path in total_paths:
            for i in range(1, len(path)):
                prev_hub, prev_turn = path[i - 1]
                curr_hub, curr_turn = path[i]

                # Drone advances
                if curr_hub.name != prev_hub.name:
                    travel_time = curr_turn - prev_turn

                    for flight_step in range(1, travel_time):
                        flight_turn = prev_turn + flight_step
                        if flight_turn not in turn_moves:
                            turn_moves[flight_turn] = []
                        turn_moves[flight_turn].append(
                            f"{drone.id}-{prev_hub.name}-{curr_hub.name}"
                        )

                    meta_color = ValidList.valid_colors.get(
                        curr_hub.color, "\033[37m"
                        )
                    if curr_turn not in turn_moves:
                        turn_moves[curr_turn] = []
                    turn_moves[curr_turn].append(
                        f"{meta_color}{drone.id}-{curr_hub.name}\033[0m"
                        )

                # Drone waits

        if not turn_moves:
            return

        max_turn = max(turn_moves.keys())

        # Print movement lines
        for turn in range(1, max_turn + 1):
            moves = turn_moves.get(turn, [])
            if moves:
                print(" ".join(moves))

            if self.show_capacity:

                print(f"Capacity info for turn {turn}:")

                for hub in self.map.hubs.values():
                    if hub.hub_type not in ("start", "end"):
                        used = self._reservation_table._hub_occup.get((hub.name, turn), 0)
                        print(
                            f"Hub {hub.name} (capacity {hub.max_drones}): "
                            f"{used} drones"
                        )
                        for conn in self.map.connections:
                            used = self._reservation_table._link_occup.get((conn._key(), turn), 0)
                            print(
                                f"Connection {conn.zone1.name}-{conn.zone2.name} "
                                f"(capacity {conn.capacity}): {used} drones"
                            )
