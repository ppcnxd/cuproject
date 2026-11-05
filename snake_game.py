import array
import math
import os
import random
import sys

import pygame

pygame.mixer.pre_init(44100, -16, 1, 512)
pygame.init()

# ======================================================================
# 1) ค่าคงที่ และข้อมูลของกระดาน
# ======================================================================
WIDTH, HEIGHT = 1000, 700
FPS = 60
CELL = 60              # ขนาดช่อง
BX, BY = 30, 40        # ตำแหน่งมุมซ้ายบนของกระดาน
PX = 660               # ตำแหน่งเริ่มของแผงข้อมูลด้านขวา

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_FILE = os.path.join(BASE_DIR, "settings.txt")

# บันได {ช่องล่าง: ช่องบน}
LADDERS = {4: 25, 13: 46, 33: 49, 42: 63, 50: 69, 62: 81, 74: 92}
# งู {ช่องหัว: ช่องหาง}
SNAKES = {27: 5, 40: 3, 43: 18, 54: 31, 66: 45, 76: 58, 89: 53, 99: 41}
# ช่องพิเศษ
EXTRA_ROLL = (10, 20, 36, 56, 70, 84)   # ทอยลูกเต๋าอีกรอบ
BACK_3 = (15, 29, 48, 61, 78, 94)       # ถอยกลับ 3 ช่อง
CARD_CELLS = (8, 23, 38, 52, 67, 87)    # ตกช่องนี้แล้วได้การ์ดเพิ่ม 1 ใบ

START_HEARTS = 3
START_CARDS = 5   # จำนวนการ์ดตอนเริ่มเกม
MAX_HAND = 5      # ถือการ์ดได้สูงสุดกี่ใบ
DIAG_RANGE = 4    # การ์ดต่อยแนวเฉียงใช้ได้ในระยะกี่ช่อง
PUSH_DISTANCE = 3  # ผลักไปไกลกี่ช่อง

# สี
WHITE = (255, 255, 255)
BLACK = (20, 20, 20)
BG = (30, 34, 52)
PANEL_BG = (42, 47, 70)
CELL_LIGHT = (250, 240, 205)
CELL_DARK = (232, 210, 160)
GRID = (150, 125, 80)
GRAY = (110, 115, 130)
GOLD = (255, 205, 70)
PLAYER_COLORS = [(230, 70, 70), (70, 130, 235), (70, 190, 100), (240, 170, 40)]
TOKEN_OFFSETS = [(-12, -12), (12, -12), (-12, 12), (12, 12)]
SNAKE_COLORS = [(60, 160, 70), (150, 70, 170), (220, 120, 40), (40, 150, 180)]

# การ์ดพลัง (dict: ชื่อรหัส -> ข้อมูล)
CARDS = {
    "minus":   {"name": "Minus", "desc": "คนถัดไปเดินถอยหลัง",   "color": (150, 90, 200)},
    "reverse": {"name": "Reverse", "desc": "ย้อนลำดับการเล่น",   "color": (60, 150, 200)},
    "skip":    {"name": "Skip", "desc": "ข้ามคนถัดไป",           "color": (200, 140, 50)},
    "punch":   {"name": "ต่อยเฉียง", "desc": "ดันคนในแนวทแยงออกไป", "color": (200, 80, 80)},
    "bomb":    {"name": "ระเบิด", "desc": "สุ่มคนอื่นเสียหัวใจ 1", "color": (90, 90, 90)},
}
CARD_KEYS = list(CARDS.keys())


# ======================================================================
# 2) ฟังก์ชันช่วยเรื่องตำแหน่งช่อง
# ======================================================================
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


# ======================================================================
# 3) ฟอนต์ / วาดข้อความ / ปุ่ม
# ======================================================================
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


# ======================================================================
# 4) ระบบเสียง (สร้างเสียงเองด้วยโค้ด ไม่ต้องมีไฟล์เสียง)
# ======================================================================
def make_sound(notes, volume=0.4):
    """notes = list ของ (ความถี่, ความยาววินาที)
       ความถี่เป็น 0 = เงียบ, "noise" = เสียงซ่า, (a, b) = เสียงเลื่อนจาก a ไป b"""
    rate = 44100
    samples = array.array("h")
    phase = 0.0
    for freq, dur in notes:
        n = int(rate * dur)
        for i in range(n):
            if isinstance(freq, str):
                v = random.uniform(-1, 1) * (1 - i / n) ** 2
            elif freq == 0:
                v = 0
            else:
                if isinstance(freq, tuple):
                    f = freq[0] + (freq[1] - freq[0]) * i / n
                else:
                    f = freq
                phase += f / rate
                v = 0.6 if math.sin(2 * math.pi * phase) >= 0 else -0.6
                v *= min(1.0, i / (rate * 0.005), (n - i) / (rate * 0.04))
            samples.append(int(v * volume * 32767))
    init = pygame.mixer.get_init()
    if init and init[2] == 2:          # ถ้า mixer เป็นสเตอริโอ ให้ซ้ำข้อมูล 2 ช่อง
        stereo = array.array("h")
        for s in samples:
            stereo.append(s)
            stereo.append(s)
        samples = stereo
    return pygame.mixer.Sound(buffer=samples.tobytes())


class SoundManager:
    def __init__(self):
        self.enabled = pygame.mixer.get_init() is not None
        self.volume = 0.7
        self.muted = False
        self.sounds = {}
        self.load_settings()
        if self.enabled:
            self.build_sounds()

    def build_sounds(self):
        s = self.sounds
        s["click"] = make_sound([(800, 0.05)])
        s["dice"] = make_sound([("noise", 0.05), (0, 0.04)] * 6)
        s["step"] = make_sound([(520, 0.04)], 0.25)
        s["ladder"] = make_sound([(392, 0.09), (440, 0.09), (494, 0.09), (523, 0.09),
                                  (587, 0.09), (659, 0.09), (784, 0.25)])
        s["snake"] = make_sound([((700, 120), 0.8)])
        s["win"] = make_sound([(523, 0.15), (659, 0.15), (784, 0.15), (1047, 0.3),
                               (0, 0.05), (784, 0.15), (1047, 0.5)])
        s["card"] = make_sound([(660, 0.06), (880, 0.1)])
        s["bomb"] = make_sound([("noise", 0.6)], 0.6)
        s["punch"] = make_sound([("noise", 0.1), ((300, 80), 0.15)], 0.6)
        s["special"] = make_sound([(880, 0.08), (1175, 0.14)])
        s["back"] = make_sound([(330, 0.1), (247, 0.18)])
        self.apply_volume()

    def apply_volume(self):
        for snd in self.sounds.values():
            snd.set_volume(0 if self.muted else self.volume)

    def play(self, name):
        if self.enabled and not self.muted and name in self.sounds:
            self.sounds[name].play()

    def change_volume(self, delta):
        self.volume = round(min(1.0, max(0.0, self.volume + delta)), 1)
        self.apply_volume()
        self.save_settings()

    def toggle_mute(self):
        self.muted = not self.muted
        self.apply_volume()
        self.save_settings()

    # ---- อ่าน/เขียนไฟล์ตั้งค่า ----
    def load_settings(self):
        if not os.path.exists(SETTINGS_FILE):
            return
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    if "=" not in line:
                        continue
                    key, value = line.strip().split("=", 1)
                    if key == "volume":
                        self.volume = min(1.0, max(0.0, float(value)))
                    elif key == "muted":
                        self.muted = (value == "1")
        except (OSError, ValueError):
            pass

    def save_settings(self):
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                f.write("volume=" + str(self.volume) + "\n")
                f.write("muted=" + ("1" if self.muted else "0") + "\n")
        except OSError:
            pass


# ======================================================================
# 5) วาดกระดาน (วาดครั้งเดียวเก็บไว้ในภาพ)
# ======================================================================
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


# ======================================================================
# 6) ผู้เล่น
# ======================================================================
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


# ======================================================================
# 7) ตัวเกม
# ======================================================================
class Game:
    # phase: CARD (เลือกใช้การ์ด) -> ROLL (รอทอย) -> ROLLING (ลูกเต๋ากลิ้ง)
    #        -> MOVING (เดิน) -> WAIT (หน่วงนิดหน่อย) -> ตาถัดไป
    #        OVER = มีผู้ชนะแล้ว

    def __init__(self, app, num_players):
        self.app = app
        self.sound = app.sound
        self.board_surf = app.board_surf
        self.num_players = num_players
        self.players = []
        for i in range(num_players):
            p = Player(i, "ผู้เล่น " + str(i + 1), PLAYER_COLORS[i])
            for _ in range(START_CARDS):                  # เริ่มมีการ์ด 5 ใบ
                p.cards.append(random.choice(CARD_KEYS))
            self.players.append(p)
        self.direction = 1
        self.current = random.randrange(num_players)      # สุ่มคนเริ่ม
        self.log = []
        self.dice = 1
        self.dice_timer = 0.0
        self.dice_flick = 0.0
        self.move_queue = []        # list ของ (ช่อง, เวลา)
        self.stage = 0
        self.extra = False
        self.timer = 0.0
        self.winner = None
        self.effects = []           # เอฟเฟกต์ระเบิด [x, y, เวลา]
        self.phase = "CARD"
        self.add_log("สุ่มได้ " + self.players[self.current].name + " เริ่มก่อน!")
        self.start_turn()

    # ---------------- ตัวช่วย ----------------
    def cur(self):
        return self.players[self.current]

    def add_log(self, text):
        self.log.append(text)
        if len(self.log) > 30:
            self.log.pop(0)

    def alive_players(self):
        return [p for p in self.players if p.alive]

    def next_index(self, idx):
        """หาลำดับผู้เล่นคนถัดไปที่ยังมีชีวิต ตามทิศทางปัจจุบัน"""
        n = len(self.players)
        i = idx
        for _ in range(n):
            i = (i + self.direction) % n
            if self.players[i].alive:
                return i
        return idx

    # ---------------- เริ่มตา ----------------
    def start_turn(self):
        p = self.cur()
        self.extra = False
        self.phase = "CARD"
        self.add_log("ตาของ " + p.name + " (เลือกใช้การ์ดหรือข้าม)")

    def advance_turn(self):
        n = self.next_index(self.current)
        while self.players[n].skip:
            self.players[n].skip = False
            self.add_log(self.players[n].name + " ถูกข้ามตา!")
            n = self.next_index(n)
        self.current = n
        self.start_turn()

    # ---------------- การ์ด ----------------
    def card_rect(self, i):
        return pygame.Rect(PX, 312 + i * 33, 300, 30)

    def skip_rect(self):
        return pygame.Rect(PX, 480, 200, 28)

    def roll_rect(self):
        return pygame.Rect(PX, 516, 200, 44)

    def dice_rect(self):
        return pygame.Rect(880, 490, 70, 70)

    def use_card(self, i):
        p = self.cur()
        key = p.cards[i]
        if key == "punch" and not self.diag_targets(p):
            self.add_log("ไม่มีผู้เล่นอยู่ในแนวทแยง ใช้การ์ดนี้ไม่ได้")
            return
        p.cards.pop(i)
        self.sound.play("card")
        self.add_log(p.name + " ใช้การ์ด " + CARDS[key]["name"])
        if key == "minus":
            target = self.players[self.next_index(self.current)]
            target.minus = True
            self.add_log(target.name + " ต้องเดินถอยหลังตาหน้า")
        elif key == "reverse":
            self.direction = -self.direction
            self.add_log("ลำดับการเล่นถูกย้อนกลับ!")
        elif key == "skip":
            target = self.players[self.next_index(self.current)]
            target.skip = True
            self.add_log(target.name + " จะถูกข้ามตา")
        elif key == "punch":
            self.sound.play("punch")
            for target, sr, sc in self.diag_targets(p):
                self.push_player(target, sr, sc)
        elif key == "bomb":
            self.sound.play("bomb")
            victims = [t for t in self.alive_players() if t is not p]
            target = random.choice(victims)
            target.hearts -= 1
            self.effects.append([target.draw_pos[0], target.draw_pos[1], 0.0])
            self.add_log("ระเบิดลง " + target.name + "! เหลือหัวใจ " + str(target.hearts))
            if target.hearts <= 0:
                self.add_log(target.name + " ตายแล้ว!")
                if len(self.alive_players()) == 1:
                    self.win(p)
                    return
        self.phase = "ROLL"

    def diag_targets(self, user):
        """คืนค่า list ของ (ผู้เล่น, ทิศแถว, ทิศคอลัมน์) ที่อยู่ในแนวทแยงของ user"""
        result = []
        if user.pos == 0:
            return result
        r, c = cell_rc(user.pos)
        for t in self.players:
            if t is user or not t.alive or t.pos == 0:
                continue
            r2, c2 = cell_rc(t.pos)
            dr = r2 - r
            dc = c2 - c
            if dr != 0 and abs(dr) == abs(dc) and abs(dr) <= DIAG_RANGE:
                result.append((t, 1 if dr > 0 else -1, 1 if dc > 0 else -1))
        return result

    def push_player(self, t, sr, sc):
        r, c = cell_rc(t.pos)
        moved = 0
        for _ in range(PUSH_DISTANCE):
            nr = r + sr
            nc = c + sc
            if nr < 0 or nr > 9 or nc < 0 or nc > 9:
                break
            if rc_cell(nr, nc) == 100:       # ไม่ให้ผลักไปชนะ
                break
            r, c = nr, nc
            moved += 1
        if moved == 0:
            self.add_log(t.name + " ติดขอบ ผลักไม่ไป")
            return
        new_cell = rc_cell(r, c)
        dest = new_cell
        if new_cell in LADDERS:
            dest = LADDERS[new_cell]
        elif new_cell in SNAKES:
            dest = SNAKES[new_cell]
        t.go_to(dest, 0.7)
        self.add_log(t.name + " ถูกต่อยไปช่อง " + str(dest))

    # ---------------- ทอยลูกเต๋า ----------------
    def start_roll(self):
        self.phase = "ROLLING"
        self.dice_timer = 0.8
        self.dice_flick = 0.0
        self.sound.play("dice")

    def begin_move(self):
        p = self.cur()
        v = self.dice
        self.move_queue = []
        backward = False
        if p.minus:
            p.minus = False
            backward = True
            self.add_log(p.name + " ทอยได้ " + str(v) + " แต่ต้องเดินถอยหลัง!")
        else:
            self.add_log(p.name + " ทอยได้ " + str(v))
        if not backward:
            if p.pos + v > 100:
                self.add_log("เกิน 100 ต้องทอยให้พอดี อยู่ที่เดิม")
            else:
                for c in range(p.pos + 1, p.pos + v + 1):
                    self.move_queue.append((c, 0.2))
        else:
            c = p.pos - 1
            while c >= max(p.pos - v, 1):
                self.move_queue.append((c, 0.2))
                c -= 1
        self.stage = 0 if self.move_queue else 1
        self.phase = "MOVING"

    def resolve_cell(self, p):
        """ตรวจช่องที่ยืนอยู่ว่าเป็นบันได/งู/ช่องพิเศษหรือไม่"""
        pos = p.pos
        if pos in LADDERS:
            self.move_queue.append((LADDERS[pos], 0.9))
            self.sound.play("ladder")
            self.add_log("เจอบันได! ไต่ขึ้นไปช่อง " + str(LADDERS[pos]))
        elif pos in SNAKES:
            self.move_queue.append((SNAKES[pos], 0.9))
            self.sound.play("snake")
            self.add_log("เจองู! ไถลลงไปช่อง " + str(SNAKES[pos]))
        elif pos in EXTRA_ROLL:
            self.extra = True
            self.sound.play("special")
            self.add_log("ช่องพิเศษ! ได้ทอยอีกรอบ")
        elif pos in CARD_CELLS:
            if len(p.cards) < MAX_HAND:
                key = random.choice(CARD_KEYS)
                p.cards.append(key)
                self.sound.play("card")
                self.add_log("ช่องการ์ด! ได้การ์ด " + CARDS[key]["name"])
            else:
                self.add_log("ช่องการ์ด! แต่การ์ดเต็มมือแล้ว")
        elif pos in BACK_3:
            for k in range(1, 4):
                self.move_queue.append((pos - k, 0.25))
            self.sound.play("back")
            self.add_log("ช่องพิเศษ! ถอยกลับ 3 ช่อง")

    def win(self, p):
        self.winner = p
        self.phase = "OVER"
        self.timer = 1.5
        self.sound.play("win")
        self.add_log(p.name + " ชนะ!")

    # ---------------- อัปเดตทุกเฟรม ----------------
    def update(self, dt):
        for p in self.players:
            p.update(dt)
        for e in self.effects:
            e[2] += dt
        self.effects = [e for e in self.effects if e[2] < 0.7]

        if self.phase == "ROLLING":
            self.dice_timer -= dt
            self.dice_flick -= dt
            if self.dice_flick <= 0:
                self.dice = random.randint(1, 6)
                self.dice_flick = 0.07
            if self.dice_timer <= 0:
                self.dice = random.randint(1, 6)
                self.begin_move()

        elif self.phase == "MOVING":
            p = self.cur()
            if p.moving():
                return
            if self.move_queue:
                cell, dur = self.move_queue.pop(0)
                p.go_to(cell, dur)
                if dur <= 0.25:
                    self.sound.play("step")
            elif self.stage == 0:
                self.stage = 1
                if p.pos == 100:
                    self.win(p)
                else:
                    self.resolve_cell(p)
            else:
                if p.pos == 100:
                    self.win(p)
                else:
                    self.phase = "WAIT"
                    self.timer = 0.5

        elif self.phase == "WAIT":
            self.timer -= dt
            if self.timer <= 0:
                if self.extra:
                    self.phase = "ROLL"
                    self.extra = False
                    self.add_log(self.cur().name + " ทอยอีกรอบ")
                else:
                    self.advance_turn()

        elif self.phase == "OVER":
            self.timer -= dt
            if self.timer <= 0:
                self.app.show_win(self.winner)

    # ---------------- รับเมาส์/คีย์บอร์ด ----------------
    def click(self, pos):
        p = self.cur()
        if self.phase == "CARD":
            for i in range(len(p.cards)):
                if self.card_rect(i).collidepoint(pos):
                    self.use_card(i)
                    return
            if self.skip_rect().collidepoint(pos):
                self.sound.play("click")
                self.add_log(p.name + " ไม่ใช้การ์ด")
                self.phase = "ROLL"
        elif self.phase == "ROLL":
            if self.roll_rect().collidepoint(pos) or self.dice_rect().collidepoint(pos):
                self.start_roll()

    def key(self, event):
        if event.key == pygame.K_SPACE:
            if self.phase == "ROLL":
                self.start_roll()
            elif self.phase == "CARD":
                self.add_log(self.cur().name + " ไม่ใช้การ์ด")
                self.phase = "ROLL"

    # ---------------- วาด ----------------
    def draw(self, surf):
        surf.fill(BG)
        surf.blit(self.board_surf, (BX, BY))
        pygame.draw.rect(surf, WHITE, (BX - 3, BY - 3, CELL * 10 + 6, CELL * 10 + 6), 3)
        draw_text(surf, "เริ่มต้น", 18, WHITE, BX + 80, BY + CELL * 10 + 20)

        # ตัวหมาก (คนที่กำลังเล่นวาดทีหลังสุดจะได้อยู่บนสุด)
        for p in self.players:
            if p.alive and p is not self.cur():
                p.draw(surf, False)
        if self.cur().alive:
            self.cur().draw(surf, True)

        for e in self.effects:
            radius = int(e[2] * 100)
            pygame.draw.circle(surf, (255, 160, 40), (int(e[0]), int(e[1])), radius, 6)
            pygame.draw.circle(surf, (255, 230, 90), (int(e[0]), int(e[1])), radius // 2, 4)

        self.draw_panel(surf)

    def draw_panel(self, surf):
        pygame.draw.rect(surf, PANEL_BG, (PX - 12, 0, WIDTH - PX + 12, HEIGHT))
        cur = self.cur()
        draw_text(surf, "ตาของ " + cur.name, 24, cur.color, PX, 8)
        dir_text = "ลำดับ: ปกติ" if self.direction == 1 else "ลำดับ: ย้อนกลับ"
        draw_text(surf, dir_text, 16, (200, 200, 210), PX + 300, 14, "right")

        # รายชื่อผู้เล่น
        for i, p in enumerate(self.players):
            y = 48 + i * 58
            rect = pygame.Rect(PX, y, 300, 52)
            pygame.draw.rect(surf, (58, 64, 92), rect, border_radius=8)
            if p is cur:
                pygame.draw.rect(surf, p.color, rect, 3, border_radius=8)
            pygame.draw.circle(surf, p.color, (PX + 22, y + 26), 13)
            draw_text(surf, str(p.idx + 1), 16, WHITE, PX + 22, y + 26, "center")
            draw_text(surf, p.name, 18, WHITE, PX + 44, y + 4)
            for k in range(START_HEARTS):
                draw_heart(surf, PX + 56 + k * 24, y + 38, 18,
                           (235, 60, 80) if k < p.hearts else GRAY, k < p.hearts)
            if p.alive:
                draw_text(surf, "ช่อง " + str(p.pos), 16, GOLD, PX + 294, y + 4, "right")
                status = "การ์ด " + str(len(p.cards))
                if p.skip:
                    status += " | ถูกข้าม"
                if p.minus:
                    status += " | ถอยหลัง"
                draw_text(surf, status, 14, (200, 200, 210), PX + 294, y + 30, "right")
            else:
                draw_text(surf, "ตายแล้ว", 18, (240, 90, 90), PX + 294, y + 14, "right")

        # การ์ดในมือ
        in_card_phase = (self.phase == "CARD")
        if in_card_phase:
            draw_text(surf, "เลือกใช้การ์ด 1 ใบ หรือกด 'ไม่ใช้การ์ด'", 16, GOLD, PX, 288)
        else:
            draw_text(surf, "การ์ดในมือ", 16, (200, 200, 210), PX, 288)
        for i, key in enumerate(cur.cards):
            info = CARDS[key]
            draw_button(surf, self.card_rect(i), info["name"] + " - " + info["desc"], 16,
                        info["color"], in_card_phase)
        if in_card_phase:
            draw_button(surf, self.skip_rect(), "ไม่ใช้การ์ด", 18, (80, 120, 90))

        # ปุ่มทอยและลูกเต๋า
        draw_button(surf, self.roll_rect(), "ทอยลูกเต๋า (Space)", 19, (220, 120, 40),
                    self.phase == "ROLL")
        draw_dice(surf, self.dice_rect(), self.dice)

        # บันทึกเหตุการณ์
        pygame.draw.line(surf, GRAY, (PX, 568), (PX + 300, 568), 1)
        recent = self.log[-4:]
        for i, text in enumerate(recent):
            shade = 255 if i == len(recent) - 1 else 175
            draw_text(surf, text, 16, (shade, shade, shade), PX, 576 + i * 28)


# ======================================================================
# 8) โปรแกรมหลัก (เมนู / ตั้งค่า / เกม / หน้าชนะ)
# ======================================================================
class App:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("เกมบันไดงู - Snakes & Ladders")
        self.sound = SoundManager()
        self.board_surf = build_board_surface()
        self.game = None
        self.num_players = 2
        self.winner = None
        self.buttons = []
        self.state = "MENU"
        self.set_state("MENU")

    # ---------- สลับหน้า ----------
    def set_state(self, state):
        self.state = state
        self.buttons = []
        cx = WIDTH // 2
        if state == "MENU":
            self.buttons = [
                Button((cx - 150, 300, 300, 62), "เริ่มเกม", lambda: self.set_state("PLAYERS"), 30, (70, 150, 90)),
                Button((cx - 150, 380, 300, 62), "ตั้งค่าเสียง", lambda: self.set_state("SETTINGS"), 30),
                Button((cx - 150, 460, 300, 62), "ออกจากเกม", self.quit, 30, (180, 70, 70)),
            ]
        elif state == "PLAYERS":
            self.buttons = [
                Button((cx - 150, 280, 300, 62), "2 ผู้เล่น", lambda: self.start_game(2), 30),
                Button((cx - 150, 360, 300, 62), "3 ผู้เล่น", lambda: self.start_game(3), 30),
                Button((cx - 150, 440, 300, 62), "4 ผู้เล่น", lambda: self.start_game(4), 30),
                Button((cx - 150, 540, 300, 56), "กลับ", lambda: self.set_state("MENU"), 26, (120, 120, 130)),
            ]
        elif state == "SETTINGS":
            mute_text = "เสียง: ปิดอยู่ (กดเพื่อเปิด)" if self.sound.muted else "เสียง: เปิดอยู่ (กดเพื่อปิด)"
            self.buttons = [
                Button((cx - 190, 300, 60, 60), "-", self.volume_down, 36),
                Button((cx + 130, 300, 60, 60), "+", self.volume_up, 36),
                Button((cx - 190, 400, 380, 60), mute_text, self.toggle_mute, 24),
                Button((cx - 150, 520, 300, 56), "กลับ", lambda: self.set_state("MENU"), 26, (120, 120, 130)),
            ]
        elif state == "WIN":
            self.buttons = [
                Button((cx - 150, 450, 300, 62), "เล่นอีกครั้ง", lambda: self.start_game(self.num_players), 28, (70, 150, 90)),
                Button((cx - 150, 530, 300, 62), "กลับเมนู", lambda: self.set_state("MENU"), 28),
            ]

    def volume_down(self):
        self.sound.change_volume(-0.1)
        self.sound.play("click")

    def volume_up(self):
        self.sound.change_volume(0.1)
        self.sound.play("click")

    def toggle_mute(self):
        self.sound.toggle_mute()
        self.set_state("SETTINGS")     # สร้างปุ่มใหม่เพื่อเปลี่ยนข้อความ
        self.sound.play("click")

    def start_game(self, n):
        self.num_players = n
        self.game = Game(self, n)
        self.state = "PLAY"
        self.buttons = []
        self.sound.play("click")

    def show_win(self, winner):
        self.winner = winner
        self.set_state("WIN")

    def quit(self):
        pygame.quit()
        sys.exit()

    # ---------- event / update / draw ----------
    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.quit()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.state == "PLAY":
                self.game.click(event.pos)
            else:
                for b in list(self.buttons):
                    if b.click(event.pos):
                        break
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.state == "PLAY":
                    self.set_state("MENU")
                elif self.state != "MENU":
                    self.set_state("MENU")
            elif self.state == "PLAY":
                self.game.key(event)

    def update(self, dt):
        if self.state == "PLAY":
            self.game.update(dt)

    def draw_background(self):
        for y in range(0, HEIGHT, 4):
            k = y / HEIGHT
            color = (int(30 + 30 * k), int(34 + 40 * k), int(70 + 60 * k))
            pygame.draw.rect(self.screen, color, (0, y, WIDTH, 4))

    def draw(self):
        s = self.screen
        if self.state == "PLAY":
            self.game.draw(s)
        elif self.state == "WIN":
            self.game.draw(s)
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 190))
            s.blit(overlay, (0, 0))
            draw_text(s, "ผู้ชนะ!", 60, GOLD, WIDTH // 2, 180, "center")
            pygame.draw.circle(s, WHITE, (WIDTH // 2, 290), 52)
            pygame.draw.circle(s, self.winner.color, (WIDTH // 2, 290), 46)
            draw_text(s, str(self.winner.idx + 1), 56, WHITE, WIDTH // 2, 290, "center")
            draw_text(s, self.winner.name + " เป็นผู้ชนะเกมนี้", 34, WHITE, WIDTH // 2, 380, "center")
            for b in self.buttons:
                b.draw(s)
        else:
            self.draw_background()
            cx = WIDTH // 2
            if self.state == "MENU":
                draw_text(s, "บันไดงู", 90, GOLD, cx, 140, "center")
                draw_text(s, "SNAKES & LADDERS", 30, WHITE, cx, 215, "center")
                draw_text(s, "ใช้เมาส์คลิกเล่น  |  Space = ทอยลูกเต๋า  |  Esc = กลับเมนู", 18,
                          (190, 190, 210), cx, 640, "center")
            elif self.state == "PLAYERS":
                draw_text(s, "เลือกจำนวนผู้เล่น", 56, GOLD, cx, 150, "center")
            elif self.state == "SETTINGS":
                draw_text(s, "ตั้งค่าเสียง", 56, GOLD, cx, 150, "center")
                draw_text(s, "ระดับเสียงเอฟเฟกต์", 26, WHITE, cx, 260, "center")
                bar = pygame.Rect(cx - 110, 315, 220, 30)
                pygame.draw.rect(s, (60, 64, 90), bar, border_radius=8)
                fill = pygame.Rect(bar.x, bar.y, int(bar.w * self.sound.volume), bar.h)
                pygame.draw.rect(s, (90, 200, 120) if not self.sound.muted else GRAY, fill, border_radius=8)
                pygame.draw.rect(s, WHITE, bar, 2, border_radius=8)
                draw_text(s, str(int(self.sound.volume * 100)) + "%", 22, WHITE, cx, 375, "center")
                if not self.sound.enabled:
                    draw_text(s, "(ไม่พบอุปกรณ์เสียงในเครื่องนี้)", 18, (240, 120, 120), cx, 480, "center")
            for b in self.buttons:
                b.draw(s)

    def run(self):
        clock = pygame.time.Clock()
        while True:
            dt = clock.tick(FPS) / 1000.0
            for event in pygame.event.get():
                self.handle_event(event)
            self.update(dt)
            self.draw()
            pygame.display.flip()


if __name__ == "__main__":
    App().run()