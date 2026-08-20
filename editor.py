import tkinter as tk
from tkinter import ttk, colorchooser, messagebox, filedialog
import json
import os
import random
import math

# Путь для сохранения кастомных данных
CUSTOM_DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "custom_data.json")

# Дефолтные значения для новых персонажей
DEFAULT_CHARACTER = {
    "name": "Новый персонаж",
    "color": (255, 200, 0),
    "radius": 12,
    "speed": 5,
    "shoot_delay": 6,
    "focus_delay": 10,
    "bombs": 3,
    "lives": 3,
    "power": 1,
    "desc": "Описание",
    "focus_speed": 2.5,
    "aura_radius": 90,
    "pierce": False,
    "weave_shot": False,
    "dashable": False,
    "salt_explosion": False,
    "aura_slowdown": False,
    "random_bomb": False,
    "auto_shoot": False,
    "speed_bonus": 0,
    "bullet_type": "normal",
    "dash_cooldown": 70,
    "dash_timer": 10,
    "frozen_timer": 0,
    "temp_speed_timer": 0,
}

# Список булевых способностей
ABILITY_BOOLS = [
    ("pierce", "Прошивающие пули"),
    ("weave_shot", "Веерная стрельба (Вова)"),
    ("dashable", "Рывок (Лёня)"),
    ("salt_explosion", "Солевой взрыв (Брат)"),
    ("aura_slowdown", "Аура замедления (Папа-буёк)"),
    ("random_bomb", "Случайная бомба (Лёва)"),
    ("auto_shoot", "Автострельба"),
]

# Числовые поля (не булевы)
NUMERIC_FIELDS = [
    ("speed", "Скорость"),
    ("shoot_delay", "Задержка выстрела"),
    ("focus_delay", "Задержка фокуса"),
    ("bombs", "Бомбы"),
    ("lives", "Жизни"),
    ("power", "Сила"),
    ("radius", "Радиус"),
    ("focus_speed", "Скорость фокуса"),
    ("aura_radius", "Радиус ауры"),
    ("speed_bonus", "Бонус скорости"),
    ("dash_cooldown", "Кулдаун рывка"),
    ("dash_timer", "Длительность рывка"),
]

# Типы пуль
BULLET_TYPES = ["normal", "laser", "explosive", "split", "homing", "pierce"]


class CharacterEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Редактор персонажей — Арсений: Битва за Вайфай")
        self.root.geometry("1200x750")
        self.root.minsize(800, 600)  # минимальный размер окна
        self.root.resizable(True, True)  # можно растягивать мышкой

        # Загружаем персонажей из config.py, потом можно загрузить из JSON
        import config
        self.characters = {k: v.copy() for k, v in config.CHARACTERS.items()}
        self.current_key = None

        # Создаём Notebook (вкладки)
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Вкладка персонажей
        self.char_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.char_frame, text="Персонажи")

        # Левая панель: список и кнопки
        left_frame = ttk.Frame(self.char_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        # Список персонажей
        self.listbox = tk.Listbox(left_frame, width=30, height=25, selectmode=tk.SINGLE)
        self.listbox.pack(fill=tk.Y, expand=True)
        self.listbox.bind('<<ListboxSelect>>', self.on_select)

        # Кнопки управления списком
        btn_list_frame = ttk.Frame(left_frame)
        btn_list_frame.pack(fill=tk.X, pady=5)

        ttk.Button(btn_list_frame, text="➕", width=3, command=self.add_character).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_list_frame, text="🗑️", width=3, command=self.delete_character).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_list_frame, text="📋", width=3, command=self.copy_character).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_list_frame, text="▲", width=3, command=lambda: self.move_character(-1)).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_list_frame, text="▼", width=3, command=lambda: self.move_character(1)).pack(side=tk.LEFT, padx=2)

        # Правая панель: редактирование и предпросмотр
        right_frame = ttk.Frame(self.char_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Секция предпросмотра портрета
        preview_frame = ttk.LabelFrame(right_frame, text="Предпросмотр")
        preview_frame.pack(fill=tk.X, pady=5)
        self.canvas = tk.Canvas(preview_frame, width=200, height=200, bg="#1e1e2e", highlightthickness=0)
        self.canvas.pack(pady=5)

        # Поля редактирования (внутри Scrollable Frame, чтобы помещалось при разном размере окна)
        edit_frame = ttk.LabelFrame(right_frame, text="Параметры")
        edit_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Создаём Canvas для прокрутки внутри edit_frame
        canvas = tk.Canvas(edit_frame, borderwidth=0)
        scrollbar = ttk.Scrollbar(edit_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Теперь заполняем scrollable_frame полями
        self.build_edit_fields()

        # Кнопки сохранения/загрузки/экспорта
        bottom_frame = ttk.Frame(right_frame)
        bottom_frame.pack(fill=tk.X, pady=10)
        ttk.Button(bottom_frame, text="💾 Сохранить JSON", command=self.save_json).pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom_frame, text="📥 Загрузить JSON", command=self.load_json).pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom_frame, text="📋 Экспорт Python", command=self.export_python).pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom_frame, text="✅ Применить", command=self.apply_changes).pack(side=tk.LEFT, padx=5)

        self.refresh_list()
        if self.listbox.size() > 0:
            self.listbox.selection_set(0)
            self.on_select(None)

    def build_edit_fields(self):
        """Создаёт все поля ввода в scrollable_frame."""
        self.vars = {}  # словарь для хранения переменных

        # Имя
        ttk.Label(self.scrollable_frame, text="Имя:").grid(row=0, column=0, sticky="w", pady=3, padx=5)
        self.vars["name"] = tk.StringVar()
        ttk.Entry(self.scrollable_frame, textvariable=self.vars["name"], width=30).grid(row=0, column=1, pady=3, padx=5)

        # Цвет
        ttk.Label(self.scrollable_frame, text="Цвет (R,G,B):").grid(row=1, column=0, sticky="w", pady=3, padx=5)
        color_frame = ttk.Frame(self.scrollable_frame)
        color_frame.grid(row=1, column=1, sticky="w", pady=3, padx=5)
        self.vars["color"] = tk.StringVar()
        ttk.Entry(color_frame, textvariable=self.vars["color"], width=15).pack(side=tk.LEFT)
        self.color_preview = tk.Label(color_frame, text="   ", width=5, relief="sunken")
        self.color_preview.pack(side=tk.LEFT, padx=5)
        ttk.Button(color_frame, text="Выбрать", command=self.choose_color).pack(side=tk.LEFT, padx=5)

        # Числовые поля
        row = 2
        self.numeric_vars = {}
        for key, label in NUMERIC_FIELDS:
            ttk.Label(self.scrollable_frame, text=label + ":").grid(row=row, column=0, sticky="w", pady=3, padx=5)
            var = tk.StringVar()
            ttk.Entry(self.scrollable_frame, textvariable=var, width=10).grid(row=row, column=1, pady=3, padx=5)
            self.numeric_vars[key] = var
            row += 1

        # Тип пуль
        ttk.Label(self.scrollable_frame, text="Тип пуль:").grid(row=row, column=0, sticky="w", pady=3, padx=5)
        self.vars["bullet_type"] = tk.StringVar(value="normal")
        ttk.Combobox(self.scrollable_frame, textvariable=self.vars["bullet_type"], values=BULLET_TYPES, state="readonly").grid(row=row, column=1, pady=3, padx=5)
        row += 1

        # Описание
        ttk.Label(self.scrollable_frame, text="Описание:").grid(row=row, column=0, sticky="w", pady=3, padx=5)
        self.vars["desc"] = tk.StringVar()
        ttk.Entry(self.scrollable_frame, textvariable=self.vars["desc"], width=40).grid(row=row, column=1, pady=3, padx=5)
        row += 1

        # Способности (чекбоксы)
        ttk.Label(self.scrollable_frame, text="Способности:").grid(row=row, column=0, sticky="w", pady=3, padx=5)
        row += 1
        self.ability_vars = {}
        for key, label in ABILITY_BOOLS:
            var = tk.BooleanVar()
            chk = ttk.Checkbutton(self.scrollable_frame, text=label, variable=var)
            chk.grid(row=row, column=1, sticky="w", pady=2, padx=5)
            self.ability_vars[key] = var
            row += 1

    def refresh_list(self):
        self.listbox.delete(0, tk.END)
        for key in self.characters:
            self.listbox.insert(tk.END, self.characters[key]["name"])

    def get_selected_key(self):
        selection = self.listbox.curselection()
        if not selection:
            return None
        index = selection[0]
        keys = list(self.characters.keys())
        return keys[index]

    def on_select(self, event):
        self.apply_changes(silent=True)  # применяем предыдущие изменения без сообщений
        key = self.get_selected_key()
        if not key:
            return
        self.current_key = key
        char = self.characters[key]
        # Заполняем поля
        self.vars["name"].set(char["name"])
        self.vars["color"].set(', '.join(map(str, char["color"])))
        self.color_preview.config(bg='#%02x%02x%02x' % tuple(char["color"]))
        for field_key, _ in NUMERIC_FIELDS:
            self.numeric_vars[field_key].set(str(char.get(field_key, DEFAULT_CHARACTER[field_key])))
        self.vars["bullet_type"].set(char.get("bullet_type", "normal"))
        self.vars["desc"].set(char.get("desc", ""))
        for ab_key, _ in ABILITY_BOOLS:
            self.ability_vars[ab_key].set(char.get(ab_key, False))
        # Предпросмотр
        self.draw_preview(char)

    def draw_preview(self, char):
        """Рисует упрощённый портрет персонажа на Canvas."""
        self.canvas.delete("all")
        color = char["color"]
        radius = char.get("radius", 12) * 3  # масштаб
        cx, cy = 100, 100

        # Тело
        self.canvas.create_oval(cx - radius, cy - radius, cx + radius, cy + radius, fill='#%02x%02x%02x' % color, outline="white", width=2)

        # Голова
        head_radius = radius * 0.45
        head_y = cy - radius - head_radius
        self.canvas.create_oval(cx - head_radius, head_y - head_radius, cx + head_radius, head_y + head_radius, fill="#ffe0bd", outline="white", width=2)

        # Глаза
        eye_off = head_radius * 0.3
        eye_y = head_y - head_radius * 0.2
        self.canvas.create_oval(cx - eye_off - 3, eye_y - 3, cx - eye_off + 3, eye_y + 3, fill="black")
        self.canvas.create_oval(cx + eye_off - 3, eye_y - 3, cx + eye_off + 3, eye_y + 3, fill="black")

        # Рот
        mouth_y = head_y + head_radius * 0.2
        self.canvas.create_line(cx - head_radius * 0.2, mouth_y, cx + head_radius * 0.2, mouth_y, fill="black", width=2)

    def choose_color(self):
        try:
            current = tuple(map(int, self.vars["color"].get().split(',')))
        except:
            current = (255, 255, 255)
        color_code = colorchooser.askcolor(title="Выберите цвет", initialcolor=current)[0]
        if color_code:
            self.vars["color"].set(', '.join(map(str, [int(c) for c in color_code])))
            self.color_preview.config(bg='#%02x%02x%02x' % tuple(int(c) for c in color_code))

    def apply_changes(self, silent=False):
        """Применяет текущие значения полей к выбранному персонажу."""
        key = self.current_key
        if not key:
            return
        char = self.characters[key]
        try:
            color_tuple = tuple(map(int, self.vars["color"].get().split(',')))
            if len(color_tuple) != 3:
                raise ValueError
        except:
            if not silent:
                messagebox.showerror("Ошибка", "Цвет должен быть в формате R,G,B (например 255,0,0)")
            return
        # Проверяем числовые поля
        try:
            numeric_values = {}
            for field_key, _ in NUMERIC_FIELDS:
                val = float(self.numeric_vars[field_key].get())
                if field_key in ("bombs", "lives", "power", "radius"):
                    val = int(val)
                numeric_values[field_key] = val
        except:
            if not silent:
                messagebox.showerror("Ошибка", "Числовые поля должны содержать числа")
            return

        char["name"] = self.vars["name"].get()
        char["color"] = color_tuple
        char.update(numeric_values)
        char["bullet_type"] = self.vars["bullet_type"].get()
        char["desc"] = self.vars["desc"].get()
        for ab_key, _ in ABILITY_BOOLS:
            char[ab_key] = self.ability_vars[ab_key].get()

        # Обновляем список и предпросмотр
        self.refresh_list()
        self.draw_preview(char)
        if not silent:
            messagebox.showinfo("Готово", f"Изменения для {char['name']} применены")

    def add_character(self):
        """Создаёт нового персонажа с уникальным ключом."""
        # Генерируем ключ вида custom_1, custom_2...
        existing = set(self.characters.keys())
        i = 1
        while f"custom_{i}" in existing:
            i += 1
        new_key = f"custom_{i}"
        self.characters[new_key] = DEFAULT_CHARACTER.copy()
        self.refresh_list()
        self.listbox.selection_clear(0, tk.END)
        self.listbox.selection_set(tk.END)
        self.listbox.see(tk.END)
        self.on_select(None)

    def delete_character(self):
        """Удаляет выбранного персонажа."""
        key = self.get_selected_key()
        if not key:
            return
        if len(self.characters) <= 1:
            messagebox.showwarning("Предупреждение", "Нельзя удалить последнего персонажа")
            return
        if messagebox.askyesno("Подтверждение", f"Удалить персонажа {self.characters[key]['name']}?"):
            del self.characters[key]
            self.current_key = None
            self.refresh_list()
            if self.listbox.size() > 0:
                self.listbox.selection_set(0)
                self.on_select(None)

    def copy_character(self):
        """Дублирует выбранного персонажа."""
        key = self.get_selected_key()
        if not key:
            return
        source = self.characters[key]
        new_key = key + "_copy"
        i = 1
        while new_key in self.characters:
            new_key = f"{key}_copy{i}"
            i += 1
        self.characters[new_key] = source.copy()
        self.characters[new_key]["name"] = source["name"] + " (копия)"
        self.refresh_list()
        self.listbox.selection_clear(0, tk.END)
        self.listbox.selection_set(tk.END)
        self.listbox.see(tk.END)
        self.on_select(None)

    def move_character(self, direction):
        """Перемещает выбранного персонажа вверх/вниз в списке."""
        key = self.get_selected_key()
        if not key:
            return
        keys = list(self.characters.keys())
        index = keys.index(key)
        new_index = index + direction
        if 0 <= new_index < len(keys):
            # Меняем порядок в словаре (Python 3.7+ сохраняет порядок)
            items = list(self.characters.items())
            items[index], items[new_index] = items[new_index], items[index]
            self.characters = dict(items)
            self.refresh_list()
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(new_index)
            self.listbox.see(new_index)
            self.on_select(None)

    def save_json(self):
        self.apply_changes(silent=True)
        with open(CUSTOM_DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(self.characters, f, ensure_ascii=False, indent=2)
        messagebox.showinfo("Сохранено", f"Данные сохранены в {CUSTOM_DATA_PATH}")

    def load_json(self):
        path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Проверяем, что это словарь с персонажами
            if isinstance(data, dict) and all(isinstance(v, dict) for v in data.values()):
                self.characters = data
                self.refresh_list()
                if self.listbox.size() > 0:
                    self.listbox.selection_set(0)
                    self.on_select(None)
                messagebox.showinfo("Загружено", "Персонажи загружены")
            else:
                messagebox.showerror("Ошибка", "Неверный формат JSON")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить: {e}")

    def export_python(self):
        self.apply_changes(silent=True)
        python_code = "CHARACTERS = " + json.dumps(self.characters, ensure_ascii=False, indent=4)
        self.root.clipboard_clear()
        self.root.clipboard_append(python_code)
        messagebox.showinfo("Экспорт", "Python-код скопирован в буфер обмена")


def main():
    root = tk.Tk()
    app = CharacterEditor(root)
    root.mainloop()


if __name__ == "__main__":
    main()