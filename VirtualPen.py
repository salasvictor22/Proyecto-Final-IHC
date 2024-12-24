#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Virtual Pen App with Interactive Canvas
"""

# Importar los paquetes necesarios
from collections import deque
from imutils.video import VideoStream
import numpy as np
import cv2
import imutils
import time
import tkinter as tk
from tkinter import Canvas
import threading
from maze_game import MazeGame


# Configurar la ventana de Tkinter
root = tk.Tk()
root.title("Virtual Pen with Interactive Canvas")
root.geometry("800x600")

# Variables globales
running = False
pts = deque(maxlen=1024)
line_color = (0, 0, 255)

# Definir límites de color en el espacio de color HSV (valores iniciales)
greenLower = (100, 150, 50)
greenUpper = (140, 255, 255)

# Variables para el modo de dibujo en la pizarra
drawing = False
last_x, last_y = None, None

# Inicializar la pizarra interactiva
canvas = Canvas(root, width=600, height=400, bg="white")
canvas.pack(pady=20)

# Función para manejar el dibujo en la pizarra
def start_drawing(event):
    global drawing, last_x, last_y
    drawing = True
    last_x, last_y = event.x, event.y

def stop_drawing(event):
    global drawing
    drawing = False

def rgb_to_hex(rgb):
    return '#{:02x}{:02x}{:02x}'.format(rgb[0], rgb[1], rgb[2])
    
def draw_on_canvas(event):
    global drawing, last_x, last_y
    if drawing:
        canvas.create_line(last_x, last_y, event.x, event.y, fill=line_color, width=2)
        last_x, last_y = event.x, event.y

# Función para sincronizar el lápiz virtual con la pizarra
def draw_virtual_on_canvas(center):
    if center is not None:
        x, y = center
        hex_color = rgb_to_hex(line_color)  # Convertir el color RGB a hexadecimal
        canvas.create_oval(x - 2, y - 2, x + 2, y + 2, fill=hex_color)

# Configuración de eventos de la pizarra
canvas.bind("<ButtonPress-1>", start_drawing)
canvas.bind("<B1-Motion>", draw_on_canvas)
canvas.bind("<ButtonRelease-1>", stop_drawing)

# Función para iniciar el flujo de video
def start_stream():
    global running
    running = True
    thread = threading.Thread(target=run_video_stream)
    thread.start()


# Función para cambiar el color de la línea
def set_line_color(color):
    global line_color
    line_color = color 

# Función para borrar la pantalla
def clear_screen():
    pts.clear()  # Limpia el deque
    canvas.delete("all")  # Borra todo del canvas

# Función para actualizar el rango de color HSV
def update_color_range():
    global greenLower, greenUpper
    try:
        greenLower = (
            int(hue_low_entry.get()), int(sat_low_entry.get()), int(val_low_entry.get())
        )
        greenUpper = (
            int(hue_high_entry.get()), int(sat_high_entry.get()), int(val_high_entry.get())
        )
    except ValueError:
        print("Por favor ingresa valores válidos para el rango de color.")

# Función para cerrar la aplicación
def close_app():
    global running
    running = False
    root.quit()

# Función principal para el procesamiento del video
def run_video_stream():
    global running
    vs = VideoStream(src=0).start()
    time.sleep(2.0)

    while running:
        frame = vs.read()
        frame = cv2.flip(frame, 1)
        frame = imutils.resize(frame, width=600)
        blurred = cv2.GaussianBlur(frame, (11, 11), 0)
        hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

        mask = cv2.inRange(hsv, greenLower, greenUpper)
        mask = cv2.erode(mask, None, iterations=2)
        mask = cv2.dilate(mask, None, iterations=2)

        cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)
        center = None

        if len(cnts) > 0:
            c = max(cnts, key=cv2.contourArea)
            ((x, y), radius) = cv2.minEnclosingCircle(c)
            M = cv2.moments(c)
            center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))

        pts.appendleft(center)

        # Dibujar las líneas del lápiz virtual
        for i in range(1, len(pts)):
            if pts[i - 1] is None or pts[i] is None:
                continue
            thickness = int(np.sqrt(1024 / float(i + 1)) * 2.5)
            cv2.line(frame, pts[i - 1], pts[i], line_color, thickness)

        # Sincronizar con la pizarra
        if center:
            draw_virtual_on_canvas(center)

        cv2.imshow("Virtual Pen", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break

    vs.stop()
    cv2.destroyAllWindows()
    
def start_maze_game():
    """Lanza la ventana del laberinto."""
    maze_window = tk.Toplevel(root)  # Crea una nueva ventana secundaria
    maze_window.title("Laberinto")
    MazeGame(maze_window, virtual_pen_callback=None)  # Inicia el laberinto en la nueva ventana

# Función para obtener la posición del lápiz virtual
def virtual_pen_callback():
    if pts and pts[0] is not None:
        return pts[0]
    return (0, 0)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Virtual Pen App with Interactive Maze Game
"""

import cv2
import numpy as np
import tkinter as tk
from tkinter import messagebox

class MazeGame:
    def __init__(self, master, virtual_pen_callback, level="easy"):
        self.master = master
        self.virtual_pen_callback = virtual_pen_callback
        self.level = level  # Determina el nivel del laberinto (easy, medium, hard)

        # Configurar el canvas para mostrar el laberinto
        self.canvas = tk.Canvas(master, width=400, height=400, bg="white")
        self.canvas.pack()

        # Crear el laberinto según el nivel
        self.maze_size = 8  # Tamaño del laberinto 8x8
        self.cell_size = 50  # Tamaño de cada celda
        self.start = (0, 0)  # Coordenadas iniciales
        self.end = (7, 7)  # Coordenadas finales
        self.create_maze()

        # Inicializar la posición actual del lápiz
        self.current_position = [self.start[0] * self.cell_size, self.start[1] * self.cell_size]
        self.draw_cursor()

        # Iniciar el bucle de detección
        self.running = True
        self.check_collision()

    def create_maze(self):
        """Dibuja el laberinto en el canvas según el nivel de dificultad."""
        self.maze_image = np.ones((self.maze_size * self.cell_size, self.maze_size * self.cell_size, 3), dtype=np.uint8) * 255

        # Define paredes para diferentes niveles de dificultad
        if self.level == "easy 1":
            walls = [
                    (2, 0), (2, 1), (2, 2), (2, 3), (2, 4), (2, 5),
                    (3, 0), (3, 1), (3, 2), (3, 3), (3, 4), (3, 5), 
                    (4, 0), (4, 1), (4, 2), (4, 3), (4, 4), (4, 5), 
                    (5, 0), (5, 1), (5, 2), (5, 3), (5, 4), (5, 5), 
                    (6, 0), (6, 1), (6, 2), (6, 3), (6, 4), (6, 5),  
                    (7, 0), (7, 1), (7, 2), (7, 3), (7, 4), (7, 5),
                    ]
        elif self.level == "easy 2":
            walls = [
                    (0, 5), (0, 6), (0, 7),  
                    (1, 5), (1, 6), (1, 7),  
                    (2, 0), (2, 1), (2, 2), (2, 5), (2, 6), (2, 7),  
                    (3, 0), (3, 1), (3, 2), (3, 5), (3, 6), (3, 7),  
                    (4, 0), (4, 1), (4, 2), (4, 5), (4, 6), (4, 7),  
                    (5, 0), (5, 1), (5, 2), (5, 5), (5, 6), (5, 7),  
                    (6, 0), (6, 1), (6, 2),   
                    (7, 0), (7, 1), (7, 2), 
                    ]
        elif self.level == "medium 1":
            walls = [
                    (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (0, 6), (0, 7),  
                    (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7),  
                    (2, 0), (2, 3), (2, 4), (2, 5), (2, 6), (2, 7),  
                    (3, 0), (3, 1), (3, 4), (3, 5), (3, 6), (3, 7),  
                    (4, 0), (4, 1), (4, 2), (4, 5), (4, 6), (4, 7),  
                    (5, 0), (5, 1), (5, 2), (5, 3), (5, 6), (5, 7),  
                    (6, 0), (6, 1), (6, 2), (6, 3), (6, 4), (6, 7),  
                    (7, 0), (7, 1), (7, 2), (7, 3), (7, 4), (7, 5), ]
        elif self.level == "medium 2":
            walls = [
                    (0, 4), (0, 5), (0, 6), (0, 7),  
                    (1, 0), (1, 1), (1, 2), (1, 5), (1, 6), (1, 7),  
                    (2, 0), (2, 1), (2, 2), (2, 6), (2, 7),
                    (3, 0), (3, 1), (3, 2), (3, 3), (3, 4), (3, 7),  
                    (4, 0), (4, 1), (4, 2), (4, 3), (4, 4), (4, 7),  
                    (5, 0), (5, 1), (5, 2), (5, 3), (5, 6), (5, 7),  
                    (6, 0), (6, 1), (6, 2), (6, 5), (6, 6), (6, 7),  
                    (7, 0), (7, 1), (7, 2),
                    ]
        elif self.level == "hard 2":
            walls = [
                    (0, 3), (0, 7),  
                    (1, 0), (1, 1), (1, 3), (1, 5), (1, 7),  
                    (2, 0), (2, 1), (2, 5),  
                    (3, 0), (3, 1), (3, 2), (3, 3),(3, 4), (3, 5), (3, 6),  
                    (4, 5),  
                    (5, 1), (5, 2), (5, 3), (5, 7),  
                    (6, 3), (6, 4), (6, 5), (6, 6), (6, 7),  
                    (7, 0), (7, 1), 
                    ]            
        elif self.level == "hard 1":
            walls = [
                    (0, 7), (1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (1, 7),
                    (2, 0), (2, 4), (2, 7),
                    (3, 2), (3, 6), (3, 7),
                    (4, 3), (4, 1), (4, 2), (4, 4), (4, 5), (4, 6), (4, 7),
                    (5, 2), (5, 6), (5, 7), 
                    (6, 0), (6, 2), (6, 4), (6, 6), (6, 7),
                    (7, 0), (7, 4), 
            ]

        # Dibujar las paredes del laberinto
        for i, j in walls:
            x1, y1 = i * self.cell_size, j * self.cell_size
            x2, y2 = x1 + self.cell_size, y1 + self.cell_size
            self.canvas.create_rectangle(x1, y1, x2, y2, fill="black")

        # Dibujar inicio y final
        start_x, start_y = self.start[0] * self.cell_size, self.start[1] * self.cell_size
        end_x, end_y = self.end[0] * self.cell_size, self.end[1] * self.cell_size
        self.canvas.create_rectangle(start_x, start_y, start_x + self.cell_size, start_y + self.cell_size, fill="green")
        self.canvas.create_rectangle(end_x, end_y, end_x + self.cell_size, end_y + self.cell_size, fill="red")

    def draw_cursor(self):
        """Dibuja el cursor actual en el canvas."""
        x, y = self.current_position
        self.cursor = self.canvas.create_oval(x, y, x + 10, y + 10, fill="blue")

    def update_cursor(self, position):
        """Actualiza la posición del cursor."""
        self.current_position = [position[0] - 5, position[1] - 5]
        self.canvas.coords(self.cursor, self.current_position[0], self.current_position[1],
                           self.current_position[0] + 10, self.current_position[1] + 10)

    def check_collision(self):
        """Verifica si el cursor toca una pared o llega al final."""
        if not self.running:
            return

        # Obtener la posición actual del lápiz virtual
        position = self.virtual_pen_callback()
        if position:
            self.update_cursor(position)

            # Convertir las coordenadas a índices del laberinto
            x, y = self.current_position[0] + 5, self.current_position[1] + 5
            i, j = x // self.cell_size, y // self.cell_size

            # Verificar si toca una pared
            if self.canvas.find_overlapping(x, y, x, y):
                overlapping_items = self.canvas.find_overlapping(x, y, x, y)
                for item in overlapping_items:
                    color = self.canvas.itemcget(item, "fill")
                    if color == "black":
                        messagebox.showerror("Error", "¡Te chocaste con una pared! Intenta de nuevo.")
                        self.reset_game()
                        return

            # Verificar si llegó al final
            if (i, j) == self.end:
                messagebox.showinfo("Victoria", "¡Llegaste a la meta! Felicitaciones.")
                self.running = False
                return

        self.master.after(50, self.check_collision)

    def reset_game(self):
        """Reinicia el juego."""
        self.current_position = [self.start[0] * self.cell_size, self.start[1] * self.cell_size]
        self.canvas.coords(self.cursor, self.current_position[0], self.current_position[1],
                           self.current_position[0] + 10, self.current_position[1] + 10)
        self.running = True
        self.check_collision()


def start_maze_game(level, virtual_pen_callback):
    """Inicia el juego del laberinto con las coordenadas del lápiz virtual."""
    maze_window = tk.Toplevel()
    maze_window.title(f"Laberinto - Nivel {level.capitalize()}")
    MazeGame(maze_window, virtual_pen_callback, level)


# Botones para seleccionar el nivel del laberinto
frame_levels = tk.Frame(root)
frame_levels.pack(pady=10)

easy_button = tk.Button(frame_levels, text="Laberinto Nivel 1", command=lambda: start_maze_game("easy 1", virtual_pen_callback))
easy_button.grid(row=0, column=0, padx=5)

medium_button = tk.Button(frame_levels, text="Laberinto Nivel 2", command=lambda: start_maze_game("easy 2", virtual_pen_callback))
medium_button.grid(row=0, column=1, padx=5)

hard_button = tk.Button(frame_levels, text="Laberinto Nivel 3", command=lambda: start_maze_game("medium 1", virtual_pen_callback))
hard_button.grid(row=0, column=2, padx=5)

easy_button = tk.Button(frame_levels, text="Laberinto Nivel 4", command=lambda: start_maze_game("medium 2", virtual_pen_callback))
easy_button.grid(row=0, column=4, padx=5)

medium_button = tk.Button(frame_levels, text="Laberinto Nivel 5", command=lambda: start_maze_game("hard 2", virtual_pen_callback))
medium_button.grid(row=0, column=5, padx=5)

hard_button = tk.Button(frame_levels, text="Laberinto Nivel 6", command=lambda: start_maze_game("hard 1", virtual_pen_callback))
hard_button.grid(row=0, column=6, padx=5)


# Configuración de la interfaz gráfica
frame_buttons = tk.Frame(root)
frame_buttons.pack(pady=10)

start_button = tk.Button(frame_buttons, text="Iniciar", command=start_stream)
start_button.grid(row=0, column=0, padx=5)

clear_button = tk.Button(frame_buttons, text="Borrar", command=clear_screen)
clear_button.grid(row=0, column=1, padx=5)

close_button = tk.Button(frame_buttons, text="Cerrar", command=close_app)
close_button.grid(row=0, column=2, padx=5)


frame_colors = tk.Frame(root)
frame_colors.pack(pady=10)

red_button = tk.Button(frame_colors, text="Rojo", bg="red", command=lambda: set_line_color((255, 0, 0)))
red_button.grid(row=0, column=0, padx=5)

blue_button = tk.Button(frame_colors, text="Azul", bg="blue", command=lambda: set_line_color((0, 0, 255)))
blue_button.grid(row=0, column=1, padx=5)

green_button = tk.Button(frame_colors, text="Verde", bg="green", command=lambda: set_line_color((0, 255, 0)))
green_button.grid(row=0, column=2, padx=5)

yellow_button = tk.Button(frame_colors, text="Amarillo", bg="yellow", command=lambda: set_line_color((255, 255, 0)))
yellow_button.grid(row=0, column=3, padx=5)

brown_button = tk.Button(frame_colors, text="Café", bg="#8B4513", command=lambda: set_line_color((139, 69, 19)))
brown_button.grid(row=0, column=4, padx=5)

gray_button = tk.Button(frame_colors, text="Gris", bg="gray", command=lambda: set_line_color((128, 128, 128)))
gray_button.grid(row=0, column=5, padx=5)

purple_button = tk.Button(frame_colors, text="Morado", bg="purple", command=lambda: set_line_color((128, 0, 128)))
purple_button.grid(row=0, column=6, padx=5)

orange_button = tk.Button(frame_colors, text="Anaranjado", bg="orange", command=lambda: set_line_color((255, 165, 0)))
orange_button.grid(row=0, column=7, padx=5)

light_blue_button = tk.Button(frame_colors, text="Celeste", bg="#87CEEB", command=lambda: set_line_color((0, 255, 255)))
light_blue_button.grid(row=0, column=8, padx=5)

black_button = tk.Button(frame_colors, text="Negro", bg="black", fg="white", command=lambda: set_line_color((0, 0, 0)))
black_button.grid(row=0, column=9, padx=5)


frame_color_range = tk.Frame(root)
frame_color_range.pack(pady=10)

tk.Label(frame_color_range, text="Hue Lower").grid(row=0, column=0)
hue_low_entry = tk.Entry(frame_color_range, width=5)
hue_low_entry.insert(0, greenLower[0])
hue_low_entry.grid(row=0, column=1)

tk.Label(frame_color_range, text="Hue Upper").grid(row=0, column=2)
hue_high_entry = tk.Entry(frame_color_range, width=5)
hue_high_entry.insert(0, greenUpper[0])
hue_high_entry.grid(row=0, column=3)

tk.Label(frame_color_range, text="Saturation Lower").grid(row=1, column=0)
sat_low_entry = tk.Entry(frame_color_range, width=5)
sat_low_entry.insert(0, greenLower[1])
sat_low_entry.grid(row=1, column=1)

tk.Label(frame_color_range, text="Saturation Upper").grid(row=1, column=2)
sat_high_entry = tk.Entry(frame_color_range, width=5)
sat_high_entry.insert(0, greenUpper[1])
sat_high_entry.grid(row=1, column=3)

tk.Label(frame_color_range, text="Value Lower").grid(row=2, column=0)
val_low_entry = tk.Entry(frame_color_range, width=5)
val_low_entry.insert(0, greenLower[2])
val_low_entry.grid(row=2, column=1)

tk.Label(frame_color_range, text="Value Upper").grid(row=2, column=2)
val_high_entry = tk.Entry(frame_color_range, width=5)
val_high_entry.insert(0, greenUpper[2])
val_high_entry.grid(row=2, column=3)

apply_button = tk.Button(root, text="Aplicar Rango de Color", command=update_color_range)
apply_button.pack(pady=10)

root.protocol("WM_DELETE_WINDOW", close_app)
root.mainloop()
