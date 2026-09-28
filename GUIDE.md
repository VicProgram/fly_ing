# Guía del proyecto Fly-in

## 1. Cómo funciona el proyecto (para el evaluador)

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

---

## 2. Guía para implementar visualización en vivo

### Qué pide la hoja de corrección

> "The program provides a clear visual feedback (colored terminal output and/or graphical interface)"
> "Colors specified in zone metadata are used for visualization"
> "The visual system clearly shows drone positions and movements"

### Estado actual

El output usa colores ANSI para los nombres de zonas, pero **no hay** un mini-mapa ASCII ni retroalimentación visual de posiciones en tiempo real.

### Propuesta de implementación

#### Opción A: Mini-mapa ASCII en stderr (recomendada)

**Dónde:** Crear un nuevo archivo `visualizer.py`

**Cómo funciona:**
1. Capturar la salida del solver antes de imprimirla
2. Por turno, dibujar una cuadrícula ASCII con:
   - Las zonas como caracteres coloreados
   - Los drones como números dentro de las zonas
   - Las conexiones como líneas entre zonas
3. Enviar el dibujo a **stderr** para mantener stdout limpio

**Estructura sugerida:**

```python
# visualizer.py
class Visualizer:
    def __init__(self, dronemap: DroneMap):
        self.map = dronemap
        self.grid = self._build_grid()

    def _build_grid(self) -> list[list[str]]:
        """Construye una cuadrícula vacía basada en las coordenadas de los hubs."""
        ...

    def render_turn(self, turn: int, drone_positions: dict) -> str:
        """Genera el frame ASCII para un turno dado."""
        ...

    def display(self, frame: str) -> None:
        """Imprime el frame en stderr."""
        print(frame, file=sys.stderr)
```

**Integración en `models.py`:**
- En `Solver.print_simulation_output()`, llamar al visualizer antes de imprimir cada turno
- Pasar la posición de cada dron en cada turno

**Ejemplo de output en stderr:**
```
Turn 3:
  ┌───┐     ┌───┐     ┌───┐
  │ S │─────│ X │─────│ G │
  │   │     │ 2 │     │   │
  └───┘     └───┘     └───┘
         ↑ D1 en vuelo X→G
```

#### Opción B: Output enriquecido con colores (mínimo esfuerzo)

**Dónde:** Modificar `models.py` en `print_simulation_output()`

**Cómo:**
- Usar códigos ANSI para colorear cada zona según su metadata `[color=...]`
- Mostrar la posición de cada dron con un formato más visual
- Ejemplo: `[D1→X]` en lugar de `D1-X`

#### Opción C: Interfaz gráfica con curses (máximo esfuerzo)

**Dónde:** Crear `visualizer.py` usando `curses`

**Cómo:**
- Usar `curses` para dibujar una interfaz en tiempo real
- Mostrar el mapa, los drones moviéndose, y estadísticas
- Permitir pausa/reproducción paso a paso

### Recomendación

La **Opción A** es la mejor relación esfuerzo/beneficio:
- Cumple con los requisitos de la hoja de corrección
- No rompe la separación stdout/stderr
- Es fácil de implementar y mantener
- No requiere dependencias externas

### Pasos para implementar la Opción A

1. Crear `visualizer.py` con la clase `Visualizer`
2. Construir la cuadrícula a partir de las coordenadas `(x, y)` de los hubs
3. En `Solver.print_simulation_output()`, llamar al visualizer por turno
4. Enviar el frame a stderr con `print(..., file=sys.stderr)`
5. Probar con los mapas de `maps/easy/`, `maps/medium/`, `maps/hard/`
