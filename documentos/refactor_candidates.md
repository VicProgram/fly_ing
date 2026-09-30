# Refactor Candidates — Fly-in

> Propuestas de simplificación de funciones para reducir líneas sin cambios complejos.
> No se ha modificado ningún código. Solo análisis.

---

## 1. `Solver.get_move_costs` — `models.py:421-432` (~11 líneas → 1)

**Ahorro: ~3-4 líneas (cuerpo de la función)**

El `if to_hub.zone_type == "blocked": return 999999` es **redundante** — `ValidList.zone_costs` ya mapea `"blocked"` a `999999`.

### Antes
```python
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
```

### Después
```python
def get_move_costs(self, to_hub: Hub) -> int:
    """Calculate the movement cost to enter a destination zone.

    Args:
        to_hub: The destination hub.

    Returns:
        The movement cost in turns based on zone type.
    """
    return ValidList.zone_costs.get(to_hub.zone_type, 1)
```

---

## 2. `DroneMap.get_neighbors` — `models.py:268-285` (~17 líneas → 9)

**Ahorro: ~6-8 líneas**

El loop manual con `if/elif` se puede reemplazar con una list comprehension.

### Antes
```python
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
```

### Después
```python
def get_neighbors(self, hub: Hub) -> list[tuple[Hub, Connection]]:
    """Find all adjacent hubs and their connecting connections.

    Args:
        hub: The hub to find neighbors for.

    Returns:
        List of (neighbor_hub, connection) tuples.
    """
    return [
        (conn.zone2 if conn.zone1.name == hub.name else conn.zone1, conn)
        for conn in self.connections
        if conn.zone1.name == hub.name or conn.zone2.name == hub.name
    ]
```

---

## 3. `Solver.print_simulation_output` — `models.py:603-653` (~50 líneas → ~42)

**Ahorro: ~8-10 líneas**

Usar `collections.defaultdict(list)` para eliminar los bloques `if turn not in turn_moves` y simplificar el loop final.

### Antes
```python
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
```

### Después
```python
def print_simulation_output(
        self, total_paths: list[tuple[Drone, list[tuple[Hub, int]]]]
        ) -> None:
    """Print the simulation output turn by turn.

    For each turn, prints a space-separated list of drone movements
    in the format D<ID>-<zone> or D<ID>-<connection> for drones in flight.

    Args:
        total_paths: List of (drone, path) tuples for all drones.
    """
    turn_moves: defaultdict[int, list[str]] = defaultdict(list)

    for drone, path in total_paths:
        for i in range(1, len(path)):
            prev_hub, prev_turn = path[i - 1]
            curr_hub, curr_turn = path[i]

            # Drone advances
            if curr_hub.name != prev_hub.name:
                travel_time = curr_turn - prev_turn

                for flight_step in range(1, travel_time):
                    flight_turn = prev_turn + flight_step
                    turn_moves[flight_turn].append(
                        f"{drone.id}-{prev_hub.name}-{curr_hub.name}"
                    )

                meta_color = ValidList.valid_colors.get(
                    curr_hub.color, "\033[37m"
                )
                turn_moves[curr_turn].append(
                    f"{meta_color}{drone.id}-{curr_hub.name}\033[0m"
                )

            # Drone waits

    if not turn_moves:
        return

    # Print movement lines
    for turn in sorted(turn_moves):
        moves = turn_moves[turn]
        if moves:
            print(" ".join(moves))
```

**Nota:** Requiere añadir `from collections import defaultdict` al inicio del archivo.

---

## 4. `Parser.parse_line` — `parsing.py:114-228` (~114 líneas → ~95)

**Ahorro: ~15-20 líneas**

Colapsar los tres casos de hub-type en un dict lookup + una sola llamada `Hub(...)`.

### Antes (líneas 159-179)
```python
            new_hub: Any = None
            match prefix:
                case "start_hub":
                    new_hub = Hub(
                        name, x, y, zone_type, color, "start", max_drones
                    )
                    self.hub_counter += 1
                case "end_hub":
                    new_hub = Hub(
                        name, x, y, zone_type, color, "end", max_drones
                    )
                    self.hub_counter += 1
                case "hub":
                    new_hub = Hub(
                        name, x, y, zone_type, color, "normal", max_drones
                    )
                    self.hub_counter += 1
                case _:
                    raise ValueError(f"Unknown hub prefix: '{prefix}'")

            self.map.add_hub(new_hub)
```

### Después
```python
            hub_type = {"start_hub": "start", "end_hub": "end", "hub": "normal"}.get(prefix)
            if hub_type is None:
                raise ValueError(f"Unknown hub prefix: '{prefix}'")

            self.hub_counter += 1
            self.map.add_hub(Hub(name, x, y, zone_type, color, hub_type, max_drones))
```

---

## 5. `Solver.find_path` — `models.py:460-565` (~105 líneas → ~85)

**Ahorro: ~20-25 líneas**

Extraer un helper local `_push_state` para eliminar la duplicación entre los bloques de move-action y wait-action.

### Antes (fragmento representativo)
```python
                # Move action
                new_cost = current_cost + move_cost + bonus
                new_key = (neighbor_hub, next_turn)
                if new_cost < min_cost.get(new_key, float('inf')):
                    min_cost[new_key] = new_cost
                    heapq.heappush(
                        queue,
                        (
                            new_cost + heuristic(neighbor_hub, end_hub),
                            next_turn,
                            neighbor_hub,
                            path + [(neighbor_hub, next_turn)],
                            new_cost,
                        ),
                    )

                # Wait action
                new_cost = current_cost + 1 + 0.0001
                new_key = (current_hub, next_turn)
                if new_cost < min_cost.get(new_key, float('inf')):
                    min_cost[new_key] = new_cost
                    heapq.heappush(
                        queue,
                        (
                            new_cost + heuristic(current_hub, end_hub),
                            next_turn,
                            current_hub,
                            path + [(current_hub, next_turn)],
                            new_cost,
                        ),
                    )
```

### Después
```python
                def _push_state(
                    hub: Hub, turn: int, cost: float, path: list[tuple[Hub, int]]
                ) -> None:
                    key = (hub, turn)
                    if cost < min_cost.get(key, float('inf')):
                        min_cost[key] = cost
                        heapq.heappush(
                            queue,
                            (cost + heuristic(hub, end_hub), turn, hub, path + [(hub, turn)], cost),
                        )

                # Move action
                move_cost = self.get_move_costs(neighbor_hub)
                bonus = 0.01 if neighbor_hub.zone_type == "priority" else 0.0
                _push_state(neighbor_hub, next_turn, current_cost + move_cost + bonus, path)

                # Wait action
                _push_state(current_hub, next_turn, current_cost + 1 + 0.0001, path)
```

---

## Resumen

| # | Función | Archivo | Líneas actuales | Ahorro |
|---|---------|---------|-----------------|--------|
| 1 | `Solver.get_move_costs` | `models.py` | 11 | ~3-4 |
| 2 | `DroneMap.get_neighbors` | `models.py` | 17 | ~6-8 |
| 3 | `Solver.print_simulation_output` | `models.py` | 50 | ~8-10 |
| 4 | `Parser.parse_line` | `parsing.py` | 114 | ~15-20 |
| 5 | `Solver.find_path` | `models.py` | 105 | ~20-25 |

---

## Notas

- Todos los cambios son de **bajo riesgo** y no alteran el comportamiento.
- Enfoque: eliminar duplicación, condicionales redundantes y aprovechar built-ins de Python (`defaultdict`, dict lookups, comprehensions).
- No se ha modificado ningún código.
