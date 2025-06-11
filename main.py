VERSION = "0.0.1"

import pygame
import random
import os
import json

import glob

import math
import numpy as np

from character import character_from_file
from unit import *
from dialogue import DialogueManager
from item import *
from particle import Particle

from tcod import path

all_levels = [
    ("Tutorial", "level1.json"),
    ("Threadville Hooligans", "sidelevel1.json"),
    ("YYY", "sidelevel2.json"),
    ("Face-off Against Bori", "level2.json"),
]

level_descriptions = [
    "Replay the tutorial.",
    "Two toys have gone missing\nfrom Threadville. The village-\npeople suspect foul-play. Find\nthe missing toys!",
    "Sidequest #2",
    "Battle Bori, an unrelenting\nforce of chaos. This is the\nend of the demo."
]

level_challenges = [
    [
        "Beat the level.",
        "Beat the level in 2 turns\nor less.",
    ],
    [
        "Beat the level.",
        "Beat the level in 3 turns\nor less.",
    ],
    [
        "Beat the level.",
        "Beat the level in 3 turns\nor less.",
    ],
    [
        "Beat the level.",
        "Beat the level in 4 turns\nor less.",
    ]
]

completed_challenges = [
    [
        False,
        False,
    ],
    [
        False,
        False,
    ],
    [
        False,
        False,
    ],
    [
        False,
        False,
    ]
]

def get_level_with_name(name):
    for level in all_levels:
        if level[0] == name:
            return level
    return None

available_levels = [
    all_levels[0]
]

played_levels = []

sell_falloff = 0.25

character_names = ["Milo", "Toto", "Grub"]
character_colors = ["#ff8080", "#80ff80", "#8080ff"]
character_classes = [ScoutUnit, SoldierUnit, HeavyUnit]

character_buffer = []

OUTLINE = True
PAPERTEX = False

pygame.init()

SOUNDS = {}

for f in glob.glob(os.path.join('assets', 'audio', '**.wav')):
    SOUNDS.update({f.split('\\')[-1].split('.')[0]: pygame.mixer.Sound(f)})

for i in SOUNDS:
    SOUNDS[i].set_volume(0.0)

pygame.display.set_caption("Toybox Tactics")

WRONG_FONT = pygame.font.Font(os.path.join("assets", "visual", "Smudge.ttf"), 24)
FONT = pygame.font.Font(os.path.join("assets", "visual", "nunito.ttf"), 24)
SMALL_FONT = pygame.font.Font(os.path.join("assets", "visual", "nunito.ttf"), 16)
BIG_FONT = pygame.font.Font(os.path.join("assets", "visual", "nunito.ttf"), 30)

WIDTH, HEIGHT = 900, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))

TILE_SIZE = (80, 40)

FINDER = pygame.image.load("_finder.png")
FINDER = pygame.transform.scale(FINDER, (TILE_SIZE[0], TILE_SIZE[1]))

BG = pygame.Surface((WIDTH, HEIGHT))

for y in range(0, HEIGHT):
    pygame.draw.line(BG, pygame.Color("darkslategray2").lerp("darkslategray4", y / HEIGHT), (0, y), (WIDTH, y), 1)

b_width = 1

PG_CE_POWERED = pygame.image.load(os.path.join('assets', 'visual', 'pygame_ce_powered_lowres.webp')).convert_alpha()

_tex = pygame.image.load(os.path.join('assets', 'visual', 'paper.png')).convert()

def clamp(value, min_value, max_value):
    return max(min_value, min(value, max_value))

def lerp(a, b, t):
    return a + (b - a) * t

def from_world_pos(x, y):
    return [(x - y) * TILE_SIZE[0] / 2, (x + y) * TILE_SIZE[1] / 2]

def from_screen_pos(sx, sy, ox = 0, oy = 0):
    w, h = TILE_SIZE
    cx, cy = sx // w, sy // h
    
    wx = cy + cx
    wy = cy - cx
    
    x, y = (wx - ox, wy - oy)

    offx, offy = sx % w, sy % h

    col = FINDER.get_at((offx, offy))

    if col == pygame.Color("red"):
        x -= 1
    elif col == pygame.Color("green"):
        y -= 1
    elif col == pygame.Color("blue"):
        y += 1
    elif col == pygame.Color("yellow"):
        x += 1

    return x, y

def darken(color, value=0.2):
    c = pygame.Color(color)
    return (c.r * (1 - value), c.g * (1 - value), c.b * (1 - value))

def draw_tile(x, y, color, border=False):
    i, j = from_world_pos(x, y)
    if not border:
        pygame.draw.polygon(screen, darken(color, 0.4), [
            (i, j + TILE_SIZE[1] / 2),
            (i, j + TILE_SIZE[1] * 1.5),
            (i + TILE_SIZE[0] / 2, j + TILE_SIZE[1] * 2.0),
            (i + TILE_SIZE[0] / 2, j + TILE_SIZE[1]),
        ])

        pygame.draw.polygon(screen, darken(color, 0.2), [
            (i + TILE_SIZE[0] / 2, j + TILE_SIZE[1]),
            (i + TILE_SIZE[0] / 2, j + TILE_SIZE[1] * 2.0),
            (i + TILE_SIZE[0], j + TILE_SIZE[1] * 1.5),
            (i + TILE_SIZE[0], j + TILE_SIZE[1] / 2),
        ])

        pygame.draw.polygon(screen, color, [
            (i + TILE_SIZE[0] / 2, j),
            (i + TILE_SIZE[0], j + TILE_SIZE[1] / 2),
            (i + TILE_SIZE[0] / 2, j + TILE_SIZE[1]),
            (i, j + TILE_SIZE[1] / 2),
        ])
    else:
        pygame.draw.polygon(screen, darken(color, 0.4), [
            (i, j + TILE_SIZE[1] / 2),
            (i, j + TILE_SIZE[1] * 1.5),
            (i + TILE_SIZE[0] / 2, j + TILE_SIZE[1] * 2.0),
            (i + TILE_SIZE[0] / 2, j + TILE_SIZE[1]),
        ], b_width)

        pygame.draw.polygon(screen, darken(color, 0.2), [
            (i + TILE_SIZE[0] / 2, j + TILE_SIZE[1]),
            (i + TILE_SIZE[0] / 2, j + TILE_SIZE[1] * 2.0),
            (i + TILE_SIZE[0], j + TILE_SIZE[1] * 1.5),
            (i + TILE_SIZE[0], j + TILE_SIZE[1] / 2),
        ], b_width)

        pygame.draw.polygon(screen, color, [
            (i + TILE_SIZE[0] / 2, j),
            (i + TILE_SIZE[0], j + TILE_SIZE[1] / 2),
            (i + TILE_SIZE[0] / 2, j + TILE_SIZE[1]),
            (i, j + TILE_SIZE[1] / 2),
        ], b_width)

def draw_tile_flat(x, y, color, border=False):
    i, j = from_world_pos(x, y)
    if not border:
        pygame.draw.polygon(screen, color, [
            (i + TILE_SIZE[0] / 2, j),
            (i + TILE_SIZE[0], j + TILE_SIZE[1] / 2),
            (i + TILE_SIZE[0] / 2, j + TILE_SIZE[1]),
            (i, j + TILE_SIZE[1] / 2),
        ])
    else:
        pygame.draw.polygon(screen, color, [
            (i + TILE_SIZE[0] / 2, j),
            (i + TILE_SIZE[0], j + TILE_SIZE[1] / 2),
            (i + TILE_SIZE[0] / 2, j + TILE_SIZE[1]),
            (i, j + TILE_SIZE[1] / 2),
        ], b_width)

def draw_small_tile(x, y, color):
    i, j = from_world_pos(x, y)
    w, h = TILE_SIZE[0] * 0.8, TILE_SIZE[1] * 0.8
    
    i += TILE_SIZE[0] * 0.1
    j += TILE_SIZE[1] * 0.1

    surf = pygame.Surface((w, h), pygame.SRCALPHA)

    pygame.draw.polygon(surf, color, [
        (0 + w / 2, 0),
        (0 + w, 0 + h / 2),
        (0 + w / 2, 0 + h),
        (0, 0 + h / 2),
    ])

    surf.set_alpha(128)

    screen.blit(surf, (i, j))

def draw_tree(x, y):
    i, j = from_world_pos(x, y)

    j -= TILE_SIZE[1] / 2

    pygame.draw.rect(screen, "saddlebrown", (i + TILE_SIZE[0] / 2 - TILE_SIZE[0] / 10, j, TILE_SIZE[0] / 5, TILE_SIZE[1]))

    for k in range(3):
        pygame.draw.polygon(screen, "green" + str((3 - k) + 1), [
            (i + TILE_SIZE[0] / 2, j),
            (i + TILE_SIZE[0] * 0.75, j + TILE_SIZE[1] / 2),
            (i + TILE_SIZE[0] * 0.25, j + TILE_SIZE[1] / 2),
        ])
        j -= TILE_SIZE[1] * (0.5 / 3.0)

def draw_rock(x, y):
    i, j = from_world_pos(x, y)

    i -= 8

    j -= TILE_SIZE[1] / 2
    
    pygame.draw.polygon(screen, "darkgray", [
        (20 + i + TILE_SIZE[0] / 2, j + 20),
        (20 + i + TILE_SIZE[0] * 0.7, j + TILE_SIZE[1]),
        (20 + i + TILE_SIZE[0] * 0.3, j + TILE_SIZE[1]),
    ])
    
    pygame.draw.polygon(screen, "gray", [
        (i + TILE_SIZE[0] / 2, j),
        (i + TILE_SIZE[0] * 0.75, j + TILE_SIZE[1]),
        (i + TILE_SIZE[0] * 0.25, j + TILE_SIZE[1]),
    ])

def draw_unit(unit, friendly, x, y, is_selected=False, show_path=False):
    character = unit.character

    i, j = from_world_pos(unit.draw_x + x, unit.draw_y + y)

    if show_path:
        p = [(unit.y, unit.x)] + unit.path if len(unit.path) > 1 else []

        for k in range(len(p) - 1):
            px1, py1 = from_world_pos(p[k][1] + x, p[k][0] + y)
            px2, py2 = from_world_pos(p[k + 1][1] + x, p[k + 1][0] + y)
            pygame.draw.line(screen, "yellow", (px1 + TILE_SIZE[0] / 2, py1 + TILE_SIZE[1] / 2), (px2 + TILE_SIZE[0] / 2, py2 + TILE_SIZE[1] / 2), 3)

            if k == 0:
                pygame.draw.circle(screen, "yellow", (px1 + TILE_SIZE[0] / 2, py1 + TILE_SIZE[1] / 2), 5)
            if k == len(p) - 2:
                pygame.draw.circle(screen, "yellow", (px2 + TILE_SIZE[0] / 2, py2 + TILE_SIZE[1] / 2), 5)

    character.x = i + TILE_SIZE[0] / 2
    character.y = j - TILE_SIZE[1] / 4

    character.draw(screen, pygame.Vector2(0, 0), False, False, PAPERTEX, _tex, 'skyblue' if friendly else 'brown1', is_selected)

def draw_star(win, x, y, scale=10, rotation=0, col='lightyellow'):
    points = [
        [
            math.cos(math.radians(rotation + -90 + i * 36)) * (scale if i % 2 == 0 else scale / 2),
            math.sin(math.radians(rotation + -90 + i * 36)) * (scale if i % 2 == 0 else scale / 2)
        ]
        for i in range(10)
    ]

    pygame.draw.polygon(win, col, [[p[0] + x, p[1] + y] for p in points])

def GenerateSolidsMap(input_map, units_input, world_width=10, world_height=10):
    solids = np.array([[ 0 for _ in range(world_width) ] for _ in range(world_height)])
    solids[:] = True

    for x in range(world_width):
        for y in range(world_height):
            if input_map[y * world_width + x] not in [0, 4]:
                solids[y, x] = False
            for unit in units_input:
                if int(unit.x) == x and int(unit.y) == y:
                    solids[y, x] = False
    
    return solids

def play_tap_sound():
    SOUNDS[f"tap{random.randint(1, 3)}"].play()

def save_characters():
    # TODO FINISH THIS POST-DEMO

    global character_buffer

    data = {
        "characters": [
            {

            }
        ]
    }

def main():
    global character_buffer
    global available_levels
    clock = pygame.time.Clock()
    delta = 0.0

    main_menu_loadin = 1.0

    main_menu = True
    splash_screen = 4.0

    cam = pygame.Vector2(6, -4)

    selected_pos = (0, 0)

    def level_from_file(f):
        world_size = (0, 0)
        level = ""
        nature = []
        units = []

        data = {}

        with open(f, 'r') as file:
            data = json.load(file)
            file.close()
        
        world_size = (data['width'], data['height'])

        level = data['schema']

        for y in range(world_size[1]):
            for x in range(world_size[0]):
                nature.append(data['scenery'][y][x])
            
        for u in data['units']:
            match u['type']:
                case 'scout':
                    units.append(ScoutUnit(True, u['x'], u['y']))
                case 'soldier':
                    units.append(SoldierUnit(True, u['x'], u['y']))
                case 'heavy':
                    units.append(HeavyUnit(True, u['x'], u['y']))
                case 'bori':
                    units.append(Bori(True, u['x'], u['y']))

        return world_size, level, nature, units, data['during_battle_dialogue'], data['post_battle_dialogue'], data['available_sidequests'], data['next_level'], data['reward']

    current_level = 0

    level_name, level_filename = all_levels[current_level]

    # schemas are forest, mountain, desert, icy, and chaos
    world_size, schema, nature, enemy_units, thru_dialogue, end_dialogue, available_sidequests, next_level, level_reward = level_from_file(os.path.join("assets", "levels", level_filename))

    friendly_units = []
    
    units = []

    current_unit = 0

    turn = 0

    selected_unit = None

    party_inventory = {
        Potion: 3
    }

    c = GenerateSolidsMap(nature, units, world_size[0], world_size[1])

    graph = path.SimpleGraph(cost=c, cardinal=1, diagonal=0)

    c2 = GenerateSolidsMap(nature, enemy_units, world_size[0], world_size[1])

    graph_enemies_only = path.SimpleGraph(cost=c2, cardinal=1, diagonal=0)

    def mouse_to_tile_pos(ox=0, oy=0):
        mx, my = pygame.mouse.get_pos()
        x, y = from_screen_pos(mx, my, int(ox), int(oy))

        x = clamp(x, 0, world_size[0] - 1)
        y = clamp(y, 0, world_size[1] - 1)

        return (x, y)

    def unit_path_to(unit, sx, sy, include_target=True): 
        if unit in enemy_units:
            finder = path.Pathfinder(graph_enemies_only)
        else:
            finder = path.Pathfinder(graph)

        unit.target_x = sx
        unit.target_y = sy

        finder.add_root((unit.y, unit.x))

        unit.path = finder.path_to((sy, sx)).tolist()[1:]

        if include_target:
            unit.path.append((sy, sx))

    def draw_unit_move_grid(unit, cam_x, cam_y, graph):
        finder = path.Pathfinder(graph)

        finder.add_root((unit.y, unit.x))
        
        possible_moves = []

        for x in range(-unit.max_move, unit.max_move + 1):
            for y in range(-unit.max_move, unit.max_move + 1):
                if 0 <= unit.x + x < world_size[0] and 0 <= unit.y + y < world_size[1]:    
                    try:
                        try:
                            p = finder.path_to((unit.y + y, unit.x + x)).tolist()[1:]
                            if 0 < len(p) <= unit.max_move:
                                possible_moves.append((unit.x + x, unit.y + y))

                                draw_small_tile(unit.x + x + cam_x, unit.y + y + cam_y, "cyan")
                        except RuntimeError:
                            pass
                    except IndexError:
                        pass

        return possible_moves

    def get_grid_of_size(unit, size=1):
        possible_moves = []

        for x in range(-size, size + 1):
            for y in range(-size, size + 1):
                if x == 0 and y == 0:
                    continue
                if 0 <= unit.x + x < world_size[0] and 0 <= unit.y + y < world_size[1]:
                    if abs(x) + abs(y) <= size:
                        possible_moves.append((unit.x + x, unit.y + y))

        return possible_moves

    popups = []

    buttons = 0

    def add_text_popup(text, x, y, color="black"):
        t = SMALL_FONT.render(str(text), True, color)
        
        sx, sy = from_world_pos(x, y)

        sx += TILE_SIZE[0] / 2 - t.get_width() / 2

        popups.append({
            "text": text,
            "color": color,
            "x": sx,
            "y": sy,
            "time": 1.0
        })

    def draw_button(scr, x, y, w, h, text):
        can_show_info = True

        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.polygon(surf, (0, 0, 0, 255), [
            (0, 0), (0 + w - 20, 0),
            (0 + w, 0 + h), (0, 0 + h)
        ])

        surf.blit(SMALL_FONT.render(text, True, 'white'), (5, 3))

        if not pygame.Rect(x, y, w, h).collidepoint(pygame.mouse.get_pos()):
            surf.set_alpha(128)
        else:
            surf.set_alpha(192)
            can_show_info = False

        scr.blit(surf, (x, y))

        pygame.draw.polygon(scr, 'white', [
            (x, y), (x + w - 20, y),
            (x + w, y + h), (x, y + h)
        ], 2)

        return can_show_info

    units_should_move = False

    allowed_moves = []
    allowed_attacks = []

    ap_w = 0

    selected_action = "none"

    getting_target = False
    
    animation_time = 0.0

    banner_text = "Placement Phase"
    banner_time = 3.0

    placing_unit = 0

    battling = True
    won = False

    placed = False

    messages = []

    # non-battling variables
    curtain_timer = 0
    battle_ss = pygame.Surface((WIDTH, HEIGHT))

    menu = -1 # post battle seq

    dialogue_manager = DialogueManager(FONT, BIG_FONT, 'white', 'white')

    for i in range(len(thru_dialogue[turn])):
        dialogue_manager.queue_text(thru_dialogue[turn][i])

    shop_inventory = {
        Potion: 10,
        PaperArmorItem: 2,
        ThumbtackItem: 2,
        CardboardArmor: 2,
        Toothpick: 2,
        FoilArmor: 2,
        SewingNeedle: 2,
        Match: 1
    }

    button_reward = 80
    reward_falloff = 0.75

    def get_reward(n):
        return int(button_reward * pow(reward_falloff, n))

    run = True
    while run:
        delta = clock.tick_busy_loop(60) / 1000.0

        keys = pygame.key.get_pressed()

        selected_pos = mouse_to_tile_pos(cam.x, cam.y)
            
        evs = []

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            else:
                evs.append(event)
        
        sp = bool(splash_screen)

        splash_screen = max(0, splash_screen - delta)

        if splash_screen:
            splash_screen_surf = pygame.Surface((WIDTH, HEIGHT))
            splash_screen_surf.fill('mediumpurple')
            
            t = pygame.time.get_ticks() / 150
            t %= 50

            for x in range(WIDTH // 50 + 1):
                for y in range(HEIGHT // 50 + 1):
                    if (x + y) % 2 == 0:
                        fx, fy = 25 + x * 50 - t, 25 + y * 50 - t
                        q = 1 - abs(2 * ((fx + fy) / (WIDTH + HEIGHT) - 0.5))
                        r = 25 * pow(q, 1)
                        pygame.draw.circle(splash_screen_surf, darken('mediumpurple', 0.1), (fx, fy), r)

            splash_screen_surf.blit(PG_CE_POWERED, (WIDTH - PG_CE_POWERED.get_width() - 5, HEIGHT - PG_CE_POWERED.get_height() - 5))

            splash_screen_surf.blit(t := BIG_FONT.render("Toybox Tactics", True, 'black'), (2 + WIDTH // 2 - t.get_width() // 2, 2 + HEIGHT // 4 - t.get_height() // 2))
            splash_screen_surf.blit(t := BIG_FONT.render("Toybox Tactics", True, 'white'), (WIDTH // 2 - t.get_width() // 2, HEIGHT // 4 - t.get_height() // 2))

            splash_screen_surf.blit(t := FONT.render("A Paper Opcode Game", True, 'black'), (1 + WIDTH // 2 - t.get_width() // 2, 1 + HEIGHT // 3 - t.get_height() // 2))
            splash_screen_surf.blit(t := FONT.render("A Paper Opcode Game", True, 'white'), (WIDTH // 2 - t.get_width() // 2, HEIGHT // 3 - t.get_height() // 2))

            screen.blit(splash_screen_surf, (0, 0))
            black_screen = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            black_screen.fill('black')
            z = splash_screen / 4.0
            black_screen.set_alpha(int(255 * pow(2 * (z - 0.5), 2)))
            screen.blit(black_screen, (0, 0))

            pygame.display.flip()
            continue

        if sp:
            SOUNDS['maintheme'].play()

        if main_menu:
            for event in evs:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    w, h = 80, 30
                    s = 10
                    if pygame.Rect(WIDTH // 2 - w // 2, HEIGHT // 2 - h // 2 + (h + s) * 0, w, h).collidepoint(pygame.mouse.get_pos()):
                        main_menu = False
                    if pygame.Rect(WIDTH // 2 - w // 2, HEIGHT // 2 - h // 2 + (h + s) * 1, w, h).collidepoint(pygame.mouse.get_pos()):
                        run = False

            main_menu_loadin = max(0, main_menu_loadin - delta)

            screen.fill('mediumpurple')
            
            t = pygame.time.get_ticks() / 150
            t %= 50

            for x in range(WIDTH // 50 + 1):
                for y in range(HEIGHT // 50 + 1):
                    if (x + y) % 2 == 0:
                        fx, fy = 25 + x * 50 - t, 25 + y * 50 - t
                        q = 1 - abs(2 * ((fx + fy) / (WIDTH + HEIGHT) - 0.5))
                        r = 25 * pow(q, 1)
                        pygame.draw.circle(screen, darken('mediumpurple', 0.1), (fx, fy), r)

            screen.blit(PG_CE_POWERED, (WIDTH - PG_CE_POWERED.get_width() - 5, HEIGHT - PG_CE_POWERED.get_height() - 5))

            screen.blit(t := BIG_FONT.render("Toybox Tactics", True, 'black'), (2 + WIDTH // 2 - t.get_width() // 2, 2 + HEIGHT // 4 - t.get_height() // 2))
            screen.blit(t := BIG_FONT.render("Toybox Tactics", True, 'white'), (WIDTH // 2 - t.get_width() // 2, HEIGHT // 4 - t.get_height() // 2))

            w, h = 80, 30
            s = 10
            draw_button(screen, WIDTH // 2 - w // 2, HEIGHT // 2 - h // 2 + (h + s) * 0, w, h, "Play")
            draw_button(screen, WIDTH // 2 - w // 2, HEIGHT // 2 - h // 2 + (h + s) * 1, w, h, "Quit")

            screen.blit(t := SMALL_FONT.render(f"A Paper Opcode Game | v{VERSION}", True, 'white'), (5, HEIGHT - t.get_height() - 5))

            black_screen = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            black_screen.fill('black')
            z = main_menu_loadin
            black_screen.set_alpha(int(255 * pow(z, 2)))
            screen.blit(black_screen, (0, 0))

            pygame.display.flip()

            continue

        for event in evs:
            if event.type == pygame.KEYDOWN:
                if battling:
                    if event.key == pygame.K_SPACE:
                        battling = False
                        won = True
                        curtain_timer = 2.0

                        SOUNDS['maintheme'].stop()

                        SOUNDS['battle_win'].play()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if battling:
                    if dialogue_manager.has_dialogue():
                        dialogue_manager.on_confirm()
                        continue

                    if event.button == 1 and not turn & 1:
                        if selected_action == "move":
                            if selected_pos in allowed_moves:
                                units_should_move = True
                        elif selected_action == "attack":
                            if selected_pos in allowed_attacks:
                                for unit in units:
                                    if unit.x == selected_pos[0] and unit.y == selected_pos[1]:
                                        if unit != selected_unit:
                                            if unit.health > 0:
                                                if unit.armor and random.random() <= unit.armor.protection_chance + unit.defense / 100:
                                                    add_text_popup(f"Protected!", unit.x + cam.x, unit.y + cam.y, "forestgreen")
                                                else:
                                                    d = selected_unit.weapon.damage
                                                    d += random.randint(0, selected_unit.strength)
                                                    if unit.armor: d -= random.randint(0, unit.armor.protection_value)
                                                    add_text_popup(f"-{d}", unit.x + cam.x, unit.y + cam.y, "brown1")
                                                    unit.health -= d
                                                if unit.health <= 0:
                                                    if unit in friendly_units:
                                                        friendly_units.remove(unit)
                                                    else:
                                                        if selected_unit.give_xp(unit.xp_given):
                                                            # true on level up
                                                            add_text_popup(f"Level up!", selected_unit.x + cam.x, selected_unit.y + cam.y, "gold")
                                                            messages.append(f"{selected_unit.name} leveled up!")
                                                        else:
                                                            add_text_popup(f"+{unit.xp_given} xp!", selected_unit.x + cam.x, selected_unit.y + cam.y, "gold")
                                                            messages.append(f"{selected_unit.name} gained {unit.xp_given} xp!")
                                                        enemy_units.remove(unit)

                                                        buttons += random.randint(6, 12)

                                                    units.remove(unit)
                                                    SOUNDS["smash"].play()
                                                else:
                                                    play_tap_sound()
                                            else:
                                                SOUNDS["footstep"].play()
                                        break
                                        
                                selected_action = "none"
                                selected_unit.action_points -= 1
                        elif selected_action == "items":
                            w, h = 100, 30
                            x, y = from_world_pos(selected_unit.x + cam.x, selected_unit.y + cam.y)
                            x += selected_unit.character.scale * 2
                            y -= selected_unit.character.scale
                            for i in range(len(party_inventory)):
                                if pygame.Rect(x, y, w, h).collidepoint(pygame.mouse.get_pos()):
                                    if not list(party_inventory.keys())[i]().requires_target:
                                        o = list(party_inventory.keys())[i]().on_use(selected_unit, None)
                                        party_inventory.update({ list(party_inventory.keys())[i]: list(party_inventory.values())[i] - 1 })
                                        if o:
                                            add_text_popup(o[0], selected_unit.x + cam.x, selected_unit.y + cam.y, o[1])
                                        selected_action = "none"
                                        selected_unit.action_points -= 1
                                    else:
                                        getting_target = True
                                y += h
                        elif selected_action == "none" and placed:
                            s = 50
                            w, h = 80, 30
                            x, y = from_world_pos(selected_unit.x + cam.x, selected_unit.y + cam.y)
                            x += selected_unit.character.scale * 2
                            y -= selected_unit.character.scale
                            for i in range(4):
                                if pygame.Rect(x, y, w, h).collidepoint(pygame.mouse.get_pos()):
                                    selected_action = ["move", "attack", "items", "wait"][i]
                                    
                                    if selected_action == "attack":
                                        allowed_attacks = get_grid_of_size(selected_unit, selected_unit.weapon.range)
                                        
                                        SOUNDS["swoosh"].play()

                                    if selected_action == "wait":
                                        selected_action = "none"
                                        
                                        selected_unit.action_points  = 0

                                        SOUNDS["unknown"].play()

                                    break

                                y += h
                        elif selected_action == "none" and not placed:
                            if nature[selected_pos[1] * world_size[0] + selected_pos[0]] == 16:
                                if not len(character_buffer):
                                    friendly_units.append(character_classes[placing_unit](True, selected_pos[0], selected_pos[1], character_names[placing_unit]))
                                else:
                                    friendly_units.append(character_buffer.pop(0))
                                    friendly_units[-1].health = friendly_units[-1].max_health
                                    friendly_units[-1].action_points = friendly_units[-1].max_action_points
                                    friendly_units[-1].x = friendly_units[-1].target_x = friendly_units[-1].draw_x = selected_pos[0]
                                    friendly_units[-1].y = friendly_units[-1].target_y = friendly_units[-1].draw_y = selected_pos[1]
                                placing_unit += 1

                                nature[selected_pos[1] * world_size[0] + selected_pos[0]] = 0

                                if placing_unit == len(character_classes):
                                    banner_text = "Player Turn"
                                    banner_time = 3.0

                                    units = friendly_units + enemy_units

                                    selected_unit = units[current_unit]

                                    placed = True

                                    for y in range(world_size[1]):
                                        for x in range(world_size[0]):
                                            nature[y * world_size[0] + x] %= 16

                    elif event.button == 3:
                        selected_action = "none"
                else:
                    mx, my = pygame.mouse.get_pos()

                    match menu:
                        case -1:
                            w, h = 90, 30

                            for i in range(len(words)):
                                if pygame.Rect(WIDTH // 2 - w // 2, HEIGHT * 0.85 - h // 2 + (h + 10) * i, w, h).collidepoint(pygame.mouse.get_pos()):
                                    match i:
                                        case 0:
                                            menu = 0
                                        case 1:
                                            run = False
                        case 0:
                            if dialogue_manager.has_dialogue():
                                dialogue_manager.on_confirm()
                            else:
                                w, h = 100, 30
                                if pygame.Rect(WIDTH - w - 10, HEIGHT - h - 10, w, h).collidepoint(mx, my):
                                    menu = 1
                                
                                w, h = 200, 30
                                x, y = WIDTH // 3 - w // 2, HEIGHT // 3
                                y += FONT.size("Shop Items")[1] + 5

                                for i, (k, v) in enumerate(shop_inventory.items()):
                                    if pygame.Rect(x, y, w, h).collidepoint(mx, my):
                                        if k().price <= buttons:
                                            buttons -= k().price
                                            if party_inventory.get(k):
                                                party_inventory[k] += 1
                                            else:
                                                party_inventory.update({ k: 1 })
                                            shop_inventory[k] = max(0, shop_inventory[k] - 1)

                                            SOUNDS['chaChing'].play()
                                
                                    y += h
                                
                                for i in range(len(shop_inventory)):
                                    try:
                                        k = list(shop_inventory.keys())[i]
                                        if shop_inventory[k] == 0:
                                            shop_inventory.pop(k)
                                    except IndexError:
                                        pass
                        case 1:
                            if dialogue_manager.has_dialogue():
                                dialogue_manager.on_confirm()
                            else:
                                w, h = 200, 30
                                x, y = WIDTH // 3 - w // 2, HEIGHT // 3

                                surf.blit(t := FONT.render("Available Battles", True, 'black'), (x + 1, y + 1))
                                surf.blit(t := FONT.render("Available Battles", True, 'white'), (x, y))

                                y += t.get_height() + 5

                                for i, (name, filename) in enumerate(available_levels):
                                    if pygame.Rect(x, y, w, h).collidepoint(mx, my):
                                        current_level = all_levels.index(get_level_with_name(name))
                                        break
                                    y += h

                                w, h = 100, 30
                                if pygame.Rect(WIDTH - w - 10, HEIGHT - h - 10, w, h).collidepoint(mx, my):
                                    menu = 2
                                if pygame.Rect(10, HEIGHT - h - 10, w, h).collidepoint(mx, my):
                                    menu = 0
                        case 2:
                            if dialogue_manager.has_dialogue():
                                dialogue_manager.on_confirm()
                            else:
                                w, h = 100, 30
                                if pygame.Rect(WIDTH - w - 10, HEIGHT - h - 10, w, h).collidepoint(mx, my) and next_level:
                                    # TO BATTLE !!!!
                                    level_name, level_filename = all_levels[current_level]

                                    # schemas are forest, mountain, desert, icy, and chaos
                                    world_size, schema, nature, enemy_units, thru_dialogue, end_dialogue, available_sidequests, next_level, level_reward = level_from_file(os.path.join("assets", "levels", level_filename))
                                                                        
                                    character_buffer = friendly_units.copy()
                                    save_characters()
                                    friendly_units = []
                                    
                                    units = []

                                    current_unit = 0

                                    turn = 0

                                    selected_unit = None

                                    c = GenerateSolidsMap(nature, units, world_size[0], world_size[1])

                                    graph = path.SimpleGraph(cost=c, cardinal=1, diagonal=0)

                                    c2 = GenerateSolidsMap(nature, enemy_units, world_size[0], world_size[1])

                                    graph_enemies_only = path.SimpleGraph(cost=c2, cardinal=1, diagonal=0)

                                    menu = -1
                                    placing_unit = 0
                                    battling = True
                                    placed = False

                                    messages = []
                                    popups.clear()
                                if pygame.Rect(10, HEIGHT - h - 10, w, h).collidepoint(mx, my):
                                    menu = 1

        if battling and placed:
            if len(friendly_units) == 0:
                battling = False
                won = False
                curtain_timer = 2.0

                reward = get_reward(turn) // 2

                buttons = max(0, buttons - reward)

                messages.append(f"You lost {reward} buttons!")

                SOUNDS['maintheme'].stop()
            elif len(enemy_units) == 0:
                battling = False
                won = True
                curtain_timer = 2.0

                available_levels += [get_level_with_name(n) for n in available_sidequests]

                played_levels.append(get_level_with_name(level_name))

                match current_level:
                    case 0:
                        n = 2
                    case 1 | 2:
                        n = 3
                    case 3:
                        n = 4

                completed_challenges[current_level][0] = True
                completed_challenges[current_level][1] = turn // 2 < n

                if next_level:
                    current_level = all_levels.index(get_level_with_name(next_level))

                reward = get_reward(turn)

                buttons += reward

                messages.append(f"You won {reward} buttons!")

                if level_reward > 0:
                    buttons += level_reward
                    messages.append(f"You were rewarded {level_reward} buttons!")

                SOUNDS['maintheme'].stop()

                SOUNDS['battle_win'].play()

                for i in range(len(end_dialogue)):
                    dialogue_manager.queue_text(end_dialogue[i])

        if battling:
            if placed:
                c = GenerateSolidsMap(nature, units, world_size[0], world_size[1])

                graph = path.SimpleGraph(cost=c, cardinal=1, diagonal=0)

                if turn & 1 and selected_action == "none" and animation_time <= 0:
                    allowed_moves = draw_unit_move_grid(selected_unit, cam.x, cam.y, graph)
                    
                    cx, cy = selected_unit.x, selected_unit.y

                    closest_distance = 0xffff
                    closest_enemy = None

                    for unit in friendly_units:
                        distance = abs(unit.x - selected_unit.x) + abs(unit.y - selected_unit.y)

                        if distance < closest_distance:
                            closest_distance = distance
                            closest_enemy = unit

                    if abs(closest_enemy.x - selected_unit.x) + abs(closest_enemy.y - selected_unit.y) <= 1:    
                        allowed_attacks = get_grid_of_size(selected_unit, selected_unit.weapon.range)

                        if (closest_enemy.x, closest_enemy.y) in allowed_attacks:
                            unit = closest_enemy
                            if unit.health > 0:
                                if unit.armor and random.random() <= unit.armor.protection_chance:
                                    add_text_popup(f"Protected!", unit.x + cam.x, unit.y + cam.y, "forestgreen")
                                else:
                                    d = selected_unit.weapon.damage
                                    d += random.randint(0, selected_unit.strength)
                                    if unit.armor: d -= random.randint(0, unit.armor.protection_value)
                                    add_text_popup(f"-{d}", unit.x + cam.x, unit.y + cam.y, "brown1")
                                    unit.health -= d
                                if unit.health <= 0:
                                    if unit in friendly_units:
                                        friendly_units.remove(unit)
                                    else:
                                        enemy_units.remove(unit)
                                    units.remove(unit)
                                    SOUNDS["smash"].play()
                                else:
                                    play_tap_sound()
                            else:
                                SOUNDS["footstep"].play()

                            animation_time = 0.5
                        else:                    
                            selected_unit.action_points  = 0

                            SOUNDS["unknown"].play()

                            animation_time = 0.5
                        
                        selected_unit.action_points -= 1
                    else:
                        selected_action = "move"

                        closest_distance = 0xffff
                        closest_tile = None

                        for tile in allowed_moves:
                            distance = abs(tile[0] - closest_enemy.x) + abs(tile[1] - closest_enemy.y)

                            if distance < closest_distance:
                                closest_distance = distance
                                closest_tile = tile

                        if closest_tile:
                            cx, cy = closest_tile

                            unit_path_to(selected_unit, cx, cy, False)
                            
                        units_should_move = True

                if selected_action == "move":
                    if units_should_move:
                        every_unit_in_place = True
                        
                        for unit in units:
                            if unit.update(delta):
                                SOUNDS["thud"].play()
                                
                            if len(unit.path) > 0 or unit.draw_x != unit.x or unit.draw_y != unit.y:
                                every_unit_in_place = False

                        units_should_move = not every_unit_in_place

                        if not units_should_move:
                            for unit in units:
                                unit.draw_x = unit.x
                                unit.draw_y = unit.y

                            selected_unit.action_points -= 1
                            selected_action = "none"

                            animation_time = 0.5
                    elif not turn & 1:
                        for unit in units:
                            if unit == selected_unit:
                                if selected_pos in allowed_moves:
                                    unit_path_to(unit, selected_pos[0], selected_pos[1])
                            else:
                                unit.path = []
                else:
                    if animation_time > 0:
                        animation_time = max(0, animation_time - delta)

                if selected_unit.action_points <= 0:
                    selected_unit.done_with_turn = True

                    if (turn % 2 == 0 and all(unit.done_with_turn for unit in friendly_units)) or (turn % 2 == 1 and all(unit.done_with_turn for unit in enemy_units)):
                        animation_time = 0.5

                        turn += 1

                        if turn < len(thru_dialogue):
                            for i in range(len(thru_dialogue[turn])):
                                dialogue_manager.queue_text(thru_dialogue[turn][i])

                        if turn & 1:
                            # enemy turn
                            current_unit = 0
                            selected_unit = enemy_units[current_unit]
                            selected_action = "none"

                            banner_text = "Enemy Turn"
                            banner_time = 3.0
                        else:
                            current_unit = 0
                            selected_unit = friendly_units[current_unit]
                            selected_action = "none"

                            banner_text = "Player Turn"
                            banner_time = 3.0

                        selected_unit.action_points = selected_unit.max_action_points

                        for u in units:
                            u.done_with_turn = False
                    else:
                        animation_time = 0.5
                        
                        current_unit += 1
                        if turn & 1:
                            # enemy turn
                            if current_unit >= len(enemy_units):
                                current_unit = 0
                            selected_unit = enemy_units[current_unit]
                        else:
                            # friendly turn
                            if current_unit >= len(friendly_units):
                                current_unit = 0
                            selected_unit = friendly_units[current_unit]
                        
                        selected_action = "none"
                        selected_unit.action_points = selected_unit.max_action_points
                        selected_unit.done_with_turn = False

            screen.blit(BG, (0, 0))

            t = pygame.time.get_ticks() / 100
            t %= 50

            for x in range(WIDTH // 50 + 1):
                for y in range(HEIGHT // 50 + 1):
                    if (x + y) % 2 == 0:
                        fx, fy = 25 + x * 50 - t, 25 + y * 50 - t
                        q = 1 - abs(2 * (((fx + fy) / (WIDTH + HEIGHT) - 0.5)))
                        r = 25 * pow(q, 1)
                        pygame.draw.circle(screen, darken(pygame.Color('darkslategray2').lerp('darkslategray4', clamp(fy / HEIGHT, 0, 1)), 0.1), (fx, fy), r)

            match schema:
                case "forest":
                    colors = ["darkolivegreen2"]
                case "mountain":
                    colors = ["lightsteelblue"]
                case "desert":
                    colors = ["lightsalmon"]
                case "icy":
                    colors = ["lightcyan"]
                case "chaos":
                    colors = ["mediumpurple"]
                case _:
                    colors = ["green"]
            
            colors.append(darken(colors[0], 0.1))

            for x in range(world_size[0]):
                for y in range(world_size[1]):
                    if nature[y * world_size[0] + x] in [3, 4]: # water or bridge
                        oy = - 0.25 + math.sin((x + y) + pygame.time.get_ticks() / 200) * 0.05
                        color = "deepskyblue" if (x + y) % 2 == 0 else darken("deepskyblue", 0.1)
                        draw_tile(x + cam.x - oy, y + cam.y - oy, color)
                        if OUTLINE: draw_tile(x + cam.x - oy, y + cam.y - oy, darken(color, 0.3), True)

                        if nature[y * world_size[0] + x] == 4:
                            bridge_color = "chocolate4" if (x + y) % 2 == 0 else darken("chocolate4", 0.1)
                            draw_tile_flat(x + cam.x, y + cam.y, bridge_color)
                            if OUTLINE: draw_tile_flat(x + cam.x, y + cam.y, darken(bridge_color, 0.3), True)
                        continue

                    color = colors[0] if (x + y) % 2 == 0 else colors[1]
                    draw_tile(x + cam.x, y + cam.y, color)
                    if OUTLINE: draw_tile(x + cam.x, y + cam.y, darken(color, 0.3), True)

            match selected_action:
                case "move":
                    if not units_should_move:
                        allowed_moves = draw_unit_move_grid(selected_unit, cam.x, cam.y, graph)
                case "attack":
                    for t in allowed_attacks:
                        draw_small_tile(t[0] + cam.x, t[1] + cam.y, "brown1")

            for x in range(world_size[0]):
                for y in range(world_size[1]):
                    if nature[y * world_size[0] + x] == 1:
                        draw_tree(x + cam.x, y + cam.y)
                    if nature[y * world_size[0] + x] == 2:
                        draw_rock(x + cam.x, y + cam.y)
                    if nature[y * world_size[0] + x] == 16:
                        draw_small_tile(x + cam.x, y + cam.y, 'yellow')
                        
                    for u in friendly_units + enemy_units:
                        if int(u.x) == x and int(u.y) == y:
                            draw_unit(u, u in friendly_units, cam.x, cam.y, u == selected_unit, selected_action == "move")
                            if u.weapon:
                                fx, fy = from_world_pos(u.draw_x + cam.x, u.draw_y + cam.y)
                                u.weapon.draw(screen, delta, fx, fy, u.character.scale)

            battle_ss = screen.copy()

            for popup in popups:
                popup["time"] -= delta
                popup["y"] -= delta * 25
                if popup["time"] <= 0:
                    popups.remove(popup)
                else:
                    small = SMALL_FONT.render(popup["text"], True, 'black')
                    small.set_alpha(int(255 * popup["time"]))
                    screen.blit(small, (popup["x"] + 1, popup["y"] + 1))
                    small = SMALL_FONT.render(popup["text"], True, popup["color"])
                    small.set_alpha(int(255 * popup["time"]))
                    screen.blit(small, (popup["x"], popup["y"]))

            can_show_info = True

            if selected_action == "none" and not turn & 1:
                if selected_unit and selected_unit.placed:
                    screen.blit(t := FONT.render("Select an Action", True, 'black'), (WIDTH // 2 - t.get_width() // 2, 10))
                    s = 50
                    w, h = 80, 30
                    x, y = from_world_pos(selected_unit.x + cam.x, selected_unit.y + cam.y)
                    x += selected_unit.character.scale * 2
                    y -= selected_unit.character.scale
                    for i in range(4):
                        can_show_info = draw_button(screen, x, y, w, h, ["Move", "Attack", "Items", "Wait"][i])
                        y += h

                # draw unit info
                if can_show_info:
                    for unit in units:
                        if not unit.placed:
                            continue
                        if unit.x == selected_pos[0] and unit.y == selected_pos[1]:
                            mx, my = pygame.mouse.get_pos()
                            mx -= 150
                            pygame.draw.rect(screen, '#606060', (mx, my, 300, 40), 0, -1, 8, 8)
                            pygame.draw.rect(screen, '#404040', (mx, my + 40, 300, 160), 0, -1, -1, -1, 8, 8)
                            
                            info_string = f"{unit.name}"
                            if unit in friendly_units: info_string += f" ({unit.health}/{unit.max_health} HP)"

                            screen.blit(t := FONT.render(info_string, True, 'black'), (1 + mx + 150 - t.get_width() / 2, 1 + my + 5))
                            screen.blit(t := FONT.render(info_string, True, 'white'), (mx + 150 - t.get_width() / 2, my + 5))
                            
                            for i, line in enumerate(unit.description + ["", "Equipped with:", f"{unit.armor.name}, {unit.weapon.name}"]):
                                screen.blit(t := SMALL_FONT.render(line, True, 'black'), (1 + mx + 5, 1 + my + 45 + i * SMALL_FONT.size(line)[1]))
                                screen.blit(t := SMALL_FONT.render(line, True, 'white'), (mx + 5, my + 45 + i * SMALL_FONT.size(line)[1]))

                            break
            elif selected_action == "items" and not turn & 1:
                screen.blit(t := FONT.render("Select an Item", True, 'black'), (WIDTH // 2 - t.get_width() // 2, 10))
                s = 50
                w, h = 100, 30
                x, y = from_world_pos(selected_unit.x + cam.x, selected_unit.y + cam.y)
                x += selected_unit.character.scale * 2
                y -= selected_unit.character.scale
                for i in range(len(party_inventory)):
                    can_show_info = draw_button(screen, x, y, w, h, f"{list(party_inventory.values())[i]}x {list(party_inventory.keys())[i]().name}")
                    y += h

            # draw ap bar

            if selected_unit:
                ap_w = lerp(ap_w, (WIDTH - 100) * (selected_unit.action_points / selected_unit.max_action_points), 0.1)
                pygame.draw.rect(screen, 'darkgray', (WIDTH // 2 - (WIDTH - 100) // 2, HEIGHT - 50, WIDTH - 100, 20), 0, 8)
                pygame.draw.rect(screen, 'orange', (WIDTH // 2 - ap_w // 2, HEIGHT - 50, ap_w, 20), 0, 8)

                screen.blit(t := SMALL_FONT.render(f"AP: {selected_unit.action_points} / {selected_unit.max_action_points}", True, 'black'), (50, HEIGHT - 25))

            screen.blit(t := SMALL_FONT.render(f"Turn {1 + turn // 2}", True, 'black'), (WIDTH - t.get_width() - 5, 5))

            x, y = 0, 20
            w = 185
            h = 50
            t = 50
            s = 20
            # draw player units on side
            for unit in friendly_units:
                if not unit.placed:
                    continue

                surf = pygame.Surface((w, h), pygame.SRCALPHA)
                pygame.draw.polygon(surf, (0, 0, 0, 128), [
                    (0, 0), (0 + w - t, 0),
                    (0 + w, 0 + h), (0, 0 + h)
                ])

                surf.blit(FONT.render(unit.name, True, 'white'), (5, 3))
                surf.blit(SMALL_FONT.render(f"{unit.health} / {unit.max_health} HP - LVL {unit.level}", True, 'white'), (5, 30))

                screen.blit(surf, (x, y))

                pygame.draw.polygon(screen, 'yellow' if unit == selected_unit else 'white', [
                    (x, y), (x + w - t, y),
                    (x + w, y + h), (x, y + h)
                ], 2)

                try:
                    su = unit.character.surf.subsurface((unit.character.scale, unit.character.scale, unit.character.scale * 2, h - 10))
                    screen.blit(su, (x + w - t, y + h - su.get_height()))
                except AttributeError:
                    pass

                y += h + s

            if not placed:
                screen.blit(t := FONT.render(f"Place {character_names[placing_unit]}", True, 'black'), (WIDTH // 2 - t.get_width() // 2, 10))

            # draw banner
            if banner_time > 0 and banner_text:
                banner_time -= delta
                bt = banner_time / 3.0
                s = pygame.Surface((WIDTH, 100), pygame.SRCALPHA)

                s.fill((0, 0, 0, 128))
                for i in range(WIDTH // 20):
                    for j in range(100 // 20):
                        if (i + j) % 2 == 0:
                            pygame.draw.rect(s, (64, 64, 64, 128), (i * 20, j * 20, 20, 20), 0)
                pygame.draw.rect(s, (255, 255, 255, 255), (0, 0, WIDTH, 100), 1)
                s.blit(t := BIG_FONT.render(banner_text, True, 'white'), (WIDTH // 2 - t.get_width() // 2, 50 - t.get_height() // 2))

                s.set_alpha(int(255 * bt))

                screen.blit(s, (0, 100 * (1 - bt)))

            dialogue_manager.draw(screen)
        else:
            curtain_timer = max(0, curtain_timer - delta)

            # non-battle drawing code
            screen.blit(battle_ss, (0, 0))
            
            surf = pygame.Surface((WIDTH, HEIGHT))
            
            surf.fill(colors[0])

            t = pygame.time.get_ticks() / 100
            t %= 50

            for x in range(WIDTH // 50 + 1):
                for y in range(HEIGHT // 50 + 1):
                    if (x + y) % 2 == 0:
                        fx, fy = 25 + x * 50 - t, 25 + y * 50 - t
                        q = 1 - abs(2 * (((fx + fy) / (WIDTH + HEIGHT) - 0.5)))
                        r = 25 * pow(q, 1)
                        pygame.draw.circle(surf, colors[1], (fx, fy), r)

            match menu:
                case -1:
                    surf.blit(t := BIG_FONT.render(f"Battle {"Won" if won else "Lost"}!", True, "black"), (2 + WIDTH // 2 - t.get_width() // 2, 27))
                    surf.blit(t := BIG_FONT.render(f"Battle {"Won" if won else "Lost"}!", True, "white"), (WIDTH // 2 - t.get_width() // 2, 25))

                    w, h = 90, 30

                    words = ["Continue", "Quit"]
                    for i in range(len(words)):
                        draw_button(surf, WIDTH // 2 - w // 2, HEIGHT * 0.85 - h // 2 + (h + 10) * i, w, h, words[i])
            
                    subsurf = pygame.Surface((WIDTH // 2, HEIGHT // 2), pygame.SRCALPHA)

                    pygame.draw.rect(subsurf, (0, 0, 0, 128), (0, 0, WIDTH // 2, HEIGHT // 3), 0, 8)

                    ly = 5
                    for line in messages:
                        subsurf.blit(t := FONT.render(line, True, 'white'), (5, ly))
                        ly += t.get_height()

                    surf.blit(subsurf, (WIDTH // 4, HEIGHT // 2 - HEIGHT // 6))
                case 0: # shop
                    surf.blit(t := BIG_FONT.render("Shop", True, 'black'), (WIDTH // 2 - t.get_width() // 2 + 2, 7))
                    surf.blit(t := BIG_FONT.render("Shop", True, 'white'), (WIDTH // 2 - t.get_width() // 2, 5))
                    
                    w, h = 200, 30
                    x, y = WIDTH // 3 - w // 2, HEIGHT // 3

                    surf.blit(t := FONT.render("Shop Items", True, 'black'), (x + 1, y + 1))
                    surf.blit(t := FONT.render("Shop Items", True, 'white'), (x, y))

                    y += t.get_height() + 5

                    for i, (k, v) in enumerate(shop_inventory.items()):
                        t = f"{v}x {k().name} - {k().price}b"
                        option_surf = pygame.Surface((w, h), pygame.SRCALPHA)

                        color = (0, 0, 0, 192) if pygame.Rect(x, y, w, h).collidepoint(pygame.mouse.get_pos()) else (0, 0, 0, 128)

                        if len(shop_inventory) == 1:
                            pygame.draw.rect(option_surf, color, (0, 0, w, h), 0, 8)
                        else:
                            if i == 0:
                                pygame.draw.rect(option_surf, color, (0, 0, w, h), 0, -1, 8, 8, -1, -1)
                            elif i == len(shop_inventory) - 1:
                                pygame.draw.rect(option_surf, color, (0, 0, w, h), 0, -1, -1, -1, 8, 8)
                            else:
                                pygame.draw.rect(option_surf, color, (0, 0, w, h))

                        surf.blit(option_surf, (x, y))
                        surf.blit(text := SMALL_FONT.render(t, True, 'white'), (x + 5, y + h // 2 - text.get_height() // 2))

                        y += h

                    x, y = WIDTH * (2 / 3) - w // 2, HEIGHT // 3

                    surf.blit(t := FONT.render("Your Items", True, 'black'), (x + 1, y + 1))
                    surf.blit(t := FONT.render("Your Items", True, 'white'), (x, y))

                    y += t.get_height() + 5

                    for i, (k, v) in enumerate(party_inventory.items()):
                        t = f"{v}x {k().name} - {int(k().price * (1 - sell_falloff))}b"
                        option_surf = pygame.Surface((w, h), pygame.SRCALPHA)

                        color = (0, 0, 0, 192) if pygame.Rect(x, y, w, h).collidepoint(pygame.mouse.get_pos()) else (0, 0, 0, 128)

                        if len(party_inventory) == 1:
                            pygame.draw.rect(option_surf, color, (0, 0, w, h), 0, 8)
                        else:
                            if i == 0:
                                pygame.draw.rect(option_surf, color, (0, 0, w, h), 0, -1, 8, 8, -1, -1)
                            elif i == len(party_inventory) - 1:
                                pygame.draw.rect(option_surf, color, (0, 0, w, h), 0, -1, -1, -1, 8, 8)
                            else:
                                pygame.draw.rect(option_surf, color, (0, 0, w, h))

                        surf.blit(option_surf, (x, y))
                        surf.blit(text := SMALL_FONT.render(t, True, 'white'), (x + 5, y + h // 2 - text.get_height() // 2))

                        y += h

                    surf.blit(t := FONT.render(f"{buttons}b", True, 'black'), (1 + WIDTH // 2 - t.get_width() // 2, 1 + HEIGHT // 3))
                    surf.blit(t := FONT.render(f"{buttons}b", True, 'white'), (WIDTH // 2 - t.get_width() // 2, HEIGHT // 3))

                    dialogue_manager.draw(surf)

                    w, h = 100, 30
                    draw_button(surf, WIDTH - w - 10, HEIGHT - h - 10, w, h, "To Tavern")
                case 1: # tavern
                    surf.blit(t := BIG_FONT.render("Tavern", True, 'black'), (WIDTH // 2 - t.get_width() // 2 + 2, 7))
                    surf.blit(t := BIG_FONT.render("Tavern", True, 'white'), (WIDTH // 2 - t.get_width() // 2, 5))
                    
                    w, h = 200, 30
                    x, y = WIDTH // 3 - w // 2, HEIGHT // 3

                    surf.blit(t := FONT.render("Available Battles", True, 'black'), (x + 1, y + 1))
                    surf.blit(t := FONT.render("Available Battles", True, 'white'), (x, y))

                    y += t.get_height() + 5

                    for i, (name, filename) in enumerate(available_levels):
                        t = name
                        option_surf = pygame.Surface((w, h), pygame.SRCALPHA)

                        if name == all_levels[current_level][0]:
                            color = (255, 192, 0, 192) if pygame.Rect(x, y, w, h).collidepoint(pygame.mouse.get_pos()) else (255, 192, 0, 128)
                        else:
                            color = (0, 0, 0, 192) if pygame.Rect(x, y, w, h).collidepoint(pygame.mouse.get_pos()) else (0, 0, 0, 128)

                        if len(available_levels) == 1:
                            pygame.draw.rect(option_surf, color, (0, 0, w, h), 0, 8)
                        else:
                            if i == 0:
                                pygame.draw.rect(option_surf, color, (0, 0, w, h), 0, -1, 8, 8, -1, -1)
                            elif i == len(available_levels) - 1:
                                pygame.draw.rect(option_surf, color, (0, 0, w, h), 0, -1, -1, -1, 8, 8)
                            else:
                                pygame.draw.rect(option_surf, color, (0, 0, w, h))

                        surf.blit(option_surf, (x, y))
                        surf.blit(text := SMALL_FONT.render(t, True, 'white'), (x + 5, y + h // 2 - text.get_height() // 2))

                        y += h

                    x, y = WIDTH * (2 / 3) - w // 2, HEIGHT // 3

                    surf.blit(t := FONT.render("Selected Battle", True, 'black'), (x + 1, y + 1))
                    surf.blit(t := FONT.render("Selected Battle", True, 'white'), (x, y))

                    w *= 1.75
                    h *= 10
                    h += 10

                    y += t.get_height() + 5

                    l = all_levels[current_level]

                    t = f"{l[0]}"
                    option_surf = pygame.Surface((w, h), pygame.SRCALPHA)

                    color = (0, 0, 0, 192)

                    pygame.draw.rect(option_surf, color, (0, 0, w, h), 0, 8)

                    surf.blit(option_surf, (x, y))
                    surf.blit(text := BIG_FONT.render(t, True, 'white'), (x + 5, y + 5))

                    y += 5 + text.get_height()

                    surf.blit(text := FONT.render(level_descriptions[current_level], True, 'white'), (x + 5, y))
                    y += text.get_height() + FONT.size(' ')[1]

                    for index, challenge in enumerate(level_challenges[current_level]):
                        surf.blit(text := FONT.render(challenge, True, 'white'), (x + 5, y))
                        y += text.get_height()
                        draw_star(surf, x + w - 20, y - 20, 15, col='yellow' if completed_challenges[current_level][index] else 'gray')

                    dialogue_manager.draw(surf)

                    w, h = 100, 30
                    draw_button(surf, WIDTH - w - 10, HEIGHT - h - 10, w, h, "To Toybox")
                    draw_button(surf, 10, HEIGHT - h - 10, w, h, "To Shop")
                case 2: # toybox
                    surf.blit(t := BIG_FONT.render("Toybox", True, 'black'), (WIDTH // 2 - t.get_width() // 2 + 2, 7))
                    surf.blit(t := BIG_FONT.render("Toybox", True, 'white'), (WIDTH // 2 - t.get_width() // 2, 5))
                    
                    surf.blit(t := FONT.render(f"Selected Battle: {all_levels[current_level][0]}", True, 'black'), (WIDTH // 2 - t.get_width() // 2 + 1, HEIGHT - t.get_height() - 5 + 1))
                    surf.blit(t := FONT.render(f"Selected Battle: {all_levels[current_level][0]}", True, 'white'), (WIDTH // 2 - t.get_width() // 2, HEIGHT - t.get_height() - 5))

                    dialogue_manager.draw(surf)

                    w, h = 100, 30
                    draw_button(surf, WIDTH - w - 10, HEIGHT - h - 10, w, h, "To Battle")
                    draw_button(surf, 10, HEIGHT - h - 10, w, h, "To Tavern")

            v = HEIGHT * ((1 - curtain_timer / 2.0) ** 2)
            screen.blit(surf, (0, -HEIGHT + v))

        pygame.display.flip()
    
    pygame.quit()

if __name__ == "__main__":
    main()