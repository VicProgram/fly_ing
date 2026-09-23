import sys
from models import ansi_colors

class TerminalVisualizer:
    def __init__(self, map_data):
        self.map = map_data
        self.hubs = list(map_data.hubs.values())
        
        # Calcular dimensiones del mapa 2D
        if self.hubs:
            self.min_x = min(h.x for h in self.hubs)
            self.max_x = max(h.x for h in self.hubs)
            self.min_y = min(h.y for h in self.hubs)
            self.max_y = max(h.y for h in self.hubs)
        else:
            self.min_x = self.max_x = self.min_y = self.max_y = 0

    def render_turn(self, turn: int, drone_positions: dict, total_drones: int, delivered: int):
        """
        Renders a ASCII frame for the current turn to sys.stderr.
        drone_positions: dict {hub_name: count_of_drones}
        """
        sys.stderr.write(f"\n--- [ TURNO {turn} ] ---\n")
        
        # Escalado simple para rejilla ASCII
        width = max(self.max_x - self.min_x + 1, 1)
        height = max(self.max_y - self.min_y + 1, 1)
        
        # Crear matriz vacía
        grid = [[" . " for _ in range(width)] for _ in range(height)]
        
        # Colocar Hubs en la rejilla
        for hub in self.hubs:
            gx = hub.x - self.min_x
            gy = hub.y - self.min_y
            
            # Obtener color ANSI
            color_code = ansi_colors.get(getattr(hub, "color", "white").lower(), ansi_colors["RESET"])
            
            # Formato de representación (ejemplo: [A:2] si hay drones, o [A])
            drones_here = drone_positions.get(hub.name, 0)
            label = f"{hub.name[:2]}:{drones_here}" if drones_here > 0 else f"{hub.name[:3]}"
            
            grid[gy][gx] = f"{color_code}[{label:^3}]{ansi_colors['RESET']}"

        # Imprimir mapa (invertimos Y para que el origen (0,0) esté abajo a la izquierda)
        for row in reversed(grid):
            sys.stderr.write(" ".join(row) + "\n")
            
        # Telemetría básica
        sys.stderr.write(f"Estado: {delivered}/{total_drones} drones entregados.\n")
        sys.stderr.flush()


import sys
from visualizer import TerminalVisualizer

def main():
    if len(sys.argv) < 2:
        sys.exit(1)
        
    map_path = sys.argv[1]
    is_visual = "--visual" in sys.argv

    # 1. Parsear mapa y resolver rutas
    # map_data, simulation_turns = solve_simulation(map_path)
    
    # 2. Si piden visualización, inicializar
    visualizer = TerminalVisualizer(map_data) if is_visual else None

    # 3. Bucle de ejecución/impresión por turnos
    for turn, step_info in enumerate(simulation_turns):
        
        # Salida estándar obligatoria por el subject (NO cambiar)
        print(step_info["stdout_line"])
        
        # Si está activado --visual, mandamos el frame gráfico por stderr
        if visualizer:
            visualizer.render_turn(
                turn=turn,
                drone_positions=step_info["drone_hub_counts"],
                total_drones=step_info["total_drones"],
                delivered=step_info["delivered_count"]
            )

if __name__ == "__main__":
    main()