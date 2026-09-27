# PLAN DE RESOLUCIÓN — Fly-in

Documento de referencia para completar todos los puntos pendientes del TODO.
Tiempo estimado total: 2-3 días de trabajo.

---

## FASE 1 — Parser (desbloqueo rápido)

### Punto 16 — Quitar `.lower()` de nombres

**Archivo:** `parsing.py`

**Pasos:**
1. Línea 78: cambiar `name = name.strip().lower()` → `name = name.strip()`
2. Línea 157: cambiar `zone_1 = zone_1.strip().lower()` → `zone_1 = zone_1.strip()`
3. Línea 158: cambiar `zone_2 = zone_2.strip().lower()` → `zone_2 = zone_2.strip()`
4. Línea 214: cambiar `key, val = key.strip().lower(), val.strip()` → `key, val = key.strip(), val.strip()`

**Verificación:**
- Crear un mapa con `hub: Alpha 0 0` y `hub: alpha 1 1` → deben ser hubs distintos
- La salida debe imprimir `Alpha` y `alpha` tal cual

---

### Punto 13b — Error en `nb_drones` duplicado

**Archivo:** `parsing.py`

**Pasos:**
1. En `parse_line` (línea 95), antes de procesar `nb_drones:`, verificar si `self.drones_parsed` ya es True
2. Si ya es True, lanzar `ValueError("nb_drones ya fue definido")`

**Código sugerido:**
```python
if line_stripped.startswith("nb_drones:"):
    if self.drones_parsed:
        raise ValueError("nb_drones ya fue definido anteriormente")
    # ... resto del código igual
```

**Verificación:**
- Un mapa con dos líneas `nb_drones:` debe dar error con línea y causa

---

### Punto 12 — Validar metadata completa

**Archivo:** `parsing.py`

**Pasos:**
1. En `parse_metadata` (línea 192), reemplazar el loop actual por validación estricta:
   - Verificar que cada token tenga exactamente un `=`
   - Verificar que la clave esté en `allow_keys`
   - Verificar que el valor sea un entero >= 1 para capacidades
   - Verificar que `color` sea una sola palabra (sin espacios)
2. Lanzar `ValueError` con mensaje claro en cada caso

**Verificación:**
- `[max_drones=-1]` → error
- `[max_drones=abc]` → error
- `[foo=bar]` → error (clave desconocida)
- `[color=dark red]` → error (dos palabras)
- `[zone=restricted max_drones=2]` → OK

---

### Punto 14 + 38 — Unificar manejo de errores

**Archivo:** `parsing.py` y `fly_ing.py`

**Pasos:**
1. En `parsing.py`, `parse_file`: quitar los `sys.exit(1)` internos y dejar que las excepciones se propaguen
2. En `fly_ing.py`, `main`: el `try/except ValueError` ya captura todo
3. Asegurar que todos los mensajes de error salgan por `sys.stderr` con formato `"Error (line N): causa"`

**Verificación:**
- Mapa con error en línea 5 → mensaje por stderr con "Error (line 5): ..."
- Sin traceback

---

## FASE 2 — Bug de capacidad (punto 5)

**Archivo:** `models.py`

**Pasos:**
1. En `find_path`, antes de aceptar un movimiento (línea 310), verificar TODOS los turnos de la conexión:
   ```python
   link_ok = all(
       self._reservation_table.link_available(connection, t)
       for t in range(curr_turn, next_turn)
   )
   ```
   Esto YA está en líneas 299-304. El problema está en el paso de espera.

2. En el paso de espera (línea 333-350), añadir comprobación de conexión:
   - Cuando un dron espera, está ocupando la conexión hacia el siguiente turno
   - Verificar que la conexión que se usará después tenga capacidad

3. Alternativa más simple: en `add_path` (línea 354), al reservar conexiones, verificar capacidad antes de reservar:
   ```python
   for t in range(prev_turn, turn):
       if not self._reservation_table.link_available(conn, t):
           # buscar ruta alternativa o esperar
   ```

**Verificación:**
- El reproductor mínimo del TODO debe pasar 20/20 limpio
- Los 10 mapas x 6 reps sin violaciones de capacidad
- `hard/02` ya no produce conexiones sobre capacidad

---

## FASE 3 — Formato de salida (puntos 10, 11, 37)

**Archivo:** `models.py`

### Punto 11 — Mostrar vuelo en conexiones

**Pasos:**
1. En `print_simulation_output` (línea 381), el loop de flight_turns ya existe (línea 395-401)
2. Asegurar que se imprima `D<ID>-<origen>-<destino>` para cada turno de vuelo
3. El nombre de la conexión debe ser `f"{prev_hub.name}-{curr_hub.name}"`, NO `"Conn3"`

**Verificación:**
- Un dron volando hacia restricted debe mostrar:
  ```
  D1-s-h1    (turno 1, en vuelo)
  D1-h1      (turno 2, llegada)
  ```

### Punto 10 — Limpiar stdout

**Pasos:**
1. Asegurar que `print_simulation_output` solo use `print()` para las líneas de movimiento
2. Cualquier otra info (métricas, debug) → `sys.stderr.write()`
3. Verificar que no queden cabeceras "Turno NI:" ni "(Sin movimientos)"

**Verificación:**
- `python3 fly_ing.py mapa.txt | wc -l` = número exacto de turnos
- No hay nada más en stdout

### Punto 37 — Borrar código comentado

**Pasos:**
1. En `fly_ing.py`, borrar líneas comentadas de pruebas
2. Asegurar que no queden llamadas a `print_avances()`

---

## FASE 4 — Visual (punto 20)

**Archivo:** `fly_ing.py` y `visualizer.py`

**Pasos:**
1. En `fly_ing.py`, importar `TerminalVisualizer`:
   ```python
   from visualizer import TerminalVisualizer
   ```
2. Añadir flag `--visual` en `main()`:
   ```python
   is_visual = "--visual" in sys.argv
   ```
3. Crear el visualizer si el flag está activo
4. En `print_simulation_output`, llamar a `visualizer.render_turn()` por cada turno
5. Asegurar que la salida visual vaya por `sys.stderr` (no ensucia stdout)

**Verificación:**
- `python3 fly_ing.py mapa.txt --visual` muestra el mini-mapa
- `python3 fly_ing.py mapa.txt` (sin flag) no muestra visual
- El stdout sigue siendo solo líneas de movimiento

---

## FASE 5 — Calidad de código (puntos 23, 24, 25)

### Punto 23 — mypy 6 errores

**Pasos:**
1. Ejecutar `make lint` para ver los errores exactos
2. Arreglar cada uno:
   - `visualizer.py:83,86`: cambiar `Dict[str, int]` → `Dict[str, Tuple[int, int]]`
   - `models.py:185`: añadir `-> None` a `clear()`
   - `models.py:198,228`: cambiar tipo a `Optional[Hub]` o añadir assert
3. Verificar con `make lint`

### Punto 24 — Docstrings PEP 257

**Pasos:**
1. Añadir docstring a todas las clases (8 clases)
2. Añadir docstring a todas las funciones/métodos (35 funciones)
3. Formato Google:
   ```python
   def funcion(param: tipo) -> tipo:
       """Qué hace la función.
       
       Args:
           param: descripción.
       
       Returns:
           descripción.
       
       Raises:
           ValueError: cuándo.
       """
   ```

### Punto 25 — Código muerto

**Pasos:**
1. Buscar usos de cada función con `grep`
2. Si no se usa → borrar
3. Si se usa → mantener
4. Especial atención a: `Drone.location`, `in_transit`, `turn`, `has_arrived`, `get_drone_info`, `Solver.history`, `curr_turn`, `get_drones_in_hub`, `get_drones_in_con`, `can_move_hub`, `can_move_conn`

---

## FASE 6 — README (punto 27)

**Archivo:** `README.md` (crear en la raíz)

**Pasos:**
1. Crear `README.md` con:
   - Primera línea: `*This project has been created as part of the 42 curriculum by <login>.*`
   - Sección "Description"
   - Sección "Instructions" (make install / run / debug / lint / clean)
   - Sección "Resources" (referencias + cómo usaste IA)
   - Sección "Algorithm" (A* espacio-tiempo, tabla de reservas, esperas, restricted, priority, complejidad)
   - Sección "Visual Representation"

**Verificación:**
- `ls README.md` existe
- Todas las secciones presentes
- En inglés

---

## FASE 7 — Menores (opcional)

| Punto | Descripción | Tiempo |
|-------|-------------|--------|
| 6 | Quitar `id(hub)` del heap | 10 min |
| 9 | Dict de adyacencia | 15 min |
| 21 | Métricas secundarias | 15 min |
| 26 | Renombrar variables | 10 min |
| 29 | Mapas propios | 30 min |
| 31 | Estudiar para explicar | 30 min |
| 36 | Usage message | 2 min |
| 39 | Newline en stderr | 2 min |
| 40 | Magic number 700 | 5 min |
| 41 | Wait cost hack | 10 min |
| 42 | used_coords | 5 min |

---

## ORDEN RECOMENDADO DE TRABAJO

```
Día 1:
  Mañana:  Fase 1 (puntos 16, 13b, 12, 14+38) — 1 hora
  Tarde:   Fase 2 (punto 5) — 1-2 horas

Día 2:
  Mañana:  Fase 3 (puntos 11, 10, 37) — 1 hora
  Tarde:   Fase 4 (punto 20) — 1 hora

Día 3:
  Mañana:  Fase 5 (puntos 23, 24, 25) — 2 horas
  Tarde:   Fase 6 (punto 27) — 1 hora
  Extra:   Fase 7 (menores) — 1 hora
```

---

## VERIFICACIÓN FINAL

Antes de dar por terminado:

```bash
make lint                    # 0 errores
make run                     # funciona
make run MAP=maps/hard/02    # funciona
python3 fly_ing.py maps/easy/01.txt --visual  # visual OK
```

Los 10 mapas deben dar los mismos turnos que antes:
```
easy/01 4    easy/02 4    easy/03 4
medium/01 8  medium/02 15  medium/03 7
hard/01 13   hard/02 16   hard/03 26
challenger 43
```
