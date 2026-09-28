import sys
from models import ansi_colors


class TerminalVisualizer:
    """Renders the simulation state as an ASCII mini-map on stderr.

    Displays the network grid with color-coded hubs, drone occupancy
    counts, and delivered drone progress.

    Attributes:
        map: The DroneMap being visualized.
        hubs: List of all hubs in the network.
        min_x: Minimum x-coordinate for grid bounds.
        max_x: Maximum x-coordinate for grid bounds.
        min_y: Minimum y-coordinate for grid bounds.
        max_y: Maximum y-coordinate for grid bounds.
    """

    def __init__(self, map_data) -> None:
        """Initialize the visualizer with map data.

        Args:
            map_data: The DroneMap instance containing hubs and connections.
        """
        self.map = map_data
        self.hubs = list(map_data.hubs.values())

        if self.hubs:
            self.min_x = min(h.x for h in self.hubs)
            self.max_x = max(h.x for h in self.hubs)
            self.min_y = min(h.y for h in self.hubs)
            self.max_y = max(h.y for h in self.hubs)
        else:
            self.min_x = self.max_x = self.min_y = self.max_y = 0

    def render_turn(self, turn: int, drone_positions: dict, total_drones: int, delivered: int) -> None:
        """Render a single turn's state to stderr.

        Draws the mini-map grid with hub colors and drone counts,
        followed by delivery progress.

        Args:
            turn: Current turn number.
            drone_positions: Mapping from hub name to drone count.
            total_drones: Total number of drones in the simulation.
            delivered: Number of drones that have reached the end zone.
        """
        sys.stderr.write(f"\n--- [ TURN {turn} ] ---\n")

        width = max(self.max_x - self.min_x + 1, 1)
        height = max(self.max_y - self.min_y + 1, 1)

        grid = [[" . " for _ in range(width)] for _ in range(height)]

        for hub in self.hubs:
            gx = hub.x - self.min_x
            gy = hub.y - self.min_y

            color_code = ansi_colors.get(getattr(hub, "color", "white").lower(), ansi_colors["RESET"])

            drones_here = drone_positions.get(hub.name, 0)
            label = f"{hub.name[:2]}:{drones_here}" if drones_here > 0 else f"{hub.name[:3]}"

            grid[gy][gx] = f"{color_code}[{label:^3}]{ansi_colors['RESET']}"

        for row in reversed(grid):
            sys.stderr.write(" ".join(row) + "\n")

        sys.stderr.write(f"Status: {delivered}/{total_drones} drones delivered.\n")
        sys.stderr.flush()


def main() -> None:
    """Entry point for standalone visualizer execution.

    Parses command-line arguments and runs the simulation with
    visual feedback enabled.
    """
    if len(sys.argv) < 2:
        sys.exit(1)

    map_path = sys.argv[1]
    is_visual = "--visual" in sys.argv

    from parsing import Parser
    from models import DroneMap, Solver

    drone_map = DroneMap()
    parser = Parser(drone_map)
    parser.parse_file(map_path)

    visualizer = TerminalVisualizer(drone_map) if is_visual else None

    solver = Solver(drone_map, parser.nb_drones)

    # TODO: integrate visualizer into solver.run()
    solver.run()


if __name__ == "__main__":
    main()
