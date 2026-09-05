"""Prototype of spawn dialogue cascades for W.I.T.C.H. Tetris.

Intended flow::

    Phobos spawn remark -> optional character reply -> rare Phobos counter

This module is isolated from ``main.py`` and deliberately disabled.  It keeps
the rejected experiment reproducible for development, but the game does not
display its text as subtitles or play its queue while Tetris is running.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
import random
from typing import Any


PIECE_CHARACTER = {
    "I": "cornelia",
    "J": "taranee",
    "L": "hay_lin",
    "T": "caleb",
    "O": "blunk",
    "S": "irma",
    "Z": "will",
}


@dataclass(frozen=True)
class DialogueBeat:
    speaker: str
    text: str
    audio_key: str | None = None
    delay_after_frames: int = 12
    minimum_display_frames: int = 90


@dataclass(frozen=True)
class DialogueSequence:
    exchange_id: str
    character: str
    beats: tuple[DialogueBeat, ...]


@dataclass
class DialogueProbabilities:
    """Conditional chances; the third value applies only after a reply."""

    phobos_starts: float = 0.055
    character_replies: float = 0.30
    phobos_counters: float = 0.20

    def __post_init__(self) -> None:
        for value in (self.phobos_starts, self.character_replies, self.phobos_counters):
            if not 0.0 <= value <= 1.0:
                raise ValueError("dialogue probabilities must be between 0 and 1")


@dataclass
class SpawnDialogueDirector:
    exchanges: list[dict[str, Any]]
    seed: int = 0
    probabilities: DialogueProbabilities = field(default_factory=DialogueProbabilities)
    cooldown_pieces: int = 12
    recent_limit: int = 5
    enabled: bool = True
    pieces_until_ready: int = 0
    recent_ids: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self._rng = random.Random(self.seed)
        ids = [item.get("id") for item in self.exchanges]
        if any(not item for item in ids) or len(ids) != len(set(ids)):
            raise ValueError("each dialogue exchange needs a unique non-empty id")

    @classmethod
    def from_json(cls, path: str | Path, **kwargs: Any) -> "SpawnDialogueDirector":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(exchanges=data["spawn_exchanges"], **kwargs)

    def on_piece_spawn(
        self,
        kind: str,
        *,
        guardians_gone: bool = False,
        guardians_route: bool = False,
        voice_busy: bool = False,
    ) -> DialogueSequence | None:
        """Possibly create one cascade for a newly spawned tetromino.

        Suppression flags mirror the safeguards already present in ``main.py``.
        A returned sequence is data only; playing it is the caller's job.
        """

        character = PIECE_CHARACTER.get(kind)
        if not self.enabled or not character or guardians_gone or guardians_route or voice_busy:
            return None
        if self.pieces_until_ready:
            self.pieces_until_ready -= 1
            return None
        if self._rng.random() >= self.probabilities.phobos_starts:
            return None

        pool = [item for item in self.exchanges if item.get("character") == character]
        fresh = [item for item in pool if item["id"] not in self.recent_ids]
        if fresh:
            pool = fresh
        if not pool:
            return None

        exchange = self._rng.choice(pool)
        beats = [self._pick_beat("phobos", exchange["phobos"])]
        if exchange.get("character_reply") and self._rng.random() < self.probabilities.character_replies:
            beats.append(self._pick_beat(character, exchange["character_reply"]))
            if exchange.get("phobos_counter") and self._rng.random() < self.probabilities.phobos_counters:
                beats.append(self._pick_beat("phobos", exchange["phobos_counter"]))

        self.pieces_until_ready = self.cooldown_pieces
        self.recent_ids.append(exchange["id"])
        self.recent_ids = self.recent_ids[-self.recent_limit:]
        return DialogueSequence(exchange["id"], character, tuple(beats))

    def _pick_beat(self, speaker: str, variants: list[dict[str, Any]]) -> DialogueBeat:
        selected = self._rng.choice(variants)
        return DialogueBeat(
            speaker=speaker,
            text=selected["text"],
            audio_key=selected.get("audio"),
            delay_after_frames=int(selected.get("delay_after_frames", 12)),
            minimum_display_frames=int(
                selected.get("minimum_display_frames", max(90, min(240, 60 + len(selected["text"]) * 2)))
            ),
        )


@dataclass
class DialogueQueue:
    """Small playback queue that prevents simultaneous spoken lines."""

    pending: list[DialogueBeat] = field(default_factory=list)
    current: DialogueBeat | None = None
    delay_frames: int = 0
    current_frames: int = 0

    def enqueue(self, sequence: DialogueSequence) -> bool:
        if self.current or self.pending:
            return False
        self.pending.extend(sequence.beats)
        return True

    def tick(self, *, audio_busy: bool = False) -> DialogueBeat | None:
        if self.current:
            self.current_frames += 1
        if self.current and (audio_busy or self.current_frames < self.current.minimum_display_frames):
            return None
        if self.current:
            self.delay_frames = self.current.delay_after_frames
            self.current = None
            self.current_frames = 0
        if self.delay_frames:
            self.delay_frames -= 1
            return None
        if not self.current and self.pending:
            self.current = self.pending.pop(0)
            self.current_frames = 0
            return self.current
        return None

    @property
    def active(self) -> bool:
        return bool(self.current or self.pending or self.delay_frames)
