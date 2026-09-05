"""One-screen endless minigame skeletons inspired by Game & Watch pacing.

The mechanics are original W.I.T.C.H.-themed state machines.  They do not use
Nintendo artwork, layouts, timing tables or code.  A pygame adapter can draw
each state on the existing 860x1060 canvas.  There is deliberately no victory
state: difficulty rises until ``status == 'lost'``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import random


@dataclass
class BlunkTreasureEscapeState:
    """Steal treasure and escape the pursuing serpent form of Cedric."""

    path_length: int = 5
    position: int = 0
    cedric_position: int = 6
    carried: int = 0
    banked: int = 0
    lives: int = 3
    tick_count: int = 0
    safe_ticks: int = 60
    status: str = "playing"

    @property
    def level(self) -> int:
        return 1 + self.banked // 5

    def move(self, direction: int) -> bool:
        if self.status != "playing" or direction not in (-1, 1):
            return False
        old = self.position
        self.position = max(0, min(self.path_length, self.position + direction))
        if self.position == self.path_length and old != self.path_length:
            self.carried = 1
        if self.position == 0 and old != 0 and self.carried:
            self.banked += self.carried
            self.carried = 0
            self.cedric_position = self.path_length + 1
        self._check_catch()
        return True

    def tick(self) -> None:
        if self.status != "playing":
            return
        self.tick_count += 1
        self.safe_ticks = max(0, self.safe_ticks - 1)
        interval = max(14, 54 - self.level * 4)
        if self.tick_count % interval == 0:
            if self.cedric_position > self.position:
                self.cedric_position -= 1
            elif self.cedric_position < self.position:
                self.cedric_position += 1
        self._check_catch()

    def _check_catch(self) -> None:
        if self.safe_ticks or self.position != self.cedric_position:
            return
        self.lives -= 1
        self.carried = 0
        self.position = 0
        self.cedric_position = self.path_length + 1
        self.safe_ticks = 60
        if self.lives <= 0:
            self.status = "lost"


@dataclass
class CorneliaManholeState:
    """Move one stone cover between cracks in a Meridian street."""

    seed: int = 0
    holes: int = 4
    cover: int = 1
    lives: int = 3
    score: int = 0
    tick_count: int = 0
    travellers: list[list[int]] = field(default_factory=list)
    status: str = "playing"

    def __post_init__(self) -> None:
        self._rng = random.Random(self.seed)

    def move_cover(self, delta: int) -> None:
        if self.status == "playing":
            self.cover = max(0, min(self.holes - 1, self.cover + delta))

    def tick(self) -> None:
        if self.status != "playing":
            return
        self.tick_count += 1
        level = 1 + self.score // 10
        if self.tick_count % max(26, 82 - level * 4) == 0:
            self.travellers.append([self._rng.randrange(self.holes), 0])
        for traveller in self.travellers[:]:
            traveller[1] += 1
            if traveller[1] < max(14, 32 - level):
                continue
            self.travellers.remove(traveller)
            if traveller[0] == self.cover:
                self.score += 1
            else:
                self.lives -= 1
                if self.lives <= 0:
                    self.status = "lost"


@dataclass
class IrmaOilPanicState:
    """Catch dark-water drops, then dump the full vessel on Phobos's guards."""

    seed: int = 0
    lanes: int = 5
    lane: int = 2
    capacity: int = 3
    stored: int = 0
    lives: int = 3
    score: int = 0
    tick_count: int = 0
    drops: list[list[float | int]] = field(default_factory=list)
    status: str = "playing"

    def __post_init__(self) -> None:
        self._rng = random.Random(self.seed)

    def move(self, delta: int) -> None:
        if self.status == "playing":
            self.lane = max(0, min(self.lanes - 1, self.lane + delta))

    def dump(self) -> bool:
        if self.status != "playing" or self.stored < self.capacity:
            return False
        self.score += self.stored * 3
        self.stored = 0
        return True

    def tick(self) -> None:
        if self.status != "playing":
            return
        self.tick_count += 1
        level = 1 + self.tick_count // 1080
        if self.tick_count % max(30, 86 - level * 4) == 0:
            self.drops.append([self._rng.randrange(self.lanes), 0.0])
        speed = 3.0 + min(5.0, (level - 1) * 0.32)
        for drop in self.drops[:]:
            drop[1] = float(drop[1]) + speed
            if float(drop[1]) < 100.0:
                continue
            self.drops.remove(drop)
            if int(drop[0]) == self.lane and self.stored < self.capacity:
                self.stored += 1
                self.score += 1
            else:
                self.lives -= 1
                if self.lives <= 0:
                    self.status = "lost"


GAME_WATCH_PROTOTYPES = (
    BlunkTreasureEscapeState,
    CorneliaManholeState,
    IrmaOilPanicState,
)
