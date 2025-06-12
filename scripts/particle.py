import pygame
import random
import math

class Particle:
    def __init__(self, x, y, lifetime=1.0):
        self.ox, self.oy = x, y
        self.x = x
        self.y = y
        self.rotation = random.random() * math.tau
        self.lifetime = lifetime
        self.time = lifetime
        self.speed = random.randint(10, 30)
        self.rot_speed = random.randint(-20, 20)
        self.color = 'orange' if random.random() < 0.7 else 'red' if random.random() < 0.5 else 'yellow'
        self.n = random.randint(3, 4)

    def update(self, delta):
        self.y -= delta * self.speed
        self.time = max(0, self.time - delta)
        self.rotation += self.rot_speed * delta

        if self.time == 0:
            self.x, self.y = self.ox, self.oy
            self.time = self.lifetime
            self.n = random.randint(3, 4)
            self.color = 'orange' if random.random() < 0.7 else 'red' if random.random() < 0.5 else 'yellow'

    def draw(self, screen):
        scale = (self.time / self.lifetime) * 10
        r = math.radians(self.rotation)

        n = self.n

        points = [
            (math.cos(r + i * (math.tau / n)), math.sin(r + i * (math.tau / n)))
            for i in range(n)
        ]

        pygame.draw.polygon(screen, self.color, [(self.x + p[0] * scale, self.y + p[1] * scale) for p in points])