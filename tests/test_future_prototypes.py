import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from prototypes.dialogue_cascade import (  # noqa: E402
    DialogueProbabilities,
    DialogueQueue,
    SpawnDialogueDirector,
)
from prototypes.future_minigames import (  # noqa: E402
    CedricBookCipherState,
    ElementalSealState,
    LightOfMeridianState,
    PortalRelayState,
    RebelCourierState,
    rotate_connectors,
)
from prototypes.game_watch_skeletons import (  # noqa: E402
    BlunkTreasureEscapeState,
    CorneliaManholeState,
    IrmaOilPanicState,
)


class FutureMinigameTests(unittest.TestCase):
    def test_four_rotations_restore_connector(self):
        for mask in range(16):
            self.assertEqual(rotate_connectors(mask, 4), mask)

    def test_portal_relay_is_scrambled_but_solution_connects(self):
        for seed in range(20):
            state = PortalRelayState.create(seed=seed)
            self.assertFalse(state.round_complete)
            state.apply_solution()
            self.assertTrue(state.round_complete)

    def test_light_balance_stays_endless_until_it_is_lost(self):
        stable = LightOfMeridianState()
        stable.step(20)
        self.assertEqual(stable.status, "playing")
        self.assertEqual(stable.stable_ticks, 20)

        unstable = LightOfMeridianState(energy=[0, 50, 50])
        unstable.step(100)
        self.assertEqual(unstable.status, "lost")

    def test_book_cipher_accepts_complete_pattern(self):
        state = CedricBookCipherState(seed=3)
        state.begin_input()
        current_pattern = state.pattern[:]
        results = [state.press(rune) for rune in current_pattern]
        self.assertEqual(results[-1], "round_complete")
        self.assertEqual(state.phase, "preview")
        self.assertEqual(state.round_number, 2)

    def test_elemental_seal_mapping(self):
        state = ElementalSealState(seed=2)
        self.assertTrue(state.choose(state.required_guardian))
        self.assertEqual(state.status, "playing")
        self.assertEqual(state.resolved, 1)

        state = ElementalSealState(seed=2)
        wrong = next(name for name in ("will", "irma", "cornelia") if name != state.required_guardian)
        self.assertFalse(state.choose(wrong))
        self.assertEqual(state.lives, 2)

    def test_every_rebel_route_has_reachable_safe_path(self):
        for seed in range(40):
            state = RebelCourierState(seed=seed)
            reachable = {state.lane}
            for blocked in state.patrols:
                reachable = {
                    lane + delta
                    for lane in reachable
                    for delta in (-1, 0, 1)
                    if 0 <= lane + delta < 3 and lane + delta not in blocked
                }
                self.assertTrue(reachable)

    def test_rebel_courier_continues_after_first_stage(self):
        state = RebelCourierState(seed=8, route_length=4)
        for _ in range(4):
            safe = next(lane for lane in range(3) if lane not in state.patrols[state.row] and abs(lane-state.lane) <= 1)
            state.advance(safe-state.lane)
        self.assertEqual(state.status, "playing")
        before = len(state.patrols)
        state.advance(0)
        self.assertGreater(len(state.patrols), before)
        self.assertEqual(state.stage, 2)


class DialogueCascadeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = ROOT / "prototypes" / "dialogue_cascade_sample.json"
        cls.data = json.loads(path.read_text(encoding="utf-8"))["spawn_exchanges"]

    def test_full_three_beat_cascade(self):
        director = SpawnDialogueDirector(
            self.data,
            seed=1,
            probabilities=DialogueProbabilities(1.0, 1.0, 1.0),
        )
        sequence = director.on_piece_spawn("Z")
        self.assertIsNotNone(sequence)
        self.assertEqual([beat.speaker for beat in sequence.beats], ["phobos", "will", "phobos"])

    def test_reply_and_counter_are_conditional(self):
        director = SpawnDialogueDirector(
            self.data,
            seed=1,
            probabilities=DialogueProbabilities(1.0, 0.0, 1.0),
        )
        sequence = director.on_piece_spawn("S")
        self.assertEqual(len(sequence.beats), 1)

    def test_route_and_audio_guards_suppress_dialogue(self):
        director = SpawnDialogueDirector(
            self.data,
            probabilities=DialogueProbabilities(1.0, 1.0, 1.0),
        )
        self.assertIsNone(director.on_piece_spawn("I", guardians_route=True))
        self.assertIsNone(director.on_piece_spawn("I", guardians_gone=True))
        self.assertIsNone(director.on_piece_spawn("I", voice_busy=True))

    def test_queue_never_starts_two_lines_at_once(self):
        director = SpawnDialogueDirector(
            self.data,
            probabilities=DialogueProbabilities(1.0, 1.0, 1.0),
        )
        sequence = director.on_piece_spawn("T")
        queue = DialogueQueue()
        self.assertTrue(queue.enqueue(sequence))
        first = queue.tick(audio_busy=False)
        self.assertEqual(first.speaker, "phobos")
        self.assertIsNone(queue.tick(audio_busy=True))
        self.assertEqual(queue.current, first)
        self.assertFalse(queue.enqueue(sequence))


class GameWatchSkeletonTests(unittest.TestCase):
    def test_blunk_can_bank_treasure_without_victory_state(self):
        state = BlunkTreasureEscapeState()
        for _ in range(state.path_length):
            state.move(1)
        for _ in range(state.path_length):
            state.move(-1)
        self.assertEqual(state.banked, 1)
        self.assertEqual(state.status, "playing")

    def test_manhole_cover_scores_only_on_matching_hole(self):
        state = CorneliaManholeState(cover=2)
        state.travellers = [[2, 31]]
        state.tick()
        self.assertEqual(state.score, 1)

    def test_irma_dumps_only_full_vessel(self):
        state = IrmaOilPanicState()
        self.assertEqual((state.lanes, state.lane), (5, 2))
        self.assertFalse(state.dump())
        state.stored = state.capacity
        self.assertTrue(state.dump())
        self.assertEqual(state.stored, 0)


if __name__ == "__main__":
    unittest.main()
