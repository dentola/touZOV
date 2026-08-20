import pygame
import math
import random
import config

class Bullet:
    def __init__(self, x, y, angle, speed, color=config.RED, radius=8, custom_sprite=None):
        self.x, self.y = x, y
        self.angle = angle
        self.speed = speed
        self.color = color
        self.radius = radius
        self.custom_sprite = None  # не используется
        self.alive = True
        self.grazed = False
        self.pierce = False
        self.freeze = False

    def update(self, dt, slow=1.0):
        self.x += math.cos(self.angle) * self.speed * dt * 60 * slow
        self.y += math.sin(self.angle) * self.speed * dt * 60 * slow
        if (self.x < -50 or self.x > config.PLAYFIELD_WIDTH + 50 or
                self.y < -50 or self.y > config.PLAYFIELD_HEIGHT + 50):
            self.alive = False

    def draw(self, surf):
        pygame.draw.circle(surf, self.color, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surf, config.WHITE, (int(self.x), int(self.y)), self.radius, 1)

    def get_rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2)


class SquareBullet(Bullet):
    def draw(self, surf):
        rect = pygame.Rect(int(self.x) - self.radius, int(self.y) - self.radius, self.radius * 2, self.radius * 2)
        pygame.draw.rect(surf, self.color, rect)
        pygame.draw.rect(surf, config.WHITE, rect, 1)


class TriangleBullet(Bullet):
    def draw(self, surf):
        points = [
            (self.x + math.cos(self.angle) * self.radius, self.y + math.sin(self.angle) * self.radius),
            (self.x + math.cos(self.angle + 2.4) * self.radius, self.y + math.sin(self.angle + 2.4) * self.radius),
            (self.x + math.cos(self.angle - 2.4) * self.radius, self.y + math.sin(self.angle - 2.4) * self.radius),
        ]
        pygame.draw.polygon(surf, self.color, points)
        pygame.draw.polygon(surf, config.WHITE, points, 1)


class StarBullet(Bullet):
    def draw(self, surf):
        points = []
        for i in range(10):
            angle = self.angle + math.pi * i / 5
            r = self.radius if i % 2 == 0 else self.radius // 2
            px = self.x + math.cos(angle) * r
            py = self.y + math.sin(angle) * r
            points.append((px, py))
        pygame.draw.polygon(surf, self.color, points)
        pygame.draw.polygon(surf, config.WHITE, points, 1)


class RingBullet(Bullet):
    def draw(self, surf):
        pygame.draw.circle(surf, self.color, (int(self.x), int(self.y)), self.radius, 2)


class LightningBullet(Bullet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._jitter = [random.randint(-4, 4) for _ in range(4)]

    def draw(self, surf):
        points = [(self.x, self.y)]
        for i in range(1, 5):
            offset = self._jitter[i - 1]
            px = self.x - math.cos(self.angle) * i * 8 + offset
            py = self.y - math.sin(self.angle) * i * 8 + offset
            points.append((px, py))
        pygame.draw.lines(surf, self.color, False, points, 2)
        pygame.draw.circle(surf, self.color, (int(self.x), int(self.y)), 3)


class TextBullet(Bullet):
    def __init__(self, x, y, angle, speed, text, color=config.WHITE, size=24):
        super().__init__(x, y, angle, speed, color, max(6, size // 3))
        self.text = text
        self.size = size
        self.font = pygame.font.Font(config.FONT_PATH, size) if config.FONT_PATH else pygame.font.Font(None, size)

    def draw(self, surf):
        rendered = self.font.render(self.text, True, self.color)
        rect = rendered.get_rect(center=(int(self.x), int(self.y)))
        surf.blit(rendered, rect)


class LaserBullet(Bullet):
    def __init__(self, x, y, angle, speed=0, color=config.CYAN, length=420, width=5):
        super().__init__(x, y, angle, speed, color, width)
        self.length = length
        self.pierce = True
        self.life = 14
        self.warmup = 10

    def update(self, dt, slow=1.0):
        if self.warmup > 0:
            self.warmup -= 1
            return
        self.life -= 1
        if self.life <= 0:
            self.alive = False

    def draw(self, surf):
        dx = math.cos(self.angle) * self.length
        dy = math.sin(self.angle) * self.length
        end_x, end_y = self.x + dx, self.y + dy
        if self.warmup > 0:
            pygame.draw.line(surf, self.color, (int(self.x), int(self.y)), (int(end_x), int(end_y)), 1)
        else:
            glow = tuple(min(255, c + 60) for c in self.color)
            pygame.draw.line(surf, glow, (int(self.x), int(self.y)), (int(end_x), int(end_y)), self.radius + 5)
            pygame.draw.line(surf, self.color, (int(self.x), int(self.y)), (int(end_x), int(end_y)), self.radius)
            pygame.draw.line(surf, config.WHITE, (int(self.x), int(self.y)), (int(end_x), int(end_y)), max(1, self.radius - 2))

    def get_rect(self):
        if self.warmup > 0:
            return pygame.Rect(int(self.x), int(self.y), 0, 0)
        dx = math.cos(self.angle) * self.length
        dy = math.sin(self.angle) * self.length
        return pygame.Rect(int(min(self.x, self.x + dx)), int(min(self.y, self.y + dy)), int(abs(dx)) or 1, int(abs(dy)) or 1)


class ExplosiveBullet(Bullet):
    def __init__(self, x, y, angle, speed, color=config.RED, radius=6):
        super().__init__(x, y, angle, speed, color, radius)
        self.explosion_radius = 60
        self.explosion_damage = 30

    def explode(self, enemies, boss, secret_boss):
        for enemy in enemies:
            if math.hypot(enemy.x - self.x, enemy.y - self.y) < self.explosion_radius:
                enemy.hp -= self.explosion_damage
        if boss and boss.alive and math.hypot(boss.x - self.x, boss.y - self.y) < self.explosion_radius:
            boss.hp -= self.explosion_damage
        if secret_boss and secret_boss.alive and math.hypot(secret_boss.x - self.x, secret_boss.y - self.y) < self.explosion_radius:
            secret_boss.hp -= self.explosion_damage
        return {'x': self.x, 'y': self.y, 'radius': 4, 'max_radius': self.explosion_radius, 'alpha': 220, 'color': config.ORANGE}


class SplitBullet(Bullet):
    def __init__(self, x, y, angle, speed, color=config.PURPLE, radius=4):
        super().__init__(x, y, angle, speed, color, radius)
        self.split_timer = 28

    def update(self, dt, slow=1.0):
        super().update(dt, slow)
        if not self.alive:
            return False
        self.split_timer -= 1
        if self.split_timer <= 0:
            self.alive = False
            return True
        return False

    def split(self):
        parts = []
        for i in range(5):
            a = self.angle + math.radians(i * 72)
            parts.append(Bullet(self.x, self.y, a, 5, self.color, 3))
        return parts


class HomingBullet(Bullet):
    def __init__(self, x, y, angle, speed, color=config.GREEN, radius=5, target=None, turn_rate=0.05, homing_time=90, custom_sprite=None):
        super().__init__(x, y, angle, speed, color, radius)
        self.target = target
        self.turn_rate = turn_rate
        self.homing_time = homing_time

    def update(self, dt, slow=1.0):
        if self.homing_time > 0 and self.target is not None and getattr(self.target, "alive", True):
            self.homing_time -= 1
            desired = math.atan2(self.target.y - self.y, self.target.x - self.x)
            diff = (desired - self.angle + math.pi) % (2 * math.pi) - math.pi
            self.angle += max(-self.turn_rate, min(self.turn_rate, diff))
        super().update(dt, slow)

    def draw(self, surf):
        tip = (self.x + math.cos(self.angle) * self.radius * 1.6, self.y + math.sin(self.angle) * self.radius * 1.6)
        tail1 = (self.x + math.cos(self.angle + 2.6) * self.radius, self.y + math.sin(self.angle + 2.6) * self.radius)
        tail2 = (self.x + math.cos(self.angle - 2.6) * self.radius, self.y + math.sin(self.angle - 2.6) * self.radius)
        pygame.draw.polygon(surf, self.color, [tip, tail1, tail2])
        flame = (self.x - math.cos(self.angle) * self.radius, self.y - math.sin(self.angle) * self.radius)
        pygame.draw.circle(surf, config.YELLOW, (int(flame[0]), int(flame[1])), 2)


class FreezeBullet(Bullet):
    def __init__(self, x, y, angle, speed, color=None, radius=6):
        super().__init__(x, y, angle, speed, color or config.ICE, radius)
        self.freeze = True
        self.spin = random.uniform(0, math.pi)

    def update(self, dt, slow=1.0):
        super().update(dt, slow)
        self.spin += 0.15 * dt * 60

    def draw(self, surf):
        pts = []
        for i in range(6):
            a = self.spin + i * math.pi / 3
            pts.append((self.x + math.cos(a) * self.radius, self.y + math.sin(a) * self.radius))
        pygame.draw.polygon(surf, self.color, pts)
        pygame.draw.polygon(surf, config.WHITE, pts, 1)


class BounceBullet(Bullet):
    def __init__(self, x, y, angle, speed, color=config.YELLOW, radius=5, bounces=2):
        super().__init__(x, y, angle, speed, color, radius)
        self.bounces = bounces

    def update(self, dt, slow=1.0):
        self.x += math.cos(self.angle) * self.speed * dt * 60 * slow
        self.y += math.sin(self.angle) * self.speed * dt * 60 * slow
        bounced = False
        if self.x < 0:
            self.x = 0
            self.angle = math.pi - self.angle
            bounced = True
        elif self.x > config.PLAYFIELD_WIDTH:
            self.x = config.PLAYFIELD_WIDTH
            self.angle = math.pi - self.angle
            bounced = True
        if self.y < 0:
            self.y = 0
            self.angle = -self.angle
            bounced = True
        elif self.y > config.PLAYFIELD_HEIGHT:
            self.y = config.PLAYFIELD_HEIGHT
            self.angle = -self.angle
            bounced = True
        if bounced:
            self.bounces -= 1
            if self.bounces < 0:
                self.alive = False

    def draw(self, surf):
        pygame.draw.circle(surf, self.color, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surf, config.BLACK, (int(self.x), int(self.y)), self.radius, 1)


class PierceBullet(Bullet):
    def __init__(self, x, y, angle, speed, color=config.SILVER, radius=3):
        super().__init__(x, y, angle, speed, color, radius)
        self.pierce = True

    def draw(self, surf):
        tail = (self.x - math.cos(self.angle) * self.radius * 5, self.y - math.sin(self.angle) * self.radius * 5)
        tip = (self.x + math.cos(self.angle) * self.radius * 3, self.y + math.sin(self.angle) * self.radius * 3)
        pygame.draw.line(surf, self.color, tail, tip, max(2, self.radius))
        pygame.draw.circle(surf, config.WHITE, (int(tip[0]), int(tip[1])), max(1, self.radius - 1))


class VoidBullet(Bullet):
    def __init__(self, x, y, angle, speed, color=None, radius=7):
        super().__init__(x, y, angle, speed, color or config.VOID, radius)
        self.pulse = 0.0

    def update(self, dt, slow=1.0):
        super().update(dt, slow)
        self.pulse += 0.2 * dt * 60

    def draw(self, surf):
        r = max(2, int(self.radius + math.sin(self.pulse) * 2))
        pygame.draw.circle(surf, self.color, (int(self.x), int(self.y)), r)
        pygame.draw.circle(surf, config.PURPLE, (int(self.x), int(self.y)), r, 2)
        pygame.draw.circle(surf, config.WHITE, (int(self.x), int(self.y)), 2)