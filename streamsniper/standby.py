#!/usr/bin/env python3
"""
StreamSniper Standby Screen
A fullscreen clock/status display shown while waiting for the stream to go live.
Requires: python3-pygame  (sudo apt install python3-pygame)
"""

import pygame
import sys
import time
import math
from datetime import datetime

from config import load_channels


def watch_label():
    """Text for the standby screen: one name, a count, or a prompt."""
    ch = load_channels()
    if not ch:
        return "NO CHANNELS SET"
    if len(ch) == 1:
        return ch[0].upper()
    return f"{len(ch)} CHANNELS"

# Colors
BG          = (8, 8, 16)
ACCENT      = (100, 220, 255)
ACCENT_DIM  = (30, 80, 120)
WHITE       = (230, 240, 255)
MUTED       = (60, 80, 110)
PULSE_COLOR = (255, 80, 120)

def draw_scan_line(surface, y, width, alpha=15):
    s = pygame.Surface((width, 1), pygame.SRCALPHA)
    s.fill((255, 255, 255, alpha))
    surface.blit(s, (0, y))

def main():
    pygame.init()
    info = pygame.display.Info()
    W, H = info.current_w, info.current_h

    screen = pygame.display.set_mode((W, H), pygame.FULLSCREEN | pygame.NOFRAME)
    pygame.display.set_caption("StreamSniper Standby")
    pygame.mouse.set_visible(False)
    clock = pygame.time.Clock()

    # Fonts
    try:
        font_huge  = pygame.font.Font(None, int(H * 0.22))
        font_large = pygame.font.Font(None, int(H * 0.07))
        font_med   = pygame.font.Font(None, int(H * 0.045))
        font_small = pygame.font.Font(None, int(H * 0.03))
    except:
        font_huge  = pygame.font.SysFont("monospace", 120, bold=True)
        font_large = pygame.font.SysFont("monospace", 48)
        font_med   = pygame.font.SysFont("monospace", 32)
        font_small = pygame.font.SysFont("monospace", 22)

    frame = 0

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pygame.quit(); sys.exit()

        screen.fill(BG)
        now = datetime.now()
        frame += 1

        # Subtle grid
        for x in range(0, W, 60):
            pygame.draw.line(screen, (15, 20, 35), (x, 0), (x, H), 1)
        for y in range(0, H, 60):
            pygame.draw.line(screen, (15, 20, 35), (0, y), (W, y), 1)

        # Scan line animation
        scan_y = int((frame * 2) % H)
        for i in range(3):
            draw_scan_line(screen, (scan_y + i * 8) % H, W, 12 - i * 3)

        # Pulsing circle behind clock
        pulse = 0.5 + 0.5 * math.sin(frame * 0.03)
        radius = int(H * 0.28 + pulse * 20)
        glow_surf = pygame.Surface((W, H), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*ACCENT_DIM, 40), (W // 2, H // 2), radius)
        pygame.draw.circle(glow_surf, (*ACCENT_DIM, 15), (W // 2, H // 2), radius + 40)
        screen.blit(glow_surf, (0, 0))

        # Clock — HH:MM
        colon_visible = now.second % 2 == 0
        time_str = now.strftime("%H:%M") if colon_visible else now.strftime("%H %M")
        time_surf = font_huge.render(time_str, True, WHITE)
        time_rect = time_surf.get_rect(center=(W // 2, H // 2 - int(H * 0.04)))
        screen.blit(time_surf, time_rect)

        # Date
        date_str = now.strftime("%A, %B %d")
        date_surf = font_med.render(date_str, True, MUTED)
        date_rect = date_surf.get_rect(center=(W // 2, H // 2 + int(H * 0.15)))
        screen.blit(date_surf, date_rect)

        # Divider line
        line_w = int(W * 0.25)
        pygame.draw.line(screen, ACCENT_DIM,
                         (W // 2 - line_w // 2, H // 2 + int(H * 0.19)),
                         (W // 2 + line_w // 2, H // 2 + int(H * 0.19)), 1)

        # Status text
        pulse_alpha = int(180 + 75 * math.sin(frame * 0.05))
        status_color = (
            max(0, min(255, PULSE_COLOR[0])),
            max(0, min(255, PULSE_COLOR[1])),
            max(0, min(255, PULSE_COLOR[2]))
        )
        status_surf = font_large.render(f"● WAITING FOR {watch_label()}", True, status_color)
        status_rect = status_surf.get_rect(center=(W // 2, H // 2 + int(H * 0.24)))
        screen.blit(status_surf, status_rect)

        # Bottom hint
        hint = font_small.render("StreamSniper — stream will launch automatically", True, MUTED)
        hint_rect = hint.get_rect(center=(W // 2, H - 30))
        screen.blit(hint, hint_rect)

        # Corner dots
        dot_pulse = int(100 + 155 * abs(math.sin(frame * 0.04)))
        for corner in [(20, 20), (W - 20, 20), (20, H - 20), (W - 20, H - 20)]:
            pygame.draw.circle(screen, (*ACCENT[:2], dot_pulse), corner, 4)

        pygame.display.flip()
        clock.tick(30)

if __name__ == "__main__":
    main()
