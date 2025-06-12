import pygame
import os
import random
import math

from .character import character_from_file

from .particle import Particle

from .constants import DamageType

MAX_STAT_LEVEL = 99

def sign(value):
    if value < 0:
        return -1
    elif value > 0:
        return 1
    else:
        return 0

def lerp(a, b, t):
    return a + (b - a) * t

XP_MOD = 1.25

class Weapon:
    price = 100

    def __init__(self, name, damage, r, heavy, damage_type=DamageType.NORMAL):
        self.name = name
        self.damage = damage
        self.range = r
        self.heavy = heavy

        self.damage_type = damage_type

    def __str__(self):
        return f"{self.name} ({self.damage} damage, {self.range} range)"
    
    def __repr__(self):
        return f"Weapon({self.name}, {self.damage}, {self.range})"

    def draw(self, win, delta, x, y, scale):
        pass

class Thumbtack(Weapon):
    price = 25

    def __init__(self):
        super().__init__("Thumbtack", 50, 1, False)

    def draw(self, win, delta, x, y, scale):
        pygame.draw.polygon(win, 'silver', [(x + 2 * scale, y - scale), (x + 2 * scale - 5, y), (x + 2 * scale + 5, y)])

        pygame.draw.polygon(win, 'violetred', [
            (x + 2 * scale - 10, y), (x + 2 * scale + 10, y),
            (x + 2 * scale + 5, y + scale * 0.5), (x + 2 * scale + 10, y + scale),
            (x + 2 * scale - 10, y + scale), (x + 2 * scale - 5, y + scale * 0.5)
        ])

class Toothpick(Weapon):
    price = 40

    def __init__(self):
        super().__init__("Toothpick", 50, 2, False)

    def draw(self, win, delta, x, y, scale):
        pygame.draw.line(win, 'chocolate', (x + 2 * scale, y - scale), (x + 2 * scale, y + scale), scale // 6)

class SewingNeedle(Weapon):
    price = 50

    def __init__(self):
        super().__init__("Sewing Needle", 60, 2, True)

    def draw(self, win, delta, x, y, scale):
        pygame.draw.line(win, 'silver', (x + 2 * scale, y - scale), (x + 2 * scale, y + scale), scale // 6)

class Match(Weapon):
    price = 100

    def __init__(self):
        super().__init__("Match", 40, 2, True, DamageType.FIRE)
        self.particles = [Particle(-50, -50, 0.5 * random.random() + 1.0) for _ in range(10)]

    def draw(self, win, delta, x, y, scale):
        pygame.draw.line(win, 'chocolate4', (x + 2 * scale, y - scale), (x + 2 * scale, y + scale), scale // 6)

        for p in self.particles:
            p.ox = x + random.randint(-5, 5) + 2 * scale
            p.oy = y - scale
            p.update(delta)
            p.draw(win)

class Armor:
    price = 100

    def __init__(self, name, protection_value, heavy):
        self.name = name
        self.protection_value = protection_value
        self.heavy = heavy

class PaperArmor(Armor):
    price = 30

    def __init__(self):
        super().__init__("Paper Armor", 10, False)

class CardboardArmor(Armor):
    price = 40
    def __init__(self):
        super().__init__("Cardboard Armor", 20, False)

class FoilArmor(Armor):
    price = 50
    def __init__(self):
        super().__init__("Foil Armor", 30, True)

class Unit:
    classname = "Unit"

    def __init__(self, placed, name, description, heavy, health, action_points, character, max_move, xp_given, strength, defense, accuracy, agility, x, y):
        self.name = name
        self.description = description
        self.heavy = heavy
        self.health = health
        self.max_health = health
        self.action_points = action_points
        self.max_action_points = action_points
        self.character = character
        self.max_move = max_move
        self.xp_given = xp_given
        self.x = x
        self.y = y
        self.target_x = x
        self.target_y = y

        self.strength = strength
        self.defense = defense
        self.accuracy = accuracy

        self.xp = 0
        self.xp_to_level_up = 4

        self.weapon = Match() if self.name == "Bori" else Thumbtack()
        self.armor = None if self.name in ["Milo", "Toto", "Grub"] else PaperArmor()

        self.draw_x = x
        self.draw_y = y

        self.path = []

        self.cooldown = 0.3

        self.done_with_turn = False

        self.defending = False

        self.level = 1

        self.placed = placed

        self.onfire = False
        self.particles = []

    def update(self, delta):
        self.draw_x = lerp(self.draw_x, self.x, 0.1)
        self.draw_y = lerp(self.draw_y, self.y, 0.1)

        self.cooldown -= delta

        if self.cooldown <= 0:
            self.cooldown += 0.3
            
            p = self.path.pop(0) if len(self.path) else (self.y, self.x)

            self.draw_x = self.x
            self.draw_y = self.y

            self.x = p[1]
            self.y = p[0]
            return len(self.path) > 0

    def particle_update(self, delta, cam, world_to_screen):
        if self.onfire:
            wx, wy = self.character.x, self.character.y
            while len(self.particles) < 10:
                self.particles.append(Particle(wx + random.randint(-5, 5), wy + random.randint(-5, 5), 1 + random.random() * 0.5))
            
            for p in self.particles:
                p.ox, p.oy = wx + random.randint(-5, 5), wy + random.randint(-5, 5)
                p.update(delta)
        else:
            if len(self.particles):
                self.particles.pop()

        return False

    def give_xp(self, value):
        self.xp += value

        if self.xp >= self.xp_to_level_up:
            self.xp -= self.xp_to_level_up
            self.xp_to_level_up = math.ceil(self.xp_to_level_up * XP_MOD)

            self.level += 1

            # stats up
            self.max_health += random.randint(1, 3)
            self.strength += random.randint(1, 3)
            self.defense += random.randint(1, 3)
            self.accuracy += random.randint(1, 3)
            
            return True

        return False

    def calculate_hit_chance(self):
        return 0.75 + max(0, math.log10(self.accuracy) / 8)

    def calculate_protection_chance(self):
        return -1 + pow(2, self.defense / (MAX_STAT_LEVEL + 1))

class ScoutUnit(Unit):
    classname = "Scout"
    def __init__(self, placed, x, y, name = classname):
        super().__init__(placed, name, [
            "The Scout is a fast and agile unit,",
            "perfect for reconnaissance and quick",
            "strikes.",
        ], False, 150, 3, character_from_file(os.path.join("assets", "characters", "scout.char")), 3, 4, 5, 5, 5, 5, x, y)
    
class SoldierUnit(Unit):
    classname = "Soldier"
    def __init__(self, placed, x, y, name = classname):
        super().__init__(placed, name, [
            "The Soldier is a balanced unit,",
            "capable of both offense and defense.",
        ], False, 200, 2, character_from_file(os.path.join("assets", "characters", "soldier.char")), 3, 5, 5, 5, 5, 5, x, y)

class HeavyUnit(Unit):
    classname = "Hvy. Soldier"
    def __init__(self, placed, x, y, name = classname):
        super().__init__(placed, name, [
            "The Heavy Soldier is a powerful unit,",
            "with high health and damage output,",
            "but slower movement speed.",
        ], True, 300, 2, character_from_file(os.path.join("assets", "characters", "heavy.char")), 2, 6, 5, 5, 5, 5, x, y)
        
class Bori(Unit):
    def __init__(self, placed, x, y, name = "Bori"):
        super().__init__(placed, name, [
            "Bori has been completely and utterly",
            "corrupted by chaos, and acts as a",
            "powerful host for the maligned force."
        ], True, 500, 3, character_from_file(os.path.join("assets", "characters", "bori.char")), 2, 10, 5, 5, 5, 5, x, y)