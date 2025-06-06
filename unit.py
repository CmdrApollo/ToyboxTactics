import os
from character import character_from_file

def sign(value):
    if value < 0:
        return -1
    elif value > 0:
        return 1
    else:
        return 0

def lerp(a, b, t):
    return a + (b - a) * t

XP_MOD = 1.2

class Weapon:
    def __init__(self, name, damage, r, heavy):
        self.name = name
        self.damage = damage
        self.range = r
        self.heavy = heavy

    def __str__(self):
        return f"{self.name} ({self.damage} damage, {self.range} range)"
    
    def __repr__(self):
        return f"Weapon({self.name}, {self.damage}, {self.range})"

class Thumbtack(Weapon):
    def __init__(self):
        super().__init__("Thumbtack", 5, 1, False)

class Toothpick(Weapon):
    def __init__(self):
        super().__init__("Toothpick", 4, 2, False)

class SewingNeedle(Weapon):
    def __init__(self):
        super().__init__("Sewing Needle", 5, 2, False)

class Armor:
    def __init__(self, name, protection_chance, heavy):
        self.name = name
        self.protection_chance = protection_chance
        self.heavy = heavy

class PaperArmor(Armor):
    def __init__(self):
        super().__init__("Paper Armor", 0.1, False)

class CardboardArmor(Armor):
    def __init__(self):
        super().__init__("Cardboard Armor", 0.2, False)

class FoilArmor(Armor):
    def __init__(self):
        super().__init__("Foil Armor", 0.3, True)

class Unit:
    def __init__(self, placed, name, description, heavy, health, action_points, character, max_move, xp_given, strength, defense, x, y):
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

        self.xp = 0
        self.xp_to_level_up = 10

        self.weapon = SewingNeedle()
        self.armor = PaperArmor()

        self.draw_x = x
        self.draw_y = y

        self.path = []

        self.cooldown = 0.3

        self.done_with_turn = False

        self.defending = False

        self.level = 1

        self.placed = placed

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
        return False

    def give_xp(self, value):
        self.xp += value

        if self.xp >= self.xp_to_level_up:
            self.xp -= self.xp_to_level_up
            self.xp_to_level_up = int(self.xp_to_level_up * XP_MOD)

            self.level += 1
            
            return True

        return False

class ScoutUnit(Unit):
    def __init__(self, placed, x, y, name = "Scout"):
        super().__init__(placed, name, [
            "The Scout is a fast and agile unit,",
            "perfect for reconnaissance and quick",
            "strikes.",
        ], False, 15, 3, character_from_file(os.path.join("assets", "characters", "scout.char")), 3, 1, 1, 1, x, y)
    
class SoldierUnit(Unit):
    def __init__(self, placed, x, y, name = "Soldier"):
        super().__init__(placed, name, [
            "The Soldier is a balanced unit,",
            "capable of both offense and defense.",
        ], False, 20, 2, character_from_file(os.path.join("assets", "characters", "soldier.char")), 3, 2, 1, 2, x, y)

class HeavyUnit(Unit):
    def __init__(self, placed, x, y, name = "Hvy. Soldier"):
        super().__init__(placed, name, [
            "The Heavy Soldier is a powerful unit,",
            "with high health and damage output,",
            "but slower movement speed.",
        ], True, 30, 2, character_from_file(os.path.join("assets", "characters", "heavy.char")), 2, 3, 2, 1, x, y)