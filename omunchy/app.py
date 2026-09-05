"""Game loop, screens, and input. Sounds are wired into every gameplay beat."""

from __future__ import annotations

import random
import sys

import pygame

from omunchy.audio import Audio
from omunchy.board import Board, generate_board
from omunchy.constants import (
    BG,
    BG_DEEP,
    BLACK,
    CELL_BG,
    CELL_BG_ALT,
    CELL_BORDER,
    CELL_EMPTY,
    CELL_HL,
    CREAM,
    CYAN,
    EMBER,
    FLAME,
    FPS,
    GOLD,
    GREEN,
    grid_geometry,
    HINT_H,
    HIT_IFRAMES,
    HUD_BG,
    HUD_H,
    MAX_COLS,
    MAX_ROWS,
    MODE_BLURBS,
    MODE_LABELS,
    MODES,
    MOVE_DELAY,
    MUNCH_LOCK,
    ORANGE,
    RED,
    RULE_BG,
    RULE_H,
    START_LIVES,
    TITLE,
    TROGGLE_FREEZE,
    WHITE,
    WINDOW_H,
    WINDOW_W,
    YELLOW,
)
from omunchy.entities import (
    Muncher,
    Troggle,
    apply_hunter_eats,
    player_hits_hazard,
    safe_player_spawn,
    spawn_troggles,
)
from omunchy.celebrate import CELEBRATE_SECONDS, banner_for_level, is_celebration_level
from omunchy.rules import Rule, rule_for
from omunchy.sprites import cell_rect, draw_outlined_text, fire_surface, muncher_surface, troggle_surface
from omunchy.title_art import (
    BLURB_A,
    BLURB_B,
    CONTROLS_HINT,
    START_HINT,
    TAGLINE,
    TITLE_BANNER,
    TITLE_DOODLE,
)

TITLE_ST, MODE_ST, INTRO_ST, PLAY_ST, PAUSE_ST, CLEAR_ST, CELEBRATE_ST, OVER_ST = range(8)


def _font(size: int, bold: bool = False) -> pygame.font.Font:
    names = ("DejaVu Sans Mono", "Liberation Mono", "FreeMono", "monospace")
    for name in names:
        path = pygame.font.match_font(name, bold=bold)
        if path:
            return pygame.font.Font(path, size)
    return pygame.font.Font(None, size)


class Game:
    def __init__(self) -> None:
        pygame.display.set_caption(TITLE)
        self.fullscreen = True
        self.screen = self._make_screen(fullscreen=True)
        self.clock = pygame.time.Clock()
        self.audio = Audio()
        self.rng = random.Random()
        self.running = True

        self.font_xl = _font(56, True)
        self.font_lg = _font(40, True)
        self.font_md = _font(28, True)
        self.font_sm = _font(20, True)
        self.font_tiny = _font(16)
        self.font_cell = _font(30, True)
        self.font_ascii = _font(15, True)
        self.font_doodle = _font(16)

        self.state = TITLE_ST
        self.mode_index = 0
        self.selected_mode = "multiples"
        self.level = 1
        self.score = 0
        self.best = 0
        self.lives = START_LIVES
        self.rule: Rule | None = None
        self.board: Board | None = None
        self.player = Muncher(row=1, col=1)
        self.troggles: list[Troggle] = []
        self.move_cool = 0.0
        self.freeze = 0.0
        self.flash_wrong = 0.0
        self.banner_timer = 0.0
        self.celebrate_banner = "Nice!"
        self.confetti: list[int] = []
        self.anim = 0.0
        self.held: set[int] = set()

        self.audio.play("title")
        self.audio.play_bg()

    def start_run(self, mode: str) -> None:
        self.selected_mode = mode
        self.level = 1
        self.score = 0
        self.lives = START_LIVES
        self._begin_level()

    def _board_size(self) -> tuple[int, int]:
        if self.board is not None:
            return self.board.rows, self.board.cols
        return MAX_ROWS, MAX_COLS

    def _grid_geom(self) -> tuple[int, int, int, int]:
        rows, cols = self._board_size()
        return grid_geometry(rows, cols)

    def _begin_level(self) -> None:
        self.rule = rule_for(self.selected_mode, self.level)
        self.board = generate_board(self.rule, self.level, self.rng)
        rows, cols = self.board.rows, self.board.cols
        occupied: set[tuple[int, int]] = set()
        pr, pc = safe_player_spawn(occupied, self.rng, rows, cols)
        self.player = Muncher(row=pr, col=pc)
        occupied.add((pr, pc))
        self.troggles = spawn_troggles(self.level, (pr, pc), self.rng, rows, cols)
        self.move_cool = 0.0
        self.freeze = 0.35
        self.flash_wrong = 0.0
        self.banner_timer = 0.0
        self.state = INTRO_ST


    def _make_screen(self, fullscreen: bool = True):
        """16:9 logical frame. Prefer fullscreen + SCALED; windowed if that fails."""
        logical = (WINDOW_W, WINDOW_H)
        attempts: list[int] = []
        if fullscreen:
            attempts.extend((pygame.FULLSCREEN | pygame.SCALED, pygame.FULLSCREEN))
        attempts.extend((pygame.SCALED | pygame.RESIZABLE, pygame.RESIZABLE, 0))
        last_error: pygame.error | None = None
        for flags in attempts:
            try:
                surface = pygame.display.set_mode(logical, flags)
                self.fullscreen = bool(flags & pygame.FULLSCREEN)
                return surface
            except pygame.error as exc:
                last_error = exc
        if last_error is not None:
            surface = pygame.display.set_mode(logical)
            self.fullscreen = False
            return surface
        surface = pygame.display.set_mode(logical)
        self.fullscreen = False
        return surface

    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            self._events()
            self._update(dt)
            self._draw()
        self.audio.shutdown()
        pygame.quit()

    def _events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYUP:
                self.held.discard(event.key)
            elif event.type == pygame.KEYDOWN:
                # Celebrate skip
                if self.state == CELEBRATE_ST and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    self._begin_level()
                    continue
                self.held.add(event.key)
                self._keydown(event.key)

    def _keydown(self, key: int) -> None:
        if key in (pygame.K_m,):
            self.audio.toggle_mute()
            return
        if key == pygame.K_F11:
            self.fullscreen = not self.fullscreen
            self.screen = self._make_screen(fullscreen=self.fullscreen)
            return
        if key == pygame.K_q and self.state in (TITLE_ST, OVER_ST, PAUSE_ST):
            if self.state == PAUSE_ST:
                self.state = TITLE_ST
                self.audio.play("title")
                return
            self.running = False
            return

        if self.state == TITLE_ST:
            if key in (pygame.K_RETURN, pygame.K_SPACE):
                self.state = MODE_ST
            elif key == pygame.K_ESCAPE:
                self.running = False
            return
        if self.state == MODE_ST:
            if key in (pygame.K_UP, pygame.K_w, pygame.K_i):
                self.mode_index = (self.mode_index - 1) % len(MODES)
            elif key in (pygame.K_DOWN, pygame.K_s, pygame.K_k):
                self.mode_index = (self.mode_index + 1) % len(MODES)
            elif key in (pygame.K_RETURN, pygame.K_SPACE):
                self.start_run(MODES[self.mode_index])
            elif key == pygame.K_ESCAPE:
                self.state = TITLE_ST
                self.audio.play("title")
            return
        if self.state == INTRO_ST:
            if key in (pygame.K_SPACE, pygame.K_RETURN):
                self.state = PLAY_ST
            elif key == pygame.K_ESCAPE:
                self.state = PAUSE_ST
            return
        if self.state == PLAY_ST:
            if key == pygame.K_ESCAPE:
                self.state = PAUSE_ST
                return
            if key in (pygame.K_SPACE,):
                self._munch()
                return
            self._try_move_key(key)
            return
        if self.state == PAUSE_ST:
            if key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
                self.state = PLAY_ST
            return
        if self.state == CLEAR_ST:
            if key in (pygame.K_SPACE, pygame.K_RETURN):
                self._advance_from_clear()
            return
        if self.state == CELEBRATE_ST:
            if key in (pygame.K_SPACE, pygame.K_RETURN):
                self._begin_level()
            return
        if self.state == OVER_ST:
            if key in (pygame.K_SPACE, pygame.K_RETURN):
                self.start_run(self.selected_mode)
            elif key == pygame.K_ESCAPE:
                self.state = TITLE_ST
                self.audio.play("title")


    def _advance_from_clear(self) -> None:
        """Leave CLEAR_ST exactly once (timer or key)."""
        if self.state != CLEAR_ST:
            return
        cleared = self.level
        self.level += 1
        if is_celebration_level(cleared):
            self.state = CELEBRATE_ST
            self.banner_timer = 0.0
            self.celebrate_banner = banner_for_level(cleared)
            self.audio.play("celebrate")
        else:
            self._begin_level()

    def _try_move_key(self, key: int) -> None:
        mapping = {
            pygame.K_LEFT: (0, -1),
            pygame.K_a: (0, -1),
            pygame.K_j: (0, -1),
            pygame.K_RIGHT: (0, 1),
            pygame.K_d: (0, 1),
            pygame.K_l: (0, 1),
            pygame.K_UP: (-1, 0),
            pygame.K_w: (-1, 0),
            pygame.K_i: (-1, 0),
            pygame.K_DOWN: (1, 0),
            pygame.K_s: (1, 0),
            pygame.K_k: (1, 0),
        }
        step = mapping.get(key)
        if not step:
            return
        rows, cols = self._board_size()
        if self.player.try_step(*step, rows, cols):
            self.move_cool = MOVE_DELAY

    def _held_move(self) -> None:
        order = (
            (pygame.K_LEFT, pygame.K_a, pygame.K_j, 0, -1),
            (pygame.K_RIGHT, pygame.K_d, pygame.K_l, 0, 1),
            (pygame.K_UP, pygame.K_w, pygame.K_i, -1, 0),
            (pygame.K_DOWN, pygame.K_s, pygame.K_k, 1, 0),
        )
        for a, b, c, dr, dc in order:
            if a in self.held or b in self.held or c in self.held:
                rows, cols = self._board_size()
                if self.player.try_step(dr, dc, rows, cols):
                    self.move_cool = MOVE_DELAY
                return

    def _munch(self) -> None:
        if self.board is None or self.rule is None:
            return
        if not self.player.can_move():
            return
        cell = self.board.cell(self.player.row, self.player.col)
        if cell.munched:
            return
        self.player.chomp_timer = MUNCH_LOCK
        if self.rule.is_correct(cell.value):
            cell.munched = True
            self.score += 50 + self.level * 10
            self.audio.play("correct")
            if self.board.remaining_correct() == 0:
                self.score += 100 * self.level
                self.best = max(self.best, self.score)
                self.state = CLEAR_ST
                self.banner_timer = 0.0
                self.audio.play("level_clear")
        else:
            self.audio.play("wrong")
            self.flash_wrong = 0.35
            self._lose_life(from_troggle=False)

    def _lose_life(self, from_troggle: bool) -> None:
        self.lives -= 1
        self.best = max(self.best, self.score)
        if from_troggle:
            self.audio.play("hit")
        if self.lives <= 0:
            self.state = OVER_ST
            self.audio.play("game_over")
            return
        self.player.iframe_timer = HIT_IFRAMES
        self.freeze = TROGGLE_FREEZE
        rows, cols = self._board_size()
        occupied = {(t.row, t.col) for t in self.troggles}
        pr, pc = safe_player_spawn(occupied, self.rng, rows, cols)
        self.player.row, self.player.col = pr, pc

    def _update(self, dt: float) -> None:
        self.anim += dt
        self.flash_wrong = max(0.0, self.flash_wrong - dt)
        self.banner_timer += dt
        if self.state == CLEAR_ST:
            if self.banner_timer >= 1.2:
                self._advance_from_clear()
            return
        if self.state == CELEBRATE_ST:
            if self.banner_timer >= CELEBRATE_SECONDS:
                self._begin_level()
            return
        if self.state != PLAY_ST:
            return
        self.player.tick(dt)
        self.move_cool = max(0.0, self.move_cool - dt)
        self.freeze = max(0.0, self.freeze - dt)
        rows, cols = self._board_size()
        if self.move_cool <= 0:
            self._held_move()
        pack = tuple(self.troggles)
        if self.freeze <= 0:
            for troggle in self.troggles:
                troggle.update(dt, self.player.pos, self.rng, rows, cols, pack)
            self.troggles = apply_hunter_eats(self.troggles)
        else:
            for troggle in self.troggles:
                troggle.tick_specials(dt, self.player.pos, rows, cols)
        if not self.player.invulnerable():
            if player_hits_hazard(self.player.pos, self.troggles, rows, cols):
                self._lose_life(from_troggle=True)
        self.troggles = [t for t in self.troggles if not t.exploded]

    def _draw(self) -> None:
        self.screen.fill(BG)
        if self.state == TITLE_ST:
            self._draw_title()
        elif self.state == MODE_ST:
            self._draw_modes()
        elif self.state in (INTRO_ST, PLAY_ST, PAUSE_ST, CLEAR_ST, CELEBRATE_ST):
            self._draw_playfield()
            if self.state == INTRO_ST:
                self._draw_intro_overlay()
            elif self.state == PAUSE_ST:
                self._draw_pause()
            elif self.state == CLEAR_ST:
                self._draw_clear()
            elif self.state == CELEBRATE_ST:
                self._draw_celebrate()
        elif self.state == OVER_ST:
            self._draw_playfield()
            self._draw_game_over()
        pygame.display.flip()

    def _draw_hud(self) -> None:
        pygame.draw.rect(self.screen, HUD_BG, (0, 0, WINDOW_W, HUD_H))
        pygame.draw.rect(self.screen, (18, 70, 48), (0, HUD_H - 3, WINDOW_W, 3))
        draw_outlined_text(self.screen, f"SCORE {self.score:05d}", self.font_sm, GOLD, (120, 24))
        draw_outlined_text(self.screen, f"BEST {self.best:05d}", self.font_tiny, CREAM, (120, 48))
        rows, cols = self._board_size()
        draw_outlined_text(
            self.screen,
            f"LEVEL {self.level}  {rows}×{cols}",
            self.font_sm,
            CREAM,
            (WINDOW_W // 2, 24),
        )
        mode_name = MODE_LABELS.get(self.selected_mode, "")
        draw_outlined_text(self.screen, mode_name.upper(), self.font_tiny, CYAN, (WINDOW_W // 2, 48))

        lives_x = WINDOW_W - 210
        draw_outlined_text(self.screen, "LIVES", self.font_tiny, CREAM, (lives_x, 18))
        for i in range(START_LIVES):
            x = lives_x + 36 + i * 34
            color = YELLOW if i < self.lives else (50, 50, 40)
            pygame.draw.circle(self.screen, color, (x, 46), 10)
            pygame.draw.circle(self.screen, BLACK, (x, 46), 10, 2)

        mute = "MUTED" if self.audio.muted else ("NO AUDIO" if not self.audio.available else "M MUTE")
        mute_color = ORANGE if self.audio.muted or not self.audio.available else (140, 180, 150)
        draw_outlined_text(self.screen, mute, self.font_tiny, mute_color, (WINDOW_W - 70, 20))

        pygame.draw.rect(self.screen, RULE_BG, (0, HUD_H, WINDOW_W, RULE_H))
        rule_text = self.rule.title if self.rule else ""
        draw_outlined_text(self.screen, rule_text, self.font_md, WHITE, (WINDOW_W // 2, HUD_H + RULE_H // 2))

    def _draw_playfield(self) -> None:
        self._draw_hud()
        if self.board is None:
            return
        grid_left, grid_top, _grid_w, _grid_h = self._grid_geom()
        rows, cols = self.board.rows, self.board.cols
        flash = self.flash_wrong > 0 and int(self.anim * 16) % 2 == 0
        for r in range(rows):
            for c in range(cols):
                rect = cell_rect(r, c, grid_left, grid_top)
                cell = self.board.cell(r, c)
                if cell.munched:
                    fill = CELL_EMPTY
                else:
                    fill = CELL_BG_ALT if (r + c) % 2 else CELL_BG
                    if flash and (self.player.row, self.player.col) == (r, c):
                        fill = RED
                pygame.draw.rect(self.screen, fill, rect.inflate(-4, -4), border_radius=6)
                pygame.draw.rect(self.screen, CELL_BORDER, rect.inflate(-4, -4), 2, border_radius=6)
                if not cell.munched:
                    draw_outlined_text(
                        self.screen,
                        cell.label,
                        self.font_cell,
                        CREAM,
                        rect.center,
                    )

        self._draw_hazards(grid_left, grid_top, rows, cols)

        # Player highlight
        pref = cell_rect(self.player.row, self.player.col, grid_left, grid_top)
        pygame.draw.rect(self.screen, CELL_HL, pref.inflate(-2, -2), 3, border_radius=8)

        frame = int(self.anim * 6)
        show_player = not (self.player.invulnerable() and int(self.anim * 12) % 2 == 0)
        if show_player:
            hop = -6 if self.player.hop_timer > 0 else 0
            sprite = muncher_surface(
                frame,
                self.player.facing[0],
                self.player.chomp_timer > 0,
                self.player.invulnerable(),
            )
            dest = sprite.get_rect(center=(pref.centerx, pref.centery + hop + 8))
            self.screen.blit(sprite, dest)

        for troggle in self.troggles:
            trect = cell_rect(troggle.row, troggle.col, grid_left, grid_top)
            flash_t = troggle.is_telegraphing and int(self.anim * 10) % 2 == 0
            sprite = troggle_surface(troggle.kind, frame, troggle.heading[0], flash_t)
            dest = sprite.get_rect(center=(trect.centerx, trect.centery + 8))
            self.screen.blit(sprite, dest)

        pygame.draw.rect(self.screen, BG_DEEP, (0, WINDOW_H - HINT_H, WINDOW_W, HINT_H))
        hint = "ARROWS/WASD/IJKL move   SPACE munch   ESC pause   M mute   F11 window"
        draw_outlined_text(
            self.screen,
            hint,
            self.font_tiny,
            CREAM,
            (WINDOW_W // 2, WINDOW_H - HINT_H // 2),
        )

    def _draw_hazards(self, grid_left: int, grid_top: int, rows: int, cols: int) -> None:
        frame = int(self.anim * 8)
        for troggle in self.troggles:
            if troggle.kind == "fire" and (troggle.is_firing or troggle.is_winding_fire):
                fr, fc = troggle.front_cell()
                if not (0 <= fr < rows and 0 <= fc < cols):
                    continue
                rect = cell_rect(fr, fc, grid_left, grid_top)
                if troggle.is_firing:
                    glow = pygame.Surface(rect.inflate(-8, -8).size, pygame.SRCALPHA)
                    glow.fill((*EMBER, 90))
                    self.screen.blit(glow, rect.inflate(-8, -8).topleft)
                    flame = fire_surface(frame)
                    self.screen.blit(flame, flame.get_rect(center=(rect.centerx, rect.centery + 6)))
                else:
                    pygame.draw.rect(self.screen, FLAME, rect.inflate(-10, -10), 2, border_radius=6)
            if troggle.is_telegraphing:
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = troggle.row + dr, troggle.col + dc
                    if not (0 <= nr < rows and 0 <= nc < cols):
                        continue
                    rect = cell_rect(nr, nc, grid_left, grid_top)
                    pulse = 80 + int(70 * abs((self.anim * 8) % 2 - 1))
                    pygame.draw.rect(
                        self.screen,
                        (pulse, 60, 40),
                        rect.inflate(-8, -8),
                        3,
                        border_radius=6,
                    )

    def _dim(self, alpha: int = 170) -> None:
        veil = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
        veil.fill((0, 0, 0, alpha))
        self.screen.blit(veil, (0, 0))

    def _draw_ascii_block(
        self,
        lines: tuple[str, ...],
        font: pygame.font.Font,
        color: tuple[int, int, int],
        center_x: int,
        top_y: int,
        outlined: bool = False,
        line_gap: int = 1,
    ) -> int:
        line_h = font.get_height() + line_gap
        for i, line in enumerate(lines):
            y = top_y + i * line_h
            if outlined:
                draw_outlined_text(self.screen, line, font, color, (center_x, y))
            else:
                img = font.render(line, True, color)
                self.screen.blit(img, img.get_rect(center=(center_x, y)))
        return top_y + len(lines) * line_h

    def _draw_title(self) -> None:
        cx = WINDOW_W // 2
        y = self._draw_ascii_block(TITLE_BANNER, self.font_ascii, GOLD, cx, 58, outlined=True)
        y = self._draw_ascii_block(TITLE_DOODLE, self.font_doodle, CREAM, cx, y + 10)
        draw_outlined_text(self.screen, TAGLINE, self.font_sm, CREAM, (cx, y + 18))
        draw_outlined_text(self.screen, BLURB_A, self.font_sm, WHITE, (cx, y + 48))
        draw_outlined_text(self.screen, BLURB_B, self.font_sm, WHITE, (cx, y + 76))
        pulse = 180 + int(40 * abs((self.anim * 2) % 2 - 1))
        draw_outlined_text(self.screen, START_HINT, self.font_md, (pulse, pulse, 80), (cx, y + 126))
        m = muncher_surface(int(self.anim * 6), 1, int(self.anim * 2) % 4 == 0, False)
        self.screen.blit(m, m.get_rect(center=(cx, y + 196)))
        kinds = ("wander", "chase", "fire", "exploder", "hunter")
        frame = int(self.anim * 5)
        for i, kind in enumerate(kinds):
            sprite = troggle_surface(kind, frame, 1 if i % 2 == 0 else -1)
            x = cx + (i - 2) * 180
            self.screen.blit(sprite, sprite.get_rect(center=(x, y + 286)))
        draw_outlined_text(self.screen, CONTROLS_HINT, self.font_tiny, CREAM, (cx, WINDOW_H - 28))

    def _draw_modes(self) -> None:
        draw_outlined_text(self.screen, "CHOOSE A MODE", self.font_lg, GOLD, (WINDOW_W // 2, 90))
        for i, mode in enumerate(MODES):
            y = 180 + i * 70
            selected = i == self.mode_index
            label = MODE_LABELS[mode]
            color = YELLOW if selected else CREAM
            if selected:
                pygame.draw.rect(
                    self.screen,
                    (20, 80, 50),
                    pygame.Rect(180, y - 28, WINDOW_W - 360, 56),
                    border_radius=8,
                )
                pygame.draw.rect(
                    self.screen,
                    CELL_HL,
                    pygame.Rect(180, y - 28, WINDOW_W - 360, 56),
                    2,
                    border_radius=8,
                )
                draw_outlined_text(self.screen, "▶", self.font_md, GOLD, (220, y))
            draw_outlined_text(self.screen, label, self.font_md, color, (WINDOW_W // 2, y))
        blurb = MODE_BLURBS[MODES[self.mode_index]]
        draw_outlined_text(self.screen, blurb, self.font_sm, WHITE, (WINDOW_W // 2, 560))
        draw_outlined_text(
            self.screen,
            "↑↓ select    ENTER start    ESC back    M mute",
            self.font_tiny,
            CREAM,
            (WINDOW_W // 2, 660),
        )

    def _draw_intro_overlay(self) -> None:
        self._dim(150)
        draw_outlined_text(self.screen, "GET READY", self.font_lg, GOLD, (WINDOW_W // 2, 250))
        if self.rule:
            draw_outlined_text(self.screen, self.rule.title, self.font_xl, WHITE, (WINDOW_W // 2, 340))
        draw_outlined_text(
            self.screen,
            "Munch matching cells. Leave the rest.",
            self.font_sm,
            CREAM,
            (WINDOW_W // 2, 420),
        )
        draw_outlined_text(
            self.screen,
            "The board starts small and grows as you level up.",
            self.font_tiny,
            CREAM,
            (WINDOW_W // 2, 456),
        )
        draw_outlined_text(self.screen, "Press SPACE to start", self.font_md, YELLOW, (WINDOW_W // 2, 500))

    def _draw_pause(self) -> None:
        self._dim()
        draw_outlined_text(self.screen, "PAUSED", self.font_xl, GOLD, (WINDOW_W // 2, 300))
        mute = "Sound: muted" if self.audio.muted else "Sound: on"
        draw_outlined_text(self.screen, mute, self.font_sm, CREAM, (WINDOW_W // 2, 380))
        draw_outlined_text(
            self.screen,
            "ESC / SPACE resume     M mute     Q title",
            self.font_sm,
            WHITE,
            (WINDOW_W // 2, 450),
        )

    def _draw_clear(self) -> None:
        self._dim(140)
        draw_outlined_text(self.screen, "LEVEL CLEAR!", self.font_xl, GREEN, (WINDOW_W // 2, 300))
        draw_outlined_text(
            self.screen,
            f"Score {self.score}    Next: Level {self.level + 1}",
            self.font_sm,
            CREAM,
            (WINDOW_W // 2, 380),
        )
        draw_outlined_text(self.screen, "Press SPACE", self.font_md, YELLOW, (WINDOW_W // 2, 460))

    def _draw_game_over(self) -> None:
        self._dim()
        draw_outlined_text(self.screen, "GAME OVER", self.font_xl, RED, (WINDOW_W // 2, 280))
        draw_outlined_text(self.screen, f"Score  {self.score}", self.font_md, GOLD, (WINDOW_W // 2, 360))
        draw_outlined_text(self.screen, f"Reached level {self.level}", self.font_sm, CREAM, (WINDOW_W // 2, 410))
        draw_outlined_text(
            self.screen,
            "SPACE play again    ESC title    Q quit",
            self.font_sm,
            WHITE,
            (WINDOW_W // 2, 500),
        )



    def _start_celebrate(self) -> None:
        """Enter celebration (also used by smoke tests)."""
        self.state = CELEBRATE_ST
        self.banner_timer = 0.0
        self.celebrate_banner = banner_for_level(self.level if self.level % 3 == 0 else 3)
        self.confetti = list(range(48))
        self.audio.play("celebrate")

    def _finish_celebrate(self) -> None:
        """Leave celebration and start the next level."""
        if self.state != CELEBRATE_ST:
            return
        self.level += 1
        self._begin_level()

    def _draw_celebrate(self) -> None:
        overlay = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))
        # simple pixel confetti
        rng = random.Random(self.level * 17 + int(self.anim * 8))
        for _ in range(48):
            x = rng.randint(20, WINDOW_W - 20)
            y = rng.randint(80, WINDOW_H - 40)
            c = rng.choice((GOLD, CYAN, ORANGE, YELLOW, GREEN, RED))
            pygame.draw.rect(self.screen, c, (x, y, 6, 6))
        # bouncing muncher
        bounce = int(abs(__import__('math').sin(self.anim * 8)) * 18)
        sprite = muncher_surface(int(self.anim * 10) % 2, 1, True, False)
        rect = sprite.get_rect(center=(WINDOW_W // 2, WINDOW_H // 2 + 40 - bounce))
        self.screen.blit(sprite, rect)
        draw_outlined_text(self.screen, self.celebrate_banner, self.font_xl, GOLD, (WINDOW_W // 2, WINDOW_H // 2 - 60))
        draw_outlined_text(self.screen, "Space / Enter to continue", self.font_sm, CREAM, (WINDOW_W // 2, WINDOW_H - 70))


def main() -> None:
    pygame.mixer.pre_init(22050, -16, 1, 512)
    pygame.init()
    try:
        Game().run()
    except KeyboardInterrupt:
        pygame.quit()
        sys.exit(0)


if __name__ == "__main__":
    main()