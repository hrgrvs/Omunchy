"""Game loop, screens, and input. Sounds are wired into every gameplay beat."""

from __future__ import annotations

from dataclasses import dataclass
import math
import random
import sys

import pygame

from omunchy.audio import Audio, spawn_sound_name
from omunchy.board import Board, generate_board
from omunchy.constants import (
    BG,
    BG_DEEP,
    BLACK,
    CELL_BG,
    CELL_BG_ALT,
    CELL_BORDER,
    CELL_DIGIT,
    CELL_EMPTY,
    CELL_EMPTY_BORDER,
    CELL_HL,
    CREAM,
    CYAN,
    EAT_CORRECT,
    EAT_WRONG,
    EMBER,
    FLAME,
    FPS,
    GOLD,
    GREEN,
    grid_geometry,
    HERO_NAME,
    HINT_H,
    HIT_IFRAMES,
    HUD_BG,
    HUD_H,
    INTRO_DIM_ALPHA,
    MAX_COLS,
    MAX_ROWS,
    MODE_BLURBS,
    MODE_LABELS,
    MODES,
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
    FireField,
    IncomingTroggle,
    Muncher,
    Troggle,
    apply_hunter_eats,
    apply_ignitions,
    bounce_from_wander,
    look_toward,
    missing_roster_kinds,
    next_incoming,
    player_hits_hazard,
    safe_player_spawn,
    spawn_troggles,
    wander_at,
)
from omunchy.celebrate import CELEBRATE_SECONDS, banner_for_level, is_celebration_level
from omunchy.pairings import Carry, WRONG_PAIR_COSTS_LIFE, apply_pairings_space, restore_carry
from omunchy.rules import Rule, rule_for
from omunchy.progress import stable_rng
from omunchy.sprites import (
    cell_rect,
    draw_cell_digit,
    draw_outlined_text,
    eat_label_transform,
    fire_surface,
    muncher_surface,
    munchy_sprite_center,
    troggle_surface,
)
from omunchy.title_art import (
    BLURB_A,
    BLURB_B,
    CONTROLS_HINT,
    LICENSE_LINE,
    TAGLINE,
    draw_title_word,
)
from omunchy.bestiary import PAUSE_MENU, TITLE_MENU, TROGGLE_GUIDE
from omunchy.wearables import Outfit, Wearable, offer_wearables

TITLE_ST, MODE_ST, INTRO_ST, PLAY_ST, PAUSE_ST, CLEAR_ST, CELEBRATE_ST, WARDROBE_ST, BESTIARY_ST, OVER_ST = range(10)

# One KEYDOWN = one step. Never latch these behind a missed KEYUP (macOS).
DIRECTION_KEYS = frozenset(
    (
        pygame.K_LEFT,
        pygame.K_RIGHT,
        pygame.K_UP,
        pygame.K_DOWN,
        pygame.K_a,
        pygame.K_d,
        pygame.K_w,
        pygame.K_s,
        pygame.K_j,
        pygame.K_l,
        pygame.K_i,
        pygame.K_k,
    )
)
MOVE_KEYS: dict[int, tuple[int, int]] = {
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
_FOCUS_EVENT_TYPES = tuple(
    getattr(pygame, name)
    for name in (
        "WINDOWFOCUSLOST",
        "WINDOWFOCUSGAINED",
        "WINDOWMINIMIZED",
        "WINDOWRESTORED",
        "ACTIVEEVENT",
        "APP_WILLENTERBACKGROUND",
        "APP_DIDENTERFOREGROUND",
    )
    if hasattr(pygame, name)
)


def _is_os_key_repeat(event: pygame.event.Event) -> bool:
    """True for SDL hold-repeat KEYDOWNs. A real tap has repeat == 0."""
    return bool(getattr(event, "repeat", 0))


def _disable_text_input() -> None:
    """IME/text-input on macOS can swallow keys until the window is clicked."""
    stop = getattr(pygame.key, "stop_text_input", None)
    if stop is not None:
        stop()


@dataclass
class EatFx:
    """In-progress chomp: the digit dives into the mouth (or bounces back)."""

    label: str
    row: int
    col: int
    correct: bool
    age: float = 0.0
    duration: float = EAT_CORRECT
    pending_clear: bool = False
    pending_life: bool = False

    @property
    def progress(self) -> float:
        return 1.0 if self.duration <= 0 else min(1.0, self.age / self.duration)

    @property
    def done(self) -> bool:
        return self.age >= self.duration


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
        self.font_cell = _font(34, True)
        pygame.key.set_repeat()  # tap-only: no OS/pygame key-repeat stepping
        _disable_text_input()

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
        self.freeze = 0.0
        self.flash_wrong = 0.0
        self.banner_timer = 0.0
        self.celebrate_banner = "Nice!"
        self.confetti: list[int] = []
        self.anim = 0.0
        self.held: set[int] = set()
        self.outfit = Outfit()
        self.eat_fx: EatFx | None = None
        self.wear_choices: list[Wearable] = []
        self.wear_index = 0
        self.title_index = 0
        self.pause_index = 0
        self.bestiary_back = TITLE_ST
        self.carried: Carry | None = None
        self.fires = FireField()
        self.incoming: list[IncomingTroggle] = []
        self._spawn_cues: list[tuple[float, str]] = []

        self.audio.play("title")
        self.audio.play_bg()

    def start_run(self, mode: str) -> None:
        self.selected_mode = mode
        self.level = 1
        self.score = 0
        self.lives = START_LIVES
        self.outfit = Outfit()
        self.eat_fx = None
        self.carried = None
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
        self.rng = stable_rng("play", self.selected_mode, self.level)
        self.board = generate_board(self.rule, self.level, seed_key=self.selected_mode)
        rows, cols = self.board.rows, self.board.cols
        spawn_rng = stable_rng("spawn", self.selected_mode, self.level)
        occupied: set[tuple[int, int]] = set()
        pr, pc = safe_player_spawn(occupied, spawn_rng, rows, cols)
        self.player = Muncher(row=pr, col=pc)
        occupied.add((pr, pc))
        self.troggles = spawn_troggles(self.level, (pr, pc), spawn_rng, rows, cols)
        self.fires = FireField()
        self.incoming = []
        self._queue_spawn_cues([t.kind for t in self.troggles])
        self.freeze = 0.35
        self.flash_wrong = 0.0
        self.banner_timer = 0.0
        self.eat_fx = None
        self.carried = None
        self.state = INTRO_ST

    def _queue_spawn_cues(self, kinds: list[str]) -> None:
        """Stagger per-type warning cues so kids can tell who is arriving."""
        delay = 0.0
        seen: set[str] = set()
        cues: list[tuple[float, str]] = []
        for kind in kinds:
            if kind in seen:
                continue
            seen.add(kind)
            cues.append((delay, kind))
            delay += 0.16
        self._spawn_cues = cues

    def _tick_spawn_cues(self, dt: float) -> None:
        leftover: list[tuple[float, str]] = []
        for wait, kind in self._spawn_cues:
            wait -= dt
            if wait <= 0:
                self.audio.play(spawn_sound_name(kind))
            else:
                leftover.append((wait, kind))
        self._spawn_cues = leftover


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
            elif _FOCUS_EVENT_TYPES and event.type in _FOCUS_EVENT_TYPES:
                # macOS fullscreen / Cmd-Tab often drops KEYUP; don't keep a dead latch.
                self.held.clear()
            elif event.type == pygame.KEYUP:
                self.held.discard(event.key)
            elif event.type == pygame.KEYDOWN:
                if _is_os_key_repeat(event):
                    continue
                if event.key == pygame.K_ESCAPE:
                    # Escape always unsticks: clear a stale held set and handle the tap.
                    self.held.clear()
                    self._keydown(event.key)
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
            self.held.clear()
            pygame.key.set_repeat()
            _disable_text_input()
            pygame.event.pump()
            return
        if key == pygame.K_q and self.state in (TITLE_ST, OVER_ST, PAUSE_ST):
            if self.state == PAUSE_ST:
                self.state = TITLE_ST
                self.audio.play("title")
                return
            self.running = False
            return

        if self.state == TITLE_ST:
            if key in (pygame.K_LEFT, pygame.K_a, pygame.K_j, pygame.K_UP, pygame.K_w, pygame.K_i):
                self.title_index = (self.title_index - 1) % len(TITLE_MENU)
            elif key in (pygame.K_RIGHT, pygame.K_d, pygame.K_l, pygame.K_DOWN, pygame.K_s, pygame.K_k):
                self.title_index = (self.title_index + 1) % len(TITLE_MENU)
            elif key == pygame.K_t:
                self._open_bestiary(TITLE_ST)
            elif key in (pygame.K_RETURN, pygame.K_SPACE):
                if TITLE_MENU[self.title_index] == "Troggles":
                    self._open_bestiary(TITLE_ST)
                else:
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
                self.pause_index = 0
                self.state = PAUSE_ST
            return
        if self.state == PLAY_ST:
            if key == pygame.K_ESCAPE:
                self.pause_index = 0
                self.state = PAUSE_ST
                return
            if key in (pygame.K_SPACE,):
                self._munch()
                return
            self._try_move_key(key)
            return
        if self.state == PAUSE_ST:
            if key in (pygame.K_UP, pygame.K_w, pygame.K_i):
                self.pause_index = (self.pause_index - 1) % len(PAUSE_MENU)
            elif key in (pygame.K_DOWN, pygame.K_s, pygame.K_k):
                self.pause_index = (self.pause_index + 1) % len(PAUSE_MENU)
            elif key == pygame.K_t:
                self._open_bestiary(PAUSE_ST)
            elif key in (pygame.K_RETURN, pygame.K_SPACE):
                self._pause_confirm()
            elif key == pygame.K_ESCAPE:
                self.state = PLAY_ST
            return
        if self.state == BESTIARY_ST:
            if key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE, pygame.K_t, pygame.K_q):
                self._close_bestiary()
            return
        if self.state == CLEAR_ST:
            if key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_ESCAPE):
                self._advance_from_clear()
            return
        if self.state == CELEBRATE_ST:
            if key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_ESCAPE):
                self._open_wardrobe()
            return
        if self.state == WARDROBE_ST:
            if key in (pygame.K_LEFT, pygame.K_a, pygame.K_j, pygame.K_UP, pygame.K_w, pygame.K_i):
                self.wear_index = (self.wear_index - 1) % max(1, len(self.wear_choices))
            elif key in (pygame.K_RIGHT, pygame.K_d, pygame.K_l, pygame.K_DOWN, pygame.K_s, pygame.K_k):
                self.wear_index = (self.wear_index + 1) % max(1, len(self.wear_choices))
            elif key in (pygame.K_RETURN, pygame.K_SPACE):
                self._apply_wear_choice(skip=False)
            elif key == pygame.K_ESCAPE:
                self._apply_wear_choice(skip=True)
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
        step = MOVE_KEYS.get(key)
        if not step:
            return
        rows, cols = self._board_size()
        # Chomp is visual lock for munch only — a legal direction tap always steps.
        self.player.try_step(*step, rows, cols, ignore_chomp=True)

    def _munch(self) -> None:
        if self.board is None or self.rule is None:
            return
        if not self.player.can_move():
            return
        if self.eat_fx is not None and not self.eat_fx.done:
            return
        if self.rule.mode == "pairings":
            self._pairings_space()
            return
        cell = self.board.cell(self.player.row, self.player.col)
        if cell.munched:
            return
        correct = self.rule.is_correct(cell.value)
        duration = EAT_CORRECT if correct else EAT_WRONG
        self.player.chomp_timer = max(MUNCH_LOCK, duration)
        if correct:
            cell.munched = True
            self.score += 50 + self.level * 10
            self.audio.play("correct")
            pending_clear = self.board.remaining_correct() == 0
            self.eat_fx = EatFx(
                label=cell.label,
                row=cell.row,
                col=cell.col,
                correct=True,
                duration=duration,
                pending_clear=pending_clear,
            )
        else:
            self.audio.play("wrong")
            self.flash_wrong = 0.35
            self.eat_fx = EatFx(
                label=cell.label,
                row=cell.row,
                col=cell.col,
                correct=False,
                duration=duration,
                pending_life=True,
            )

    def _pairings_space(self) -> None:
        """Grab, drop, or eat a pair. Wrong pairs drop the carry (no life)."""
        assert self.board is not None and self.rule is not None
        result = apply_pairings_space(self.board, self.carried, self.player.row, self.player.col)
        self.carried = result.carry
        if result.kind == "noop":
            return
        if result.kind == "grab":
            self.player.hop_timer = 0.12
            return
        if result.kind == "drop":
            self.player.hop_timer = 0.12
            return
        duration = EAT_CORRECT if result.kind == "eat_ok" else EAT_WRONG
        self.player.chomp_timer = max(MUNCH_LOCK, duration)
        if result.kind == "eat_ok":
            self.score += 50 + self.level * 10
            self.audio.play("correct")
            self.eat_fx = EatFx(
                label=result.eat_label,
                row=result.eat_row,
                col=result.eat_col,
                correct=True,
                duration=duration,
                pending_clear=result.pending_clear,
            )
            return
        self.audio.play("wrong")
        self.flash_wrong = 0.35
        self.eat_fx = EatFx(
            label=result.eat_label,
            row=result.eat_row,
            col=result.eat_col,
            correct=False,
            duration=duration,
            pending_life=WRONG_PAIR_COSTS_LIFE,
        )

    def _finish_eat(self) -> None:
        fx = self.eat_fx
        self.eat_fx = None
        if fx is None:
            return
        if fx.pending_clear:
            self.score += 100 * self.level
            self.best = max(self.best, self.score)
            self.state = CLEAR_ST
            self.banner_timer = 0.0
            self.audio.play("level_clear")
            return
        if fx.pending_life:
            self._lose_life(from_troggle=False)

    def _lose_life(self, from_troggle: bool) -> None:
        if self.board is not None and self.carried is not None:
            restore_carry(self.board, self.carried)
            self.carried = None
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
        occupied |= self.fires.cells()
        occupied |= {(inc.row, inc.col) for inc in self.incoming}
        pr, pc = safe_player_spawn(occupied, self.rng, rows, cols)
        self.player.row, self.player.col = pr, pc
        self.player.prev_row, self.player.prev_col = pr, pc

    def _update(self, dt: float) -> None:
        self.anim += dt
        self.flash_wrong = max(0.0, self.flash_wrong - dt)
        self.banner_timer += dt
        if self.state in (INTRO_ST, PLAY_ST):
            self._tick_spawn_cues(dt)
        if self.state == CLEAR_ST:
            if self.banner_timer >= 1.2:
                self._advance_from_clear()
            return
        if self.state == CELEBRATE_ST:
            if self.banner_timer >= CELEBRATE_SECONDS:
                self._open_wardrobe()
            return
        if self.state != PLAY_ST:
            return
        if self.eat_fx is not None:
            self.eat_fx.age += dt
            if self.eat_fx.done:
                self._finish_eat()
                if self.state != PLAY_ST:
                    return
        self.player.tick(dt)
        self.freeze = max(0.0, self.freeze - dt)
        rows, cols = self._board_size()
        pack = tuple(self.troggles)
        if self.freeze <= 0:
            for troggle in self.troggles:
                troggle.update(dt, self.player.pos, self.rng, rows, cols, pack)
            self.troggles = apply_hunter_eats(self.troggles)
        else:
            for troggle in self.troggles:
                troggle.tick_specials(dt, self.player.pos, rows, cols)
        apply_ignitions(self.troggles, self.fires, rows, cols)
        self.fires.tick(dt)
        wanderer = wander_at(self.player.pos, self.troggles)
        if wanderer is not None:
            bounce_from_wander(self.player, wanderer, rows, cols)
        if not self.player.invulnerable():
            if player_hits_hazard(self.player.pos, self.troggles, rows, cols, self.fires):
                self._lose_life(from_troggle=True)
        self.troggles = [t for t in self.troggles if not t.exploded]
        self._refill_troggles()
        self._tick_incoming(dt)

    def _refill_troggles(self) -> None:
        """Queue replacements (with a warning cue) when the roster is short."""
        rows, cols = self._board_size()
        missing = missing_roster_kinds(
            self.level,
            rows,
            cols,
            [t.kind for t in self.troggles],
            [inc.kind for inc in self.incoming],
        )
        if not missing:
            return
        occupied = {(t.row, t.col) for t in self.troggles}
        occupied |= {(inc.row, inc.col) for inc in self.incoming}
        occupied |= self.fires.cells()
        occupied.add(self.player.pos)
        for kind in missing:
            incoming = next_incoming(
                kind,
                self.level,
                self.player.pos,
                occupied,
                self.rng,
                rows,
                cols,
            )
            if incoming is None:
                continue
            occupied.add((incoming.row, incoming.col))
            self.incoming.append(incoming)
            self.audio.play(spawn_sound_name(kind))

    def _tick_incoming(self, dt: float) -> None:
        ready: list[IncomingTroggle] = []
        waiting: list[IncomingTroggle] = []
        for inc in self.incoming:
            inc.warn -= dt
            if inc.warn <= 0:
                ready.append(inc)
            else:
                waiting.append(inc)
        self.incoming = waiting
        for i, inc in enumerate(ready):
            self.troggles.append(inc.to_troggle(i))

    def _draw(self) -> None:
        self.screen.fill(BG)
        if self.state == TITLE_ST:
            self._draw_title()
        elif self.state == MODE_ST:
            self._draw_modes()
        elif self.state == WARDROBE_ST:
            self._draw_wardrobe()
        elif self.state == BESTIARY_ST:
            self._draw_bestiary()
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
        if self.carried is not None:
            draw_outlined_text(
                self.screen,
                f"holding {self.carried.label}",
                self.font_sm,
                GOLD,
                (WINDOW_W - 140, HUD_H + RULE_H // 2),
            )

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
                    border = CELL_EMPTY_BORDER
                else:
                    fill = CELL_BG_ALT if (r + c) % 2 else CELL_BG
                    border = CELL_BORDER
                    if flash and (self.player.row, self.player.col) == (r, c):
                        fill = RED
                pygame.draw.rect(self.screen, fill, rect.inflate(-4, -4), border_radius=6)
                pygame.draw.rect(self.screen, border, rect.inflate(-4, -4), 2, border_radius=6)
                eating_here = (
                    self.eat_fx is not None
                    and self.eat_fx.row == r
                    and self.eat_fx.col == c
                )
                if not cell.munched and not eating_here:
                    draw_cell_digit(
                        self.screen,
                        cell.label,
                        self.font_cell,
                        CELL_DIGIT,
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
            chomping = self.player.chomp_timer > 0 or (
                self.eat_fx is not None and not self.eat_fx.done
            )
            standing = self.board.cell(self.player.row, self.player.col)
            # Open mouth over an unmunched number so kids can still read it.
            peeking = (not chomping) and (not standing.munched)
            sprite = muncher_surface(
                frame,
                self.player.facing[0],
                chomping,
                self.player.invulnerable(),
                self.outfit,
                peeking=peeking,
            )
            dest = sprite.get_rect(center=munchy_sprite_center(pref.center, hop))
            self.screen.blit(sprite, dest)
            if peeking:
                # Digit is wider than the 56px sprite (equals-mode expressions).
                # Redraw on top so the number is never covered, mouth hole behind.
                draw_cell_digit(
                    self.screen,
                    standing.label,
                    self.font_cell,
                    CELL_DIGIT,
                    pref.center,
                )
            if self.carried is not None:
                self._draw_carried_badge(pref, hop)
        self._draw_eat_fx(grid_left, grid_top)

        for inc in self.incoming:
            irect = cell_rect(inc.row, inc.col, grid_left, grid_top)
            pulse = 80 + int(70 * abs((self.anim * 8) % 2 - 1))
            pygame.draw.rect(self.screen, (pulse, pulse, 40), irect.inflate(-8, -8), 3, border_radius=6)
            ghost = troggle_surface(inc.kind, frame, inc.heading[0])
            ghost.set_alpha(110)
            self.screen.blit(ghost, ghost.get_rect(midbottom=(irect.centerx, irect.bottom - 4)))

        for troggle in self.troggles:
            trect = cell_rect(troggle.row, troggle.col, grid_left, grid_top)
            flash_t = troggle.is_telegraphing and int(self.anim * 10) % 2 == 0
            look_x = look_y = 0
            if troggle.kind == "chase":
                look_x, look_y = look_toward(troggle.pos, self.player.pos)
            sprite = troggle_surface(
                troggle.kind,
                frame,
                troggle.heading[0],
                flash_t,
                look_x,
                look_y,
            )
            dest = sprite.get_rect(midbottom=(trect.centerx, trect.bottom - 4))
            self.screen.blit(sprite, dest)

        pygame.draw.rect(self.screen, BG_DEEP, (0, WINDOW_H - HINT_H, WINDOW_W, HINT_H))
        space = "SPACE grab / pair" if self.rule and self.rule.mode == "pairings" else "SPACE munch"
        hint = f"ARROWS/WASD/IJKL tap to move   {space}   ESC pause / leave a screen   M mute   F11 window"
        draw_outlined_text(
            self.screen,
            hint,
            self.font_tiny,
            CREAM,
            (WINDOW_W // 2, WINDOW_H - HINT_H // 2),
        )

    def _draw_hazards(self, grid_left: int, grid_top: int, rows: int, cols: int) -> None:
        frame = int(self.anim * 8)
        burning = self.fires.cells()
        for row, col in burning:
            rect = cell_rect(row, col, grid_left, grid_top)
            glow = pygame.Surface(rect.inflate(-8, -8).size, pygame.SRCALPHA)
            glow.fill((*EMBER, 90))
            self.screen.blit(glow, rect.inflate(-8, -8).topleft)
            flame = fire_surface(frame)
            self.screen.blit(flame, flame.get_rect(center=(rect.centerx, rect.centery + 6)))
        for troggle in self.troggles:
            if troggle.kind == "fire" and troggle.is_winding_fire:
                fr, fc = troggle.front_cell()
                if not (0 <= fr < rows and 0 <= fc < cols) or (fr, fc) in burning:
                    continue
                rect = cell_rect(fr, fc, grid_left, grid_top)
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

    def _draw_carried_badge(self, pref: pygame.Rect, hop: int) -> None:
        """Carried digit sits above Munchy — never inside the open mouth."""
        if self.carried is None:
            return
        label = self.carried.label
        cx = pref.centerx + (22 if self.player.facing[0] >= 0 else -22)
        cy = pref.top + hop + 6
        cy = max(HUD_H + RULE_H + 14, cy)
        # Pill wide enough for 3-digit addends (900) so digits stay readable.
        img = self.font_sm.render(label, True, WHITE)
        box = img.get_rect()
        box.inflate_ip(16, 8)
        box.center = (cx, cy)
        pygame.draw.rect(self.screen, (12, 36, 28), box, border_radius=8)
        pygame.draw.rect(self.screen, GOLD, box, 2, border_radius=8)
        draw_outlined_text(self.screen, label, self.font_sm, WHITE, box.center)

    def _draw_eat_fx(self, grid_left: int, grid_top: int) -> None:
        fx = self.eat_fx
        if fx is None or fx.done:
            return
        rect = cell_rect(fx.row, fx.col, grid_left, grid_top)
        dx, dy, scale, alpha = eat_label_transform(fx.progress, fx.correct)
        color = GREEN if fx.correct else RED
        img = self.font_cell.render(fx.label, True, color)
        if scale != 1.0:
            w = max(2, int(img.get_width() * scale))
            h = max(2, int(img.get_height() * max(0.35, scale * (0.7 if fx.correct else 1.0))))
            img = pygame.transform.scale(img, (w, h))
        img.set_alpha(max(0, min(255, int(255 * alpha))))
        dest = img.get_rect(center=(rect.centerx + int(dx), rect.centery + int(dy)))
        self.screen.blit(img, dest)

    def _draw_title(self) -> None:
        cx = WINDOW_W // 2
        y = draw_title_word(self.screen, self.anim, cx, 64)
        draw_outlined_text(self.screen, TAGLINE, self.font_sm, CREAM, (cx, y + 28))
        draw_outlined_text(self.screen, BLURB_A, self.font_sm, WHITE, (cx, y + 62))
        draw_outlined_text(self.screen, BLURB_B, self.font_sm, WHITE, (cx, y + 90))
        for i, label in enumerate(TITLE_MENU):
            selected = i == self.title_index
            px = cx - 140 + i * 280
            box = pygame.Rect(px - 110, y + 118, 220, 48)
            pygame.draw.rect(self.screen, (20, 80, 50) if selected else (10, 40, 28), box, border_radius=8)
            pygame.draw.rect(self.screen, CELL_HL if selected else CELL_BORDER, box, 2, border_radius=8)
            color = YELLOW if selected else CREAM
            draw_outlined_text(self.screen, label, self.font_md, color, (px, y + 142))
        m = muncher_surface(int(self.anim * 6), 1, int(self.anim * 2) % 4 == 0, False)
        self.screen.blit(m, m.get_rect(center=(cx, y + 210)))
        kinds = ("wander", "chase", "fire", "exploder", "hunter")
        frame = int(self.anim * 5)
        for i, kind in enumerate(kinds):
            look_x = look_y = 0
            if kind == "chase":
                # Parade sits under Munchy — pupils glance up at him.
                look_y = -1
            sprite = troggle_surface(kind, frame, 1 if i % 2 == 0 else -1, look_x=look_x, look_y=look_y)
            x = cx + (i - 2) * 180
            self.screen.blit(sprite, sprite.get_rect(center=(x, y + 300)))
        draw_outlined_text(self.screen, LICENSE_LINE, self.font_tiny, CREAM, (cx, WINDOW_H - 48))
        draw_outlined_text(self.screen, CONTROLS_HINT, self.font_tiny, CREAM, (cx, WINDOW_H - 24))

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
        self._dim(INTRO_DIM_ALPHA)
        draw_outlined_text(self.screen, "GET READY", self.font_lg, GOLD, (WINDOW_W // 2, 250))
        if self.rule:
            draw_outlined_text(self.screen, self.rule.title, self.font_xl, WHITE, (WINDOW_W // 2, 340))
        if self.rule and self.rule.mode == "pairings":
            how = f"Grab one number (Space), then have {HERO_NAME} eat it with a partner that makes the target."
            extra = "A wrong pair drops what you were carrying — you keep your lives."
        else:
            how = f"Steer {HERO_NAME}. Munch matching cells. Leave the rest."
            extra = "The board starts small and grows as you level up."
        draw_outlined_text(
            self.screen,
            how,
            self.font_sm,
            CREAM,
            (WINDOW_W // 2, 420),
        )
        draw_outlined_text(
            self.screen,
            extra,
            self.font_tiny,
            CREAM,
            (WINDOW_W // 2, 456),
        )
        draw_outlined_text(
            self.screen,
            "SPACE / ENTER start    ESC pause",
            self.font_md,
            YELLOW,
            (WINDOW_W // 2, 500),
        )

    def _draw_pause(self) -> None:
        self._dim()
        draw_outlined_text(self.screen, "PAUSED", self.font_xl, GOLD, (WINDOW_W // 2, 200))
        mute = "Sound: muted" if self.audio.muted else "Sound: on"
        draw_outlined_text(self.screen, mute, self.font_tiny, CREAM, (WINDOW_W // 2, 258))
        for i, label in enumerate(PAUSE_MENU):
            y = 320 + i * 64
            selected = i == self.pause_index
            box = pygame.Rect(WINDOW_W // 2 - 180, y - 24, 360, 50)
            pygame.draw.rect(self.screen, (20, 80, 50) if selected else (10, 40, 28), box, border_radius=8)
            pygame.draw.rect(self.screen, CELL_HL if selected else CELL_BORDER, box, 2, border_radius=8)
            if selected:
                draw_outlined_text(self.screen, "▶", self.font_md, GOLD, (WINDOW_W // 2 - 150, y))
            draw_outlined_text(
                self.screen,
                label,
                self.font_md,
                YELLOW if selected else CREAM,
                (WINDOW_W // 2, y),
            )
        draw_outlined_text(
            self.screen,
            "↑↓ select    ENTER    ESC resume    T Troggles    Q title",
            self.font_tiny,
            WHITE,
            (WINDOW_W // 2, 540),
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
        draw_outlined_text(
            self.screen,
            "SPACE / ENTER / ESC continue",
            self.font_md,
            YELLOW,
            (WINDOW_W // 2, 460),
        )

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
        """Leave celebration (used by smoke tests) and open the wearable pick."""
        if self.state != CELEBRATE_ST:
            return
        self.level += 1
        self._open_wardrobe()

    def _open_bestiary(self, back: int) -> None:
        self.bestiary_back = back
        self.state = BESTIARY_ST

    def _close_bestiary(self) -> None:
        self.state = self.bestiary_back
        if self.state == TITLE_ST:
            self.audio.play("title")

    def _pause_confirm(self) -> None:
        choice = PAUSE_MENU[self.pause_index]
        if choice == "Troggles":
            self._open_bestiary(PAUSE_ST)
        elif choice == "Title":
            self.state = TITLE_ST
            self.audio.play("title")
        else:
            self.state = PLAY_ST

    def _draw_bestiary(self) -> None:
        cx = WINDOW_W // 2
        draw_outlined_text(self.screen, "TROGGLES", self.font_lg, GOLD, (cx, 48))
        draw_outlined_text(
            self.screen,
            "Meet the five Troggle types. They unlock as you level up.",
            self.font_tiny,
            CREAM,
            (cx, 88),
        )
        frame = int(self.anim * 6)
        for i, (kind, name, blurb) in enumerate(TROGGLE_GUIDE):
            y = 128 + i * 108
            box = pygame.Rect(80, y, WINDOW_W - 160, 98)
            pygame.draw.rect(self.screen, (10, 40, 28), box, border_radius=10)
            pygame.draw.rect(self.screen, CELL_BORDER, box, 2, border_radius=10)
            look_x = look_y = 0
            if kind == "chase":
                look_x = 1
            sprite = troggle_surface(kind, frame, 1 if i % 2 == 0 else -1, look_x=look_x, look_y=look_y)
            self.screen.blit(sprite, sprite.get_rect(center=(150, y + 49)))
            draw_outlined_text(self.screen, name, self.font_md, YELLOW, (430, y + 32))
            draw_outlined_text(self.screen, blurb, self.font_sm, WHITE, (430, y + 68))
        back = "ESC back to pause" if self.bestiary_back == PAUSE_ST else "ESC back to title"
        draw_outlined_text(self.screen, f"{back}    ENTER / T close", self.font_tiny, CREAM, (cx, WINDOW_H - 28))

    def _open_wardrobe(self) -> None:
        """Short list of wearables after a celebration / every ~3 levels."""
        if self.state not in (CELEBRATE_ST, CLEAR_ST, WARDROBE_ST):
            # Allow tests to jump here after bumping the level.
            pass
        choices = offer_wearables(
            self.selected_mode,
            self.level,
            self.outfit.ids(),
            frozenset(self.outfit.slots),
        )
        if not choices:
            self._begin_level()
            return
        self.wear_choices = list(choices)
        self.wear_index = 0
        self.state = WARDROBE_ST

    def _apply_wear_choice(self, skip: bool = False) -> None:
        if not skip and self.wear_choices:
            self.outfit.wear(self.wear_choices[self.wear_index])
        self._begin_level()

    def _draw_wardrobe(self) -> None:
        cx = WINDOW_W // 2
        draw_outlined_text(self.screen, "NEW GEAR!", self.font_lg, GOLD, (cx, 70))
        draw_outlined_text(
            self.screen,
            "Pick one thing to wear. One per spot — a new hat replaces the old hat.",
            self.font_tiny,
            CREAM,
            (cx, 118),
        )
        n = max(1, len(self.wear_choices))
        gap = min(260, 1080 // n)
        start_x = cx - (n - 1) * gap // 2
        for i, item in enumerate(self.wear_choices):
            x = start_x + i * gap
            selected = i == self.wear_index
            box = pygame.Rect(x - 110, 170, 220, 340)
            pygame.draw.rect(self.screen, (20, 80, 50) if selected else (10, 40, 28), box, border_radius=12)
            pygame.draw.rect(
                self.screen,
                CELL_HL if selected else CELL_BORDER,
                box,
                3 if selected else 2,
                border_radius=12,
            )
            preview = self.outfit.copy()
            preview.wear(item)
            sprite = muncher_surface(int(self.anim * 6), 1, False, False, preview)
            self.screen.blit(sprite, sprite.get_rect(center=(x, 280)))
            draw_outlined_text(self.screen, item.name, self.font_sm, WHITE if selected else CREAM, (x, 360))
            draw_outlined_text(
                self.screen,
                item.category.replace("mustache", "stache"),
                self.font_tiny,
                GOLD if selected else CREAM,
                (x, 392),
            )
            draw_outlined_text(
                self.screen,
                f"wears on {item.slot}",
                self.font_tiny,
                CREAM,
                (x, 420),
            )
            if selected:
                draw_outlined_text(self.screen, "▶", self.font_md, GOLD, (x, 455))
        worn = ", ".join(w.name for w in self.outfit.resolve()) or "nothing yet"
        draw_outlined_text(self.screen, f"Wearing: {worn}", self.font_tiny, CYAN, (cx, 540))
        draw_outlined_text(
            self.screen,
            "←→ / IJKL pick    ENTER wear it    ESC skip",
            self.font_sm,
            WHITE,
            (cx, 600),
        )
        draw_outlined_text(
            self.screen,
            "You can stack a hat, cape, glasses, mustache, cane, and shoes.",
            self.font_tiny,
            CREAM,
            (cx, 640),
        )

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
        # bouncing Munchy
        bounce = int(abs(math.sin(self.anim * 8)) * 18)
        sprite = muncher_surface(int(self.anim * 10) % 2, 1, True, False, self.outfit)
        rect = sprite.get_rect(center=(WINDOW_W // 2, WINDOW_H // 2 + 40 - bounce))
        self.screen.blit(sprite, rect)
        draw_outlined_text(self.screen, self.celebrate_banner, self.font_xl, GOLD, (WINDOW_W // 2, WINDOW_H // 2 - 60))
        draw_outlined_text(
            self.screen,
            "SPACE / ENTER / ESC continue",
            self.font_sm,
            CREAM,
            (WINDOW_W // 2, WINDOW_H - 70),
        )


def main() -> None:
    from omunchy.update import maybe_update_and_reexec

    maybe_update_and_reexec()
    pygame.mixer.pre_init(22050, -16, 1, 512)
    pygame.init()
    try:
        Game().run()
    except KeyboardInterrupt:
        pygame.quit()
        sys.exit(0)


if __name__ == "__main__":
    main()