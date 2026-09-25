import sys
from visualizer import TerminalVisualizer
from models import ansi_colors

class TerminalVisualizer:
    def __init__(self, map_data):
        self.map = map_data
        self.hubs = list(map_data.hubs.values())

        if self.hubs:
            self.min_x = min(h.x for h in self.hubs)
            self.max_x = max(h.x for h in self.hubs)
            self.min_y = min(h.y for h in self.hubs)
            self.max_y = max(h.y for h in self.hubs)
        else:
            self.min_x = self.max_x = self.min_y = self.max_y = 0

    def render_turn(self, turn: int, drone_positions: dict, total_drones: int, delivered: int):
        """
        Renders a ASCII frame for the current turn to sys.stderr.
        drone_positions: dict {hub_name: count_of_drones}
        """
        sys.stderr.write(f"\n--- [ TURNO {turn} ] ---\n")

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

        sys.stderr.write(f"Estado: {delivered}/{total_drones} drones entregados.\n")
        sys.stderr.flush()


def main():
    if len(sys.argv) < 2:
        sys.exit(1)

    map_path = sys.argv[1]
    is_visual = "--visual" in sys.argv

    visualizer = TerminalVisualizer(map_data) if is_visual else None

    for turn, step_info in enumerate(simulation_turns):

        print(step_info["stdout_line"])

        if visualizer:
            visualizer.render_turn(
                turn=turn,
                drone_positions=step_info["drone_hub_counts"],
                total_drones=step_info["total_drones"],
                delivered=step_info["delivered_count"]
            )


if __name__ == "__main__":
    main()
