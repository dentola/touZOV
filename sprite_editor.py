import pygame
import sys
import math
import json
import os
from pygame.locals import *

# ---------- Настройки ----------
WIDTH, HEIGHT = 1024, 768
FPS = 60
BG_COLOR = (30, 30, 30)
PANEL_COLOR = (50, 50, 50)
GRID_COLOR = (70, 70, 70)
CELL_SIZE = 20
ZOOM_STEP = 1.2
MAX_UNDO = 50

# Палитра
PALETTE = [
    (0, 0, 0),       # чёрный (прозрачный)
    (255, 255, 255), # белый
    (255, 50, 50),   # красный
    (50, 255, 50),   # зелёный
    (50, 100, 255),  # синий
    (255, 255, 0),   # жёлтый
    (255, 165, 0),   # оранжевый
    (255, 105, 180), # розовый
    (200, 50, 255),  # пурпурный
    (0, 255, 255),   # циан
    (150, 220, 255), # лёд
    (210, 210, 225), # серебро
    (110, 0, 140),   # войд
    (255, 215, 0),   # золото
    (139, 69, 19),   # коричневый
    (0, 52, 89),     # тёмно-синий
    (255, 242, 232)  # #FFF2E8
]

ASCII_CHARS = " .ABCDEFGHIJKLMNOP"

# ---------- Функция копирования в буфер ----------
def copy_to_clipboard(text):
    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        root.clipboard_clear()
        root.clipboard_append(text)
        root.update()
        root.destroy()
        return True
    except:
        pass
    try:
        import subprocess
        subprocess.run(['xclip', '-selection', 'clipboard'], input=text.encode('utf-8'), check=True)
        return True
    except:
        pass
    try:
        import subprocess
        subprocess.run(['xsel', '-b'], input=text.encode('utf-8'), check=True)
        return True
    except:
        return False

# ---------- Класс редактора ----------
class SpriteEditor:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Спрайтовый редактор — TouZOV")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)

        self.canvas_sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64)]
        self.canvas_width, self.canvas_height = self.canvas_sizes[0]
        self.pixels = [[(0,0,0) for _ in range(self.canvas_width)] for _ in range(self.canvas_height)]
        self.zoom = 1.0
        self.offset_x = 300
        self.offset_y = 50

        self.tool = "brush"
        self.current_color = PALETTE[2]
        self.palette_index = 2

        self.undo_stack = []
        self.redo_stack = []

        self.drawing = False
        self.show_grid = True

        self.push_undo()

    def push_undo(self):
        snapshot = [row[:] for row in self.pixels]
        self.undo_stack.append(snapshot)
        if len(self.undo_stack) > MAX_UNDO:
            self.undo_stack.pop(0)
        self.redo_stack.clear()

    def undo(self):
        if len(self.undo_stack) > 1:
            self.redo_stack.append(self.undo_stack.pop())
            self.pixels = [row[:] for row in self.undo_stack[-1]]
        else:
            print("Нет действий для отмены")

    def redo(self):
        if self.redo_stack:
            self.undo_stack.append(self.redo_stack.pop())
            self.pixels = [row[:] for row in self.undo_stack[-1]]

    def set_pixel(self, x, y, color):
        if 0 <= x < self.canvas_width and 0 <= y < self.canvas_height:
            if self.pixels[y][x] != color:
                self.pixels[y][x] = color
                return True
        return False

    def flood_fill(self, x, y, new_color):
        if not (0 <= x < self.canvas_width and 0 <= y < self.canvas_height):
            return
        old_color = self.pixels[y][x]
        if old_color == new_color:
            return
        stack = [(x, y)]
        while stack:
            cx, cy = stack.pop()
            if not (0 <= cx < self.canvas_width and 0 <= cy < self.canvas_height):
                continue
            if self.pixels[cy][cx] == old_color:
                self.pixels[cy][cx] = new_color
                stack.append((cx+1, cy))
                stack.append((cx-1, cy))
                stack.append((cx, cy+1))
                stack.append((cx, cy-1))

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit(); sys.exit()
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    pygame.quit(); sys.exit()
                elif event.key == K_b:
                    self.tool = "brush"
                elif event.key == K_e:
                    self.tool = "eraser"
                elif event.key == K_f:
                    self.tool = "fill"
                elif event.key == K_g:
                    self.show_grid = not self.show_grid
                elif event.key == K_z and (event.mod & KMOD_CTRL):
                    self.undo()
                elif event.key == K_y and (event.mod & KMOD_CTRL):
                    self.redo()
                elif event.key == K_c and (event.mod & KMOD_CTRL):
                    self.copy_json()
                elif event.key == K_v and (event.mod & KMOD_CTRL):
                    self.copy_ascii()
            elif event.type == MOUSEBUTTONDOWN:
                if event.button == 1:
                    if self.is_size_click(event.pos):
                        continue
                    if self.is_palette_click(event.pos):
                        continue
                    if self.is_button_click(event.pos, "json"):
                        self.copy_json()
                        continue
                    if self.is_button_click(event.pos, "ascii"):
                        self.copy_ascii()
                        continue
                    if self.is_button_click(event.pos, "python"):
                        self.export_python()
                        continue
                    if self.is_button_click(event.pos, "clear"):
                        self.clear_canvas()
                        continue
                    if self.is_button_click(event.pos, "save"):
                        self.save_to_file()
                        continue
                    if self.is_button_click(event.pos, "load"):
                        self.load_from_file()
                        continue
                    self.drawing = True
                    self.handle_draw(event.pos)
                elif event.button == 4:
                    self.zoom *= ZOOM_STEP
                elif event.button == 5:
                    self.zoom /= ZOOM_STEP
            elif event.type == MOUSEBUTTONUP:
                if event.button == 1:
                    self.drawing = False
            elif event.type == MOUSEMOTION:
                if self.drawing:
                    self.handle_draw(event.pos)

    def is_size_click(self, pos):
        x, y = pos
        y_start = 10
        for i, (w, h) in enumerate(self.canvas_sizes):
            rect = pygame.Rect(300 + i*80, y_start, 70, 25)
            if rect.collidepoint(pos):
                self.change_canvas_size(w, h)
                return True
        return False

    def change_canvas_size(self, new_w, new_h):
        if (new_w, new_h) == (self.canvas_width, self.canvas_height):
            return
        self.canvas_width, self.canvas_height = new_w, new_h
        self.pixels = [[(0,0,0) for _ in range(self.canvas_width)] for _ in range(self.canvas_height)]
        self.zoom = 1.0
        self.offset_x = 300
        self.offset_y = 50
        self.undo_stack.clear()
        self.redo_stack.clear()
        self.push_undo()
        print(f"Холст изменён на {new_w}x{new_h}")

    def is_palette_click(self, pos):
        x, y = pos
        if 10 <= x <= 100 and 50 <= y <= 50 + len(PALETTE)*30:
            index = (y - 50) // 30
            if 0 <= index < len(PALETTE):
                self.current_color = PALETTE[index]
                self.palette_index = index
                return True
        return False

    def is_button_click(self, pos, action):
        buttons = {
            "json": pygame.Rect(10, HEIGHT-80, 120, 30),
            "ascii": pygame.Rect(140, HEIGHT-80, 120, 30),
            "python": pygame.Rect(270, HEIGHT-80, 130, 30),
            "clear": pygame.Rect(410, HEIGHT-80, 90, 30),
            "save": pygame.Rect(510, HEIGHT-80, 90, 30),
            "load": pygame.Rect(610, HEIGHT-80, 90, 30),
        }
        return buttons[action].collidepoint(pos)

    def handle_draw(self, mouse_pos):
        mx, my = mouse_pos
        cell_w = int(CELL_SIZE * self.zoom)
        cell_h = int(CELL_SIZE * self.zoom)
        grid_x = (mx - self.offset_x) // cell_w
        grid_y = (my - self.offset_y) // cell_h
        if 0 <= grid_x < self.canvas_width and 0 <= grid_y < self.canvas_height:
            if self.tool == "brush":
                self.set_pixel(grid_x, grid_y, self.current_color)
            elif self.tool == "eraser":
                self.set_pixel(grid_x, grid_y, (0,0,0))
            elif self.tool == "fill":
                self.flood_fill(grid_x, grid_y, self.current_color)
            self.push_undo()

    def clear_canvas(self):
        self.pixels = [[(0,0,0) for _ in range(self.canvas_width)] for _ in range(self.canvas_height)]
        self.push_undo()

    def get_pixel_hex_list(self):
        data = []
        for y in range(self.canvas_height):
            row = []
            for x in range(self.canvas_width):
                r, g, b = self.pixels[y][x]
                row.append(f"#{r:02x}{g:02x}{b:02x}")
            data.append(row)
        return data

    def copy_json(self):
        data = {
            "width": self.canvas_width,
            "height": self.canvas_height,
            "pixels": self.get_pixel_hex_list()
        }
        json_text = json.dumps(data, indent=2)
        print("=== JSON НАЧАЛО ===")
        print(json_text)
        print("=== JSON КОНЕЦ ===")
        if copy_to_clipboard(json_text):
            print("JSON скопирован в буфер!")

    def copy_ascii(self):
        lines = []
        for y in range(self.canvas_height):
            line = ""
            for x in range(self.canvas_width):
                color = self.pixels[y][x]
                best_index = 0
                best_dist = float('inf')
                for i, pal_color in enumerate(PALETTE):
                    dist = (color[0]-pal_color[0])**2 + (color[1]-pal_color[1])**2 + (color[2]-pal_color[2])**2
                    if dist < best_dist:
                        best_dist = dist
                        best_index = i
                line += ASCII_CHARS[best_index]
            lines.append(line)
        ascii_text = "\n".join(lines)
        print("=== ASCII НАЧАЛО ===")
        print(ascii_text)
        print("=== ASCII КОНЕЦ ===")
        if copy_to_clipboard(ascii_text):
            print("ASCII скопирован в буфер!")

    def export_python(self):
        pixel_data = self.get_pixel_hex_list()
        code = "def get_custom_sprite():\n"
        code += "    import pygame\n"
        code += "    pixel_data = " + json.dumps(pixel_data, indent=4) + "\n"
        code += f"    surf = pygame.Surface(({self.canvas_width}, {self.canvas_height}), pygame.SRCALPHA)\n"
        code += "    surf.fill((0,0,0,0))\n"
        code += "    for y, row in enumerate(pixel_data):\n"
        code += "        for x, hex_color in enumerate(row):\n"
        code += "            if hex_color == '#000000':\n"
        code += "                continue\n"
        code += "            r = int(hex_color[1:3], 16)\n"
        code += "            g = int(hex_color[3:5], 16)\n"
        code += "            b = int(hex_color[5:7], 16)\n"
        code += "            surf.set_at((x, y), (r, g, b, 255))\n"
        code += "    return surf\n"
        print("=== PYTHON КОД НАЧАЛО ===")
        print(code)
        print("=== PYTHON КОД КОНЕЦ ===")
        if copy_to_clipboard(code):
            print("Python-код скопирован в буфер!")

    def save_to_file(self):
        data = {
            "width": self.canvas_width,
            "height": self.canvas_height,
            "pixels": self.get_pixel_hex_list()
        }
        with open("sprite.json", "w") as f:
            json.dump(data, f, indent=2)
        print("Сохранено в sprite.json")

    def load_from_file(self):
        if os.path.exists("sprite.json"):
            with open("sprite.json", "r") as f:
                data = json.load(f)
            self.canvas_width = data["width"]
            self.canvas_height = data["height"]
            self.pixels = []
            for row in data["pixels"]:
                new_row = []
                for hex_color in row:
                    hex_color = hex_color.lstrip('#')
                    r = int(hex_color[0:2], 16)
                    g = int(hex_color[2:4], 16)
                    b = int(hex_color[4:6], 16)
                    new_row.append((r, g, b))
                self.pixels.append(new_row)
            self.zoom = 1.0
            self.push_undo()
            print("Загружено из sprite.json")

    def draw(self):
        self.screen.fill(BG_COLOR)

        pygame.draw.rect(self.screen, PANEL_COLOR, (0, 0, 120, HEIGHT))
        pygame.draw.rect(self.screen, (100,100,100), (0, 0, 120, HEIGHT), 2)

        for i, color in enumerate(PALETTE):
            rect = pygame.Rect(10, 50 + i*30, 80, 25)
            pygame.draw.rect(self.screen, color, rect)
            pygame.draw.rect(self.screen, (200,200,200), rect, 1)
            if self.palette_index == i:
                pygame.draw.rect(self.screen, (255,255,255), rect, 3)

        y = 50 + len(PALETTE)*30 + 20
        for tool, label in [("brush", "Кисть (B)"), ("eraser", "Ластик (E)"), ("fill", "Заливка (F)")]:
            color = (100,100,100) if self.tool != tool else (200,200,200)
            pygame.draw.rect(self.screen, color, (10, y, 100, 30))
            txt = self.small_font.render(label, True, (0,0,0))
            self.screen.blit(txt, (15, y+5))
            y += 35

        # Кнопки размера
        size_y = 10
        for i, (w, h) in enumerate(self.canvas_sizes):
            rect = pygame.Rect(300 + i*80, size_y, 70, 25)
            pygame.draw.rect(self.screen, (80,80,80), rect)
            if (w, h) == (self.canvas_width, self.canvas_height):
                pygame.draw.rect(self.screen, (255,255,255), rect, 2)
            txt = self.small_font.render(f"{w}x{h}", True, (255,255,255))
            self.screen.blit(txt, (rect.x+10, rect.y+3))

        cell_w = int(CELL_SIZE * self.zoom)
        cell_h = int(CELL_SIZE * self.zoom)
        for row in range(self.canvas_height):
            for col in range(self.canvas_width):
                color = self.pixels[row][col]
                rect = pygame.Rect(self.offset_x + col*cell_w, self.offset_y + row*cell_h, cell_w, cell_h)
                pygame.draw.rect(self.screen, color, rect)
                if self.show_grid:
                    pygame.draw.rect(self.screen, GRID_COLOR, rect, 1)

        buttons = [("json", "JSON"), ("ascii", "ASCII"), ("python", "Python"),
                   ("clear", "Очистить"), ("save", "Сохранить"), ("load", "Загрузить")]
        x_pos = 10
        for action, label in buttons:
            rect = pygame.Rect(x_pos, HEIGHT-80, 120 if action in ("json","ascii","python") else 90, 30)
            pygame.draw.rect(self.screen, (80,80,80), rect)
            txt = self.small_font.render(label, True, (255,255,255))
            self.screen.blit(txt, (rect.x+10, rect.y+5))
            x_pos += rect.width + 10

        info = f"Размер: {self.canvas_width}x{self.canvas_height}  Зум: {self.zoom:.1f}  Цвет: {self.current_color}"
        txt = self.small_font.render(info, True, (255,255,255))
        self.screen.blit(txt, (10, HEIGHT-110))

        pygame.display.flip()

    def run(self):
        while True:
            self.handle_events()
            self.draw()
            self.clock.tick(FPS)


if __name__ == "__main__":
    editor = SpriteEditor()
    editor.run()