import re
import sys
from typing import Any, Tuple

from models import Connection, Drone_Map, Hub, Valid_List


class Parser:

    def __init__(self, drone_map: Drone_Map) -> None:
        self.map: Drone_Map = drone_map
        self.nb_drones: int = 0
        self.hub_counter: int = 0
        self.connection_counter: int = 0
        self.drones_parsed: bool = False

    def parse_file(self, map_path: str) -> None:
        try:
            with open(map_path, "r", encoding="utf-8") as file:
                for line_num, line in enumerate(file, 1):
                    clean_line = line.strip()

                    if not clean_line or clean_line.startswith("#"):
                        continue
                    try:
                        self.parse_line(clean_line, line_num)
                    except Exception as e:
                        print(
                            f"Ha ocurrido un error en la línea {line_num}: {e}"
                        )
                        sys.exit(1)

        except FileNotFoundError:
            print(
                f"Error: El archivo '{map_path}' no existe.",
                file=sys.stderr,
            )
            sys.exit(1)

        if self.map.start_hub is None:
            print("Error: el mapa no tiene start_hub.", file=sys.stderr)
            sys.exit(1)

        if self.map.end_hub is None:
            print("Error: el mapa no tiene end_hub.", file=sys.stderr)
            sys.exit(1)

    def parse_hub_content(
        self, content: str
    ) -> Tuple[str, int, int, str, str, int]:
        match_color = re.search(r"color=(\w+)", content)
        color = (
            match_color.group(1).lower().strip() if match_color else "none"
        )

        match_zone = re.search(r"zone=(\w+)", content)
        zo_type = match_zone.group(1).lower().strip() if match_zone else "normal"
        Valid_List.check_zone(zo_type)

        match_max_drone_nb = re.search(r"max_drones=(\d+)", content)
        max_drones = (
            int(match_max_drone_nb.group(1)) if match_max_drone_nb else 1
        )

        if max_drones <= 0:
            raise ValueError(f"max_drones debe ser positivo: '{max_drones}'")

        main_part = re.sub(r"\[.*?\]", "", content).strip()
        parts = main_part.split()

        if len(parts) != 3:
            raise ValueError(f"Formato de hub inválido: '{content}'")

        name, x_str, y_str = parts
        name = name.lower()

        if "-" in name:
            raise ValueError(
                f"Nombre de hub inválido (contiene '-'): '{name}'"
            )

        return name, int(x_str), int(y_str), zo_type, color, max_drones

    def parse_line(self, line: str, line_num: int) -> None:
        line_stripped = line.lstrip()

        if line_stripped.startswith("nb_drones:"):
            try:
                self.nb_drones = int(line_stripped.split(":")[1].strip())
                if self.nb_drones <= 0 or self.nb_drones >= 500:
                    raise ValueError(
                        "Número de drones inválido (debe ser entre 1 y 499)"
                    )
                self.drones_parsed = True
                return
            except (ValueError, IndexError) as e:
                raise ValueError(f"Estructura incorrecta en nb_drones: {e}")

        if not self.drones_parsed:
            raise ValueError(
                "La primera línea de datos válidos debe definir 'nb_drones:' "
                f"(Línea leída: '{line}')"
            )

        if any(line_stripped.startswith(p) for p in Valid_List.valid_hubs):
            prefix, content = line_stripped.split(":", 1)
            content = content.strip()

            name, x, y, zo_type, color, max_drones = self.parse_hub_content(
                content
            )

            nuevo_hub: Any = None
            match prefix:
                case "start_hub":
                    nuevo_hub = Hub(
                        name, x, y, zo_type, color, "start", max_drones
                    )
                    self.hub_counter += 1
                case "end_hub":
                    nuevo_hub = Hub(
                        name, x, y, zo_type, color, "end", max_drones
                    )
                    self.hub_counter += 1
                case "hub":
                    nuevo_hub = Hub(
                        name, x, y, zo_type, color, "normal", max_drones
                    )
                    self.hub_counter += 1
                case _:
                    raise ValueError(f"Prefijo de hub desconocido: '{prefix}'")

            self.map.add_hub(nuevo_hub)

        elif line_stripped.startswith("connection:"):
            try:
                _, content = line_stripped.split(":", 1)

                match_capacity = re.search(r"max_link_capacity=(\d+)", content)
                capacity = int(match_capacity.group(1)) if match_capacity else 1

                if capacity <= 0:
                    raise ValueError(
                        f"max_link_capacity debe ser positivo: '{capacity}'"
                    )

                content_clean = re.sub(r"\[.*?\]", "", content).strip()

                if "-" not in content_clean:
                    raise ValueError("Conexión malformada.")

                zone_1, zone_2 = content_clean.split("-", 1)
                zone_1 = zone_1.strip().lower()
                zone_2 = zone_2.strip().lower()

                first_hub = self.map.hubs.get(zone_1)
                second_hub = self.map.hubs.get(zone_2)

                if not first_hub or not second_hub:
                    raise ValueError(
                        "zona no encontrada en la conexión "
                        f"('{zone_1}' o '{zone_2}')."
                    )

                if first_hub is second_hub:
                    raise ValueError(
                        "Una conexión no puede unir un hub consigo mismo: "
                        f"'{zone_1}'"
                    )

                self.connection_counter += 1
                new_connection = Connection(
                    f"Conn{self.connection_counter}",
                    first_hub,
                    second_hub,
                    capacity,
                )
                self.map.add_connection(new_connection)

            except (ValueError, AttributeError, IndexError) as e:
                raise ValueError(f"Error procesando la conexión: {e}")

        else:
            raise ValueError(
                f"Estructura o sintaxis desconocida: '{line_stripped}'"
            )

    def print_avances(self) -> None:
        print(f"Mapa cargado exitosamente. Drones totales: {self.nb_drones}")
        print(f"Mapa cargado exitosamente. Hubs totales: {self.hub_counter}")
        print(
            "Mapa cargado exitosamente. Conexiones totales: "
            f"{self.connection_counter}"
        )
