"""game.py - กติกาเกมทั้งหมด (คลาส Game): ลำดับตา, ทอยลูกเต๋า, การเดิน, การ์ด, ช่องพิเศษ"""
import random

import pygame

from config import (
    BACK_3,
    BG,
    BX,
    BY,
    CARDS,
    CARD_CELLS,
    CARD_KEYS,
    CELL,
    DIAG_RANGE,
    EXTRA_ROLL,
    GOLD,
    GRAY,
    HEIGHT,
    LADDERS,
    MAX_HAND,
    PANEL_BG,
    PLAYER_COLORS,
    PUSH_DISTANCE,
    PX,
    SNAKES,
    START_CARDS,
    START_HEARTS,
    WHITE,
    WIDTH,
)
from ui import (
    draw_button,
    draw_dice,
    draw_heart,
    draw_text,
)
from board import cell_rc, rc_cell
from player import Player


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
