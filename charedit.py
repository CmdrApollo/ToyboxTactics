import pygame, json, math, random

from tkinter.filedialog import asksaveasfilename

from palette import PALETTE

WIDTH, HEIGHT = 1280, 720
WIN = pygame.display.set_mode((WIDTH, HEIGHT))

class Shapes:
    CIRCLE = 0
    POLY = 1

class Part:
    def __init__(self, name, color):
        self.name = name
        self.color = color

    def draw(self, win, x, y, scale, body_offset):
        pass

class Circle(Part):
    def __init__(self, name, color, x, y, radius):
        super().__init__(name, color)
        self.x = x
        self.y = y
        self.radius = radius
    
    def draw(self, win, x, y, scale, body_offset):
        o = 0
        
        if self.name in ["body", "head"] or "arm" in self.name:
            o = body_offset * scale
        if self.name == "head":
            o /= 2

        pygame.draw.circle(win, self.color, (x + self.x * scale, y + self.y * scale + o), self.radius * scale)

class Poly(Part):
    def __init__(self, name, color, points):
        super().__init__(name, color)
        self.points = points
        
    def draw(self, win, x, y, scale, body_offset):
        o = 0

        if self.name in ["body", "head"] or "arm" in self.name:
            o = body_offset * scale
        if self.name == "head":
            o /= 2

        pygame.draw.polygon(win, self.color, [(x + p[0] * scale, y + p[1] * scale + o) for p in self.points])

class Line(Part):
    def __init__(self, name, color, points, thickness):
        super().__init__(name, color)
        self.points = points
        self.thickness = thickness
        
    def draw(self, win, x, y, scale, body_offset):
        o = 0
        
        if self.name in ["body", "head"] or "arm" in self.name:
            o = body_offset * scale
        if self.name == "head":
            o /= 2

        pygame.draw.line(win, self.color, *[(x + p[0] * scale, y + p[1] * scale + o) for p in self.points], int(scale * self.thickness))

class Character:
    def __init__(self, parts: list[Part]):
        self.parts = parts
        self.x = 320
        self.y = 240
        self.scale = 400
    
    def draw(self, win):
        time = pygame.time.get_ticks() / 1000

        body_offset_y = 0

        surf = pygame.Surface((self.scale * 2, self.scale * 2), pygame.SRCALPHA)

        for part in self.parts:
            part.draw(surf, self.scale * 1, self.scale * 1, self.scale, body_offset_y)

        outline = pygame.mask.from_surface(surf).outline()

        if len(outline):
            pygame.draw.polygon(surf, 'white', outline, 1)
        
        win.blit(surf, (self.x - surf.get_width() / 2, self.y - surf.get_height() / 2))

        return surf

def load_from_file(f):
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

def save_to_file(char: Character):
    f = open(asksaveasfilename(), 'w')

    parts = []

    for part in char.parts:
        if type(part) == Circle: definition = [[part.x, part.y], part.radius]
        elif type(part) == Poly: definition = part.points
        elif type(part) == Line: definition = part.points + [part.thickness]
        else: definition = []

        d = {
            "name": part.name,
            "color": part.color,
            "shape": {
                Circle: "circle",
                Poly: "poly",
                Line: "line"
            }[type(part)],
            "definition": definition
        }
        parts.append(d)

    json.dump({"parts": parts}, f, indent='\t')

def random_character():
    parts = []

    head_col = random.choice(PALETTE)
    body_col = random.choice(PALETTE)

    while body_col == head_col:
        body_col = random.choice(PALETTE)

    template_heads = [
        Poly("head", head_col, [[-0.5, -1.0], [0.5, -1.0], [0.0, -0.25]]),
        Poly("head", head_col, [[-0.375, -1.0], [0.375, -1.0], [0.375, -0.25], [-0.375, -0.25]]),
        Circle("head", head_col, 0.0, -0.75, 0.5)
    ]
    template_bodies = [
        [
            Circle("body", body_col, 0, 0.25, 0.5),
            Circle("body", body_col, 0, -0.25, 0.3)
        ],
        [
            Circle("body", body_col, 0, 0.25, 0.4),
            Circle("body", body_col, 0, 0, 0.3),
            Circle("body", body_col, 0, -0.25, 0.2)
        ],
        [
            Circle("body", body_col, 0, 0, 0.75)
        ],
        [
            Poly("body", body_col, [[-0.5, -0.5], [0.5, -0.5], [0.333, 0.333], [0.0, 0.5], [-0.333, 0.333]])
        ],
        [
            Poly("body", body_col, [[-0.5, -0.5], [0.0, -0.75], [0.5, -0.5], [0.333, 0.333], [0.0, 0.5], [-0.333, 0.333]])
        ],
        [
            Poly("body", body_col, [[-0.5, 0.5], [0.5, 0.5], [0.333, -0.333], [0.0, -0.5], [-0.333, -0.333]])
        ],
        [
            Poly("body", body_col, [[-0.5, 0.5], [0.0, 0.75], [0.5, 0.5], [0.333, -0.333], [0.0, -0.5], [-0.333, -0.333]])
        ]
    ]

    legs_col = random.choice(PALETTE)

    while legs_col == head_col:
        legs_col = random.choice(PALETTE)

    while legs_col == body_col:
        legs_col = random.choice(PALETTE)

    parts.append(Line("leftleg", legs_col, [[-0.25, 0.25], [-0.25, 1.0]], 0.125))
    parts.append(Line("rightleg", legs_col, [[0.25, 0.25], [0.25, 1.0]], 0.125))

    for p in random.choice(template_bodies):
        parts.append(p)
    parts.append(random.choice(template_heads))

    return Character(parts)

def main():
    global SCALE
    character = Character([])

    clock = pygame.time.Clock()
    delta = 0
    
    run = True

    while run:
        delta = clock.tick(60) / 1000

        save = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    character = random_character()
                elif event.key == pygame.K_s:
                    save_to_file(character)
                elif event.key == pygame.K_p:
                    save = True

        WIN.fill('black')

        s = character.draw(WIN)

        if save:
            pygame.image.save(s, asksaveasfilename())

        pygame.display.flip()
    
    pygame.quit()

main()