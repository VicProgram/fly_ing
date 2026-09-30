from parsing import Parser
from models import Solver, DroneMap
import sys


def main() -> None:
    """Run the Fly-in simulation.

    Validates command-line arguments, parses the map file, and executes
    the solver. All errors are reported to stderr with exit code 1.
    """
    if len(sys.argv) < 2:
        print("Usage: python3 fly_ing.py <map_file>", file=sys.stderr)
        sys.exit(1)

    show_capacity = "--capacity" in sys.argv

    if show_capacity:
        print("Capacity flag detected. Displaying drone capacities.")
        map_file = sys.argv[2]

    else:
        map_file = sys.argv[1]

    drone_map = DroneMap()
    parser = Parser(drone_map)

    try:
        parser.parse_file(map_file)

    except ValueError as e:
        sys.stderr.write(f"Parse error: {e}\n")
        sys.exit(1)

    try:
        solver = Solver(drone_map, parser.nb_drones, show_capacity)
        solver.run()

    except Exception as e:
        sys.stderr.write(f"Solver error: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
