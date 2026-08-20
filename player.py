import pygame
import math
import random
import config
import bullets

class Player:
    def __init__(self, character="ars"):
        self.character = character
        char_data = config.CHARACTERS.get(character, config.CHARACTERS["ars"]).copy()

        self.name = char_data.get("name", "Неизвестный")
        self.color = tuple(char_data.get("color", config.WHITE))
        self.radius = char_data.get("radius", 20)
        self.base_speed = char_data.get("speed", 5)
        self.speed = self.base_speed
        self.focus_speed = char_data.get("focus_speed", 2.5)
        self.shoot_delay = char_data.get("shoot_delay", 6)
        self.focus_shoot_delay = char_data.get("focus_delay", 10)
        self.lives = char_data.get("lives", 5)
        self.bombs = char_data.get("bombs", 5)
        self.power = char_data.get("power", 1)

        self.pierce = char_data.get("pierce", False)
        self.weave_shot = char_data.get("weave_shot", False)
        self.dashable = char_data.get("dashable", False)
        self.salt_explosion = char_data.get("salt_explosion", False)
        self.aura_slowdown = char_data.get("aura_slowdown", False)
        self.random_bomb = char_data.get("random_bomb", False)
        self.auto_shoot = char_data.get("auto_shoot", False)

        if character == "vova":
            self.weave_shot = True
        elif character == "lenya":
            self.dashable = True
            self.focus_speed = 3.5
        elif character == "denis":
            self.pierce = True
        elif character == "brother":
            self.salt_explosion = True
        elif character == "buoyek":
            self.aura_slowdown = True
            self.aura_radius = 90
        elif character == "leva":
            self.random_bomb = True

        self.aura_radius = char_data.get("aura_radius", 90)
        self.speed_bonus = char_data.get("speed_bonus", 0)
        self.bullet_type = char_data.get("bullet_type", "normal")
        self.dash_cooldown = char_data.get("dash_cooldown", 70)
        self.dash_timer = char_data.get("dash_timer", 10)
        self.temp_speed_timer = 0
        self.frozen_timer = 0
        self.hit_radius = self.radius // 2

        self.x = config.PLAYFIELD_WIDTH // 2
        self.y = config.PLAYFIELD_HEIGHT - 100

        self.is_focus = False
        self.shoot_timer = 0
        self.invincible = 120
        self.score = 0
        self.bombs_used = 0
        self.hits_taken = 0
        self.graze = 0
        self._prev_dash_key = False
        self.alive = True

        self.enemies = []
        self.enemy_bullets = []
        self.player_bullets = []
        self.powerups = []
        self.boss = None
        self.secret_boss = None

    def set_lists(self, enemies, enemy_bullets, player_bullets, boss, secret_boss, powerups):
        self.enemies = enemies
        self.enemy_bullets = enemy_bullets
        self.player_bullets = player_bullets
        self.boss = boss
        self.secret_boss = secret_boss
        self.powerups = powerups

    def update(self, keys, dt):
        if not self.alive:
            return
        if self.invincible > 0:
            self.invincible -= 1
        if self.frozen_timer > 0:
            self.frozen_timer -= 1
        if self.temp_speed_timer > 0:
            self.temp_speed_timer -= 1

        self.is_focus = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
        speed = self.focus_speed if self.is_focus else self.base_speed
        if self.frozen_timer > 0:
            speed *= 0.3
        if self.temp_speed_timer > 0:
            speed *= 1.3

        dx, dy = 0, 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx = -speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx = speed
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy = -speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy = speed

        if dx != 0 and dy != 0:
            dx *= 0.7071
            dy *= 0.7071

        self.x += dx * dt * 60
        self.y += dy * dt * 60
        self.x = max(self.radius, min(config.PLAYFIELD_WIDTH - self.radius, self.x))
        self.y = max(self.radius, min(config.PLAYFIELD_HEIGHT - self.radius, self.y))

        if self.dashable:
            dash_key = keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]
            if dash_key and not self._prev_dash_key:
                self.dash()
            self._prev_dash_key = dash_key

        if self.auto_shoot or keys[pygame.K_z]:
            self.shoot()

    def shoot(self):
        self.shoot_timer += 1
        delay = self.focus_shoot_delay if self.is_focus else self.shoot_delay
        if self.shoot_timer < delay:
            return
        self.shoot_timer = 0

        power = min(6, self.power)
        if power < 3:
            count = 1
        elif power < 5:
            count = 3
        else:
            count = 5
        spread = 0.15 if count > 1 else 0.0
        for i in range(count):
            angle = -math.pi / 2 + (i - (count - 1) / 2) * spread
            if self.weave_shot and self.is_focus:
                angle += math.sin(pygame.time.get_ticks() * 0.005) * 0.15
            speed = 10 + power * 0.5
            bullet = self._create_bullet(angle, speed)
            self.player_bullets.append(bullet)

    def _create_bullet(self, angle, speed):
        bullet_type = self.bullet_type
        if bullet_type == "laser":
            return bullets.LaserBullet(self.x, self.y, angle, speed, color=self.color)
        elif bullet_type == "explosive":
            return bullets.ExplosiveBullet(self.x, self.y, angle, speed, color=self.color)
        elif bullet_type == "split":
            return bullets.SplitBullet(self.x, self.y, angle, speed, color=self.color)
        elif bullet_type == "homing":
            return bullets.HomingBullet(self.x, self.y, angle, speed, color=self.color, target=None)
        elif bullet_type == "pierce":
            return bullets.PierceBullet(self.x, self.y, angle, speed, color=self.color)
        else:
            return bullets.Bullet(self.x, self.y, angle, speed, color=self.color, radius=6)

    def dash(self):
        if self.dash_timer > 0:
            return
        self.invincible = 15
        self.dash_timer = self.dash_cooldown
        speed_boost = 10
        keys = pygame.key.get_pressed()
        dx, dy = 0, 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx = -speed_boost
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx = speed_boost
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy = -speed_boost
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy = speed_boost
        if dx == 0 and dy == 0:
            dy = -speed_boost
        self.x += dx
        self.y += dy

    def use_bomb(self):
        if self.bombs <= 0:
            return False
        self.bombs -= 1
        self.bombs_used += 1
        self.invincible = 30
        print(f"[BOMB] Использована бомба! Осталось: {self.bombs}")

        # Очистка экрана от вражеских пуль (для всех)
        for b in list(self.enemy_bullets):
            b.alive = False

        # Нанесение урона врагам и боссам
        for e in list(self.enemies):
            if e.alive:
                e.hp -= 50
                if e.hp <= 0:
                    e.alive = False
                    # бонусы за убийство выпадут позже в обработке
        if self.boss and self.boss.alive:
            self.boss.hp -= 100
            if self.boss.hp <= 0:
                self.boss.alive = False
        if self.secret_boss and self.secret_boss.alive:
            self.secret_boss.hp -= 80
            if self.secret_boss.hp <= 0:
                self.secret_boss.alive = False

        # Специфические способности
        if self.salt_explosion:
            print("[BOMB] Солевой взрыв активирован!")
            # Удаляем все пули, наносим ещё больше урона
            for b in list(self.enemy_bullets):
                b.alive = False
            for e in list(self.enemies):
                if e.alive:
                    e.hp -= 30
            if self.boss and self.boss.alive:
                self.boss.hp -= 30
            if self.secret_boss and self.secret_boss.alive:
                self.secret_boss.hp -= 30

        if self.random_bomb:
            print("[BOMB] Случайный эффект бомбы!")
            effects = [
                lambda: setattr(self, 'bombs', min(8, self.bombs + 2)),
                lambda: setattr(self, 'lives', self.lives + 1),
                lambda: setattr(self, 'power', min(6, self.power + 1)),
                lambda: None  # можно добавить что-то ещё
            ]
            random.choice(effects)()

        return True

    def _clear_bullets(self):
        for b in list(self.enemy_bullets):
            b.alive = False

    def hit(self):
        if self.invincible > 0:
            return
        self.lives -= 1
        self.hits_taken += 1
        self.invincible = 90
        if self.lives <= 0:
            self.alive = False

    def apply_freeze(self):
        self.frozen_timer = 60

    def in_aura(self, x, y):
        if not self.aura_slowdown:
            return False
        return math.hypot(x - self.x, y - self.y) < self.aura_radius

    def draw(self, surf):
        if not self.alive:
            return
        if self.invincible > 0 and self.invincible % 6 < 3:
            return

        pygame.draw.circle(surf, self.color, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surf, config.WHITE, (int(self.x), int(self.y)), self.radius, 2)

        head_radius = self.radius * 0.45
        head_y = int(self.y - self.radius - head_radius)
        pygame.draw.circle(surf, config.SKIN, (int(self.x), head_y), int(head_radius))
        pygame.draw.circle(surf, config.WHITE, (int(self.x), head_y), int(head_radius), 1)

        eye_off = int(head_radius * 0.3)
        eye_y = head_y - int(head_radius * 0.2)
        pygame.draw.circle(surf, config.BLACK, (int(self.x) - eye_off, eye_y), max(2, int(head_radius * 0.1)))
        pygame.draw.circle(surf, config.BLACK, (int(self.x) + eye_off, eye_y), max(2, int(head_radius * 0.1)))

        mouth_y = head_y + int(head_radius * 0.2)
        pygame.draw.line(surf, config.BLACK,
                         (int(self.x) - int(head_radius * 0.2), mouth_y),
                         (int(self.x) + int(head_radius * 0.2), mouth_y), 2)

        if self.aura_slowdown and self.aura_radius > 0:
            pygame.draw.circle(surf, (0, 255, 255, 40), (int(self.x), int(self.y)), self.aura_radius, 1)

        if self.is_focus:
            pygame.draw.circle(surf, (255, 255, 255, 120), (int(self.x), int(self.y)), self.hit_radius, 1)

    def get_rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2)