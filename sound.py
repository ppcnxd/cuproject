"""sound.py - สร้างเสียงเอฟเฟกต์ด้วยโค้ด (make_sound) และตัวจัดการเสียง (SoundManager)"""
import array
import math
import os
import random

import pygame

from config import SETTINGS_FILE


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
