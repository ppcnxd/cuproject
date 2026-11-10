"""board.py - ระบบพิกัดช่อง (cell_rc, rc_cell, cell_center) และการวาดกระดาน/บันได/งู"""
import math

import pygame

from config import (
    BACK_3,
    BLACK,
    BX,
    BY,
    CARD_CELLS,
    CELL,
    CELL_DARK,
    CELL_LIGHT,
    EXTRA_ROLL,
    GOLD,
    GRID,
    LADDERS,
    SNAKES,
    SNAKE_COLORS,
    WHITE,
)
from ui import draw_text


def cell_rc(n):
    """ช่องที่ n (1-100) -> (row, col)  row นับจากล่างขึ้นบน"""
    idx = n - 1
    row = idx // 10
    col = idx % 10
    if row % 2 == 1:          # แถวคี่เดินย้อนกลับ
        col = 9 - col
    return row, col


def rc_cell(row, col):
    """(row, col) -> หมายเลขช่อง"""
    if row % 2 == 1:
        col = 9 - col
    return row * 10 + col + 1


def cell_center(n):
    """จุดกึ่งกลางช่องบนหน้าจอ (n=0 คือจุดเริ่มต้นใต้กระดาน)"""
    if n == 0:
        return (BX + 30, BY + CELL * 10 + 32)
    row, col = cell_rc(n)
    x = BX + col * CELL + CELL // 2
    y = BY + (9 - row) * CELL + CELL // 2
    return (x, y)


def local_center(n):
    x, y = cell_center(n)
    return (x - BX, y - BY)


def draw_ladder(surf, a, b):
    ax, ay = a
    bx, by = b
    length = math.hypot(bx - ax, by - ay)
    ux, uy = (bx - ax) / length, (by - ay) / length
    px, py = -uy * 8, ux * 8          # เวกเตอร์ตั้งฉาก
    wood = (140, 90, 40)
    pygame.draw.line(surf, wood, (ax + px, ay + py), (bx + px, by + py), 5)
    pygame.draw.line(surf, wood, (ax - px, ay - py), (bx - px, by - py), 5)
    steps = int(length // 22)
    for i in range(1, steps + 1):
        t = i * 22
        cx, cy = ax + ux * t, ay + uy * t
        pygame.draw.line(surf, (170, 115, 55), (cx + px, cy + py), (cx - px, cy - py), 4)


def draw_snake(surf, head, tail, color):
    hx, hy = head
    tx, ty = tail
    length = math.hypot(tx - hx, ty - hy)
    ux, uy = (tx - hx) / length, (ty - hy) / length
    px, py = -uy, ux
    points = []
    n = 30
    for i in range(n + 1):
        t = i / n
        wave = math.sin(t * math.pi * 4) * 14 * (1 - t * 0.5)
        points.append((hx + (tx - hx) * t + px * wave, hy + (ty - hy) * t + py * wave))
    pygame.draw.lines(surf, color, False, points, 10)
    light = tuple(min(255, c + 70) for c in color)
    pygame.draw.lines(surf, light, False, points, 4)
    pygame.draw.circle(surf, color, (int(hx), int(hy)), 11)
    pygame.draw.circle(surf, WHITE, (int(hx - 4), int(hy - 3)), 3)
    pygame.draw.circle(surf, WHITE, (int(hx + 4), int(hy - 3)), 3)
    pygame.draw.circle(surf, BLACK, (int(hx - 4), int(hy - 3)), 1)
    pygame.draw.circle(surf, BLACK, (int(hx + 4), int(hy - 3)), 1)
    pygame.draw.circle(surf, (220, 40, 40), (int(hx), int(hy + 6)), 2)


def build_board_surface():
    surf = pygame.Surface((CELL * 10, CELL * 10))
    for n in range(1, 101):
        row, col = cell_rc(n)
        x = col * CELL
        y = (9 - row) * CELL
        color = CELL_LIGHT if (row + col) % 2 == 0 else CELL_DARK
        if n in EXTRA_ROLL:
            color = (150, 225, 150)
        elif n in BACK_3:
            color = (240, 150, 150)
        elif n in CARD_CELLS:
            color = (200, 170, 235)
        elif n == 100:
            color = GOLD
        pygame.draw.rect(surf, color, (x, y, CELL, CELL))
        pygame.draw.rect(surf, GRID, (x, y, CELL, CELL), 1)
        draw_text(surf, str(n), 15, (90, 70, 40), x + 4, y + 2)
        if n in EXTRA_ROLL:
            draw_text(surf, "ทอยอีก", 14, (30, 110, 40), x + CELL // 2, y + CELL - 12, "center")
        elif n in BACK_3:
            draw_text(surf, "ถอย 3", 14, (160, 30, 30), x + CELL // 2, y + CELL - 12, "center")
        elif n in CARD_CELLS:
            draw_text(surf, "+การ์ด", 14, (90, 40, 150), x + CELL // 2, y + CELL - 12, "center")
        elif n == 100:
            draw_text(surf, "จบ", 16, (120, 70, 0), x + CELL // 2, y + CELL - 14, "center")
    for low, high in LADDERS.items():
        draw_ladder(surf, local_center(low), local_center(high))
    i = 0
    for head, tail in SNAKES.items():
        draw_snake(surf, local_center(head), local_center(tail), SNAKE_COLORS[i % len(SNAKE_COLORS)])
        i += 1
    return surf
