"""player.py - คลาส Player: ข้อมูลผู้เล่น, แอนิเมชันเดิน, วาดตัวหมาก"""
import pygame

from config import (
    BLACK,
    START_HEARTS,
    TOKEN_OFFSETS,
    WHITE,
)
from ui import draw_text
from board import cell_center


class Player:
    def __init__(self, idx, name, color):
        self.idx = idx
        self.name = name
        self.color = color
        self.pos = 0                 # 0 = ยังไม่ลงกระดาน
        self.hearts = START_HEARTS
        self.cards = []              # list ของรหัสการ์ด
        self.skip = False            # ถูกข้ามตา
        self.minus = False           # ตาหน้าต้องเดินถอยหลัง
        self.draw_pos = list(cell_center(0))   # ตำแหน่งที่วาดจริง (เพื่อทำแอนิเมชัน)
        self.tween = None            # [จุดเริ่ม, จุดจบ, เวลาที่ผ่าน, เวลารวม]

    @property
    def alive(self):
        return self.hearts > 0

    def go_to(self, cell, duration):
        """ย้ายไปช่อง cell (ตำแหน่งจริงเปลี่ยนทันที ภาพค่อยๆเลื่อน)"""
        self.pos = cell
        self.tween = [tuple(self.draw_pos), cell_center(cell), 0.0, max(duration, 0.01)]

    def moving(self):
        return self.tween is not None

    def update(self, dt):
        if self.tween is None:
            return
        start, end, t, dur = self.tween
        t += dt
        k = min(t / dur, 1.0)
        self.draw_pos[0] = start[0] + (end[0] - start[0]) * k
        self.draw_pos[1] = start[1] + (end[1] - start[1]) * k
        if k >= 1.0:
            self.tween = None
        else:
            self.tween[2] = t

    def draw(self, surf, is_current):
        ox, oy = TOKEN_OFFSETS[self.idx]
        x = int(self.draw_pos[0] + ox)
        y = int(self.draw_pos[1] + oy)
        if is_current:
            pygame.draw.circle(surf, WHITE, (x, y), 16)
        pygame.draw.circle(surf, BLACK, (x, y), 14)
        pygame.draw.circle(surf, self.color, (x, y), 12)
        draw_text(surf, str(self.idx + 1), 16, WHITE, x, y, "center")
