"""Main entry point for the Fly-in drone routing simulation.

Parses command-line arguments, loads the map file, and runs the solver.
"""

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

    drone_map = DroneMap()
    parser = Parser(drone_map)

    try:
        parser.parse_file(sys.argv[1])

    except ValueError as e:
        sys.stderr.write(f"Parse error: {e}\n")
        sys.exit(1)

    try:
        solver = Solver(drone_map, parser.nb_drones)
        solver.run()
    except Exception as e:
        sys.stderr.write(f"Solver error: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
