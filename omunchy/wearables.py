"""Run-only wearable cosmetics: a big catalog, short kid-friendly pick lists.

Rule: one item per slot. A new pick in that slot replaces the old one; other
slots stay. Stack a hat, cape, glasses, mustache, cane, and shoes together.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from omunchy.progress import stable_rng

# Slot: one piece of gear at a time. Hats and crowns share the head.
SLOTS = ("head", "eyes", "mouth", "cape", "hand", "feet")
SLOT_LABELS = {
    "head": "head",
    "eyes": "eyes",
    "mouth": "mustache",
    "cape": "cape",
    "hand": "cane",
    "feet": "shoes",
}
CATEGORIES = ("cape", "hat", "crown", "mustache", "cane", "glasses", "monocle", "shoes")
CATEGORY_SLOT = {
    "cape": "cape",
    "hat": "head",
    "crown": "head",
    "mustache": "mouth",
    "cane": "hand",
    "glasses": "eyes",
    "monocle": "eyes",
    "shoes": "feet",
}

OFFER_COUNT = 4
REWARD_EVERY = 3


@dataclass(frozen=True)
class Wearable:
    id: str
    name: str
    category: str
    variant: int
    primary: tuple[int, int, int]
    accent: tuple[int, int, int]

    @property
    def slot(self) -> str:
        return CATEGORY_SLOT[self.category]


def _item(
    category: str,
    slug: str,
    name: str,
    variant: int,
    primary: tuple[int, int, int],
    accent: tuple[int, int, int],
) -> Wearable:
    return Wearable(f"{category}-{slug}", name, category, variant, primary, accent)


# Distinct palettes — bright, kid-friendly, readable on the dark arcade board.
RED = (220, 56, 56)
CRIMSON = (168, 24, 40)
BLUE = (56, 120, 236)
NAVY = (24, 56, 140)
GREEN = (48, 196, 88)
FOREST = (16, 110, 52)
GOLD = (244, 200, 48)
AMBER = (196, 140, 24)
PURPLE = (164, 80, 220)
PLUM = (96, 36, 140)
PINK = (236, 120, 180)
ROSE = (196, 48, 110)
CYAN = (64, 212, 212)
TEAL = (16, 132, 140)
ORANGE = (236, 132, 36)
RUST = (176, 72, 16)
WHITE = (244, 244, 236)
SILVER = (188, 196, 204)
BROWN = (140, 84, 40)
TAN = (212, 168, 104)
BLACK = (28, 28, 32)
LIME = (168, 228, 48)
SKY = (120, 196, 255)
MINT = (140, 236, 188)
CORAL = (255, 128, 112)
VIOLET = (120, 88, 255)


def _build_catalog() -> tuple[Wearable, ...]:
    items: list[Wearable] = []

    # Capes — long / short / star / striped shapes × colors.
    capes = (
        ("ruby", "Ruby Cape", 0, RED, CRIMSON),
        ("sky", "Sky Cape", 0, BLUE, SKY),
        ("leaf", "Leaf Cape", 0, GREEN, LIME),
        ("royal", "Royal Cape", 1, PURPLE, GOLD),
        ("sunset", "Sunset Cape", 1, ORANGE, PINK),
        ("night", "Night Cape", 1, NAVY, SILVER),
        ("star", "Star Cape", 2, NAVY, GOLD),
        ("rainbow", "Rainbow Cape", 2, PINK, CYAN),
        ("mint", "Mint Cape", 2, MINT, TEAL),
        ("gold", "Gold Cape", 3, GOLD, AMBER),
        ("stripe-red", "Candy Cape", 3, RED, WHITE),
        ("stripe-blue", "Banner Cape", 3, BLUE, WHITE),
    )
    items.extend(_item("cape", s, n, v, p, a) for s, n, v, p, a in capes)

    # Hats — cap / beanie / tall / brim / propeller.
    hats = (
        ("red-cap", "Red Cap", 0, RED, WHITE),
        ("blue-cap", "Blue Cap", 0, BLUE, WHITE),
        ("green-cap", "Green Cap", 0, GREEN, WHITE),
        ("orange-cap", "Orange Cap", 0, ORANGE, GOLD),
        ("beanie-purple", "Purple Beanie", 1, PURPLE, GOLD),
        ("beanie-pink", "Pink Beanie", 1, PINK, WHITE),
        ("beanie-lime", "Lime Beanie", 1, LIME, FOREST),
        ("top-black", "Top Hat", 2, BLACK, GOLD),
        ("top-stripe", "Magic Hat", 2, PURPLE, GOLD),
        ("wizard", "Wizard Hat", 2, NAVY, GOLD),
        ("cowboy", "Cowboy Hat", 3, BROWN, TAN),
        ("sailor", "Sailor Hat", 3, WHITE, BLUE),
        ("propeller", "Propeller Hat", 4, CYAN, RED),
        ("party", "Party Hat", 4, PINK, GOLD),
        ("winter", "Winter Hat", 1, SKY, WHITE),
    )
    items.extend(_item("hat", s, n, v, p, a) for s, n, v, p, a in hats)

    # Crowns — 3-point / 5-point / flower / star.
    crowns = (
        ("gold", "Gold Crown", 0, GOLD, AMBER),
        ("silver", "Silver Crown", 0, SILVER, WHITE),
        ("ruby", "Ruby Crown", 0, GOLD, RED),
        ("leaf", "Leaf Crown", 1, GREEN, GOLD),
        ("flower", "Flower Crown", 1, PINK, GREEN),
        ("star", "Star Crown", 2, GOLD, CYAN),
        ("rainbow", "Rainbow Crown", 2, PINK, GOLD),
        ("paper", "Paper Crown", 3, ORANGE, GOLD),
        ("ice", "Ice Crown", 3, SKY, WHITE),
        ("tiny", "Tiny Crown", 0, AMBER, GOLD),
    )
    items.extend(_item("crown", s, n, v, p, a) for s, n, v, p, a in crowns)

    # Mustaches.
    staches = (
        ("handlebar", "Handlebar", 0, BROWN, TAN),
        ("tiny", "Tiny Stache", 1, BLACK, BROWN),
        ("bushy", "Bushy Stache", 2, BROWN, BLACK),
        ("curly", "Curly Stache", 0, BLACK, SILVER),
        ("gold", "Gold Stache", 0, GOLD, AMBER),
        ("rainbow", "Rainbow Stache", 2, PINK, CYAN),
        ("pencil", "Pencil Stache", 1, BLACK, BROWN),
        ("walrus", "Walrus Stache", 2, SILVER, WHITE),
        ("twirl", "Twirl Stache", 0, PLUM, PINK),
        ("lime", "Lime Stache", 1, LIME, FOREST),
    )
    items.extend(_item("mustache", s, n, v, p, a) for s, n, v, p, a in staches)

    # Canes.
    canes = (
        ("wood", "Wood Cane", 0, BROWN, TAN),
        ("candy", "Candy Cane", 1, RED, WHITE),
        ("gold", "Gold Cane", 0, GOLD, AMBER),
        ("magic", "Magic Cane", 2, PURPLE, GOLD),
        ("rubber", "Rubber Cane", 0, BLACK, SILVER),
        ("stripe", "Stripe Cane", 1, BLUE, WHITE),
        ("mint", "Mint Cane", 1, MINT, TEAL),
        ("star", "Star Cane", 2, NAVY, GOLD),
    )
    items.extend(_item("cane", s, n, v, p, a) for s, n, v, p, a in canes)

    # Glasses.
    glasses = (
        ("round", "Round Glasses", 0, BLACK, SILVER),
        ("square", "Square Glasses", 1, NAVY, SILVER),
        ("sun", "Sun Glasses", 1, BLACK, GOLD),
        ("star", "Star Glasses", 2, GOLD, PINK),
        ("heart", "Heart Glasses", 2, RED, PINK),
        ("rainbow", "Rainbow Glasses", 0, PINK, CYAN),
        ("thick", "Thick Glasses", 1, BROWN, TAN),
        ("tiny", "Tiny Glasses", 0, SILVER, WHITE),
        ("sky", "Sky Glasses", 0, SKY, WHITE),
        ("lime", "Lime Glasses", 1, LIME, FOREST),
    )
    items.extend(_item("glasses", s, n, v, p, a) for s, n, v, p, a in glasses)

    # Monocles (Damon: "monicles").
    monocles = (
        ("gold", "Gold Monocle", 0, GOLD, AMBER),
        ("silver", "Silver Monocle", 0, SILVER, WHITE),
        ("fancy", "Fancy Monocle", 1, GOLD, PURPLE),
        ("tiny", "Tiny Monocle", 0, SILVER, BLACK),
        ("star", "Star Monocle", 1, GOLD, CYAN),
        ("green", "Green Monocle", 0, GREEN, GOLD),
        ("ruby", "Ruby Monocle", 1, RED, GOLD),
        ("sky", "Sky Monocle", 0, SKY, SILVER),
    )
    items.extend(_item("monocle", s, n, v, p, a) for s, n, v, p, a in monocles)

    # Shoes.
    shoes = (
        ("sneakers", "Sneakers", 0, RED, WHITE),
        ("blue-kicks", "Blue Kicks", 0, BLUE, WHITE),
        ("boots", "Boots", 1, BROWN, TAN),
        ("rain", "Rain Boots", 1, GOLD, FOREST),
        ("slippers", "Slippers", 2, PINK, ROSE),
        ("tap", "Tap Shoes", 0, BLACK, GOLD),
        ("rocket", "Rocket Shoes", 3, ORANGE, CYAN),
        ("socks", "Stripe Socks", 2, WHITE, RED),
        ("sandals", "Sandals", 2, TAN, BROWN),
        ("lime-kicks", "Lime Kicks", 0, LIME, WHITE),
        ("gold-boots", "Gold Boots", 1, GOLD, AMBER),
        ("purple-high", "Purple High-tops", 0, PURPLE, GOLD),
    )
    items.extend(_item("shoes", s, n, v, p, a) for s, n, v, p, a in shoes)

    return tuple(items)


CATALOG: tuple[Wearable, ...] = _build_catalog()
BY_ID: dict[str, Wearable] = {item.id: item for item in CATALOG}


@dataclass
class Outfit:
    """Equipped wearables for the current run (one id per slot)."""

    slots: dict[str, str] = field(default_factory=dict)

    def copy(self) -> "Outfit":
        return Outfit(dict(self.slots))

    def wear(self, item: Wearable) -> None:
        self.slots[item.slot] = item.id

    def ids(self) -> frozenset[str]:
        return frozenset(self.slots.values())

    def resolve(self) -> list[Wearable]:
        return [BY_ID[i] for i in self.slots.values() if i in BY_ID]

    def cache_key(self) -> tuple[str, ...]:
        return tuple(sorted(self.slots.items()))


def is_reward_level(cleared_level: int) -> bool:
    return cleared_level > 0 and cleared_level % REWARD_EVERY == 0


def offer_wearables(
    mode: str,
    level: int,
    equipped_ids: frozenset[str] | set[str],
    equipped_slots: frozenset[str] | set[str],
    count: int = OFFER_COUNT,
) -> tuple[Wearable, ...]:
    """Short pick list from the big catalog. Prefer filling empty slots."""
    rng = stable_rng("wear-offer", mode, level, *sorted(equipped_ids))
    unused = [w for w in CATALOG if w.id not in equipped_ids]
    if not unused:
        unused = list(CATALOG)
    empty = {slot for slot in SLOTS if slot not in equipped_slots}
    preferred = [w for w in unused if w.slot in empty] or unused
    rest = [w for w in unused if w not in preferred]
    rng.shuffle(preferred)
    rng.shuffle(rest)
    ordered = preferred + rest
    picked: list[Wearable] = []
    seen_slots: set[str] = set()
    # First pass: unique slots so the menu feels like a real choice.
    for item in ordered:
        if item.slot in seen_slots:
            continue
        picked.append(item)
        seen_slots.add(item.slot)
        if len(picked) >= count:
            return tuple(picked)
    for item in ordered:
        if item in picked:
            continue
        picked.append(item)
        if len(picked) >= count:
            break
    return tuple(picked)


def draw_cape(src, item: Wearable, frame: int) -> None:
    import pygame

    c, a = item.primary, item.accent
    sway = 1 if frame % 2 == 0 else 0
    v = item.variant
    if v == 0:  # long
        pygame.draw.rect(src, a, (1 + sway, 7, 3, 8))
        pygame.draw.rect(src, c, (1 + sway, 7, 3, 7))
        pygame.draw.rect(src, a, (12 - sway, 7, 3, 8))
        pygame.draw.rect(src, c, (12 - sway, 7, 3, 7))
    elif v == 1:  # royal collar + long
        pygame.draw.rect(src, a, (2, 5, 12, 2))
        pygame.draw.rect(src, c, (1 + sway, 7, 4, 8))
        pygame.draw.rect(src, c, (11 - sway, 7, 4, 8))
        pygame.draw.rect(src, a, (2 + sway, 14, 3, 1))
        pygame.draw.rect(src, a, (11 - sway, 14, 3, 1))
    elif v == 2:  # starry / clipped
        pygame.draw.rect(src, c, (1, 8, 3, 6))
        pygame.draw.rect(src, c, (12, 8, 3, 6))
        pygame.draw.rect(src, a, (2, 10, 1, 1))
        pygame.draw.rect(src, a, (13, 11, 1, 1))
        pygame.draw.rect(src, a, (1, 13, 1, 1))
    else:  # striped
        pygame.draw.rect(src, c, (1 + sway, 7, 3, 8))
        pygame.draw.rect(src, a, (1 + sway, 9, 3, 2))
        pygame.draw.rect(src, a, (1 + sway, 13, 3, 2))
        pygame.draw.rect(src, c, (12 - sway, 7, 3, 8))
        pygame.draw.rect(src, a, (12 - sway, 9, 3, 2))
        pygame.draw.rect(src, a, (12 - sway, 13, 3, 2))


def draw_hat(src, item: Wearable) -> None:
    import pygame

    c, a = item.primary, item.accent
    v = item.variant
    if v == 0:  # ball cap
        pygame.draw.rect(src, c, (3, 1, 10, 3))
        pygame.draw.rect(src, a, (10, 3, 4, 1))
        pygame.draw.rect(src, a, (6, 1, 3, 1))
    elif v == 1:  # beanie
        pygame.draw.rect(src, c, (4, 0, 8, 4))
        pygame.draw.rect(src, a, (3, 3, 10, 1))
        pygame.draw.rect(src, a, (7, 0, 2, 1))
    elif v == 2:  # tall / top / wizard
        pygame.draw.rect(src, c, (5, 0, 6, 4))
        pygame.draw.rect(src, a, (3, 3, 10, 1))
        pygame.draw.rect(src, a, (6, 0, 2, 1))
    elif v == 3:  # wide brim
        pygame.draw.rect(src, c, (4, 1, 8, 3))
        pygame.draw.rect(src, a, (1, 3, 14, 1))
    else:  # propeller / party
        pygame.draw.rect(src, c, (5, 1, 6, 3))
        pygame.draw.rect(src, a, (2, 1, 4, 1))
        pygame.draw.rect(src, a, (10, 1, 4, 1))
        pygame.draw.rect(src, a, (7, 0, 2, 1))


def draw_crown(src, item: Wearable) -> None:
    import pygame

    c, a = item.primary, item.accent
    v = item.variant
    pygame.draw.rect(src, c, (3, 2, 10, 2))
    if v == 0:  # 3-point
        pygame.draw.rect(src, c, (3, 0, 2, 2))
        pygame.draw.rect(src, c, (7, 0, 2, 3))
        pygame.draw.rect(src, c, (11, 0, 2, 2))
        pygame.draw.rect(src, a, (7, 0, 2, 1))
    elif v == 1:  # flower / leaf
        pygame.draw.rect(src, a, (4, 0, 2, 2))
        pygame.draw.rect(src, c, (7, 0, 2, 2))
        pygame.draw.rect(src, a, (10, 0, 2, 2))
    elif v == 2:  # star
        pygame.draw.rect(src, a, (7, 0, 2, 2))
        pygame.draw.rect(src, c, (5, 1, 2, 1))
        pygame.draw.rect(src, c, (9, 1, 2, 1))
        pygame.draw.rect(src, a, (3, 1, 2, 1))
        pygame.draw.rect(src, a, (11, 1, 2, 1))
    else:  # paper / ice band
        pygame.draw.rect(src, a, (3, 1, 2, 1))
        pygame.draw.rect(src, a, (7, 0, 2, 2))
        pygame.draw.rect(src, a, (11, 1, 2, 1))


def draw_mustache(src, item: Wearable, chomping: bool) -> None:
    import pygame

    if chomping:
        return
    c, a = item.primary, item.accent
    y = 8
    if item.variant == 1:  # tiny / pencil
        pygame.draw.rect(src, c, (6, y, 4, 1))
    elif item.variant == 2:  # bushy / walrus
        pygame.draw.rect(src, c, (4, y, 8, 2))
        pygame.draw.rect(src, a, (4, y + 1, 2, 1))
        pygame.draw.rect(src, a, (10, y + 1, 2, 1))
    else:  # handlebar / twirl
        pygame.draw.rect(src, c, (4, y, 8, 1))
        pygame.draw.rect(src, c, (3, y + 1, 2, 1))
        pygame.draw.rect(src, c, (11, y + 1, 2, 1))
        pygame.draw.rect(src, a, (7, y, 2, 1))


def draw_cane(src, item: Wearable, facing_x: int) -> None:
    import pygame

    c, a = item.primary, item.accent
    # Always draw on the unflipped sprite's right; the muncher flip handles facing.
    x = 14
    pygame.draw.rect(src, c, (x, 6, 1, 9))
    pygame.draw.rect(src, a, (x - 1, 6, 2, 1))
    if item.variant == 1:  # striped
        pygame.draw.rect(src, a, (x, 8, 1, 1))
        pygame.draw.rect(src, a, (x, 11, 1, 1))
        pygame.draw.rect(src, a, (x, 14, 1, 1))
    elif item.variant == 2:  # magic star tip
        pygame.draw.rect(src, a, (x, 5, 1, 1))


def draw_glasses(src, item: Wearable) -> None:
    import pygame

    c, a = item.primary, item.accent
    if item.variant == 2:  # star / heart — thicker frames
        pygame.draw.rect(src, c, (3, 4, 4, 3), 1)
        pygame.draw.rect(src, c, (9, 4, 4, 3), 1)
        pygame.draw.rect(src, a, (7, 5, 2, 1))
        pygame.draw.rect(src, a, (4, 4, 1, 1))
        pygame.draw.rect(src, a, (11, 4, 1, 1))
    elif item.variant == 1:  # square / sun
        pygame.draw.rect(src, c, (3, 4, 4, 3), 1)
        pygame.draw.rect(src, c, (9, 4, 4, 3), 1)
        pygame.draw.rect(src, a, (7, 5, 2, 1))
    else:  # round
        pygame.draw.rect(src, c, (4, 4, 3, 3), 1)
        pygame.draw.rect(src, c, (9, 4, 3, 3), 1)
        pygame.draw.rect(src, a, (7, 5, 2, 1))


def draw_monocle(src, item: Wearable) -> None:
    import pygame

    c, a = item.primary, item.accent
    pygame.draw.rect(src, c, (9, 4, 4, 4), 1)
    pygame.draw.rect(src, a, (10, 5, 2, 2))
    pygame.draw.rect(src, c, (12, 8, 1, 3))
    if item.variant == 1:
        pygame.draw.rect(src, a, (9, 3, 1, 1))


def draw_shoes(src, item: Wearable, frame: int) -> None:
    import pygame

    c, a = item.primary, item.accent
    lift = 1 if frame % 2 == 0 else 0
    y1, y2 = 13 - lift, 13 - (1 - lift)
    if item.variant == 1:  # boots — taller
        pygame.draw.rect(src, c, (4, y1 - 1, 3, 4))
        pygame.draw.rect(src, c, (9, y2 - 1, 3, 4))
        pygame.draw.rect(src, a, (4, y1 + 2, 3, 1))
        pygame.draw.rect(src, a, (9, y2 + 2, 3, 1))
    elif item.variant == 2:  # slippers / socks
        pygame.draw.rect(src, c, (4, y1, 3, 3))
        pygame.draw.rect(src, c, (9, y2, 3, 3))
        pygame.draw.rect(src, a, (4, y1, 3, 1))
        pygame.draw.rect(src, a, (9, y2, 3, 1))
    elif item.variant == 3:  # rocket
        pygame.draw.rect(src, c, (4, y1, 3, 3))
        pygame.draw.rect(src, c, (9, y2, 3, 3))
        pygame.draw.rect(src, a, (5, y1 + 2, 1, 2))
        pygame.draw.rect(src, a, (10, y2 + 2, 1, 2))
    else:  # sneakers
        pygame.draw.rect(src, c, (4, y1, 3, 3))
        pygame.draw.rect(src, c, (9, y2, 3, 3))
        pygame.draw.rect(src, a, (4, y1 + 2, 3, 1))
        pygame.draw.rect(src, a, (9, y2 + 2, 3, 1))


def paint_outfit(
    src,
    outfit: Outfit | None,
    frame: int,
    facing_x: int,
    chomping: bool,
    layer: str = "all",
) -> None:
    """Draw equipped gear onto the 16×16 muncher (cape behind the body)."""
    if outfit is None:
        return
    by_slot = {item.slot: item for item in outfit.resolve()}
    if layer in ("all", "back") and "cape" in by_slot:
        draw_cape(src, by_slot["cape"], frame)
    if layer not in ("all", "front"):
        return
    if "feet" in by_slot:
        draw_shoes(src, by_slot["feet"], frame)
    if "hand" in by_slot:
        draw_cane(src, by_slot["hand"], facing_x)
    if "mouth" in by_slot:
        draw_mustache(src, by_slot["mouth"], chomping)
    if "eyes" in by_slot:
        item = by_slot["eyes"]
        if item.category == "monocle":
            draw_monocle(src, item)
        else:
            draw_glasses(src, item)
    if "head" in by_slot:
        item = by_slot["head"]
        if item.category == "crown":
            draw_crown(src, item)
        else:
            draw_hat(src, item)
