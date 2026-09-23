*Este proyecto ha sido creado como parte del curriculum de 42 por <vabad-ro>.*

# Fly_ing — Simulador de Búsqueda de Caminos Espacio-Temporales para Drones

## Descripción
**Fly_ing** es un simulador óptimo de planificación y enrutamiento para múltiples drones desarrollado en Python. El programa modela la búsqueda de rutas en el espacio-tiempo sobre un grafo compuesto por ubicaciones (`hubs`) y conexiones bidireccionales (`connections`).

El objetivo principal es guiar a una flota de $N$ drones desde un punto de origen (`start_hub`) hasta un punto de destino (`end_hub`) en el menor número posible de turnos de simulación. El algoritmo gestiona estrictamente las colisiones espaciales, los embotellamientos en conexiones, los retrasos por zonas restringidas y las restricciones de capacidad en cada hub mediante una tabla de reservas espacio-temporal.

---

## Instrucciones

### Requisitos Previos
- Python 3.10 o superior.
- Utilidades de desarrollo Unix estándar (`make`).

### Comandos del Makefile
El proyecto incluye un `Makefile` para facilitar la ejecución, pruebas y linteo:

```bash
# Mostrar la ayuda y los comandos disponibles
make help

# Ejecutar la simulación con el mapa por defecto
make run

# Ejecutar la simulación con un mapa específico
make run MAP=maps/map1.txt

# Ejecutar la simulación con el modo visualizador interactivo
make run MAP=maps/map1.txt ARGS="--visual"

# Comprobación de calidad del código (flake8 / mypy)
make lint

# Limpiar archivos temporales, bytecode y caché
make clean

Uso DirectoBashpython3 fly_ing.py <ruta_al_mapa> [--visual]
Algoritmo y Arquitectura1. Algoritmo A* Espacio-TemporalEl núcleo de búsqueda utiliza una extensión del algoritmo A* Espacio-Temporal sobre un espacio de estados definido como $(u, t)$, donde $u$ representa el Hub actual y $t$ el turno de simulación.Espacio de Estados: Cada nodo del árbol de búsqueda representa una ubicación física en un instante de tiempo específico.Función de Coste $f(n) = g(n) + h(n)$:$g(n)$: Coste/tiempo acumulado desde el start_hub hasta el nodo $n$.$h(n)$: Heurística BFS calculada en sentido inverso desde el end_hub para estimar la distancia topológica mínima.Costes de Travesía: La duración del trayecto depende del tipo de zona:priority: Coste = 1 turno (priorizado en el desempate).normal: Coste = 1 turno.restricted: Coste = 2 turnos.blocked: Inaccesible (Coste = $\infty$).2. Tabla de Reservas (Prioritized Planning)Para garantizar una navegación libre de colisiones, los drones se planifican secuencialmente ($D_1, D_2, \dots, D_N$). Las rutas calculadas reservan su uso en una ReservationTable global:Reserva de Hubs: Garantiza que no se supere la capacidad max_drones en el turno $t$.Reserva de Conexiones: Reserva la capacidad del enlace durante toda la duración del tránsito (por ejemplo, en $[t, t+1]$ y $[t+1, t+2]$ para zonas restringidas).3. Espera Deliberada y Desempate con PrioridadCuando los canales principales están saturados, un dron puede esperar en su hub actual durante $1$ turno ($u \to u$ en $t+1$). Se aplica una pequeña penalización de desempate ($+0.0001$) a las esperas para priorizar rutas alternativas activas frente a quedarse parado cuando ambas opciones ofrecen el mismo coste.4. Complejidad y LimitacionesComplejidad Temporal: $O(N \cdot (\vert{}V\vert{} \cdot T \log(\vert{}V\vert{} \cdot T) + \vert{}E\vert{} \cdot T))$, donde $N$ es el número de drones, $V$ los hubs, $E$ las conexiones y $T$ el horizonte temporal máximo.Complejidad Espacial: $O(\vert{}V\vert{} \cdot T)$ para almacenar la tabla de reservas y estados.Limitaciones: El algoritmo de Planificación Priorizada no garantiza el óptimo global (requeriría un enfoque CBS / Cooperative Pathfinding). Los primeros drones planificados pueden reservar cuellos de botella clave, obligando a los siguientes a tomar rutas secundarias o realizar esperas.Representación Visual (--visual)Al ejecutar el programa con la bandera --visual, se activa un renderizador en terminal basado en códigos ANSI:Proyección Topológica: Muestra una representación del mapa en 2D (ASCII) utilizando las coordenadas $(x, y)$ definidas en el archivo del mapa.Colores ANSI: Renderiza cada hub respetando el color especificado en su atributo color=.Métricas en Tiempo Real:Ocupación actual de hubs ([Actual / Máximo]).Drones en tránsito a través de las conexiones.Total de drones entregados frente a drones activos por turno.Valor DiagnósticoEl visualizador en terminal permite identificar de forma inmediata cuellos de botella, validar el uso de rutas alternativas y comprobar que las restricciones de capacidad y las esperas se están aplicando correctamente durante la simulación.Recursos y Uso de Inteligencia ArtificialReferenciasSilver, D. (2005). Cooperative Pathfinding. Proceedings of the AIIDE.Hart, P. E., Nilsson, N. J., & Raphael, B. (1968). A Formal Basis for the Heuristic Determination of Minimum Cost Grid Paths. IEEE Transactions on Systems Science and Cybernetics.