import tkinter as tk

class MazeGame:
    def __init__(self, root, virtual_pen_callback=None, difficulty="medium"):
        self.root = root
        self.virtual_pen_callback = virtual_pen_callback
        self.difficulty = difficulty

        # Tamaño de la celda del laberinto
        self.cell_size = 40

        # Dimensiones del laberinto
        self.rows = 10
        self.cols = 10

        # Posición inicial del jugador
        self.player_pos = (0, 0)

        # Posición objetivo
        self.target_pos = (9, 9)

        # Generar la estructura del laberinto según la dificultad
        self.maze = self.generate_maze(self.difficulty)

        # Configuración del canvas
        self.canvas = tk.Canvas(self.root, width=self.cols * self.cell_size, height=self.rows * self.cell_size, bg="white")
        self.canvas.pack()

        # Dibujar el laberinto y el jugador
        self.draw_maze()
        self.draw_player()

        # Asignar teclas para el movimiento
        self.root.bind("<Up>", self.move_up)
        self.root.bind("<Down>", self.move_down)
        self.root.bind("<Left>", self.move_left)
        self.root.bind("<Right>", self.move_right)

    def generate_maze(self, difficulty):
        """Genera un laberinto según el nivel de dificultad."""
        if difficulty == "easy":
            return self.generate_easy_maze()
        elif difficulty == "medium":
            return self.generate_medium_maze()
        elif difficulty == "hard":
            return self.generate_hard_maze()

    def generate_easy_maze(self):
        """Genera el laberinto fácil"""
        maze = [[1 for _ in range(self.cols)] for _ in range(self.rows)]
        # Camino fácil
        maze[0][0] = 0
        maze[0][1] = 0
        maze[1][1] = 0
        maze[2][1] = 0
        maze[2][2] = 0
        maze[2][3] = 0
        maze[3][3] = 0
        maze[4][3] = 0
        maze[5][3] = 0
        maze[6][3] = 0
        maze[6][4] = 0
        maze[6][5] = 0
        maze[6][6] = 0
        maze[6][7] = 0
        maze[6][8] = 0
        maze[7][8] = 0
        maze[8][8] = 0
        maze[9][8] = 0  # Meta
        return maze

    def generate_medium_maze(self):
        """Genera el laberinto intermedio"""
        maze = [[1 for _ in range(self.cols)] for _ in range(self.rows)]
        # Camino intermedio
        row, col = 0, 0
        while row < self.rows and col < self.cols:
            maze[row][col] = 0
            if col < self.cols - 1:
                col += 1
            else:
                break
            maze[row][col] = 0
            if row < self.rows - 1:
                row += 1
            else:
                break
        return maze

    def generate_hard_maze(self):
        """Genera el laberinto difícil"""
        maze = [[1 for _ in range(self.cols)] for _ in range(self.rows)]

        # Camino difícil con más obstáculos
        maze[0][0] = 0
        maze[1][0] = 0
        maze[1][1] = 0
        maze[2][1] = 0
        maze[3][1] = 0
        maze[3][2] = 0
        maze[3][3] = 0
        maze[3][4] = 0
        maze[4][4] = 0
        maze[5][4] = 0
        maze[5][5] = 0
        maze[5][6] = 0
        maze[5][7] = 0
        maze[6][7] = 0
        maze[7][7] = 0
        maze[8][7] = 0
        maze[8][8] = 0
        maze[9][8] = 0  # Meta

        # Agregar más obstáculos alrededor
        maze[4][2] = 1
        maze[4][3] = 1
        maze[7][5] = 1
        maze[6][6] = 1
        maze[9][6] = 1

        return maze

    def draw_maze(self):
        """Dibuja el laberinto basado en la matriz."""
        for i in range(self.rows):
            for j in range(self.cols):
                x1 = j * self.cell_size
                y1 = i * self.cell_size
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size

                if self.maze[i][j] == 1:
                    # Dibuja una celda como pared
                    self.canvas.create_rectangle(x1, y1, x2, y2, fill="black", outline="black")
                elif self.maze[i][j] == 0:
                    # Dibuja un camino
                    self.canvas.create_rectangle(x1, y1, x2, y2, fill="white", outline="black")
        
        # Dibuja la meta (cuadrado rojo)
        x1 = self.target_pos[1] * self.cell_size
        y1 = self.target_pos[0] * self.cell_size
        x2 = x1 + self.cell_size
        y2 = y1 + self.cell_size
        self.canvas.create_rectangle(x1, y1, x2, y2, fill="red", outline="black")

    def draw_player(self):
        """Dibuja al jugador."""
        x1 = self.player_pos[1] * self.cell_size + 5
        y1 = self.player_pos[0] * self.cell_size + 5
        x2 = x1 + self.cell_size - 10
        y2 = y1 + self.cell_size - 10
        self.canvas.create_oval(x1, y1, x2, y2, fill="blue", tag="player")

    def move_player(self, new_pos):
        """Mueve al jugador si la posición es válida."""
        row, col = new_pos
        if 0 <= row < self.rows and 0 <= col < self.cols and self.maze[row][col] == 0:
            self.player_pos = (row, col)
            self.check_target_reached()
            self.redraw_player()

    def redraw_player(self):
        """Redibuja al jugador."""
        self.canvas.delete("player")
        self.draw_player()

    def check_target_reached(self):
        """Verifica si el jugador alcanzó la meta."""
        if self.player_pos == self.target_pos:
            self.canvas.create_text(
                self.cols * self.cell_size // 2,
                self.rows * self.cell_size // 2,
                text="¡Meta alcanzada!",
                font=("Arial", 24),
                fill="green",
                tag="message"
            )

    def move_up(self, event):
        """Mueve al jugador hacia arriba."""
        row, col = self.player_pos
        self.move_player((row - 1, col))

    def move_down(self, event):
        """Mueve al jugador hacia abajo."""
        row, col = self.player_pos
        self.move_player((row + 1, col))

    def move_left(self, event):
        """Mueve al jugador hacia la izquierda."""
        row, col = self.player_pos
        self.move_player((row, col - 1))

    def move_right(self, event):
        """Mueve al jugador hacia la derecha."""
        row, col = self.player_pos
        self.move_player((row, col + 1))
