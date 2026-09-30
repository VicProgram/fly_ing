import re
from typing import Tuple
from models import Connection, DroneMap, Hub, ValidList


class Parser:
    """Parses map files and constructs a DroneMap.

    Validates syntax, enforces uniqueness constraints, and builds
    the network topology from the input file.

    Attributes:
        map: The DroneMap being constructed.
        nb_drones: Number of drones to simulate.
        hub_counter: Running count of hubs parsed.
        connection_counter: Running count of connections parsed.
        drones_parsed: Whether nb_drones has been successfully read.
    """

    def __init__(self, dronemap: DroneMap) -> None:
        """Initialize the parser with an empty DroneMap.

        Args:
            dronemap: The DroneMap instance to populate.
        """
        self.map: DroneMap = dronemap
        self.nb_drones: int = 0
        self.hub_counter: int = 0
        self.connection_counter: int = 0
        self.drones_parsed: bool = False

    def parse_file(self, map_path: str) -> None:
        """Parse a map file and populate the DroneMap.

        Reads the file line by line, stripping comments and blank lines,
        then delegates to parse_line for each valid line.

        Args:
            map_path: Path to the map file to parse.

        Raises:
            SystemExit: On file I/O errors or parsing errors.
        """
        try:
            with open(map_path, "r", encoding="utf-8") as file:
                for line_num, line in enumerate(file, 1):
                    clean_line = line.split("#")[0].strip()

                    if not clean_line or clean_line.startswith("#"):
                        continue
                    try:
                        self.parse_line(clean_line, line_num)
                    except Exception as e:
                        raise ValueError(
                            f"Line {line_num}: {e}"
                        )

        except (FileNotFoundError, IsADirectoryError, PermissionError) as e:
            raise ValueError(f"Error opening file '{map_path}': {e}")

        except UnicodeDecodeError:
            raise ValueError(
                f"Error: File '{map_path}' is not valid UTF-8."
            )

        except OSError as e:
            raise ValueError(f"I/O error on '{map_path}': {e}")

        if self.map.start_hub is None:
            raise ValueError("Error: map has no start_hub.")

        if self.map.end_hub is None:
            raise ValueError("Error: map has no end_hub.")

    def parse_hub_content(
        self, content: str
    ) -> Tuple[str, int, int, str, str, int]:
        """Parse hub metadata and extract hub properties."""
        allow_keys = {"color", "zone", "max_drones"}
        meta = self.parse_metadata(content, allow_keys)

        color = meta.get("color", "none")
        zone_type = meta.get("zone", "normal")
        max_drones = int(meta.get("max_drones", 1))

        ValidList.check_zone(zone_type)
        main_part = re.sub(r"\[.*?\]", "", content).strip()
        parts = main_part.split()

        if len(parts) != 3:
            raise ValueError(f"Invalid hub format: '{content}'")

        name, x_str, y_str = parts
        name = name.strip()

        if "-" in name:
            raise ValueError(
                f"Invalid hub name (contains '-'): '{name}'"
            )

        try:
            x, y = int(x_str), int(y_str)
        except ValueError:
            raise ValueError(f"Invalid coordinates: '{x_str}', '{y_str}'")

        return name, x, y, zone_type, color, max_drones

    def parse_line(self, line: str, line_num: int) -> None:
        """Parse a single line of the map file.

        Dispatches to the appropriate handler based on line prefix
        (nb_drones, hub definitions, or connections).

        Args:
            line: The cleaned line content (no comments).
            line_num: Line number for error reporting.

        Raises:
            ValueError: On unknown syntax or validation failures.
        """
        line_stripped = line.lstrip()

        if line_stripped.startswith("nb_drones:"):
            try:
                if self.drones_parsed:
                    raise ValueError(
                        "Duplicate 'nb_drones:' definition found."
                    )
                self.nb_drones = int(line_stripped.split(":")[1].strip())
                if self.nb_drones <= 0:
                    raise ValueError(
                        "Invalid drone number (must be greater than 1)"
                    )
                self.drones_parsed = True
                return
            except (ValueError, IndexError) as e:
                raise ValueError(f"Incorrect structure in nb_drones: {e}")

        if not self.drones_parsed:
            raise ValueError(
                "The first valid data line must define 'nb_drones:' "
                f"(Line read: '{line}')"
            )

        if any(line_stripped.startswith(p) for p in ValidList.valid_hubs):
            prefix, content = line_stripped.split(":", 1)
            content = content.strip()

            name, x, y, zone_type, color, max_drones = self.parse_hub_content(
                content
            )

            # region
            # new_hub: Any = None
            # match prefix:
            #     case "start_hub":
            #         new_hub = Hub(
            #             name, x, y, zone_type, color, "start", max_drones
            #         )
            #         self.hub_counter += 1
            #     case "end_hub":
            #         new_hub = Hub(
            #             name, x, y, zone_type, color, "end", max_drones
            #         )
            #         self.hub_counter += 1
            #     case "hub":
            #         new_hub = Hub(
            #             name, x, y, zone_type, color, "normal", max_drones
            #         )
            #         self.hub_counter += 1
            #     case _:
            #         raise ValueError(f"Unknown hub prefix: '{prefix}'")

            # self.map.add_hub(new_hub)
            # endregion

            hub_type = {
                "start_hub": "start", "end_hub": "end", "hub": "normal"
                }.get(prefix)

            if hub_type is None:
                raise ValueError(f"Unknown hub prefix: '{prefix}'")

            self.hub_counter += 1
            self.map.add_hub(Hub(
                name, x, y, zone_type, color, hub_type, max_drones
            ))

        elif line_stripped.startswith("connection:"):
            try:
                _, content = line_stripped.split(":", 1)

                allow_keys_conn = {"max_link_capacity"}
                meta = self.parse_metadata(content, allow_keys_conn)
                capacity = int(meta.get("max_link_capacity", 1))

                content_clean = re.sub(r"\[.*?\]", "", content).strip()

                if "-" not in content_clean:
                    raise ValueError("Malformed connection.")

                zone_1, zone_2 = content_clean.split("-", 1)
                zone_1 = zone_1.strip()
                zone_2 = zone_2.strip()

                first_hub = self.map.hubs.get(zone_1)
                second_hub = self.map.hubs.get(zone_2)

                if not first_hub or not second_hub:
                    raise ValueError(
                        "Zone not found in connection "
                        f"('{zone_1}' or '{zone_2}')."
                    )

                if first_hub is second_hub:
                    raise ValueError(
                        "A connection cannot link a hub to itself: "
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
                raise ValueError(f"Error processing connection: {e}")

        else:
            raise ValueError(
                f"Unknown structure or syntax: '{line_stripped}'"
            )

    def parse_metadata(
        self, line: str, allow_keys: set[str] | None = None
    ) -> dict[str, str]:
        """Parse bracket-enclosed metadata from a line.

        Extracts key=value pairs from [...] blocks, validating keys
        against the allowed set and ensuring values are strictly valid.

        Args:
            line: The line content potentially containing metadata.
            allow_keys: Set of permitted metadata keys. Defaults to None.

        Returns:
            Dictionary of metadata key-value pairs.

        Raises:
            ValueError: On malformed metadata, unknown keys, or invalid values.
        """
        if "[" not in line and "]" not in line:
            return {}

        if (
            line.count("[") != 1
            or line.count("]") != 1
            or line.index("[") > line.index("]")
        ):
            raise ValueError(
                "Malformed metadata (must be one valid '[...]' block)"
            )

        content = line[line.index("[") + 1: line.index("]")].strip()
        if not content:
            return {}

        metadata: dict[str, str] = {}

        tokens = content.split()

        for token in tokens:
            if token.count("=") != 1:
                raise ValueError(
                    f"Malformed metadata (must be exactly one '='): '{token}'"
                )

            key, val = token.split("=", 1)
            key, val = key.strip(), val.strip()

            if not key or not val:
                raise ValueError(f"Empty key or value in metadata: '{token}'")

            if allow_keys is not None and key not in allow_keys:
                raise ValueError(f"Unknown or forbidden metadata key: '{key}'")

            if key in ("max_drones", "capacity", "max_link_capacity"):
                if not val.isdigit() or int(val) < 1:
                    raise ValueError(
                        f"Invalid value for '{key}': '{val}' "
                        "(must be a positive integer >= 1)"
                    )

            if key == "color":
                if not val.isalnum() and "_" not in val:
                    raise ValueError(f"Invalid color format: '{val}'")

            if key in metadata:
                raise ValueError(f"Duplicate metadata key found: '{key}'")

            metadata[key] = val

        return metadata
