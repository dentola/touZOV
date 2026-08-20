import pygame
import math
import random
import config
import bullets

class Enemy:
    def __init__(self, x, y, hp=20, speed=0.5, shoot_delay=60, color=config.GREEN, is_obstacle=False, bullet_mult=1.0):
        self.x = x
        self.y = y
        self.hp = hp
        self.max_hp = hp
        self.color = color
        self.radius = 15 if not is_obstacle else 20
        self.shoot_timer = 0
        self.shoot_delay = shoot_delay + random.randint(30, 90)
        self.angle = 0
        self.pattern = random.choice(['circle', 'aimed', 'spiral', 'burst'])
        self.alive = True
        self.speed = speed if not is_obstacle else 0
        self.is_obstacle = is_obstacle
        self.bullet_mult = bullet_mult
        self.drops_powerup = random.random() < 0.7

    def update(self, player, dt, enemy_bullets):
        if not self.alive:
            return
        if not self.is_obstacle:
            self.y += self.speed * dt * 60
            if self.y > config.PLAYFIELD_HEIGHT + 50:
                self.alive = False
                return
        self.shoot_timer += 1
        if not self.is_obstacle and self.shoot_timer >= self.shoot_delay:
            self.shoot_timer = 0
            speed = 3 * self.bullet_mult
            if self.pattern == 'circle':
                for i in range(8):
                    angle = math.radians(i * 45) + self.angle
                    enemy_bullets.append(bullets.Bullet(self.x, self.y, angle, speed, config.RED, 4))
                self.angle += 0.1
            elif self.pattern == 'aimed':
                dx = player.x - self.x
                dy = player.y - self.y
                angle = math.atan2(dy, dx)
                enemy_bullets.append(bullets.Bullet(self.x, self.y, angle, speed + 1, config.PINK, 4))
            elif self.pattern == 'spiral':
                enemy_bullets.append(bullets.Bullet(self.x, self.y, self.angle, speed, config.PURPLE, 5))
                self.angle += 0.2
            elif self.pattern == 'burst':
                for i in range(5):
                    angle = math.radians(i * 72) + self.angle
                    enemy_bullets.append(bullets.RingBullet(self.x, self.y, angle, speed, config.ORANGE, 4))
                self.angle += 0.05

    def draw(self, surf):
        if not self.alive:
            return
        pygame.draw.circle(surf, self.color, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surf, config.WHITE, (int(self.x), int(self.y)), self.radius, 2)
        eye_off = self.radius // 3
        pygame.draw.circle(surf, config.BLACK, (int(self.x - eye_off), int(self.y - 4)), 3)
        pygame.draw.circle(surf, config.BLACK, (int(self.x + eye_off), int(self.y - 4)), 3)
        bar_width = self.radius * 2
        bar_height = 4
        hp_ratio = max(0.0, self.hp / self.max_hp)
        pygame.draw.rect(surf, config.RED, (self.x - self.radius, self.y - self.radius - 10, bar_width, bar_height))
        pygame.draw.rect(surf, config.GREEN, (self.x - self.radius, self.y - self.radius - 10, bar_width * hp_ratio, bar_height))

    def get_rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2)