#
# COMPROBAR BIEN!!!!
#
#
import tkinter as tk
import time
from typing import Dict, Tuple, List


class DroneVisualizer:
    def __init__(
        self,
        hubs_coords: Dict[str, Tuple[int, int]],
        connections: List[Tuple[str, str]],
    ):
        self.root = tk.Tk()
        self.root.title("Fly-in Drone Simulation")
        self.canvas = tk.Canvas(self.root, width=800, height=600, bg="#1e1e1e")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.coords = hubs_coords
        self.connections = connections
        self.node_radius = 20
        self.drones: Dict[str, int] = {}  # id_dron -> id_circulo_canvas

        # Mapear coordenadas del mapa a la pantalla (escalado simple)
        self._scale_coordinates()
        self._draw_graph()

    def _scale_coordinates(self) -> None:
        """Escala las coordenadas (x,y) del mapa para que quepan."""
        xs = [c[0] for c in self.coords.values()]
        ys = [c[1] for c in self.coords.values()]

        min_x, max_x = min(xs, default=0), max(xs, default=1)
        min_y, max_y = min(ys, default=0), max(ys, default=1)

        for name, (x, y) in self.coords.items():
            screen_x = 100 + (x - min_x) / (max_x - min_x + 1e-5) * 600
            screen_y = 100 + (y - min_y) / (max_y - min_y + 1e-5) * 400
            self.coords[name] = (int(screen_x), int(screen_y))

    def _draw_graph(self) -> None:
        """Dibuja las conexiones (líneas) y los hubs (círculos)."""
        # Dibujar líneas de conexión
        for u, v in self.connections:
            x1, y1 = self.coords[u]
            x2, y2 = self.coords[v]
            self.canvas.create_line(x1, y1, x2, y2, fill="#555555", width=2)

        # Dibujar hubs
        for name, (x, y) in self.coords.items():
            r = self.node_radius
            self.canvas.create_oval(
                x - r, y - r, x + r, y + r,
                fill="#2d2d2d", outline="#00ffcc", width=2,
            )
            self.canvas.create_text(
                x, y + r + 12, text=name, fill="white",
                font=("Arial", 9, "bold"),
            )

    def animate_turn(
        self,
        turn_moves: List[Tuple[str, str]],
        delay: float = 0.5,
    ) -> None:
        """Actualiza la posición de los drones para un turno determinado."""
        for drone_id, target_hub in turn_moves:
            tx, ty = self.coords[target_hub]
            r = 12  # Tamaño del dron

            if drone_id not in self.drones:
                # Si el dron no existe aún en pantalla, lo creamos
                drone_obj = self.canvas.create_oval(
                    tx - r, ty - r, tx + r, ty + r,
                    fill="#ff4757", outline="white", width=1.5,
                )
                label_obj = self.canvas.create_text(
                    tx, ty, text=drone_id, fill="white",
                    font=("Arial", 8, "bold"),
                )
                self.drones[drone_id] = (drone_obj, label_obj)
            else:
                # Si ya existe, lo movemos al nuevo hub
                drone_obj, label_obj = self.drones[drone_id]
                self.canvas.coords(drone_obj, tx-r, ty-r, tx+r, ty+r)
                self.canvas.coords(label_obj, tx, ty)

        self.root.update()
        time.sleep(delay)  # Pausa visual entre turnos

    def start(self) -> None:
        """Mantiene la ventana abierta al finalizar la simulación."""
        self.root.mainloop()
