# Guía detallada del proyecto Fly-in

## 1. Visión general

Fly-in es un sistema de enrutamiento de drones que navega múltiples drones a través de una red de zonas conectadas, minimizando los turnos de simulación y respetando restricciones de capacidad. El sistema usa **A* en tiempo-espacio** con una **tabla de reservas** para planificar rutas libres de conflictos.

---

## 2. Estructura del proyecto

```
fly_ing/
├── fly_ing.py          # Entry point
├── models.py           # Clases del modelo y algoritmo
├── parsing.py          # Parser del archivo de mapa
├── Makefile            # Automatización
├── requirements.txt    # Dependencias
└── maps/               # Mapas de prueba
    ├── easy/
    ├── medium/
    └── hard/
```

---

## 3. Archivo por archivo

### 3.1 `fly_ing.py` — Entry point

| Función | Líneas | Descripción |
|---------|--------|-------------|
| `main()` | 6-31 | Valida args, crea `DroneMap`, `Parser` y `Solver`. Maneja errores con exit code 1. |

**Flujo:**
1. Verifica que se pase un archivo como argumento
2. Crea `DroneMap` vacío
3. Crea `Parser` y parsea el archivo
4. Crea `Solver` con el mapa y número de drones
5. Ejecuta `solver.run()`

---

### 3.2 `models.py` — Modelo y algoritmo

#### Clase `ValidList` (líneas 6-61)

Registro de tipos de zona válidos, costos y colores ANSI.

| Atributo/Función | Líneas | Descripción |
|------------------|--------|-------------|
| `valid_hubs` | 17 | Set de prefijos válidos: `{"hub:", "start_hub:", "end_hub:"}` |
| `valid_zones` | 19 | Set de tipos de zona: `{"normal", "blocked", "restricted", "priority"}` |
| `zone_costs` | 21-23 | Costo por tipo: `priority=1, normal=1, restricted=2, blocked=999999` |
| `valid_colors` | 25-48 | Diccionario de nombre de color → código ANSI |
| `check_zone(zone)` | 50-61 | Valida que un tipo de zona exista. Lanza `ValueError` si no. |

---

#### Clase `Hub` (líneas 64-106)

Representa una zona en la red de drones.

| Función | Líneas | Descripción |
|---------|--------|-------------|
| `__init__(name, x, y, zone_type, color, hub_type, max_drones)` | 77-98 | Inicializa un hub con nombre, coordenadas, tipo de zona, color, rol y capacidad |
| `__repr__()` | 100-106 | Retorna `Hub(name)` |

**Atributos:**
- `name`: Identificador único
- `x`, `y`: Coordenadas en la cuadrícula
- `zone_type`: `normal`, `blocked`, `restricted`, `priority`
- `color`: Nombre de color para display terminal
- `hub_type`: `start`, `end`, o `normal`
- `max_drones`: Capacidad máxima simultánea

---

#### Clase `Connection` (líneas 109-162)

Representa un enlace bidireccional entre dos hubs.

| Función | Líneas | Descripción |
|---------|--------|-------------|
| `__init__(name, zone1, zone2, capacity)` | 119-133 | Inicializa conexión con nombre, dos hubs y capacidad |
| `_key()` | 135-141 | Retorna `frozenset` con los nombres de los hubs (para comparación) |
| `__eq__(other)` | 143-154 | Compara conexiones por sus endpoints (sin importar orden) |
| `__hash__()` | 156-162 | Hash basado en `_key()` |

---

#### Clase `Drone` (líneas 165-199)

Representa un dron individual.

| Función | Líneas | Descripción |
|---------|--------|-------------|
| `__init__(id_drone, curr_loc)` | 176-188 | Inicializa dron con ID y hub inicial |

**Atributos:**
- `id`: Identificador único (D1, D2, ...)
- `location`: Hub o Connection actual

---

#### Clase `DroneMap` (líneas 202-285)

Contenedor de todos los hubs y conexiones.

| Función | Líneas | Descripción |
|---------|--------|-------------|
| `__init__()` | 213-220 | Inicializa mapa vacío |
| `add_hub(hub)` | 222-249 | Añade hub validando unicidad de nombre y start/end |
| `add_connection(connection)` | 251-266 | Añade conexión validando duplicados |
| `get_neighbors(hub)` | 268-285 | Retorna lista de `(hub_vecino, conexión)` dados |

---

#### Clase `ReservationTable` (líneas 288-355)

Rastrea la ocupación de hubs y conexiones a lo largo de los turnos.

| Función | Líneas | Descripción |
|---------|--------|-------------|
| `__init__()` | 298-301 | Inicializa diccionarios vacíos |
| `hub_available(hub, turn)` | 303-316 | Verifica si un hub tiene capacidad en un turno |
| `link_available(connection, turn)` | 318-330 | Verifica si una conexión tiene capacidad en un turno |
| `reserve_hub(hub_name, turn)` | 332-340 | Incrementa ocupación de un hub en un turno |
| `reserve_link(connection, turn)` | 342-350 | Incrementa ocupación de una conexión en un turno |
| `clear()` | 352-355 | Limpia todas las reservas |

**Estructura interna:**
- `_hub_occup`: `dict[tuple[str, int], int]` — `(hub_name, turn) → count`
- `_link_occup`: `dict[tuple[frozenset, int], int]` — `(connection_key, turn) → count`

---

#### Clase `Solver` (líneas 358-653)

Motor de pathfinding que planifica rutas de drones.

| Función | Líneas | Descripción |
|---------|--------|-------------|
| `__init__(dronemap, drones_number)` | 372-388 | Inicializa solver con mapa y crea drones |
| `get_drones_in_hub(hub)` | 390-399 | Cuenta drones en un hub |
| `get_drones_in_con(conn)` | 401-410 | Cuenta drones en una conexión |
| `get_move_costs(to_hub)` | 421-432 | Retorna costo de movimiento según tipo de zona |
| `run()` | 434-458 | Ejecuta pathfinding para todos los drones y simula |
| `find_path(start, end, start_turn)` | 460-565 | **A* en tiempo-espacio** — ver sección 4 |
| `add_path(path)` | 567-601 | Reserva hubs y conexiones de una ruta en la tabla |
| `print_simulation_output(total_paths)` | 603-653 | Imprime la simulación turno por turno |

---

### 3.3 `parsing.py` — Parser

#### Clase `Parser` (líneas 6-299)

| Función | Líneas | Descripción |
|---------|--------|-------------|
| `__init__(dronemap)` | 20-30 | Inicializa parser con un DroneMap |
| `parse_file(map_path)` | 32-79 | Lee archivo línea por línea, limpia comentarios, delega en `parse_line` |
| `parse_hub_content(content)` | 81-112 | Parsea metadata de un hub (color, zone, max_drones) |
| `parse_line(line, line_num)` | 114-228 | Despacha según prefijo: `nb_drones:`, `hub:`, `connection:` |
| `parse_metadata(line, allow_keys)` | 230-299 | Extrae pares `key=value` de bloques `[...]` |

---

## 4. El algoritmo: A* en tiempo-espacio

### 4.1 Concepto clave

El grafo de búsqueda incluye el **tiempo como dimensión**. Cada estado es un par `(hub, turn)` en lugar de solo `hub`. Esto permite manejar restricciones dinámicas (otros drones) sin recalcular.

### 4.2 Prioritized Planning

Cada dron planifica **secuencialmente**. Cuando un dron encuentra una ruta, la reserva en la tabla. El siguiente dron ve esas reservas como obstáculos.

### 4.3 `find_path()` paso a paso

```
1. Inicializar cola con (costo=0, turno=0, hub=start, path=[(start, 0)])
2. Inicializar min_cost = {(start.name, 0): 0.0}

3. Mientras la cola no esté vacía:
   a. Extraer estado con menor costo (heapq)
   b. Si costo > 700: ignorar (límite de seguridad)
   c. Si hub == end: retornar path
   d. Si costo > min_cost[(hub, turn)]: ignorar (ya hay mejor camino)

   e. Para cada vecino de hub actual:
      - Evitar backtracking (no volver al hub anterior)
      - Calcular step_cost = get_move_costs(vecino)
      - Si step_cost >= 999999: ignorar (zona bloqueada)
      - next_turn = curr_turn + step_cost
      - Verificar link_available para todos los turnos del viaje
      - Verificar hub_available en next_turn
      - Si ambos OK:
        * bonus = 0.01 si es priority, si no 0.0
        * new_cost = curr_cost + step_cost - bonus
        * Si new_cost < min_cost[(vecino, next_turn)]:
          - Actualizar min_cost
          - Añadir a la cola

   f. Si no es end: considerar esperar
      - next_turn = curr_turn + 1
      - wait_cost = curr_cost + 1.0001 (epsilon para desempate)
      - Si hub_available y wait_cost < min_cost:
        * Añadir a la cola

4. Si la cola se vacía sin encontrar end: retornar None
```

### 4.4 La tabla de reservas

Cuando un dron encuentra una ruta, `add_path()` reserva:
- **Hubs**: Por cada turno que el dron pasa en ese hub
- **Conexiones**: Por cada turno que el dron está en tránsito

Esto previene que otros drones usen el mismo recurso en el mismo turno.

### 4.5 Costos de movimiento

| Zona | Costo | Efecto |
|------|-------|--------|
| `normal` | 1 | Un turno para cruzar |
| `restricted` | 2 | Dos turnos para cruzar |
| `priority` | 1 | Un turno + bonus 0.01 en pathfinding |
| `blocked` | 999999 | Inaccesible |

### 4.6 Espera (waiting)

Los drones pueden esperar en su posición actual. Cuesta 1 turno + epsilon (0.0001) para que el algoritmo prefiera moverse antes que esperar.

### 4.7 Complejidad

- **Tiempo**: O((V + E) log V) por dron, donde V = número de estados (hub, turn)
- **Espacio**: O(V) para la tabla de reservas y la cola de prioridad

---

## 5. Formato de salida

Cada línea representa un turno:

| Formato | Significado |
|---------|-------------|
| `D<ID>-<zona>` | Dron llegó a una zona (coloreada con ANSI) |
| `D<ID>-<origen>-<destino>` | Dron en vuelo entre zonas |

Los drones estacionarios se omiten del output.

---

## 6. Tipos de zona

| Zona | Costo | Descripción |
|------|-------|-------------|
| `normal` | 1 | Zona estándar |
| `restricted` | 2 | El dron tarda 2 turnos en cruzar |
| `priority` | 1 | Preferido en pathfinding (bonus 0.01) |
| `blocked` | ∞ | Inaccesible |

---

## 7. Ejemplo

**Input:**
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

**Output:**
```
D1-waypoint1
D1-waypoint2 D2-waypoint1
D1-goal D2-waypoint2
D2-goal
```

**Explicación:**
- Turno 1: D1 se mueve a waypoint1
- Turno 2: D1 se mueve a waypoint2, D2 se mueve a waypoint1
- Turno 3: D1 llega a goal, D2 se mueve a waypoint2
- Turno 4: D2 llega a goal
