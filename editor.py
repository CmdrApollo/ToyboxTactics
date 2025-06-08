import pygame
import random
import os
import json

from tkinter.filedialog import asksaveasfilename, askopenfilename

import glob

import math
import numpy as np

from character import character_from_file
from unit import ScoutUnit, SoldierUnit, HeavyUnit
from dialogue import DialogueManager

from tcod import path

pygame.init()

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
        ], 1)

        pygame.draw.polygon(screen, darken(color, 0.2), [
            (i + TILE_SIZE[0] / 2, j + TILE_SIZE[1]),
            (i + TILE_SIZE[0] / 2, j + TILE_SIZE[1] * 2.0),
            (i + TILE_SIZE[0], j + TILE_SIZE[1] * 1.5),
            (i + TILE_SIZE[0], j + TILE_SIZE[1] / 2),
        ], 1)

        pygame.draw.polygon(screen, color, [
            (i + TILE_SIZE[0] / 2, j),
            (i + TILE_SIZE[0], j + TILE_SIZE[1] / 2),
            (i + TILE_SIZE[0] / 2, j + TILE_SIZE[1]),
            (i, j + TILE_SIZE[1] / 2),
        ], 1)

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
        ], 1)

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

    character.draw(screen, pygame.Vector2(0, 0), False, False, False, None, 'skyblue' if friendly else 'brown1', is_selected)

def main():
    clock = pygame.time.Clock()

    def mouse_to_tile_pos(ox=0, oy=0):
        mx, my = pygame.mouse.get_pos()
        x, y = from_screen_pos(mx, my, int(ox), int(oy))

        x = clamp(x, 0, world_size[0] - 1)
        y = clamp(y, 0, world_size[1] - 1)

        return (x, y)

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

        return world_size, level, nature, units, data['during_battle_dialogue'], data['post_battle_dialogue'], data['next_level']

    cam = pygame.Vector2(6, -4)

    world_size, level, nature, units, during_dialogue, dialogue, next_level = level_from_file(askopenfilename())

    run = True
    while run:
        delta = clock.tick_busy_loop(pygame.display.get_current_refresh_rate()) / 1000.0
        
        selected_pos = mouse_to_tile_pos(cam.x, cam.y)
        keys = pygame.key.get_pressed()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.KEYDOWN:
                if event.key >= pygame.K_1 and event.key < pygame.K_6:
                    if keys[pygame.K_LSHIFT]:
                        level = ["forest", "desert", "mountain", "icy", "chaos"][event.key - pygame.K_1]
                    else:
                        nature[selected_pos[1] * world_size[0] + selected_pos[0]] = event.key - pygame.K_1
                        for u in units[::-1]:
                            if u.x == selected_pos[0] and u.y == selected_pos[1]:
                                units.remove(u)
                if event.key == pygame.K_a: units.append(ScoutUnit(True, selected_pos[0], selected_pos[1]))
                if event.key == pygame.K_b: units.append(SoldierUnit(True, selected_pos[0], selected_pos[1]))
                if event.key == pygame.K_c: units.append(HeavyUnit(True, selected_pos[0], selected_pos[1]))
                if event.key == pygame.K_SPACE: nature[selected_pos[1] * world_size[0] + selected_pos[0]] = 0 if nature[selected_pos[1] * world_size[0] + selected_pos[0]] == 16 else 16
                if event.key == pygame.K_s and keys[pygame.K_LCTRL]:
                    with open(asksaveasfilename(), 'w') as f:
                        data = {
                            "width": world_size[0],
                            "height": world_size[1],

                            "schema": level,

                            "scenery": [[nature[y * world_size[0] + x] for x in range(world_size[0])] for y in range(world_size[1])],

                            "units": [
                                {
                                    "type": ["scout", "soldier", "heavy"][[ScoutUnit, SoldierUnit, HeavyUnit].index(type(unit))],
                                    "x": unit.x,
                                    "y": unit.y
                                }
                                for unit in units
                            ],

                            "during_battle_dialogue": during_dialogue,
                            "post_battle_dialogue": dialogue,

                            "next_level": next_level
                        }

                        json.dump(data, f, indent='\t')
                        f.close()

        screen.blit(BG, (0, 0))

        match level:
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
                if nature[y * world_size[0] + x] in [3, 4]: # water
                    oy = - 0.25 + math.sin((x + y) + pygame.time.get_ticks() / 200) * 0.05
                    color = "deepskyblue" if (x + y) % 2 == 0 else darken("deepskyblue", 0.1)
                    draw_tile(x + cam.x - oy, y + cam.y - oy, color)
                    if True: draw_tile(x + cam.x - oy, y + cam.y - oy, darken(color, 0.3) if not (x == selected_pos[0] and y == selected_pos[1]) else 'yellow', True)
                    continue

                color = colors[0] if (x + y) % 2 == 0 else colors[1]
                draw_tile(x + cam.x, y + cam.y, color)
                if True: draw_tile(x + cam.x, y + cam.y, darken(color, 0.3) if not (x == selected_pos[0] and y == selected_pos[1]) else 'yellow', True)

        for x in range(world_size[0]):
            for y in range(world_size[1]):
                if nature[y * world_size[0] + x] == 1:
                    draw_tree(x + cam.x, y + cam.y)
                if nature[y * world_size[0] + x] == 2:
                    draw_rock(x + cam.x, y + cam.y)
                if nature[y * world_size[0] + x] == 4:
                        bridge_color = "chocolate4" if (x + y) % 2 == 0 else darken("chocolate4", 0.1)
                        draw_tile_flat(x + cam.x, y + cam.y, bridge_color)
                        draw_tile_flat(x + cam.x, y + cam.y, darken(bridge_color, 0.3), True)
                if nature[y * world_size[0] + x] == 16:
                    draw_small_tile(x + cam.x, y + cam.y, 'yellow')

                for i in range(len(units)):
                    if int(units[i].x) == x and int(units[i].y) == y:
                        draw_unit(units[i], False, cam.x, cam.y, False, False)

        pygame.display.flip()

main()