from parsing import Parser
from models import Solver, Drone_Map
import sys


def main() -> None:
    if len(sys.argv) < 2:
        print("Uso: python3 -m tu_modulo mapa.txt", file=sys.stderr)
        sys.exit(1)

    drone_map = Drone_Map()
    parser = Parser(drone_map)

    try:
        parser.parse_file(sys.argv[1])
        # PRUEBAS
        # parser.print_avances()

    except ValueError as e:
        sys.stderr.write(f"Error en el parseo {e}\n")
        sys.exit(1)

    try:
        solver = Solver(drone_map, parser.nb_drones)
        solver.run()
    except Exception as e:
        sys.stderr.write(f"Error en la resolución {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
