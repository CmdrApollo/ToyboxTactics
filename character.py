import pygame
import math
import random
import json

class Part:
    def __init__(self, name, color):
        self.name = name
        self.color = color

    def draw(self, win, x, y, scale, body_offset, limb_offset):
        pass

class Circle(Part):
    def __init__(self, name, color, x, y, radius):
        super().__init__(name, color)
        self.x = x
        self.y = y
        self.radius = radius
    
    def draw(self, win, x, y, scale, body_offset, limb_offset):
        o = 0
        
        if self.name in ["body", "head"]:
            o = body_offset * scale
        if self.name == "head":
            o /= 2

        pygame.draw.circle(win, self.color, (x + self.x * scale, y + self.y * scale + o), self.radius * scale)

        return self.x - self.radius, self.y - self.radius

class Poly(Part):
    def __init__(self, name, color, points):
        super().__init__(name, color)
        self.points = points
        
    def draw(self, win, x, y, scale, body_offset, limb_offset):
        o = 0

        if self.name in ["body", "head"] or "arm" in self.name:
            o = body_offset * scale
        if self.name == "head":
            o /= 2

        pygame.draw.polygon(win, self.color, [(x + p[0] * scale, y + p[1] * scale + o) for p in self.points])

        return min(p[0] for p in self.points), min(p[1] for p in self.points)

class Line(Part):
    def __init__(self, name, color, points, thickness):
        super().__init__(name, color)
        self.points = points
        self.thickness = thickness
        
    def draw(self, win, x, y, scale, body_offset, step_cycle):
        o = 0
        
        if self.name in ["body", "head"] or "arm" in self.name:
            o = body_offset * scale
        if self.name == "head":
            o /= 2

        hip_point, foot_point = [(p[0], p[1]) for p in self.points]

        hip_point = pygame.Vector2(hip_point)
        foot_point = pygame.Vector2(foot_point)

        if "leg" in self.name:
            if step_cycle:
                if step_cycle < 1:
                    if "left" in self.name:
                        foot_point.x += 0.1 * (step_cycle - 0.5) * 2
                        foot_point.y -= 0.2 * math.sin(step_cycle * math.pi)
                    else:
                        step_cycle = 2 - step_cycle
                        foot_point.x -= 0.1 * (step_cycle - 1.5) * 2
                        foot_point.y = 1.0
                else:
                    if "left" in self.name:
                        foot_point.x -= 0.1 * (step_cycle - 1.5) * 2
                        foot_point.y = 1.0
                    else:
                        step_cycle = 2 - step_cycle
                        foot_point.x += 0.1 * (step_cycle - 0.5) * 2
                        foot_point.y -= 0.2 * math.sin(step_cycle * math.pi)

        hip_point *= scale
        hip_point.x += x; hip_point.y += y
        foot_point *= scale
        foot_point.x += x; foot_point.y += y
                
        pygame.draw.line(win, self.color, hip_point, foot_point, int(scale * self.thickness))

        return min(hip_point.x, foot_point.x) / scale, min(hip_point.y, foot_point.y) / scale

class Character:
    def __init__(self, parts: list[Part]):
        self.parts = parts
        self.x = 0
        self.y = 0
        self.scale = 30
        self.body_off_mult, self.limb_off_mult = random.randint(30, 35) / 10, 4
        self.surf = None
    
    def draw(self, win, cam, limb_move, invert_limbs, color='white', selected=False):
        time = pygame.time.get_ticks() / 1000

        body_offset_y = math.sin(time * self.body_off_mult) * 0.05
        
        if limb_move:
            limb_offset = math.fmod(time * self.limb_off_mult, 2)

            if invert_limbs: limb_offset = 2 - limb_offset
        else:
            limb_offset = 0

        self.surf = pygame.Surface((self.scale * 4, self.scale * 4), pygame.SRCALPHA)

        self.minx, self.miny = 100, 100

        for part in self.parts:
            mx, my = part.draw(self.surf, self.scale * 2, self.scale * 2, self.scale, body_offset_y, limb_offset)
            
            if mx < self.minx: self.minx = mx
            if my < self.miny: self.miny = my

        self.minx += 1
        self.minx /= 2
        self.miny += 1
        self.miny /= 2

        outline = pygame.mask.from_surface(self.surf).outline()

        w = 2

        if selected:
            w = round(2 + math.sin(pygame.time.get_ticks() / 200))

        win.blit(self.surf, (self.x - cam.x - self.surf.get_width() / 2, self.y - cam.y - self.surf.get_height() / 2))
        pygame.draw.polygon(win, color if not selected else 'yellow', [(
                self.x - cam.x - self.surf.get_width() / 2 + o[0],
                self.y - cam.y - self.surf.get_height() / 2 + o[1]
            )
            for o in outline
        ], w)

def character_from_file(f):
    data = json.load(open(f))
    parts = []

    for p in data["parts"]:
        match p["shape"]:
            case "circle":
                parts.append(Circle(p["name"], p["color"], p["definition"][0][0], p["definition"][0][1], p["definition"][1]))
            case "poly":
                parts.append(Poly(p["name"], p["color"], p["definition"]))
            case "line":
                parts.append(Line(p["name"], p["color"], p["definition"][:2], p["definition"][2]))
            case _:
                pass

    return Character(parts)