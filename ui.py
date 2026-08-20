import pygame
import math
import random
import config

font = None
big_font = None
huge_font = None
menu_font = None
dialog_font = None
side_font = None
title_font = None
small_font = None

def make_font(size):
    if config.FONT_PATH:
        return pygame.font.Font(config.FONT_PATH, size)
    return pygame.font.Font(None, size)

def init_fonts():
    global font, big_font, huge_font, menu_font, dialog_font, side_font, title_font, small_font
    font = make_font(30)
    big_font = make_font(42)
    huge_font = make_font(70)
    menu_font = make_font(80)
    dialog_font = make_font(30)
    side_font = make_font(26)
    title_font = make_font(52)
    small_font = make_font(22)

BULLET_TYPE_NAMES = {
    "normal": "ОБЫЧНЫЕ",
    "laser": "ЛАЗЕР",
    "explosive": "ВЗРЫВНЫЕ",
    "split": "РАЗДЕЛЯЮЩИЕСЯ",
    "homing": "САМОНАВОДЯЩИЕСЯ",
    "pierce": "ПРОШИВАЮЩИЕ",
}

def draw_character_portrait(surf, character_key, cx, cy, scale=1.0):
    char = config.CHARACTERS[character_key]
    color = char["color"]
    radius = char["radius"] * 4

    pygame.draw.circle(surf, color, (cx, cy), radius)
    pygame.draw.circle(surf, config.WHITE, (cx, cy), radius, 3)

    head_radius = radius * 0.45
    head_y = cy - radius - head_radius
    pygame.draw.circle(surf, config.SKIN, (cx, head_y), head_radius)
    pygame.draw.circle(surf, config.WHITE, (cx, head_y), head_radius, 2)

    eye_off = head_radius * 0.3
    eye_y = head_y - head_radius * 0.2
    pygame.draw.circle(surf, config.BLACK, (cx - eye_off, eye_y), max(2, head_radius * 0.1))
    pygame.draw.circle(surf, config.BLACK, (cx + eye_off, eye_y), max(2, head_radius * 0.1))

    mouth_y = head_y + head_radius * 0.2
    pygame.draw.line(surf, config.BLACK, (cx - head_radius * 0.2, mouth_y), (cx + head_radius * 0.2, mouth_y), 2)

    if character_key == "ars":
        hump_rect = pygame.Rect(cx - radius * 0.8, cy - radius * 0.5, radius * 0.7, radius * 0.8)
        pygame.draw.ellipse(surf, (100, 60, 30), hump_rect)
    elif character_key == "vova":
        pygame.draw.line(surf, config.BLACK, (cx - eye_off - 4, eye_y - 8), (cx - eye_off + 4, eye_y - 4), 3)
        pygame.draw.line(surf, config.BLACK, (cx + eye_off - 4, eye_y - 4), (cx + eye_off + 4, eye_y - 8), 3)
    elif character_key == "lenya":
        for i in range(3):
            y = cy - radius + 10 + i * 10
            pygame.draw.line(surf, config.WHITE, (cx - radius * 0.6, y), (cx + radius * 0.6, y), 2)
    elif character_key == "denis":
        pygame.draw.rect(surf, config.BLACK, (cx - eye_off - 8, eye_y - 6, 16, 12), 2)
        pygame.draw.rect(surf, config.BLACK, (cx + eye_off - 8, eye_y - 6, 16, 12), 2)
    elif character_key == "brother":
        beard_rect = pygame.Rect(cx - head_radius * 0.6, mouth_y + 2, head_radius * 1.2, head_radius * 0.5)
        pygame.draw.rect(surf, (100, 70, 50), beard_rect)
    elif character_key == "buoyek":
        for i in range(5):
            angle = i * 0.7
            x1 = cx + math.cos(angle) * radius * 1.2
            y1 = cy + math.sin(angle) * radius * 1.2
            x2 = cx + math.cos(angle + 0.3) * radius * 1.4
            y2 = cy + math.sin(angle + 0.3) * radius * 1.4
            pygame.draw.line(surf, config.CYAN, (x1, y1), (x2, y2), 3)
    elif character_key == "leva":
        font_q = pygame.font.Font(config.FONT_PATH, int(head_radius * 1.5)) if config.FONT_PATH else pygame.font.Font(None, int(head_radius * 1.5))
        q_surf = font_q.render("?", True, config.PINK)
        q_rect = q_surf.get_rect(center=(cx, head_y - head_radius * 1.5))
        surf.blit(q_surf, q_rect)
    elif character_key == "cirno":
        snow_center = (cx, cy + radius * 0.3)
        for i in range(6):
            angle = i * math.pi / 3
            end = (snow_center[0] + math.cos(angle) * 15, snow_center[1] + math.sin(angle) * 15)
            pygame.draw.line(surf, config.WHITE, snow_center, end, 2)
    elif character_key == "wifidemon":
        pygame.draw.line(surf, config.WHITE, (cx - head_radius * 0.5, head_y - head_radius * 0.8), (cx - head_radius * 0.5, head_y - head_radius * 1.5), 3)
        pygame.draw.line(surf, config.WHITE, (cx + head_radius * 0.5, head_y - head_radius * 0.8), (cx + head_radius * 0.5, head_y - head_radius * 1.5), 3)
        pygame.draw.circle(surf, config.RED, (cx - head_radius * 0.5, head_y - head_radius * 1.5), 4)
        pygame.draw.circle(surf, config.RED, (cx + head_radius * 0.5, head_y - head_radius * 1.5), 4)
    elif character_key == "zerg":
        for _ in range(8):
            angle = random.uniform(0, math.pi * 2)
            dist = radius * random.uniform(1.1, 1.5)
            px = cx + math.cos(angle) * dist
            py = cy + math.sin(angle) * dist
            pygame.draw.circle(surf, config.GREEN, (int(px), int(py)), 3)
    elif character_key == "shadow_ars":
        aura_surf = pygame.Surface((radius * 3, radius * 3), pygame.SRCALPHA)
        pygame.draw.circle(aura_surf, (80, 0, 120, 80), (radius * 1.5, radius * 1.5), radius * 1.2)
        surf.blit(aura_surf, (cx - radius * 1.5, cy - radius * 1.5))

stars = []
def init_stars(count=120):
    global stars
    stars = []
    for _ in range(count):
        stars.append({
            'x': random.randint(0, config.SCREEN_WIDTH),
            'y': random.randint(0, config.SCREEN_HEIGHT),
            'speed': random.uniform(0.2, 0.8),
            'size': random.randint(1, 3),
            'brightness': random.randint(50, 200)
        })

def update_stars():
    for star in stars:
        star['y'] += star['speed']
        if star['y'] > config.SCREEN_HEIGHT:
            star['y'] = 0
            star['x'] = random.randint(0, config.SCREEN_WIDTH)
        star['brightness'] = 128 + int(127 * math.sin(pygame.time.get_ticks() * 0.001 + star['x']))

def draw_stars(surf):
    for star in stars:
        color = (star['brightness'], star['brightness'], star['brightness'])
        pygame.draw.circle(surf, color, (int(star['x']), int(star['y'])), star['size'])

def draw_neon_text(surf, text, x, y, size, color, glow_color=None, glow_radius=10):
    if glow_color is None:
        glow_color = color
    for i in range(glow_radius, 0, -2):
        alpha = max(0, 50 - i * 3)
        glow_surf = make_font(size).render(text, True, glow_color)
        glow_surf.set_alpha(alpha)
        surf.blit(glow_surf, (x - i//2, y - i//2))
    main_surf = make_font(size).render(text, True, color)
    surf.blit(main_surf, (x, y))

def draw_menu(screen, menu_choice, network_mode, difficulty, selected_character, unlocked):
    if not stars:
        init_stars()
    update_stars()

    for i in range(0, config.SCREEN_HEIGHT, 2):
        color = (10, 10, 20 + i // 20)
        pygame.draw.line(screen, color, (0, i), (config.SCREEN_WIDTH, i))
    draw_stars(screen)

    draw_neon_text(screen, "TouZOV", config.SCREEN_WIDTH//2 - 200, 60, 80, config.GOLD, config.YELLOW, 12)

    portrait_cx = 280
    portrait_cy = 380
    char = config.CHARACTERS[selected_character]
    locked = selected_character not in unlocked
    draw_character_portrait(screen, selected_character, portrait_cx, portrait_cy)

    if locked:
        overlay = pygame.Surface((280, 280), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        screen.blit(overlay, (portrait_cx - 140, portrait_cy - 140))
        lock_font = huge_font if config.FONT_PATH else big_font
        lock = lock_font.render("🔒", True, config.WHITE)
        screen.blit(lock, (portrait_cx - lock.get_width()//2, portrait_cy - lock.get_height()//2))

    name_surf = big_font.render(char["name"], True, config.WHITE)
    screen.blit(name_surf, (portrait_cx - name_surf.get_width()//2, portrait_cy + 150))

    if locked:
        hint = small_font.render("🔓 Разблокируется после победы над боссом", True, (180, 180, 100))
        screen.blit(hint, (portrait_cx - hint.get_width()//2, portrait_cy + 200))
    else:
        desc_surf = small_font.render(char.get("desc", ""), True, (200, 220, 255))
        screen.blit(desc_surf, (portrait_cx - desc_surf.get_width()//2, portrait_cy + 200))

    items = [
        "НАЧАТЬ ИГРУ",
        f"РЕЖИМ: {'СЮЖЕТ' if network_mode == 0 else 'БЕСКОНЕЧНЫЙ'}",
        f"СЛОЖНОСТЬ: {config.difficulty_names[difficulty]}",
        f"ПЕРСОНАЖ: {char['name'].upper()}",
        "ВЫХОД"
    ]
    menu_x = config.SCREEN_WIDTH - 500
    y_pos = 200
    for i, item in enumerate(items):
        rect = pygame.Rect(menu_x, y_pos, 400, 60)
        active = (i == menu_choice)
        if active:
            pygame.draw.rect(screen, (60, 40, 0), rect)
            pygame.draw.rect(screen, config.GOLD, rect, 3)
            tri = [(rect.left - 20, rect.centery), (rect.left - 5, rect.centery - 10), (rect.left - 5, rect.centery + 10)]
            pygame.draw.polygon(screen, config.GOLD, tri)
            text_color = config.GOLD
        else:
            pygame.draw.rect(screen, (20, 20, 40), rect)
            pygame.draw.rect(screen, (80, 80, 80), rect, 1)
            text_color = (180, 180, 180)

        text_surf = big_font.render(item, True, text_color)
        if text_surf.get_width() > rect.width - 40:
            text_surf = small_font.render(item, True, text_color)
        screen.blit(text_surf, (rect.centerx - text_surf.get_width()//2, rect.centery - text_surf.get_height()//2))
        y_pos += 80

    # Версия и автор
    version_text = "TouZOV v1.1 stable by dentola"
    ver_surf = small_font.render(version_text, True, (150, 150, 150))
    screen.blit(ver_surf, (config.SCREEN_WIDTH//2 - ver_surf.get_width()//2, config.SCREEN_HEIGHT - 30))

    inst = small_font.render("Стрелки: выбор,  ←/→: изменить,  Enter: подтвердить,  Esc: выход", True, (150, 150, 150))
    screen.blit(inst, (config.SCREEN_WIDTH//2 - inst.get_width()//2, config.SCREEN_HEIGHT - 60))

def draw_sidebar(sidebar, player, records, spellcard_text, spellcard_timer, infinite_mode, current_level, max_level, cycle):
    sidebar.fill(config.DARK_GRAY)
    pygame.draw.rect(sidebar, (60, 60, 60), (0, 0, config.SIDEBAR_WIDTH, config.SIDEBAR_HEIGHT), 2)

    t = side_font.render("СЧЁТ", True, config.WHITE)
    sidebar.blit(t, (20, 16))
    v = side_font.render(str(player.score), True, config.GOLD)
    sidebar.blit(v, (20, 44))

    t = side_font.render("ЖИЗНИ", True, config.WHITE)
    sidebar.blit(t, (20, 92))
    for i in range(min(player.lives, 10)):
        pygame.draw.circle(sidebar, config.RED, (36 + i * 26, 118), 8)
        pygame.draw.circle(sidebar, config.WHITE, (36 + i * 26, 118), 8, 1)

    t = side_font.render("БОМБЫ", True, config.WHITE)
    sidebar.blit(t, (20, 160))
    for i in range(min(player.bombs, 10)):
        pygame.draw.circle(sidebar, config.BLUE, (36 + i * 26, 196), 9)
        pygame.draw.circle(sidebar, config.WHITE, (36 + i * 26, 196), 9, 1)

    t = side_font.render("GRAZE", True, config.WHITE)
    sidebar.blit(t, (20, 228))
    v = side_font.render(str(player.graze), True, config.CYAN)
    sidebar.blit(v, (20, 256))

    t = side_font.render("СИЛА", True, config.WHITE)
    sidebar.blit(t, (20, 304))
    v = side_font.render(str(player.power), True, config.GREEN)
    sidebar.blit(v, (20, 332))

    t = side_font.render("ТИП ПУЛЬ", True, config.WHITE)
    sidebar.blit(t, (20, 380))
    bullet_name = BULLET_TYPE_NAMES.get(player.bullet_type, "ОБЫЧНЫЕ")
    v = font.render(bullet_name, True, config.GOLD)
    if v.get_width() > config.SIDEBAR_WIDTH - 40:
        v = small_font.render(bullet_name, True, config.GOLD)
    sidebar.blit(v, (20, 410))

    # Индикатор автострельбы
    t = side_font.render("AUTO", True, config.WHITE)
    sidebar.blit(t, (20, 440))
    auto_text = "ВКЛ" if player.auto_shoot else "ВЫКЛ"
    color = config.GREEN if player.auto_shoot else config.RED
    v = small_font.render(auto_text, True, color)
    sidebar.blit(v, (20, 468))

    t = side_font.render("УРОВЕНЬ", True, config.WHITE)
    sidebar.blit(t, (20, 510))
    level_text = f"{current_level} / {max_level}" if not infinite_mode else f"{current_level} / {max_level}  (круг {cycle})"
    v = small_font.render(level_text, True, config.WHITE)
    sidebar.blit(v, (20, 538))

    t = side_font.render("РЕКОРД", True, config.WHITE)
    sidebar.blit(t, (20, 580))
    rec = records["endless_score"] if infinite_mode else records["story_score"]
    v = side_font.render(str(rec), True, config.GOLD)
    sidebar.blit(v, (20, 608))

    pygame.draw.line(sidebar, (80, 80, 80), (10, 660), (config.SIDEBAR_WIDTH - 10, 660), 1)
    ctrl_lines = ["Стрелки/WASD — движение", "Z — стрельба", "Shift — фокус", "X — бомба", "Space — авт. стрельба", "Esc — пауза"]
    yy = 672
    for line in ctrl_lines:
        s = small_font.render(line, True, (170, 170, 170))
        sidebar.blit(s, (16, yy))
        yy += 24

    if spellcard_timer > 0 and spellcard_text:
        s = small_font.render(spellcard_text, True, config.GOLD)
        sidebar.blit(s, (16, config.SIDEBAR_HEIGHT - 26))

def draw_spellcard_banner(surf, text, timer):
    if timer <= 0 or not text:
        return
    alpha = min(255, timer * 6)
    band = pygame.Surface((config.PLAYFIELD_WIDTH, 40), pygame.SRCALPHA)
    band.fill((0, 0, 0, min(140, alpha)))
    surf.blit(band, (0, config.PLAYFIELD_HEIGHT // 2 - 20))
    rendered = big_font.render(text, True, config.GOLD)
    rendered.set_alpha(alpha)
    surf.blit(rendered, (config.PLAYFIELD_WIDTH // 2 - rendered.get_width() // 2, config.PLAYFIELD_HEIGHT // 2 - rendered.get_height() // 2))

def draw_dialog(surf, speaker, text_lines, portrait_color):
    box = pygame.Rect(20, config.PLAYFIELD_HEIGHT - 190, config.PLAYFIELD_WIDTH - 40, 170)
    panel = pygame.Surface((box.width, box.height), pygame.SRCALPHA)
    panel.fill((10, 10, 30, 220))
    surf.blit(panel, box.topleft)
    pygame.draw.rect(surf, config.WHITE, box, 2)
    pygame.draw.circle(surf, portrait_color, (box.left + 55, box.top - 10), 40)
    pygame.draw.circle(surf, config.WHITE, (box.left + 55, box.top - 10), 40, 2)
    name_surf = dialog_font.render(speaker, True, config.GOLD)
    surf.blit(name_surf, (box.left + 110, box.top + 12))
    yy = box.top + 50
    for line in text_lines:
        line_surf = dialog_font.render(line, True, config.WHITE)
        surf.blit(line_surf, (box.left + 20, yy))
        yy += 34
    hint = small_font.render("Z / Enter — продолжить", True, (180, 180, 180))
    surf.blit(hint, (box.right - hint.get_width() - 14, box.bottom - 28))

def draw_pause(surf):
    overlay = pygame.Surface((config.PLAYFIELD_WIDTH, config.PLAYFIELD_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 170))
    surf.blit(overlay, (0, 0))
    title = huge_font.render("ПАУЗА", True, config.GOLD)
    surf.blit(title, (config.PLAYFIELD_WIDTH // 2 - title.get_width() // 2, config.PLAYFIELD_HEIGHT // 2 - 90))
    lines = ["Esc — продолжить", "Enter — в меню"]
    yy = config.PLAYFIELD_HEIGHT // 2
    for line in lines:
        s = font.render(line, True, config.WHITE)
        surf.blit(s, (config.PLAYFIELD_WIDTH // 2 - s.get_width() // 2, yy))
        yy += 40

def draw_game_over(surf, score, is_new_record):
    overlay = pygame.Surface((config.PLAYFIELD_WIDTH, config.PLAYFIELD_HEIGHT), pygame.SRCALPHA)
    overlay.fill((30, 0, 0, 190))
    surf.blit(overlay, (0, 0))
    title = huge_font.render("ИГРА ОКОНЧЕНА", True, config.RED)
    surf.blit(title, (config.PLAYFIELD_WIDTH // 2 - title.get_width() // 2, 220))
    score_surf = big_font.render(f"Счёт: {score}", True, config.WHITE)
    surf.blit(score_surf, (config.PLAYFIELD_WIDTH // 2 - score_surf.get_width() // 2, 320))
    if is_new_record:
        rec_surf = font.render("Новый рекорд!", True, config.GOLD)
        surf.blit(rec_surf, (config.PLAYFIELD_WIDTH // 2 - rec_surf.get_width() // 2, 370))
    hint = small_font.render("Enter — в меню", True, (200, 200, 200))
    surf.blit(hint, (config.PLAYFIELD_WIDTH // 2 - hint.get_width() // 2, 440))

def draw_victory(surf, score, is_new_record, secret_defeated):
    overlay = pygame.Surface((config.PLAYFIELD_WIDTH, config.PLAYFIELD_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 20, 40, 190))
    surf.blit(overlay, (0, 0))
    title = huge_font.render("ПОБЕДА!", True, config.GOLD)
    surf.blit(title, (config.PLAYFIELD_WIDTH // 2 - title.get_width() // 2, 200))
    if secret_defeated:
        sub = font.render("Абсолютный Арсений повержен!", True, config.PINK)
        surf.blit(sub, (config.PLAYFIELD_WIDTH // 2 - sub.get_width() // 2, 270))
    score_surf = big_font.render(f"Счёт: {score}", True, config.WHITE)
    surf.blit(score_surf, (config.PLAYFIELD_WIDTH // 2 - score_surf.get_width() // 2, 320))
    if is_new_record:
        rec_surf = font.render("Новый рекорд!", True, config.GOLD)
        surf.blit(rec_surf, (config.PLAYFIELD_WIDTH // 2 - rec_surf.get_width() // 2, 370))
    hint = small_font.render("Enter — в меню", True, (200, 200, 200))
    surf.blit(hint, (config.PLAYFIELD_WIDTH // 2 - hint.get_width() // 2, 440))

def draw_unlock_notification(surf, char_key):
    char = config.CHARACTERS.get(char_key, {})
    name = char.get("name", "???")
    overlay = pygame.Surface((config.PLAYFIELD_WIDTH, 80), pygame.SRCALPHA)
    overlay.fill((0, 20, 0, 200))
    surf.blit(overlay, (0, config.PLAYFIELD_HEIGHT // 2 - 40))
    text = f"НОВЫЙ ПЕРСОНАЖ: {name.upper()}!"
    rend = big_font.render(text, True, config.GOLD)
    surf.blit(rend, (config.PLAYFIELD_WIDTH // 2 - rend.get_width() // 2, config.PLAYFIELD_HEIGHT // 2 - 20))
