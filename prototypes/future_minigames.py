"""Pure-Python prototypes for possible W.I.T.C.H. Tetris minigames.

The classes in this module deliberately know nothing about pygame, images or
audio.  They contain deterministic game rules that can later be rendered by
the existing ``main.py`` minigame screen.  Nothing imports this module in the
current build, so adding it cannot change the released game.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import random


NORTH, EAST, SOUTH, WEST = 1, 2, 4, 8
CONNECTIONS = {
    NORTH: (0, -1, SOUTH),
    EAST: (1, 0, WEST),
    SOUTH: (0, 1, NORTH),
    WEST: (-1, 0, EAST),
}


def rotate_connectors(mask: int, turns: int = 1) -> int:
    """Rotate a four-bit N/E/S/W connector mask clockwise."""

    for _ in range(turns % 4):
        mask = ((mask << 1) & 0b1111) | ((mask >> 3) & 1)
    return mask


def _direction_bit(a: tuple[int, int], b: tuple[int, int]) -> int:
    dx, dy = b[0] - a[0], b[1] - a[1]
    return {(0, -1): NORTH, (1, 0): EAST, (0, 1): SOUTH, (-1, 0): WEST}[(dx, dy)]


@dataclass
class PortalRelayState:
    """Rotate a broken portal conduit until the Heart reaches Meridian."""

    width: int
    height: int
    grid: list[list[int]]
    solution: list[list[int]]
    start: tuple[int, int]
    target: tuple[int, int]
    cursor: tuple[int, int] = (0, 0)
    moves: int = 0

    @classmethod
    def create(cls, seed: int = 0, width: int = 7, height: int = 7) -> "PortalRelayState":
        if width < 6 or height < 4:
            raise ValueError("Portal Relay needs at least a 6x4 grid")
        rng = random.Random(seed)
        start = (0, rng.randrange(1, height - 1))
        target = (width - 1, rng.randrange(1, height - 1))
        middle_y = rng.randrange(1, height - 1)
        bend_a, bend_b = width // 3, (width * 2) // 3

        path: list[tuple[int, int]] = [start]

        def walk_to(destination: tuple[int, int]) -> None:
            x, y = path[-1]
            tx, ty = destination
            while x != tx:
                x += 1 if tx > x else -1
                path.append((x, y))
            while y != ty:
                y += 1 if ty > y else -1
                path.append((x, y))

        walk_to((bend_a, start[1]))
        walk_to((bend_a, middle_y))
        walk_to((bend_b, middle_y))
        walk_to((bend_b, target[1]))
        walk_to(target)

        solved = [[0 for _ in range(width)] for _ in range(height)]
        for a, b in zip(path, path[1:]):
            bit = _direction_bit(a, b)
            opposite = CONNECTIONS[bit][2]
            solved[a[1]][a[0]] |= bit
            solved[b[1]][b[0]] |= opposite

        # Empty cells receive harmless visual decoys. They never connect to the
        # true path in the solution but make the renderer less bare.
        decoys = (0, NORTH | SOUTH, EAST | WEST, NORTH | EAST, SOUTH | WEST)
        grid = [[rng.choice(decoys) for _ in range(width)] for _ in range(height)]
        for x, y in path:
            grid[y][x] = rotate_connectors(solved[y][x], rng.randrange(4))

        state = cls(width, height, grid, solved, start, target, cursor=start)
        if state.round_complete:
            x, y = path[len(path) // 2]
            state.grid[y][x] = rotate_connectors(state.grid[y][x])
        return state

    def move_cursor(self, dx: int, dy: int) -> None:
        x, y = self.cursor
        self.cursor = (max(0, min(self.width - 1, x + dx)),
                       max(0, min(self.height - 1, y + dy)))

    def rotate(self, x: int | None = None, y: int | None = None) -> None:
        x = self.cursor[0] if x is None else x
        y = self.cursor[1] if y is None else y
        if not (0 <= x < self.width and 0 <= y < self.height):
            raise IndexError("tile outside grid")
        self.grid[y][x] = rotate_connectors(self.grid[y][x])
        self.moves += 1

    def connected_cells(self) -> set[tuple[int, int]]:
        seen = {self.start}
        todo = [self.start]
        while todo:
            x, y = todo.pop()
            mask = self.grid[y][x]
            for bit, (dx, dy, opposite) in CONNECTIONS.items():
                if not mask & bit:
                    continue
                nx, ny = x + dx, y + dy
                if not (0 <= nx < self.width and 0 <= ny < self.height):
                    continue
                if self.grid[ny][nx] & opposite and (nx, ny) not in seen:
                    seen.add((nx, ny))
                    todo.append((nx, ny))
        return seen

    @property
    def round_complete(self) -> bool:
        """True only for the current board; the arcade loop starts a new one."""

        return self.target in self.connected_cells()

    def apply_solution(self) -> None:
        """Developer/test helper; the final UI must not expose this action."""

        self.grid = [row[:] for row in self.solution]


@dataclass
class LightOfMeridianState:
    """Keep three Meridian light wells balanced while corruption rises."""

    seed: int = 0
    energy: list[int] = field(default_factory=lambda: [50, 50, 50])
    corruption: int = 0
    stable_ticks: int = 0
    score: int = 0
    tick_count: int = 0
    vent_cooldown: int = 0
    status: str = "playing"

    SAFE_MIN = 32
    SAFE_MAX = 68

    def __post_init__(self) -> None:
        self._rng = random.Random(self.seed)

    def transfer(self, source: int, destination: int, amount: int = 8) -> bool:
        if self.status != "playing" or source == destination:
            return False
        if not (0 <= source < 3 and 0 <= destination < 3):
            return False
        amount = min(amount, self.energy[source], 100 - self.energy[destination])
        if amount <= 0:
            return False
        self.energy[source] -= amount
        self.energy[destination] += amount
        return True

    def vent(self, channel: int) -> bool:
        if self.status != "playing" or self.vent_cooldown or not 0 <= channel < 3:
            return False
        excess = max(0, self.energy[channel] - 50)
        self.energy[channel] -= min(18, excess)
        self.corruption = max(0, self.corruption - 8)
        self.vent_cooldown = 180
        return True

    def step(self, ticks: int = 1) -> None:
        for _ in range(ticks):
            if self.status != "playing":
                return
            self.tick_count += 1
            self.vent_cooldown = max(0, self.vent_cooldown - 1)
            disturbance_period = max(24, 90 - (self.tick_count // 600) * 6)
            if self.tick_count % disturbance_period == 0:
                channel = self._rng.randrange(3)
                self.energy[channel] = max(0, min(100, self.energy[channel] + self._rng.choice((-14, -10, 10, 14))))
            safe = all(self.SAFE_MIN <= value <= self.SAFE_MAX for value in self.energy)
            if safe:
                self.stable_ticks += 1
                if self.tick_count % 60 == 0:
                    self.score += 10
                self.corruption = max(0, self.corruption - (1 if self.tick_count % 30 == 0 else 0))
            else:
                self.stable_ticks = max(0, self.stable_ticks - 2)
                self.corruption += 1
            if self.corruption >= 100:
                self.status = "lost"


@dataclass
class CedricBookCipherState:
    """Repeat increasingly long rune sequences from Cedric's bookshop."""

    seed: int = 0
    rune_count: int = 6
    lives: int = 3
    pattern: list[int] = field(default_factory=list)
    input_index: int = 0
    round_number: int = 1
    score: int = 0
    phase: str = "preview"

    def __post_init__(self) -> None:
        self._rng = random.Random(self.seed)
        if not self.pattern:
            self.pattern = [self._rng.randrange(self.rune_count) for _ in range(3)]

    def begin_input(self) -> None:
        if self.phase == "preview":
            self.phase = "input"
            self.input_index = 0

    def press(self, rune: int) -> str:
        if self.phase != "input" or not 0 <= rune < self.rune_count:
            return "ignored"
        if rune != self.pattern[self.input_index]:
            self.lives -= 1
            self.input_index = 0
            if self.lives <= 0:
                self.phase = "lost"
                return "lost"
            self.phase = "preview"
            return "wrong"
        self.input_index += 1
        if self.input_index < len(self.pattern):
            return "correct"
        self.score += len(self.pattern) * 10
        self.round_number += 1
        self.pattern.append(self._rng.randrange(self.rune_count))
        self.input_index = 0
        self.phase = "preview"
        return "round_complete"


ELEMENT_GUARDIANS = {
    "earth": "cornelia",
    "fire": "taranee",
    "air": "hay_lin",
    "water": "irma",
    "heart": "will",
}


@dataclass
class ElementalSealState:
    """Select the correct Guardian before each elemental seal closes."""

    seed: int = 0
    lives: int = 3
    score: int = 0
    combo: int = 0
    resolved: int = 0
    status: str = "playing"
    current_element: str = ""

    def __post_init__(self) -> None:
        self._rng = random.Random(self.seed)
        self._elements = tuple(ELEMENT_GUARDIANS)
        self._next_seal()

    def _next_seal(self) -> None:
        self.current_element = self._rng.choice(self._elements)

    @property
    def required_guardian(self) -> str:
        return ELEMENT_GUARDIANS[self.current_element]

    def choose(self, guardian: str) -> bool:
        if self.status != "playing":
            return False
        correct = guardian == self.required_guardian
        if correct:
            self.combo += 1
            self.score += 10 + min(40, self.combo * 2)
            self.resolved += 1
            self._next_seal()
        else:
            self.combo = 0
            self.lives -= 1
            if self.lives <= 0:
                self.status = "lost"
            else:
                self._next_seal()
        return correct


@dataclass
class RebelCourierState:
    """Guide Caleb through telegraphed patrol lanes in Meridian."""

    seed: int = 0
    route_length: int = 30
    lane: int = 1
    row: int = 0
    lives: int = 3
    score: int = 0
    stage: int = 1
    status: str = "playing"
    patrols: list[set[int]] = field(default_factory=list)

    def __post_init__(self) -> None:
        self._rng = random.Random(self.seed)
        if not self.patrols:
            self._append_stage(self.lane)

    def _append_stage(self, starting_lane: int) -> None:
        # A hidden safe path moves by at most one lane per step, so every
        # generated stage is completable. Later stages use two blocked lanes
        # more often, but the minigame itself never produces a victory state.
        safe_lane = starting_lane
        double_chance = min(0.72, 0.24 + self.stage * 0.055)
        for _ in range(self.route_length):
            safe_lane = max(0, min(2, safe_lane + self._rng.choice((-1, 0, 1))))
            count = 2 if self._rng.random() < double_chance else 1
            blockable = [lane for lane in range(3) if lane != safe_lane]
            self.patrols.append(set(self._rng.sample(blockable, count)))

    def visible_patrols(self, distance: int = 4) -> list[set[int]]:
        return [set(row) for row in self.patrols[self.row:self.row + distance]]

    def advance(self, lane_delta: int = 0) -> bool:
        if self.status != "playing" or lane_delta not in (-1, 0, 1):
            return False
        self.lane = max(0, min(2, self.lane + lane_delta))
        if self.row >= len(self.patrols):
            self.stage += 1
            self._append_stage(self.lane)
        blocked = self.lane in self.patrols[self.row]
        self.row += 1
        if blocked:
            self.lives -= 1
            self.score = max(0, self.score - 15)
            if self.lives <= 0:
                self.status = "lost"
        else:
            self.score += 10
        return not blocked


PROTOTYPE_CLASSES: tuple[type, ...] = (
    PortalRelayState,
    LightOfMeridianState,
    CedricBookCipherState,
    ElementalSealState,
    RebelCourierState,
)
