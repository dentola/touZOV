import pygame
import json
import os
import sys

SCREEN_WIDTH, SCREEN_HEIGHT = 1920, 1080
WINDOW_TITLE = "TouZOV"
FPS = 60

PLAYFIELD_WIDTH, PLAYFIELD_HEIGHT = 1280, 960
PLAYFIELD_X = (SCREEN_WIDTH - PLAYFIELD_WIDTH) // 2 - 60
PLAYFIELD_Y = (SCREEN_HEIGHT - PLAYFIELD_HEIGHT) // 2

SIDEBAR_WIDTH, SIDEBAR_HEIGHT = 400, 960
SIDEBAR_X = PLAYFIELD_X + PLAYFIELD_WIDTH + 20
SIDEBAR_Y = PLAYFIELD_Y

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 50, 50)
BLUE = (50, 100, 255)
GREEN = (50, 255, 50)
YELLOW = (255, 255, 0)
PURPLE = (200, 50, 255)
CYAN = (0, 255, 255)
ORANGE = (255, 165, 0)
PINK = (255, 105, 180)
GOLD = (255, 215, 0)
DARK_GRAY = (40, 40, 40)
BROWN = (139, 69, 19)
MENU_BG = (0, 52, 89)
ICE = (150, 220, 255)
SILVER = (210, 210, 225)
VOID = (110, 0, 140)
SKIN = (255, 242, 232)

difficulty_names = ["EASY", "NORMAL", "HARD", "LUNATIC"]
difficulty_hp_mult = [0.5, 0.8, 1.2, 1.8]
difficulty_bullet_mult = [0.6, 0.9, 1.2, 1.5]
difficulty_spawn_mult = [1.8, 1.4, 1.0, 0.7]

CHARACTERS = {
    "ars":    {"name": "Арсений",   "color": BROWN,  "radius": 20, "speed": 5, "shoot_delay": 6, "focus_delay": 10, "bombs": 5, "lives": 5, "power": 1,
               "desc": "В фокусе хитбокс сжимается до предела"},
    "vova":   {"name": "Вова",      "color": RED,    "radius": 20, "speed": 5, "shoot_delay": 6, "focus_delay": 10, "bombs": 5, "lives": 5, "power": 1,
               "desc": "В фокусе стреляет веером из 5 пуль"},
    "lenya":  {"name": "Лёня",      "color": GREEN,  "radius": 20, "speed": 6, "shoot_delay": 5, "focus_delay": 9,  "bombs": 5, "lives": 5, "power": 1,
               "desc": "Рывок с неуязвимостью (Ctrl + направление)"},
    "denis":  {"name": "Денис",     "color": BLUE,   "radius": 20, "speed": 5, "shoot_delay": 6, "focus_delay": 10, "bombs": 5, "lives": 5, "power": 2,
               "desc": "Пули прошивают врагов насквозь"},
    "brother":{"name": "Брат",      "color": ORANGE, "radius": 20, "speed": 4, "shoot_delay": 7, "focus_delay": 11, "bombs": 5, "lives": 5, "power": 1,
               "desc": "При попадании сносит пули вокруг себя"},
    "buoyek": {"name": "Папа-буёк", "color": YELLOW, "radius": 20, "speed": 4, "shoot_delay": 8, "focus_delay": 12, "bombs": 5, "lives": 5, "power": 1,
               "desc": "Аура замедляет вражеские пули рядом"},
    "leva":   {"name": "Лёва",      "color": PINK,   "radius": 20, "speed": 5, "shoot_delay": 6, "focus_delay": 10, "bombs": 5, "lives": 5, "power": 1,
               "desc": "Бомба даёт случайный эффект"},
    "cirno":  {"name": "Чирно",     "color": ICE,    "radius": 20, "speed": 5, "shoot_delay": 6, "focus_delay": 10, "bombs": 5, "lives": 5, "power": 1,
               "desc": "Заморозка: вражеские пули рядом замедляются сильнее"},
    "wifidemon": {"name": "Wi-Fi Демон", "color": PURPLE, "radius": 20, "speed": 5, "shoot_delay": 6, "focus_delay": 10, "bombs": 5, "lives": 5, "power": 1,
               "desc": "Иногда пули проходят сквозь врагов"},
    "zerg":   {"name": "Рой Зергов", "color": GREEN,  "radius": 16, "speed": 7, "shoot_delay": 5, "focus_delay": 9,  "bombs": 5, "lives": 5, "power": 1,
               "desc": "Быстрый, но хрупкий; стреляет очередями"},
    "shadow_ars": {"name": "Тёмный Арсений", "color": GOLD, "radius": 20, "speed": 4, "shoot_delay": 7, "focus_delay": 11, "bombs": 5, "lives": 5, "power": 1,
               "desc": "Мощный, но медленный; бомба наносит урон по площади"},
}
CHAR_LIST = list(CHARACTERS.keys())

GRAZE_RADIUS = 30
SPELLCARD_DURATION = 150
LEVEL_COUNT = 10

BOSS_NAMES = {
    1: "Злой Вова", 2: "Злой Лёня", 3: "Злой Денис", 4: "Злой Брат",
    5: "Злой Папа-буёк", 6: "Лёва", 7: "Ледяная Чирно", 8: "Wi-Fi Демон",
    9: "Рой Зергов", 10: "Тёмный Арсений",
}

BOSS_COLORS = {
    1: (60, 10, 10), 2: (10, 60, 10), 3: (10, 10, 60), 4: (60, 30, 0),
    5: (60, 60, 0), 6: (60, 0, 30), 7: (0, 60, 60), 8: (30, 0, 60),
    9: (0, 60, 0), 10: (40, 30, 0),
}

BOSS_CHAR_UNLOCK = {
    1: "vova",
    2: "lenya",
    3: "denis",
    4: "brother",
    5: "buoyek",
    6: "leva",
    7: "cirno",
    8: "wifidemon",
    9: "zerg",
    10: "shadow_ars",
    11: "shadow_ars",
}

FONT_PATH = None

def resource_path(relative_path):
    """Возвращает правильный путь к ресурсам при работе из исходников или из собранного EXE."""
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def init_font():
    global FONT_PATH
    candidates = [
        'dejavusans', 'notosans', 'freesans', 'liberationsans', 'arial',
        'ubuntu', 'droidsans', 'couriernew', 'liberationmono',
    ]
    for name in candidates:
        path = pygame.font.match_font(name)
        if path:
            FONT_PATH = path
            return path
    return None

def load_custom_data(path="custom_data.json"):
    global CHARACTERS, CHAR_LIST
    full_path = resource_path(path)
    if not os.path.exists(full_path):
        return False
    try:
        with open(full_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            for key, char_data in data.items():
                if key in CHARACTERS:
                    base = CHARACTERS[key].copy()
                    base.update(char_data)
                    CHARACTERS[key] = base
                else:
                    CHARACTERS[key] = char_data.copy()
                    if "color" in CHARACTERS[key] and isinstance(CHARACTERS[key]["color"], list):
                        CHARACTERS[key]["color"] = tuple(CHARACTERS[key]["color"])
            CHAR_LIST = list(CHARACTERS.keys())
            return True
        else:
            return False
    except Exception:
        return False

load_custom_data()
