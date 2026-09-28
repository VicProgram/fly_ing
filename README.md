*This project has been created as part of the 42 curriculum by vic.*

# Fly-in

## Description

Fly-in is a drone routing system that navigates multiple drones through a network of connected zones while minimizing simulation turns and handling movement constraints. The system uses a pathfinding algorithm (A* in time-space with a reservation table) to schedule drone movements, respecting zone capacities, connection capacities, and zone-specific movement costs.

The project is written in Python 3.10+ and follows a fully object-oriented design. It includes a parser for the input file format, a simulation engine, and a pathfinding algorithm.

## Instructions

### Prerequisites

- Python 3.10 or later
- `python3-venv` package (for virtual environment)

### Installation

```bash
make install
```

This creates a virtual environment in `.venv/` and installs the required dependencies (flake8, mypy).

### Running the simulation

```bash
make run
```

Or with a specific map:

```bash
make run MAP=maps/easy/01_linear_path.txt
make run MAP=maps/hard/02_capacity_hell.txt
```

Or directly:

```bash
python3 fly_ing.py maps/easy/01_linear_path.txt
```

### Example

**Input** (`maps/easy/01_linear_path.txt`):

```
nb_drones: 2
start_hub: start 0 0
end_hub: goal 3 0
hub: waypoint1 1 0
hub: waypoint2 2 0
connection: start-waypoint1
connection: waypoint1-waypoint2
connection: waypoint2-goal
```

**Output**:

```
D1-waypoint1
D1-waypoint2 D2-waypoint1
D1-goal D2-waypoint2
D2-goal
```

Each line represents one turn. Drones in flight show as `D<ID>-<from>-<to>`, arrived drones as `D<ID>-<zone>` (colored by zone). Stationary drones are omitted.

### Debug mode

```bash
make debug
```

Or with a specific map:

```bash
make debug MAP=maps/medium/01_dead_end_trap.txt
```

### Linting

```bash
make lint
```

For strict type checking:

```bash
make lint-strict
```

### Clean

```bash
make clean
```

This removes the virtual environment, cache files, and temporary files.

## Resources

### Classic references

- **A* Search Algorithm**: Russell, S. & Norvig, P. (2020). *Artificial Intelligence: A Modern Approach* (4th ed.). Pearson.
- **Dijkstra's Algorithm**: Dijkstra, E. W. (1959). "A note on two problems in connexion with graphs". *Numerische Mathematik*, 1, 269-271.
- **Priority Queues and Heapq**: Python documentation — `heapq` module.
- **Object-Oriented Design**: Gamma, E., Helm, R., Johnson, R., & Vlissides, J. (1994). *Design Patterns: Elements of Reusable Object-Oriented Software*. Addison-Wesley.
- **Type Hints**: PEP 484 — Type Hints. https://peps.python.org/pep-0484/
- **Docstrings**: PEP 257 — Docstring Conventions. https://peps.python.org/pep-0257/

### How AI was used

AI tools were used to assist with the following tasks:

- **Code review and debugging**: Identifying potential bugs in the parser and pathfinding logic, such as the capacity overflow issue with restricted zones.
- **Documentation**: Helping structure the README and docstrings.
- **Algorithm design**: Discussing the A* implementation in time-space and the reservation table approach.
- **Code quality**: Running flake8 and mypy, identifying type errors, and suggesting fixes.

All AI-generated code was reviewed, tested, and understood before being integrated into the project.

## Algorithm

### Overview

The algorithm uses **A* search in time-space** combined with a **reservation table** to schedule drone paths. This approach is known as "prioritized planning" — each drone plans its path sequentially, treating previously reserved paths as obstacles.

### Key concepts

1. **Time-space graph**: The search space is expanded to include time as a dimension. Each state is `(hub, turn)` rather than just `hub`.

2. **Reservation table**: A data structure that tracks which zones and connections are occupied at each turn. When a drone plans its path, it checks the table to avoid conflicts.

3. **Movement costs**:
   - `normal`: 1 turn
   - `priority`: 1 turn (preferred in pathfinding via a small bonus)
   - `restricted`: 2 turns (drone must arrive at the destination on the next turn)
   - `blocked`: inaccessible

4. **Capacity constraints**:
   - `max_drones`: maximum drones in a zone simultaneously
   - `max_link_capacity`: maximum drones traversing a connection simultaneously
   - Start and end zones have unlimited capacity

5. **Waiting**: Drones can wait in place if movement is not possible. Waiting costs 1 turn plus a small epsilon (0.0001) to break ties in favor of moving.

### Why A* in time-space?

- **Optimality**: A* guarantees the shortest path in terms of cost.
- **Time dimension**: By including time in the state, we can handle dynamic constraints (other drones) without recalculating.
- **Reservation table**: Efficiently tracks occupancy and allows O(1) lookup for availability.

### Complexity

- **Time**: O((V + E) log V) per drone, where V is the number of (hub, turn) states and E is the number of possible movements.
- **Space**: O(V) for the reservation table and the priority queue.
- **Caching**: Paths are not cached between drones — each drone plans independently using the current state of the reservation table.

### Limitations

- **Prioritized planning does not guarantee global optimality**: The order in which drones are planned affects the result. A different order might yield fewer total turns.
- **No backtracking**: Once a drone's path is reserved, it cannot be replanned. This can lead to suboptimal solutions in complex scenarios.
- **Scalability**: For very large numbers of drones (1000+), the reservation table can become large, but the algorithm remains efficient due to the sparse nature of the reservations.

## Project structure

```
fly_ing/
├── fly_ing.py          # Main entry point
├── models.py           # Core classes: DroneMap, Solver, ReservationTable, etc.
├── parsing.py          # Parser for the input file format
├── Makefile            # Build automation
├── requirements.txt    # Python dependencies
├── maps/               # Test maps
│   ├── easy/
│   ├── medium/
│   ├── hard/
│   └── challenger/
└── README.md           # This file
```

## Performance

The algorithm meets all performance benchmarks specified in the subject:

| Map | Turns | Target |
|-----|-------|--------|
| easy/01 | 4 | ≤ 6 |
| easy/02 | 4 | ≤ 8 |
| easy/03 | 4 | ≤ 6 |
| medium/01 | 8 | ≤ 12 |
| medium/02 | 15 | ≤ 15 |
| medium/03 | 7 | ≤ 12 |
| hard/01 | 13 | ≤ 30 |
| hard/02 | 16 | ≤ 35 |
| hard/03 | 26 | ≤ 45 |
| challenger | 43 | < 45 (record) |
