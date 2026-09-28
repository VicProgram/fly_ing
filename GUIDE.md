# Guía del proyecto Fly-in

## Cómo funciona el proyecto (para el evaluador)

### Visión general

Fly-in es un sistema de enrutamiento de drones que navega múltiples drones a través de una red de zonas conectadas, minimizando los turnos de simulación y respetando restricciones de capacidad.

### Arquitectura

```
fly_ing.py          → Entry point: parsea args, crea DroneMap, Parser y Solver
models.py           → Clases: Hub, Connection, Drone, DroneMap, ReservationTable, Solver
parsing.py          → Parser: lee el archivo de mapa y construye el DroneMap
```

### Flujo de ejecución

1. **Parser** (`parsing.py`):
   - Lee el archivo de mapa línea por línea
   - Soporta comentarios con `#`
   - Reconoce: `nb_drones:`, `start_hub:`, `end_hub:`, `hub:`, `connection:`
   - Metadata opcional: `[zone=...]`, `[color=...]`, `[max_drones=...]`, `[max_link_capacity=...]`
   - Valida: zonas únicas, tipos de zona válidos, capacidades positivas, conexiones duplicadas

2. **Solver** (`models.py`):
   - Usa **A* en tiempo-espacio** con una **tabla de reservas**
   - Cada dron planifica secuencialmente (prioritized planning)
   - Estados: `(hub, turn)` — el tiempo es una dimensión del grafo
   - La tabla de reservas evita conflictos entre drones

3. **Salida**:
   - Cada línea = un turno
   - Formato: `D<ID>-<zona>` (dron en zona) o `D<ID>-<origen>-<destino>` (dron en vuelo)
   - Los drones estacionarios se omiten
   - Colores ANSI por zona

### Conceptos clave

| Concepto | Descripción |
|----------|-------------|
| **Time-space graph** | El grafo incluye tiempo como dimensión. Cada nodo es `(hub, turn)` |
| **Reservation table** | Estructura que registra qué zonas/conexiones están ocupadas en cada turno |
| **Prioritized planning** | Cada dron planifica secuencialmente, tratando rutas previas como obstáculos |
| **Movement costs** | normal=1, restricted=2, priority=1 (con bonus), blocked=inaccesible |
| **Capacity** | max_drones por zona, max_link_capacity por conexión |

### Tipos de zona

| Zona | Costo | Descripción |
|------|-------|-------------|
| `normal` | 1 | Zona estándar |
| `restricted` | 2 | El dron tarda 2 turnos en cruzar |
| `priority` | 1 | Preferido en pathfinding (bonus 0.01) |
| `blocked` | ∞ | Inaccesible |
