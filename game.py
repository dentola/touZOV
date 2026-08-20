import os
import math
import random
import json
import pygame
import config
import audio
import bullets
import enemies
import bosses
import player as player_module
import ui
import crypto

RECORDS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "records.dat")
DEFAULT_RECORDS = {"story_score": 0, "endless_score": 0, "unlocked_characters": ["ars"], "disclaimer_shown": False}

def load_records():
    return crypto.load_records_encrypted(RECORDS_PATH)

def save_records(records):
    crypto.save_records_encrypted(records, RECORDS_PATH)

def _segment_circle_hit(x1, y1, x2, y2, cx, cy, r):
    dx, dy = x2 - x1, y2 - y1
    length_sq = dx*dx + dy*dy
    if length_sq == 0:
        return math.hypot(cx-x1, cy-y1) <= r
    t = max(0.0, min(1.0, ((cx-x1)*dx + (cy-y1)*dy)/length_sq))
    px, py = x1 + t*dx, y1 + t*dy
    return math.hypot(cx-px, cy-py) <= r

def _bullet_hits_circle(b, cx, cy, cr):
    if isinstance(b, bullets.LaserBullet):
        if b.warmup > 0:
            return False
        x2 = b.x + math.cos(b.angle)*b.length
        y2 = b.y + math.sin(b.angle)*b.length
        return _segment_circle_hit(b.x, b.y, x2, y2, cx, cy, cr + b.radius*0.5)
    return math.hypot(b.x-cx, b.y-cy) < cr + b.radius

class Explosion:
    def __init__(self, x, y, max_radius=50, color=None):
        self.x, self.y = x, y
        self.radius = 2
        self.max_radius = max_radius
        self.color = color or config.ORANGE
        self.alpha = 220
        self.alive = True
    def update(self, dt):
        self.radius += 3*dt*60
        self.alpha -= 8*dt*60
        if self.radius >= self.max_radius or self.alpha <= 0:
            self.alive = False
    def draw(self, surf):
        if self.alpha <= 0:
            return
        s = pygame.Surface((self.max_radius*2, self.max_radius*2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, max(0, int(self.alpha))), (self.max_radius, self.max_radius), max(1, int(self.radius)), 3)
        surf.blit(s, (self.x - self.max_radius, self.y - self.max_radius))

class Particle:
    def __init__(self, x, y, color):
        self.x, self.y = x, y
        angle = random.uniform(0, math.pi*2)
        speed = random.uniform(1, 4)
        self.vx = math.cos(angle)*speed
        self.vy = math.sin(angle)*speed
        self.life = random.randint(15, 30)
        self.color = color
    def update(self, dt):
        self.x += self.vx*dt*60
        self.y += self.vy*dt*60
        self.vx *= 0.94
        self.vy *= 0.94
        self.life -= 1
    def draw(self, surf):
        if self.life > 0:
            pygame.draw.circle(surf, self.color, (int(self.x), int(self.y)), 2)

class PowerUp:
    COLORS = {
        'power': config.CYAN, 'life': config.PINK, 'bomb': config.BLUE,
        'weapon_homing': config.GREEN, 'weapon_pierce': config.SILVER,
        'weapon_laser': config.PURPLE, 'weapon_explosive': config.ORANGE,
        'weapon_split': config.GOLD,
    }
    LABELS = {
        'power': 'P', 'life': '1UP', 'bomb': 'B',
        'weapon_homing': 'H', 'weapon_pierce': 'PR',
        'weapon_laser': 'L', 'weapon_explosive': 'E', 'weapon_split': 'S',
    }

    def __init__(self, x, y, kind):
        self.x, self.y = x, y
        self.kind = kind
        self.vy = 2.5
        self.alive = True
        self.radius = 14

    def update(self, dt):
        self.y += self.vy * dt * 60
        if self.y > config.PLAYFIELD_HEIGHT + 30:
            self.alive = False

    def draw(self, surf):
        color = self.COLORS.get(self.kind, config.WHITE)
        pygame.draw.circle(surf, color, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surf, config.WHITE, (int(self.x), int(self.y)), self.radius, 1)
        font = pygame.font.Font(config.FONT_PATH, 14) if config.FONT_PATH else pygame.font.Font(None, 14)
        label = self.LABELS.get(self.kind, '?')
        text = font.render(label, True, config.BLACK)
        rect = text.get_rect(center=(int(self.x), int(self.y)))
        surf.blit(text, rect)

WEAPON_DROPS = ['weapon_homing','weapon_pierce','weapon_laser','weapon_explosive','weapon_split']
LEVEL_DIALOGUE = {
    1: [("player","Опять без интернета... Вова, отойди от роутера!"),("boss","Ха! Вайфай теперь мой. Попробуй отбери.")],
    2: [("boss","Лёня снова всё разбросал по комнате — не пройдёшь!"),("player","Через хаос я пройду быстрее, чем ты думаешь.")],
    3: [("boss","Денис включил все мониторы разом. Ослепнешь!"),("player","Зато у меня план получше твоего пинга.")],
    4: [("player","Брат, серьёзно? Ты обещал не мешать!"),("boss","Обещания не грузятся без хорошего сигнала.")],
    5: [("boss","Папа-буёк защищает роутер до последнего!"),("player","Тогда обойдусь без него. Погнали.")],
    6: [("boss","Лёва решает всё случайно — и это неожиданно опасно."),("player","Значит, и я буду действовать по обстоятельствам.")],
    7: [("boss","Здесь холоднее, чем твой пинг до сервера."),("player","Главное — не самая холодная часть тебя.")],
    8: [("boss","Я — Wi-Fi Демон. Ни один пакет не пройдёт мимо меня."),("player","Тогда прошибу соединение напролом.")],
    9: [("boss","Рой Зергов заполонит весь эфир!"),("player","Чем больше вас, тем громче вы упадёте.")],
    10:[("boss","Я — ты, но без тормозов и без жалости."),("player","Тогда посмотрим, кто из нас настоящий Арсений.")],
    11:[("boss","Ты думал, всё закончилось? Это было только начало."),("player","Значит, добьём это раз и навсегда.")],
}

class DynamicBackground:
    def __init__(self, width, height):
        self.width, self.height = width, height
        self.current_color = (10,10,30)
        self.target_color = (10,10,30)
        self.transition_speed = 0.025
        self.stars = self._gen_stars(250)
    def _gen_stars(self, count):
        stars = []
        for _ in range(count):
            x = random.randint(0, self.width)
            y = random.randint(0, self.height)
            r = random.randint(1,3)
            speed = random.uniform(0.1, 0.6)
            phase = random.uniform(0, 6.28)
            stars.append({'x':x,'y':y,'r':r,'speed':speed,'phase':phase})
        return stars
    def set_target_color(self, color):
        self.target_color = color
    def update(self, dt):
        for i in range(3):
            self.current_color = tuple(
                int(self.current_color[i] + (self.target_color[i]-self.current_color[i]) * self.transition_speed * dt * 60)
                for i in range(3)
            )
        for star in self.stars:
            star['y'] += star['speed'] * dt * 60
            star['x'] += math.sin(star['phase'] + pygame.time.get_ticks() * 0.001) * 0.4
            if star['y'] > self.height:
                star['y'] = 0
                star['x'] = random.randint(0, self.width)
    def draw(self, surf):
        surf.fill(self.current_color)
        for star in self.stars:
            bright = 128 + int(127 * math.sin(star['phase'] + pygame.time.get_ticks() * 0.002))
            color = (bright, bright, bright)
            pygame.draw.circle(surf, color, (int(star['x']), int(star['y'])), star['r'])

class GameSession:
    def __init__(self, character, difficulty, infinite_mode):
        self.difficulty = difficulty
        self.infinite_mode = infinite_mode
        self.player = player_module.Player(character)
        self.enemies = []
        self.enemy_bullets = []
        self.player_bullets = []
        self.powerups = []
        self.explosions = []
        self.particles = []
        self.boss = None
        self.secret_boss = None
        self.player.set_lists(self.enemies, self.enemy_bullets, self.player_bullets, self.boss, self.secret_boss, self.powerups)
        self.level = 1
        self.cycle = 1
        self.phase = "wave"
        self.wave_time = 0.0
        self.wave_duration = 16.0
        self.spawn_timer = 0.0
        self.boss_spawned = False
        self.secret_boss_active = False
        self.secret_boss_defeated = False
        self.game_over = False
        self.victory = False
        self.final_score = 0
        self.spellcard_text = ""
        self.spellcard_timer = 0
        self.unlock_notification = None
        self.unlock_timer = 0
        self.bg = DynamicBackground(config.PLAYFIELD_WIDTH, config.PLAYFIELD_HEIGHT)

    def hp_mult(self):
        return config.difficulty_hp_mult[self.difficulty] * (1 + 0.15 * (self.cycle - 1))
    def bullet_mult(self):
        return config.difficulty_bullet_mult[self.difficulty] * (1 + 0.05 * (self.cycle - 1))
    def spawn_interval(self):
        return 1.8 * config.difficulty_spawn_mult[self.difficulty]

    def spawn_boss(self):
        cls = bosses.BOSS_CLASSES[self.level]
        b = cls(config.PLAYFIELD_WIDTH//2, -60, hp_mult=self.hp_mult(), speed_mult=self.bullet_mult())
        self.boss = b
        self.player.boss = b
        self.boss_spawned = True
        self.phase = "boss"
        if self.level in config.BOSS_COLORS:
            self.bg.set_target_color(config.BOSS_COLORS[self.level])
    def spawn_secret_boss(self):
        b = bosses.SECRET_BOSS_CLASS(config.PLAYFIELD_WIDTH//2, -60, hp_mult=self.hp_mult()*1.15, speed_mult=self.bullet_mult()*1.1)
        self.secret_boss = b
        self.player.secret_boss = b
        self.secret_boss_active = True
        self.phase = "secret_boss"
        self.bg.set_target_color((40,0,40))

    def spawn_wave_enemy(self):
        x = random.uniform(60, config.PLAYFIELD_WIDTH-60)
        hp = random.randint(15, 28)
        speed = random.uniform(0.6, 1.3)
        color = random.choice([config.GREEN, config.BLUE, config.PURPLE, config.ORANGE])
        e = enemies.Enemy(x, -30, hp=hp, speed=speed, shoot_delay=random.randint(60,120), color=color, bullet_mult=self.bullet_mult())
        self.enemies.append(e)

    def drop_powerup(self, x, y):
        r = random.random()
        if r < 0.70:
            kind = 'power'
        elif r < 0.90:
            kind = 'life'
        elif r < 0.95:
            kind = 'bomb'
        else:
            kind = random.choice(WEAPON_DROPS)
        self.powerups.append(PowerUp(x, y, kind))

    def update(self, keys, dt):
        self.bg.update(dt)
        self.player.update(keys, dt)
        slow_active = self.player.aura_slowdown
        for b in list(self.enemy_bullets):
            slow = 0.4 if (slow_active and self.player.in_aura(b.x, b.y)) else 1.0
            b.update(dt, slow)
            if not b.alive:
                self.enemy_bullets.remove(b)
        for e in list(self.enemies):
            e.update(self.player, dt, self.enemy_bullets)
            if not e.alive:
                self.enemies.remove(e)
        if self.boss and self.boss.alive:
            self.boss.update(self.player, dt, self.enemy_bullets)
            self.spellcard_text = self.boss.spellcard_text
            self.spellcard_timer = self.boss.spellcard_timer
        if self.secret_boss and self.secret_boss.alive:
            self.secret_boss.update(self.player, dt, self.enemy_bullets)
            self.spellcard_text = self.secret_boss.spellcard_text
            self.spellcard_timer = self.secret_boss.spellcard_timer
        for p in list(self.player_bullets):
            if isinstance(p, bullets.SplitBullet):
                if p.update(dt):
                    self.player_bullets.extend(p.split())
            else:
                p.update(dt)
            if not p.alive and p in self.player_bullets:
                self.player_bullets.remove(p)
        for pu in list(self.powerups):
            pu.update(dt)
            if not pu.alive:
                self.powerups.remove(pu)
        for ex in list(self.explosions):
            ex.update(dt)
            if not ex.alive:
                self.explosions.remove(ex)
        for pa in list(self.particles):
            pa.update(dt)
            if pa.life <= 0:
                self.particles.remove(pa)
        self._handle_collisions()
        if self.unlock_timer > 0:
            self.unlock_timer -= 1
        if not self.player.alive:
            self.final_score = self.player.score
            self.game_over = True
            return "game_over"
        signal = self._advance_phase(dt)
        return signal

    def _spawn_burst(self, x, y, radius=40, color=None):
        self.explosions.append(Explosion(x, y, radius, color))
        for _ in range(10):
            self.particles.append(Particle(x, y, color or config.ORANGE))

    def _bullet_damage(self, pb):
        if isinstance(pb, bullets.LaserBullet):
            return 1.2
        if isinstance(pb, (bullets.HomingBullet, bullets.PierceBullet)):
            return 3
        return 2

    def _handle_collisions(self):
        player = self.player
        if player.alive and player.invincible == 0:
            for b in self.enemy_bullets:
                if _bullet_hits_circle(b, player.x, player.y, player.hit_radius):
                    if getattr(b, "freeze", False):
                        player.apply_freeze()
                        if b in self.enemy_bullets:
                            self.enemy_bullets.remove(b)
                    else:
                        player.hit()
                        self._spawn_burst(player.x, player.y, 30, config.RED)
                        if not isinstance(b, bullets.LaserBullet):
                            if b in self.enemy_bullets:
                                self.enemy_bullets.remove(b)
                    break
        for b in self.enemy_bullets:
            if b.grazed or isinstance(b, bullets.LaserBullet):
                continue
            dist = math.hypot(b.x - player.x, b.y - player.y)
            if player.hit_radius + config.GRAZE_RADIUS > dist > player.hit_radius + b.radius:
                b.grazed = True
                player.graze += 1
                player.score += 10
                audio.play_graze_sound()
        for pb in list(self.player_bullets):
            hit_enemy = False
            for e in list(self.enemies):
                if not e.alive:
                    continue
                if _bullet_hits_circle(pb, e.x, e.y, e.radius):
                    e.hp -= self._bullet_damage(pb)
                    hit_enemy = True
                    if e.hp <= 0:
                        e.alive = False
                        player.score += 100
                        self._spawn_burst(e.x, e.y, 26, e.color)
                        if e.drops_powerup:
                            self.drop_powerup(e.x, e.y)
                    if not pb.pierce:
                        break
            if hit_enemy and isinstance(pb, bullets.ExplosiveBullet):
                eff = pb.explode(self.enemies, self.boss, self.secret_boss)
                self.explosions.append(Explosion(eff['x'], eff['y'], eff['max_radius'], eff['color']))
            if hit_enemy and not pb.pierce:
                if pb in self.player_bullets:
                    self.player_bullets.remove(pb)
                continue
            for boss_obj in (self.boss, self.secret_boss):
                if boss_obj and boss_obj.alive and not boss_obj.invulnerable:
                    if _bullet_hits_circle(pb, boss_obj.x, boss_obj.y, boss_obj.radius):
                        boss_obj.hp -= self._bullet_damage(pb)
                        if isinstance(pb, bullets.ExplosiveBullet):
                            eff = pb.explode(self.enemies, self.boss, self.secret_boss)
                            self.explosions.append(Explosion(eff['x'], eff['y'], eff['max_radius'], eff['color']))
                        if not pb.pierce and pb in self.player_bullets:
                            self.player_bullets.remove(pb)
                        if boss_obj.hp <= 0:
                            boss_obj.hp = 0
                            boss_obj.alive = False
                            self._on_boss_defeated(boss_obj)
                        break
        for pu in list(self.powerups):
            if math.hypot(pu.x - player.x, pu.y - player.y) < pu.radius + player.radius:
                self._apply_powerup(pu.kind)
                self.powerups.remove(pu)

    def _apply_powerup(self, kind):
        player = self.player
        if kind == 'power':
            player.power = min(6, player.power + 1)
            player.score += 20
        elif kind == 'bomb':
            player.bombs = min(8, player.bombs + 1)
        elif kind == 'life':
            player.lives += 1
        elif kind.startswith('weapon_'):
            player.bullet_type = kind[len('weapon_'):]
        audio.play_sfx("item")

    def _on_boss_defeated(self, boss_obj):
        self.player.score += 1000
        self._spawn_burst(boss_obj.x, boss_obj.y, 90, config.GOLD)
        if boss_obj is self.secret_boss:
            self.secret_boss_defeated = True
        records = load_records()
        level = self.level if not self.secret_boss_defeated else 11
        if level in config.BOSS_CHAR_UNLOCK:
            char_key = config.BOSS_CHAR_UNLOCK[level]
            if char_key not in records["unlocked_characters"]:
                records["unlocked_characters"].append(char_key)
                save_records(records)
                self.unlock_notification = char_key
                self.unlock_timer = 180

    def _advance_phase(self, dt):
        if self.phase == "wave":
            self.wave_time += dt
            self.spawn_timer -= dt
            if self.spawn_timer <= 0 and self.wave_time < self.wave_duration:
                self.spawn_timer = self.spawn_interval()
                self.spawn_wave_enemy()
            if self.wave_time >= self.wave_duration and not self.enemies:
                self.wave_time = 0
                self.phase = "await_dialog"
                return "need_dialog"
        elif self.phase == "boss":
            if self.boss and not self.boss.alive:
                self.boss = None
                self.player.boss = None
                self.spellcard_text = ""
                self.spellcard_timer = 0
                if self.level >= config.LEVEL_COUNT:
                    if self.difficulty == 3 and not self.secret_boss_defeated:
                        self.secret_boss_active = True
                        self.phase = "await_secret_dialog"
                        return "need_secret_dialog"
                    elif self.infinite_mode:
                        self.cycle_complete()
                    else:
                        self.final_score = self.player.score
                        self.victory = True
                        return "victory"
                else:
                    self.level += 1
                    self.boss_spawned = False
                    self.wave_time = 0
                    self.spawn_timer = 0
                    self.phase = "wave"
                    self.spellcard_text = ""
                    self.spellcard_timer = 0
        elif self.phase == "secret_boss":
            if self.secret_boss and not self.secret_boss.alive:
                self.secret_boss = None
                self.player.secret_boss = None
                self.spellcard_text = ""
                self.spellcard_timer = 0
                if self.infinite_mode:
                    self.cycle_complete()
                else:
                    self.final_score = self.player.score
                    self.victory = True
                    return "victory"
        return None

    def on_dialog_finished(self):
        if self.phase == "await_dialog":
            self.spawn_boss()
        elif self.phase == "await_secret_dialog":
            self.spawn_secret_boss()

    def cycle_complete(self):
        self.cycle += 1
        self.level = 1
        self.boss = None
        self.secret_boss = None
        self.secret_boss_active = False
        self.secret_boss_defeated = False
        self.player.boss = None
        self.player.secret_boss = None
        self.boss_spawned = False
        self.wave_time = 0
        self.spawn_timer = 0
        self.phase = "wave"
        self.spellcard_text = ""
        self.spellcard_timer = 0
        self.bg.set_target_color((10,10,30))

    def draw(self, surf):
        self.bg.draw(surf)
        if self.player.alive:
            self.player.draw(surf)
        for e in self.enemies:
            e.draw(surf)
        if self.boss:
            self.boss.draw(surf)
        if self.secret_boss:
            self.secret_boss.draw(surf)
        for b in self.enemy_bullets:
            b.draw(surf)
        for pb in self.player_bullets:
            pb.draw(surf)
        for pu in self.powerups:
            pu.draw(surf)
        for ex in self.explosions:
            ex.draw(surf)
        for pa in self.particles:
            pa.draw(surf)
        ui.draw_spellcard_banner(surf, self.spellcard_text, self.spellcard_timer)
        if self.unlock_timer > 0 and self.unlock_notification:
            ui.draw_unlock_notification(surf, self.unlock_notification)

def show_disclaimer(screen):
    """Показывает дисклеймер и ждёт Enter или клик."""
    overlay = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 220))
    screen.blit(overlay, (0, 0))
    font = pygame.font.Font(config.FONT_PATH, 36) if config.FONT_PATH else pygame.font.Font(None, 36)
    lines = [
        "TouZOV — фанатская игра",
        "Создана в память о первой друн-сессии.",
        "Все персонажи и события вымышлены.",
        "Игра распространяется бесплатно.",
        "Автор: dentola",
        "Версия 1.1 stable"
    ]
    y = config.SCREEN_HEIGHT // 2 - 120
    for line in lines:
        text = font.render(line, True, config.WHITE)
        screen.blit(text, (config.SCREEN_WIDTH//2 - text.get_width()//2, y))
        y += 50
    hint = pygame.font.Font(config.FONT_PATH, 28) if config.FONT_PATH else pygame.font.Font(None, 28)
    hint_text = hint.render("Нажмите Enter или кликните для продолжения", True, config.GOLD)
    screen.blit(hint_text, (config.SCREEN_WIDTH//2 - hint_text.get_width()//2, y + 40))
    pygame.display.flip()

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    waiting = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                waiting = False
    return True

def run():
    os.environ.setdefault("SDL_VIDEO_CENTERED", "1")
    pygame.init()
    audio.init_mixer()
    config.init_font()
    ui.init_fonts()
    fullscreen = True
    flags = pygame.FULLSCREEN | pygame.SCALED | pygame.DOUBLEBUF | pygame.HWSURFACE
    screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), flags)
    pygame.display.set_caption(config.WINDOW_TITLE)
    clock = pygame.time.Clock()
    records = load_records()

    # Дисклеймер при первом запуске
    if not records.get("disclaimer_shown", False):
        if show_disclaimer(screen):
            records["disclaimer_shown"] = True
            save_records(records)

    state = "menu"
    menu_choice = 0
    game_mode = 0
    difficulty = 1
    char_index = 0
    session = None
    dialog_index = 0
    playfield_surf = pygame.Surface((config.PLAYFIELD_WIDTH, config.PLAYFIELD_HEIGHT))
    sidebar_surf = pygame.Surface((config.SIDEBAR_WIDTH, config.SIDEBAR_HEIGHT))

    def current_dialogue():
        if not session:
            return []
        lvl = 11 if session.phase == "await_secret_dialog" else session.level
        return LEVEL_DIALOGUE.get(lvl, [])

    def begin_dialog_or_skip():
        nonlocal state, dialog_index
        dialog_index = 0
        if current_dialogue():
            state = "dialog"
        else:
            session.on_dialog_finished()
            state = "playing"

    running = True
    while running:
        raw_dt = clock.tick(config.FPS) / 1000.0
        dt = min(raw_dt, 1/30)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_F4, pygame.K_F11):
                    fullscreen = not fullscreen
                    flags = (pygame.FULLSCREEN | pygame.SCALED | pygame.DOUBLEBUF | pygame.HWSURFACE) if fullscreen else 0
                    screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), flags)
                elif event.key == pygame.K_m:
                    audio.toggle_mute()
                if state == "menu":
                    if event.key in (pygame.K_UP, pygame.K_w):
                        menu_choice = (menu_choice - 1) % 5
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        menu_choice = (menu_choice + 1) % 5
                    elif event.key in (pygame.K_LEFT, pygame.K_a, pygame.K_RIGHT, pygame.K_d):
                        step = -1 if event.key in (pygame.K_LEFT, pygame.K_a) else 1
                        if menu_choice == 1:
                            game_mode = 1 - game_mode
                        elif menu_choice == 2:
                            difficulty = (difficulty + step) % 4
                        elif menu_choice == 3:
                            unlocked_list = records.get("unlocked_characters", ["ars"])
                            current_index = char_index
                            new_index = current_index
                            for _ in range(len(config.CHAR_LIST)):
                                new_index = (new_index + step) % len(config.CHAR_LIST)
                                if config.CHAR_LIST[new_index] in unlocked_list:
                                    char_index = new_index
                                    break
                    elif event.key in (pygame.K_RETURN, pygame.K_z):
                        if menu_choice == 0:
                            character = config.CHAR_LIST[char_index]
                            if character not in records.get("unlocked_characters", ["ars"]):
                                continue
                            session = GameSession(character, difficulty, game_mode == 1)
                            state = "playing"
                        elif menu_choice == 4:
                            running = False
                    elif event.key == pygame.K_ESCAPE:
                        running = False
                elif state == "dialog":
                    if event.key in (pygame.K_RETURN, pygame.K_z):
                        dialog_index += 1
                        if dialog_index >= len(current_dialogue()):
                            session.on_dialog_finished()
                            state = "playing"
                elif state == "playing":
                    if event.key == pygame.K_ESCAPE:
                        state = "paused"
                    elif event.key == pygame.K_x:
                        if session.player.use_bomb():
                            audio.play_sfx("bomb")
                    elif event.key == pygame.K_SPACE:
                        if session and session.player:
                            mode = session.player.toggle_auto_shoot()
                            audio.play_sfx("item")
                elif state == "paused":
                    if event.key == pygame.K_ESCAPE:
                        state = "playing"
                    elif event.key == pygame.K_RETURN:
                        state = "menu"
                        session = None
                elif state in ("game_over", "victory"):
                    if event.key == pygame.K_RETURN:
                        state = "menu"
                        session = None
        if state == "playing" and session is not None:
            keys = pygame.key.get_pressed()
            signal = session.update(keys, dt)
            if signal == "game_over":
                save_records(load_records())
                state = "game_over"
            elif signal == "victory":
                save_records(load_records())
                state = "victory"
            elif signal in ("need_dialog", "need_secret_dialog"):
                begin_dialog_or_skip()
        audio.update_music(state, session.secret_boss_active if session else False,
                           session.boss_spawned if session else False,
                           session.boss if session else None,
                           session.level if session else 1,
                           session.secret_boss_defeated if session else False)
        screen.fill(config.BLACK)
        if state == "menu" or session is None:
            ui.draw_menu(screen, menu_choice, game_mode, difficulty, config.CHAR_LIST[char_index], records.get("unlocked_characters", ["ars"]))
        else:
            playfield_surf.fill((0,0,0))
            session.draw(playfield_surf)
            if state == "dialog":
                dlg = current_dialogue()
                if dialog_index < len(dlg):
                    who, text = dlg[dialog_index]
                    if who == "player":
                        speaker, color = session.player.name, session.player.color
                    else:
                        active_boss = session.secret_boss or session.boss
                        speaker = active_boss.name if active_boss else config.BOSS_NAMES.get(session.level, "???")
                        color = config.RED
                    ui.draw_dialog(playfield_surf, speaker, [text], color)
            elif state == "paused":
                ui.draw_pause(playfield_surf)
            elif state == "game_over":
                rec = records["endless_score"] if session.infinite_mode else records["story_score"]
                ui.draw_game_over(playfield_surf, session.final_score, session.final_score >= rec)
            elif state == "victory":
                rec = records["endless_score"] if session.infinite_mode else records["story_score"]
                ui.draw_victory(playfield_surf, session.final_score, session.final_score >= rec, session.secret_boss_defeated)
            screen.blit(playfield_surf, (config.PLAYFIELD_X, config.PLAYFIELD_Y))
            pygame.draw.rect(screen, config.WHITE, (config.PLAYFIELD_X, config.PLAYFIELD_Y, config.PLAYFIELD_WIDTH, config.PLAYFIELD_HEIGHT), 2)
            ui.draw_sidebar(sidebar_surf, session.player, records, session.spellcard_text, session.spellcard_timer,
                            session.infinite_mode, session.level, config.LEVEL_COUNT, session.cycle)
            screen.blit(sidebar_surf, (config.SIDEBAR_X, config.SIDEBAR_Y))
            pygame.draw.rect(screen, config.WHITE, (config.SIDEBAR_X, config.SIDEBAR_Y, config.SIDEBAR_WIDTH, config.SIDEBAR_HEIGHT), 2)
        pygame.display.flip()
    save_records(load_records())
    pygame.quit()
