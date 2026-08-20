import pygame
import math
import random
import config
import bullets

class Boss:
    def __init__(self, x, y, hp, name, color, speed_mult=1.0):
        self.x = x
        self.y = y
        self.radius = 40
        self.hp = hp
        self.max_hp = hp
        self.name = name
        self.color = color
        self.shoot_timer = 0
        self.shoot_delay = 45          # увеличено (было 30)
        self.angle = 0
        self.alive = True
        self.enter_timer = 0
        self.invulnerable = True
        self.speed_mult = speed_mult
        self.phase = 0
        self.phase_thresholds = [0.55, 0.25]   # фазы наступают позже (было 0.66, 0.33)
        self.spellcard_timer = 0
        self.spellcard_text = ""

    def update(self, player, dt, enemy_bullets):
        if not self.alive:
            return
        if self.enter_timer < 60:
            self.y += 1.5 * dt * 60
            self.enter_timer += 1
            self.invulnerable = True
            return
        self.invulnerable = False
        self.move(dt)
        if self.spellcard_timer > 0:
            self.spellcard_timer -= 1
        self._check_phase()
        self.shoot_timer += 1
        if self.shoot_timer >= self.shoot_delay:
            self.shoot_timer = 0
            self.fire(player, enemy_bullets)

    def _check_phase(self):
        ratio = self.hp / self.max_hp if self.max_hp else 0
        new_phase = sum(1 for t in self.phase_thresholds if ratio <= t)
        if new_phase != self.phase:
            self.phase = new_phase
            self.on_phase_change()

    def on_phase_change(self):
        self.spellcard_timer = 120       # дольше висит надпись
        self.spellcard_text = f"{self.name} — фаза {self.phase + 1}!"
        self.shoot_delay = max(25, self.shoot_delay - 5)  # замедляем переход (было -3)

    def move(self, dt):
        self.x += math.sin(pygame.time.get_ticks() * 0.001) * 1.5 * dt * 60 * self.speed_mult
        self.y += math.cos(pygame.time.get_ticks() * 0.0013) * 0.8 * dt * 60 * self.speed_mult
        self.x = max(50, min(config.PLAYFIELD_WIDTH - 50, self.x))
        self.y = max(80, min(config.PLAYFIELD_HEIGHT - 250, self.y))

    def fire(self, player, eb):
        pass

    def fire_laser(self, eb, angle=None):
        a = angle if angle is not None else math.pi / 2
        eb.append(bullets.LaserBullet(self.x, self.y + self.radius * 0.3, a, color=self.color))

    def aim_angle(self, player):
        return math.atan2(player.y - self.y, player.x - self.x)

    def draw(self, surf):
        if not self.alive:
            return
        ring_color = config.WHITE if (self.enter_timer < 60 or self.spellcard_timer > 60) else self.color
        pygame.draw.circle(surf, self.color, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surf, ring_color, (int(self.x), int(self.y)), self.radius, 3)
        eye_off = self.radius // 3
        pygame.draw.circle(surf, config.WHITE, (int(self.x - eye_off), int(self.y - 6)), 6)
        pygame.draw.circle(surf, config.WHITE, (int(self.x + eye_off), int(self.y - 6)), 6)
        pygame.draw.circle(surf, config.BLACK, (int(self.x - eye_off), int(self.y - 6)), 3)
        pygame.draw.circle(surf, config.BLACK, (int(self.x + eye_off), int(self.y - 6)), 3)
        angry = pygame.Rect(0, 0, 14, 3)
        angry.center = (int(self.x - eye_off), int(self.y - 16))
        pygame.draw.rect(surf, config.BLACK, angry)
        angry.center = (int(self.x + eye_off), int(self.y - 16))
        pygame.draw.rect(surf, config.BLACK, angry)

        font = pygame.font.Font(config.FONT_PATH, 26) if config.FONT_PATH else pygame.font.Font(None, 26)
        name_surf = font.render(self.name, True, config.WHITE)
        surf.blit(name_surf, (self.x - name_surf.get_width() // 2, self.y - self.radius - 26))

        bar_width, bar_height = 340, 14
        hp_ratio = max(0.0, self.hp / self.max_hp)
        bx = config.PLAYFIELD_WIDTH // 2 - bar_width // 2
        by = 16
        pygame.draw.rect(surf, config.DARK_GRAY, (bx - 2, by - 2, bar_width + 4, bar_height + 4))
        pygame.draw.rect(surf, config.RED, (bx, by, bar_width, bar_height))
        pygame.draw.rect(surf, config.GREEN, (bx, by, bar_width * hp_ratio, bar_height))
        for t in self.phase_thresholds:
            tx = bx + bar_width * t
            pygame.draw.line(surf, config.WHITE, (tx, by), (tx, by + bar_height), 1)

    def get_rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius, 2 * self.radius, 2 * self.radius)


class Boss1_Vova(Boss):
    def __init__(self, x, y, hp_mult=1.0, speed_mult=1.0):
        super().__init__(x, y, int(200 * hp_mult), "Злой Вова", config.RED, speed_mult)  # HP снижен с 300
        self.shoot_delay = 30          # увеличено (было 22)
        self.move_timer = 0
        self.move_angle = 0

    def move(self, dt):
        self.move_timer += 1
        if self.move_timer % 25 == 0:   # реже меняет направление (было 20)
            self.move_angle = random.uniform(0, 2 * math.pi)
        self.x += math.cos(self.move_angle) * 3 * dt * 60 * self.speed_mult  # медленнее
        self.y += math.sin(self.move_angle) * 3 * dt * 60 * self.speed_mult
        self.x = max(50, min(config.PLAYFIELD_WIDTH - 50, self.x))
        self.y = max(80, min(config.PLAYFIELD_HEIGHT - 250, self.y))

    def fire(self, player, eb):
        if random.random() < 0.15:      # реже лазер (было 0.2)
            self.fire_laser(eb)
        # меньше пуль
        for i in range(5):              # было 7
            angle = self.angle + math.radians(i * 15 - 45)
            eb.append(bullets.SquareBullet(self.x, self.y, angle, 2.5, color=config.RED, radius=6))  # скорость снижена
        if self.phase >= 1:
            target = self.aim_angle(player)
            for off in (-0.4, 0.4):      # меньше самонаводящихся
                eb.append(bullets.HomingBullet(self.x, self.y, target + off, 3, config.RED, 5, target=player, turn_rate=0.04))
        self.angle += 0.2               # медленнее вращение


class Boss2_Lenya(Boss):
    def __init__(self, x, y, hp_mult=1.0, speed_mult=1.0):
        super().__init__(x, y, int(180 * hp_mult), "Злой Лёня", config.GREEN, speed_mult)  # HP 250->180
        self.shoot_delay = 35
        self.move_direction = 0
        self.move_counter = 0
        self.move_step = 90
        self.speed = 2.5

    def move(self, dt):
        self.move_counter += 1
        if self.move_counter >= self.move_step:
            self.move_counter = 0
            self.move_direction = (self.move_direction + 1) % 4
        s = self.speed * self.speed_mult
        if self.move_direction == 0:
            self.y += s * dt * 60
        elif self.move_direction == 1:
            self.x += s * dt * 60
        elif self.move_direction == 2:
            self.y -= s * dt * 60
        elif self.move_direction == 3:
            self.x -= s * dt * 60
        self.x = max(50, min(config.PLAYFIELD_WIDTH - 50, self.x))
        self.y = max(80, min(config.PLAYFIELD_HEIGHT - 250, self.y))

    def fire(self, player, eb):
        for i in range(5):              # было 7
            angle = self.angle + math.radians(i * 12 - 36)
            eb.append(bullets.TriangleBullet(self.x, self.y, angle, 2.5, color=config.GREEN, radius=5))
        if self.phase >= 1:
            for i in range(4):          # было 6
                angle = math.radians(i * 60) + self.angle
                eb.append(bullets.BounceBullet(self.x, self.y, angle, 3, color=config.GREEN, radius=5, bounces=2))
        self.angle += 0.1


class Boss3_Denis(Boss):
    def __init__(self, x, y, hp_mult=1.0, speed_mult=1.0):
        super().__init__(x, y, int(220 * hp_mult), "Злой Денис", config.BLUE, speed_mult)  # 300->220
        self.shoot_delay = 28

    def fire(self, player, eb):
        if random.random() < 0.1:        # реже лазер
            self.fire_laser(eb)
        for ring in range(2):           # было 3
            offset = ring * 0.5
            for i in range(10):         # было 12
                angle = math.radians(i * 30) + self.angle + offset
                speed = 2 + ring * 0.5
                eb.append(bullets.Bullet(self.x, self.y, angle, speed, color=config.BLUE, radius=4))
        if self.phase >= 1:
            angle = self.aim_angle(player)
            for off in (-0.2, 0, 0.2):
                eb.append(bullets.PierceBullet(self.x, self.y, angle + off, 5, color=config.SILVER, radius=3))
        self.angle += 0.06


class Boss4_Brother(Boss):
    def __init__(self, x, y, hp_mult=1.0, speed_mult=1.0):
        super().__init__(x, y, int(250 * hp_mult), "Злой Брат", config.ORANGE, speed_mult)  # 350->250
        self.shoot_delay = 20

    def fire(self, player, eb):
        for offset in (-0.5, 0.5):
            for i in range(5):          # было 6
                angle = self.angle + offset + math.radians(i * 15)
                eb.append(bullets.StarBullet(self.x, self.y, angle, 2.5, color=config.ORANGE, radius=5))
        if self.phase >= 1:
            for i in range(6):          # было 8
                angle = math.radians(i * 45) + self.angle * 0.5
                eb.append(bullets.FreezeBullet(self.x, self.y, angle, 2, radius=6))
        self.angle += 0.08


class Boss5_Buoyek(Boss):
    def __init__(self, x, y, hp_mult=1.0, speed_mult=1.0):
        super().__init__(x, y, int(300 * hp_mult), "Злой Папа-буёк", config.YELLOW, speed_mult)  # 400->300
        self.shoot_delay = 14

    def fire(self, player, eb):
        if random.random() < 0.15:       # реже лазер
            self.fire_laser(eb)
        for _ in range(8):              # было 12
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(1.5, 3)  # медленнее
            eb.append(bullets.RingBullet(self.x, self.y, angle, speed, color=config.YELLOW, radius=3))
        aimed_count = 2 if self.phase == 0 else 1  # меньше прицельных
        for _ in range(aimed_count):
            dx = player.x - self.x + random.randint(-50, 50)
            dy = player.y - self.y + random.randint(-50, 50)
            angle = math.atan2(dy, dx)
            eb.append(bullets.Bullet(self.x, self.y, angle, 4, color=config.RED, radius=4))
        if self.phase >= 1:
            eb.append(bullets.HomingBullet(self.x, self.y, self.aim_angle(player), 2.5, config.GOLD, 6, target=player, turn_rate=0.05))


class Boss6_Leva(Boss):
    def __init__(self, x, y, hp_mult=1.0, speed_mult=1.0):
        super().__init__(x, y, int(320 * hp_mult), "Лёва", config.PINK, speed_mult)  # 450->320
        self.shoot_delay = 16

    def move(self, dt):
        self.x += math.sin(pygame.time.get_ticks() * 0.003) * 4 * dt * 60 * self.speed_mult
        self.y += math.cos(pygame.time.get_ticks() * 0.002) * 2.5 * dt * 60 * self.speed_mult
        self.x = max(50, min(config.PLAYFIELD_WIDTH - 50, self.x))
        self.y = max(80, min(config.PLAYFIELD_HEIGHT - 250, self.y))

    def fire(self, player, eb):
        if random.random() < 0.12:
            self.fire_laser(eb)
        options = ['fan', 'ring', 'aim']  # убрал 'lightning', 'bounce', 'pierce' для простоты
        if self.phase >= 1:
            options += ['bounce']
        pattern = random.choice(options)
        if pattern == 'fan':
            for i in range(5):          # было 7
                angle = self.angle + math.radians(i * 10 - 30)
                eb.append(bullets.Bullet(self.x, self.y, angle, 3, config.PINK, 5))
        elif pattern == 'ring':
            for i in range(8):          # было 12
                angle = math.radians(i * 30) + self.angle
                eb.append(bullets.RingBullet(self.x, self.y, angle, 2.5, config.PINK, 4))
        elif pattern == 'aim':
            angle = self.aim_angle(player)
            for j in range(2):          # было 3
                eb.append(bullets.Bullet(self.x, self.y, angle + random.uniform(-0.2, 0.2), 5, config.PINK, 4))
        elif pattern == 'bounce':
            for i in range(3):          # было 4
                angle = math.radians(i * 90) + self.angle
                eb.append(bullets.BounceBullet(self.x, self.y, angle, 3, config.PINK, 5, bounces=2))
        self.angle += 0.15


class Boss7_Cirno(Boss):
    def __init__(self, x, y, hp_mult=1.0, speed_mult=1.0):
        super().__init__(x, y, int(350 * hp_mult), "Ледяная Чирно", config.CYAN, speed_mult)  # 500->350
        self.shoot_delay = 22

    def fire(self, player, eb):
        count = 6 if self.phase == 0 else 8  # было 8 и 12
        for i in range(count):
            angle = self.angle + math.radians(i * 360 / count)
            eb.append(bullets.FreezeBullet(self.x, self.y, angle, 2.5, radius=6))
        if self.phase >= 1:
            for off in (-0.4, 0.4):
                eb.append(bullets.RingBullet(self.x, self.y, self.aim_angle(player) + off, 3, config.CYAN, 5))
        self.angle += 0.1


class Boss8_WifiDemon(Boss):
    def __init__(self, x, y, hp_mult=1.0, speed_mult=1.0):
        super().__init__(x, y, int(400 * hp_mult), "Wi-Fi Демон", config.PURPLE, speed_mult)  # 550->400
        self.shoot_delay = 20

    def fire(self, player, eb):
        for i in range(4):              # было 6
            angle = self.angle + math.radians(i * 30)
            eb.append(bullets.LaserBullet(self.x, self.y, angle, color=config.PURPLE))
        if self.phase >= 1:
            for _ in range(1):          # было 2
                eb.append(bullets.HomingBullet(self.x, self.y, self.aim_angle(player), 3, config.PURPLE, 5, target=player, turn_rate=0.06, homing_time=120))
        self.angle += 0.08


class Boss9_ZergRush(Boss):
    def __init__(self, x, y, hp_mult=1.0, speed_mult=1.0):
        super().__init__(x, y, int(450 * hp_mult), "Рой Зергов", config.GREEN, speed_mult)  # 600->450
        self.shoot_delay = 12

    def fire(self, player, eb):
        count = 14 if self.phase == 0 else 20  # было 20 и 28
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(1.5, 5)    # медленнее
            eb.append(bullets.Bullet(self.x, self.y, angle, speed, config.GREEN, 3))
        if self.phase >= 1:
            for _ in range(2):               # было 3
                angle = random.uniform(0, 2 * math.pi)
                eb.append(bullets.BounceBullet(self.x, self.y, angle, 3, config.GREEN, 4, bounces=2))


class Boss10_ShadowArseny(Boss):
    def __init__(self, x, y, hp_mult=1.0, speed_mult=1.0):
        super().__init__(x, y, int(700 * hp_mult), "Тёмный Арсений", config.GOLD, speed_mult)  # 1000->700
        self.shoot_delay = 10

    def move(self, dt):
        t = pygame.time.get_ticks() * 0.002
        self.x = config.PLAYFIELD_WIDTH // 2 + 200 * math.sin(t * 0.5) * math.cos(t * 0.3)
        self.y = config.PLAYFIELD_HEIGHT // 2 - 100 + 150 * math.sin(t * 0.7)
        self.x = max(50, min(config.PLAYFIELD_WIDTH - 50, self.x))
        self.y = max(80, min(config.PLAYFIELD_HEIGHT - 200, self.y))

    def fire(self, player, eb):
        if random.random() < 0.2:
            self.fire_laser(eb)
        ring_count = 3 if self.phase < 2 else 4  # было 4 и 5
        for ring in range(ring_count):
            offset = ring * 0.3
            for i in range(12):                # было 16
                angle = math.radians(i * 22.5) + self.angle + offset
                speed = 2 + ring * 0.6
                eb.append(bullets.Bullet(self.x, self.y, angle, speed, color=config.BLUE, radius=4))
        for offset in (-0.7, 0.7):
            for i in range(6):                 # было 8
                angle = self.angle + offset + math.radians(i * 15)
                eb.append(bullets.Bullet(self.x, self.y, angle, 3, color=config.PURPLE, radius=5))
        for _ in range(3):                    # было 5
            dx = player.x - self.x + random.randint(-60, 60)
            dy = player.y - self.y + random.randint(-60, 60)
            angle = math.atan2(dy, dx)
            eb.append(bullets.Bullet(self.x, self.y, angle, 5, color=config.YELLOW, radius=4))
        for i in range(2):                    # было 3
            angle = self.angle + math.radians(i * 20 - 20)
            eb.append(bullets.VoidBullet(self.x, self.y, angle, 2.5, radius=8))
        if self.phase >= 2:
            eb.append(bullets.HomingBullet(self.x, self.y, self.aim_angle(player), 3.5, config.GOLD, 6, target=player, turn_rate=0.05, homing_time=150))
        self.angle += 0.12


class Boss11_Absolute(Boss10_ShadowArseny):
    """Секретный супербосс - открывается на Lunatic после победы над Тёмным Арсением."""
    def __init__(self, x, y, hp_mult=1.0, speed_mult=1.0):
        Boss.__init__(self, x, y, int(1100 * hp_mult), "Абсолютный Арсений", config.VOID, speed_mult)  # 1600->1100
        self.shoot_delay = 8
        self.phase_thresholds = [0.65, 0.4, 0.2]   # фазы позже

    def fire(self, player, eb):
        super().fire(player, eb)
        if self.phase >= 1:
            for i in range(4):           # было 6
                angle = math.radians(i * 60) + self.angle
                eb.append(bullets.FreezeBullet(self.x, self.y, angle, 2.5, radius=6))
        if self.phase >= 2:
            for i in range(2):           # было 3
                angle = self.aim_angle(player) + math.radians(i * 20 - 20)
                eb.append(bullets.PierceBullet(self.x, self.y, angle, 7, config.SILVER, 3))
        if self.phase >= 3:
            for i in range(3):           # было 4
                angle = math.radians(i * 90) + self.angle
                eb.append(bullets.BounceBullet(self.x, self.y, angle, 4, config.VOID, 6, bounces=2))


BOSS_CLASSES = {
    1: Boss1_Vova,
    2: Boss2_Lenya,
    3: Boss3_Denis,
    4: Boss4_Brother,
    5: Boss5_Buoyek,
    6: Boss6_Leva,
    7: Boss7_Cirno,
    8: Boss8_WifiDemon,
    9: Boss9_ZergRush,
    10: Boss10_ShadowArseny,
}

SECRET_BOSS_CLASS = Boss11_Absolute