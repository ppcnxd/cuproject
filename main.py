import sys

import pygame

# ต้องตั้งค่า mixer และ init pygame ก่อนที่โมดูลอื่นจะถูกใช้งาน
pygame.mixer.pre_init(44100, -16, 1, 512)
pygame.init()

from config import (
    FPS,
    GOLD,
    GRAY,
    HEIGHT,
    WHITE,
    WIDTH,
)
from ui import Button, draw_text
from sound import SoundManager
from board import build_board_surface
from game import Game


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
