import pygame
import random
import os
import json

import glob

import math
import numpy as np

from character import character_from_file
from unit import ScoutUnit, SoldierUnit, HeavyUnit
from dialogue import DialogueManager

from tcod import path

character_names = ["Milo", "Toto", "Grub"]
character_colors = ["#ff8080", "#80ff80", "#8080ff"]
character_classes = [ScoutUnit, SoldierUnit, HeavyUnit]

OUTLINE = True

pygame.init()

SOUNDS = {}

for f in glob.glob(os.path.join('assets', 'audio', '**.wav')):
    SOUNDS.update({f.split('\\')[-1].split('.')[0]: pygame.mixer.Sound(f)})

for i in SOUNDS:
    SOUNDS[i].set_volume(0.0)

pygame.display.set_caption("Toybox Tactics")

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

    character.draw(screen, pygame.Vector2(0, 0), False, False, 'skyblue' if friendly else 'brown1', is_selected)

    if unit.defending:
        draw_shield(unit.draw_x + x, unit.draw_y + y)

def draw_shield(x, y):
    i, j = from_world_pos(x, y)

    j -= TILE_SIZE[1] / 2

    pygame.draw.polygon(screen, "darkslategray", [
        (i + TILE_SIZE[0] / 2, j),
        (i + TILE_SIZE[0] * 0.7, j + TILE_SIZE[1] / 2),
        (i + TILE_SIZE[0] / 2, j + TILE_SIZE[1] * 1.25),
        (i + TILE_SIZE[0] * 0.3, j + TILE_SIZE[1] / 2),
    ])

    pygame.draw.polygon(screen, "cadetblue", [
        (i + TILE_SIZE[0] / 2, j + TILE_SIZE[1] * 0.25),
        (i + TILE_SIZE[0] * 0.6, j + TILE_SIZE[1] / 2),
        (i + TILE_SIZE[0] / 2, j + TILE_SIZE[1] * 1),
        (i + TILE_SIZE[0] * 0.4, j + TILE_SIZE[1] / 2),
    ])

    pygame.draw.polygon(screen, "white", [
        (i + TILE_SIZE[0] / 2, j),
        (i + TILE_SIZE[0] * 0.7, j + TILE_SIZE[1] / 2),
        (i + TILE_SIZE[0] / 2, j + TILE_SIZE[1] * 1.25),
        (i + TILE_SIZE[0] * 0.3, j + TILE_SIZE[1] / 2),
    ], 2)

def GenerateSolidsMap(input_map, units_input, world_width=10, world_height=10):
    solids = np.array([[ 0 for _ in range(world_width) ] for _ in range(world_height)])
    solids[:] = True

    for x in range(world_width):
        for y in range(world_height):
            if input_map[y * world_width + x]:
                solids[y, x] = False
            for unit in units_input:
                if int(unit.x) == x and int(unit.y) == y:
                    solids[y, x] = False
    
    return solids

def play_tap_sound():
    SOUNDS[f"tap{random.randint(1, 3)}"].play()

def main():
    clock = pygame.time.Clock()
    delta = 0.0

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

        return world_size, level, nature, units, data['next_level']

    current_level = "level1.json"

    # schemas are forest, mountain, desert, and icy
    world_size, level, nature, enemy_units, next_level = level_from_file(os.path.join("assets", "levels", current_level))

    friendly_units = []
    
    units = []

    current_unit = 0

    turn = 0

    selected_unit = None

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
    
    animation_time = 0.0

    banner_text = "Placement"
    banner_time = 3.0

    placing_unit = 0

    battling = True
    won = False

    placed = False

    messages = []

    # non-battling variables
    curtain_timer = 0
    battle_ss = pygame.Surface((WIDTH, HEIGHT))

    SOUNDS['maintheme'].play()

    menu = -1 # post battle seq

    dialogue_manager = DialogueManager(FONT, BIG_FONT, 'white', 'white')

    dialogue_manager.queue_text([
        f"<{character_colors[0]}>{character_names[0]}</>",
        "Good work, team. One more force",
        "of chaos has been vanquished."
    ])

    run = True
    while run:
        delta = clock.tick_busy_loop(pygame.display.get_current_refresh_rate()) / 1000.0

        keys = pygame.key.get_pressed()

        selected_pos = mouse_to_tile_pos(cam.x, cam.y)
            
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            elif event.type == pygame.KEYDOWN:
                if battling:
                    if event.key == pygame.K_SPACE:
                        battling = False
                        won = True
                        curtain_timer = 2.0

                        SOUNDS['maintheme'].stop()

                        SOUNDS['battle_win'].play()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if battling:
                    if event.button == 1 and not turn & 1:
                        if selected_action == "move":
                            if selected_pos in allowed_moves:
                                units_should_move = True
                                selected_unit.defending = False
                        elif selected_action == "attack":
                            if selected_pos in allowed_attacks:
                                for unit in units:
                                    if unit.x == selected_pos[0] and unit.y == selected_pos[1]:
                                        if unit != selected_unit:
                                            if unit.health > 0:
                                                if unit.armor and random.random() <= unit.armor.protection_chance:
                                                    add_text_popup(f"Protected!", unit.x + cam.x, unit.y + cam.y, "forestgreen")
                                                else:
                                                    add_text_popup(f"-{selected_unit.weapon.damage}", unit.x + cam.x, unit.y + cam.y, "brown1")
                                                    unit.health -= selected_unit.weapon.damage
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
                                                    units.remove(unit)
                                                    SOUNDS["smash"].play()
                                                else:
                                                    play_tap_sound()
                                            else:
                                                SOUNDS["footstep"].play()
                                        break
                                        
                                selected_action = "none"
                                selected_unit.action_points -= 1
                        elif selected_action == "none" and placed:
                            s = 50
                            w, h = 80, 30
                            x, y = from_world_pos(selected_unit.x + cam.x, selected_unit.y + cam.y)
                            x += selected_unit.character.scale * 2
                            y -= selected_unit.character.scale
                            for i in range(3):
                                if pygame.Rect(x, y, w, h).collidepoint(pygame.mouse.get_pos()):
                                    selected_action = ["move", "attack", "items", "defend"][i]
                                    
                                    if selected_action == "attack":
                                        allowed_attacks = get_grid_of_size(selected_unit, selected_unit.weapon.range)
                                        
                                        SOUNDS["swoosh"].play()

                                    if selected_action == "defend":
                                        selected_action = "none"
                                        
                                        selected_unit.defending = True
                                        selected_unit.action_points  = 0

                                        SOUNDS["unknown"].play()

                                    break

                                y += h
                        elif selected_action == "none" and not placed:
                            if nature[selected_pos[1] * world_size[0] + selected_pos[0]] == 16:
                                friendly_units.append(character_classes[placing_unit](True, selected_pos[0], selected_pos[1], character_names[placing_unit]))
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
                    match menu:
                        case -1:
                            w, h = 90, 30

                            if won:
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
                                pass

        if battling and placed:
            if len(friendly_units) == 0:
                battling = False
                won = False
                curtain_timer = 2.0

                SOUNDS['maintheme'].stop()
            elif len(enemy_units) == 0:
                battling = False
                won = True
                curtain_timer = 2.0

                SOUNDS['maintheme'].stop()

                SOUNDS['battle_win'].play()

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
                                    add_text_popup(f"-{selected_unit.weapon.damage}", unit.x + cam.x, unit.y + cam.y, "brown1")
                                    unit.health -= selected_unit.weapon.damage
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
                            selected_unit.defending = True
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
                    if nature[y * world_size[0] + x] == 3: # water
                        oy = - 0.25 + math.sin((x + y) + pygame.time.get_ticks() / 200) * 0.05
                        color = "deepskyblue" if (x + y) % 2 == 0 else darken("deepskyblue", 0.1)
                        draw_tile(x + cam.x - oy, y + cam.y - oy, color)
                        if OUTLINE: draw_tile(x + cam.x - oy, y + cam.y - oy, darken(color, 0.3), True)
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
                        can_show_info = draw_button(screen, x, y, w, h, ["Move", "Attack", "Items", "Defend"][i])
                        y += h

                # draw unit info
                if can_show_info:
                    for unit in units:
                        if not unit.placed:
                            continue
                        if unit.x == selected_pos[0] and unit.y == selected_pos[1]:
                            mx, my = pygame.mouse.get_pos()
                            mx -= 150
                            pygame.draw.rect(screen, 'darkgray', (mx, my, 300, 40), 0, -1, 8, 8)
                            pygame.draw.rect(screen, 'gray', (mx, my + 40, 300, 160), 0, -1, -1, -1, 8, 8)
                            
                            info_string = f"{unit.name}"
                            if unit in friendly_units: info_string += f" ({unit.health}/{unit.max_health} HP)"

                            screen.blit(t := FONT.render(info_string, True, 'black'), (mx + 150 - t.get_width() / 2, my + 5))
                            
                            for i, line in enumerate(unit.description):
                                screen.blit(t := SMALL_FONT.render(line, True, 'black'), (mx + 150 - t.get_width() / 2, my + 45 + i * SMALL_FONT.size(line)[1]))

                            break

            # draw ap bar

            if selected_unit:
                ap_w = lerp(ap_w, (WIDTH - 100) * (selected_unit.action_points / selected_unit.max_action_points), 0.1)
                pygame.draw.rect(screen, 'darkgray', (WIDTH // 2 - (WIDTH - 100) // 2, HEIGHT - 50, WIDTH - 100, 20), 0, 8)
                pygame.draw.rect(screen, 'orange', (WIDTH // 2 - ap_w // 2, HEIGHT - 50, ap_w, 20), 0, 8)

                screen.blit(t := SMALL_FONT.render(f"AP: {selected_unit.action_points} / {selected_unit.max_action_points}", True, 'black'), (50, HEIGHT - 25))

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
                surf.blit(SMALL_FONT.render(f"{unit.health} / {unit.max_health} HP", True, 'white'), (5, 30))

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
        else:
            curtain_timer = max(0, curtain_timer - delta)

            # non-battle drawing code
            screen.blit(battle_ss, (0, 0))
            
            surf = pygame.Surface((WIDTH, HEIGHT))
            
            surf.fill(colors[0])

            t = pygame.time.get_ticks() / 50
            t %= 50

            for x in range(WIDTH // 50 + 1):
                for y in range(HEIGHT // 50 + 1):
                    if (x + y) % 2 == 0:
                        pygame.draw.rect(surf, colors[1], (x * 50 - t, y * 50 - t, 50, 50))

            match menu:
                case -1:
                    surf.blit(t := BIG_FONT.render(f"Battle {"Won" if won else "Lost"}!", True, "black"), (2 + WIDTH // 2 - t.get_width() // 2, 27))
                    surf.blit(t := BIG_FONT.render(f"Battle {"Won" if won else "Lost"}!", True, "white"), (WIDTH // 2 - t.get_width() // 2, 25))

                    w, h = 90, 30

                    if won:
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
                case 0:
                    draw_button(surf, 0, 0, 80, 30, "Test")

                    dialogue_manager.draw(surf)

            v = HEIGHT * ((1 - curtain_timer / 2.0) ** 2)
            screen.blit(surf, (0, -HEIGHT + v))

        pygame.display.flip()
    
    pygame.quit()

if __name__ == "__main__":
    main()