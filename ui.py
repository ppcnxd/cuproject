"""ui.py - ฟังก์ชันวาด UI พื้นฐาน: ฟอนต์ไทย, ข้อความ, ปุ่ม, หัวใจ, ลูกเต๋า

หมายเหตุเรื่องฟอนต์ภาษาไทย:
  - โปรแกรมจะหาฟอนต์ไทยในเครื่องให้เอง (Tahoma, Leelawadee, Thonburi ฯลฯ)
  - ถ้าตัวหนังสือเป็นสี่เหลี่ยม ให้ใส่ไฟล์ฟอนต์ไทยชื่อ font.ttf ไว้โฟลเดอร์เดียวกับไฟล์เกม
"""
import os

import pygame

from config import (
    BASE_DIR,
    BLACK,
    GRAY,
    WHITE,
)


THAI_FONTS = ["leelawadeeui", "leelawadee", "tahoma", "angsananew", "cordianew",
              "thonburi", "ayuthaya", "notosansthai", "notosansthaiui",
              "tlwgtypo", "loma", "garuda", "waree", "norasi", "freeserif"]
_font_cache = {}


def get_font(size):
    if size in _font_cache:
        return _font_cache[size]
    font = None
    custom = os.path.join(BASE_DIR, "font.ttf")
    if os.path.exists(custom):
        font = pygame.font.Font(custom, size)
    else:
        for name in THAI_FONTS:
            path = pygame.font.match_font(name)
            if path:
                font = pygame.font.Font(path, size)
                break
    if font is None:
        font = pygame.font.Font(None, size)
    _font_cache[size] = font
    return font


def draw_text(surf, text, size, color, x, y, align="left"):
    img = get_font(size).render(text, True, color)
    rect = img.get_rect()
    if align == "center":
        rect.center = (x, y)
    elif align == "right":
        rect.topright = (x, y)
    else:
        rect.topleft = (x, y)
    surf.blit(img, rect)
    return rect


def draw_button(surf, rect, text, size=24, color=(70, 110, 200), enabled=True):
    hover = enabled and rect.collidepoint(pygame.mouse.get_pos())
    if not enabled:
        col = (80, 82, 95)
    elif hover:
        col = tuple(min(255, c + 35) for c in color)
    else:
        col = color
    pygame.draw.rect(surf, col, rect, border_radius=10)
    pygame.draw.rect(surf, WHITE if enabled else GRAY, rect, 2, border_radius=10)
    draw_text(surf, text, size, WHITE if enabled else (170, 170, 180),
              rect.centerx, rect.centery, "center")


class Button:
    """ปุ่มสำหรับหน้าเมนูต่างๆ"""

    def __init__(self, rect, text, action, size=28, color=(70, 110, 200)):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.action = action
        self.size = size
        self.color = color

    def draw(self, surf):
        draw_button(surf, self.rect, self.text, self.size, self.color)

    def click(self, pos):
        if self.rect.collidepoint(pos):
            self.action()
            return True
        return False


def draw_heart(surf, cx, cy, s, color, filled=True):
    r = s / 4
    width = 0 if filled else 2
    pygame.draw.circle(surf, color, (int(cx - r), int(cy - r)), int(r + 1), width)
    pygame.draw.circle(surf, color, (int(cx + r), int(cy - r)), int(r + 1), width)
    points = [(cx - 2 * r + 1, cy - r * 0.5), (cx + 2 * r - 1, cy - r * 0.5), (cx, cy + 2 * r)]
    pygame.draw.polygon(surf, color, points, width)


def draw_dice(surf, rect, value):
    pygame.draw.rect(surf, WHITE, rect, border_radius=12)
    pygame.draw.rect(surf, BLACK, rect, 3, border_radius=12)
    d = rect.w // 4
    cx, cy = rect.center
    pips = {
        1: [(0, 0)],
        2: [(-1, -1), (1, 1)],
        3: [(-1, -1), (0, 0), (1, 1)],
        4: [(-1, -1), (1, -1), (-1, 1), (1, 1)],
        5: [(-1, -1), (1, -1), (0, 0), (-1, 1), (1, 1)],
        6: [(-1, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (1, 1)],
    }
    for ox, oy in pips[value]:
        pygame.draw.circle(surf, BLACK, (cx + ox * d, cy + oy * d), rect.w // 11 + 2)
