from __future__ import annotations

import os
import unittest
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

try:
    import pygame
except ImportError:
    pygame = None

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipIf(pygame is None, "Pygame is not installed in this environment")
class PygameSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from main import Game
        cls.game = Game()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_changed_minigames_draw_one_frame(self):
        self.assertEqual(len(self.game.minigame_names), 14)
        self.assertNotIn("IRMA RAIN DANCE", self.game.minigame_names)
        self.assertNotIn("HAY LIN RESCUE", self.game.minigame_names)
        for name in ("WILL MAZE", "HAY LIN FLIGHT", "CALEB RUNNER", "HEART BREAKER",
                     "TARANEE FIRE SHOT", "CORNELIA EARTH GARDEN", "IRMA WHIRLPOOL",
                     "BLUNK TREASURE ESCAPE", "CORNELIA STONE COVERS",
                     "IRMA DARK WATER PANIC"):
            with self.subTest(name=name):
                self.game.start_minigame(name)
                self.game.update_minigame()
                self.game.draw_minigame()
        self.game.leave_minigame()

    def test_galleries_are_curated(self):
        self.game.collection_page = "ART & SPRITES"
        self.game.gallery_for("ACTION POSES")
        self.assertEqual(len(self.game.collection_gallery_files), 8)
        self.game.collection_page = "ART & SPRITES"
        self.game.gallery_for("HORROR TETROMINOES")
        self.assertEqual(len(self.game.collection_gallery_files), 7)
        self.assertTrue(all(path.name.endswith("rotation_0.png") for path in self.game.collection_gallery_files))

    def test_caleb_crouch_hitbox_matches_visible_clearance(self):
        self.game.start_minigame("CALEB RUNNER")
        obstacle=[130.0,self.game.mg_ground,50,34,False,True]
        rect=self.game.caleb_obstacle_rect(obstacle)
        self.assertTrue(self.game.caleb_player_rect(False).colliderect(rect))
        self.assertFalse(self.game.caleb_player_rect(True).colliderect(rect))

    def test_caleb_jump_moves_both_sprite_anchor_and_hitbox(self):
        self.game.start_minigame("CALEB RUNNER")
        ground = self.game.mg_ground
        self.game.handle_minigame_key(pygame.K_SPACE)
        self.assertLess(self.game.mg_vel[1], 0)
        self.game.update_minigame()
        self.assertLess(self.game.mg_player[1], ground)
        self.assertEqual(
            self.game.caleb_player_rect(False).bottom,
            int(self.game.mg_player[1] + 25),
        )

    def test_phobos_alpha_cleanup_keeps_the_dark_costume(self):
        from main import load_clean_alpha

        source = ROOT / "assets/cutscenes/lines100/phobos_action.png"
        cleaned = load_clean_alpha(source)
        repaired_pixels = pygame.mask.from_surface(cleaned, 8).count()
        damaged = pygame.image.load(str(source)).convert_alpha()
        damaged_ratio = pygame.mask.from_surface(damaged, 8).count() / (352 * 288)
        repaired_ratio = repaired_pixels / (352 * 288)
        self.assertGreater(repaired_ratio, damaged_ratio)
        self.assertEqual(cleaned.get_size(), (352, 288))
        self.assertEqual(self.game.phobos_resistance_body.get_size(), (352, 288))

    def test_will_maze_ghosts_leave_the_house_one_by_one(self):
        self.game.start_minigame("WILL MAZE")
        self.assertEqual([ghost["state"] for ghost in self.game.mg_maze_ghosts],
                         ["active", "house", "house", "house"])
        self.assertEqual([ghost["release"] for ghost in self.game.mg_maze_ghosts],
                         [0, 4 * 60, 9 * 60, 15 * 60])

    def test_blunk_steals_treasure_and_escapes_serpent_cedric(self):
        self.game.start_minigame("BLUNK TREASURE ESCAPE")
        for _ in range(5):
            self.game.handle_minigame_key(pygame.K_RIGHT)
        self.assertEqual(self.game.mg_gw_carried, 1)
        for _ in range(5):
            self.game.handle_minigame_key(pygame.K_LEFT)
        self.assertEqual(self.game.mg_gw_banked, 1)
        self.assertEqual(self.game.mg_score, 10)

    def test_two_other_game_watch_loops_score_without_victory(self):
        self.game.start_minigame("CORNELIA STONE COVERS")
        self.game.mg_objects = [[self.game.mg_gw_cover, 1]]
        self.game.update_minigame()
        self.assertEqual(self.game.mg_score, 2)
        self.assertFalse(self.game.mg_over)

        self.game.start_minigame("IRMA DARK WATER PANIC")
        self.game.mg_objects = [[self.game.mg_gw_lane, self.game.mg_arena.bottom - 91.0]]
        self.game.update_minigame()
        self.assertEqual(self.game.mg_gw_stored, 1)
        self.assertFalse(self.game.mg_over)

    def test_irma_dark_water_has_five_lanes_and_accelerates(self):
        from main import FPS, irma_dark_water_curve

        self.game.start_minigame("IRMA DARK WATER PANIC")
        self.assertEqual(self.game.mg_gw_lane, 2)
        for _ in range(10):
            self.game.handle_minigame_key(pygame.K_LEFT)
        self.assertEqual(self.game.mg_gw_lane, 0)
        for _ in range(10):
            self.game.handle_minigame_key(pygame.K_RIGHT)
        self.assertEqual(self.game.mg_gw_lane, 4)

        level_1, spawn_1, speed_1 = irma_dark_water_curve(0)
        level_5, spawn_5, speed_5 = irma_dark_water_curve(FPS * 18 * 4)
        self.assertEqual((level_1, level_5), (1, 5))
        self.assertLess(spawn_5, spawn_1)
        self.assertGreater(speed_5, speed_1)

    def test_cornelia_garden_requires_matching_colour_and_multiple_hits(self):
        self.game.start_minigame("CORNELIA EARTH GARDEN")
        self.game.mg_player = [500.0, 700.0]
        vine = [500.0, 680.0, "vine", 1, 2, 2]
        self.game.mg_objects = [vine]
        before = self.game.mg_corruption
        self.game.handle_minigame_key(pygame.K_SPACE)
        self.assertGreater(self.game.mg_corruption, before)
        self.assertEqual(vine[4], 2)
        self.assertLess(vine[1], 680.0)

        self.game.mg_garden_pulse = 0
        self.game.handle_minigame_key(pygame.K_2)
        self.game.handle_minigame_key(pygame.K_SPACE)
        self.assertEqual(vine[4], 1)
        self.game.mg_garden_pulse = 0
        self.game.handle_minigame_key(pygame.K_SPACE)
        self.assertNotIn(vine, self.game.mg_objects)
        self.assertGreaterEqual(self.game.mg_score, 12)

    def test_phobos_defeat_enters_room_and_disables_secret_codes(self):
        self.game.start_new_game()
        self.game.phobos_route = True
        self.game.story_winner = "phobos"
        self.game.record_saved = True
        self.game.game_over = True
        self.game.secret_buffer = "matri"
        self.game.physical_secret_buffer = "por"
        self.game.update()
        self.assertEqual(self.game.story_overlay, 300)
        self.assertFalse(self.game.game_over)
        self.assertEqual(self.game.secret_buffer, "")
        self.assertEqual(self.game.physical_secret_buffer, "")
        self.game.feed_secret_char("matrix")
        self.game.start_secret("porn_gallery")
        self.assertEqual(self.game.matrix_timer, 0)
        self.assertIsNone(self.game.secret_overlay)
        self.game.start_new_game()

    def test_secret_codes_only_start_during_live_tetris(self):
        self.game.start_new_game()
        self.game.matrix_timer = 0
        self.game.secret_cooldown = 0
        for mode, overlay, paused, game_over in (
            ("menu", None, False, False),
            ("game", 100, False, False),
            ("game", None, True, False),
            ("game", None, False, True),
            ("minigame", None, False, False),
        ):
            with self.subTest(mode=mode, overlay=overlay, paused=paused, game_over=game_over):
                self.game.mode = mode
                self.game.story_overlay = overlay
                self.game.paused = paused
                self.game.game_over = game_over
                self.game.start_secret("matrix")
                self.assertEqual(self.game.matrix_timer, 0)
        self.game.mode = "game"
        self.game.story_overlay = None
        self.game.paused = False
        self.game.game_over = False
        self.game.secret_cooldown = 0
        self.game.start_secret("matrix")
        self.assertGreater(self.game.matrix_timer, 0)
        self.game.toggle_pause()
        self.assertEqual(self.game.matrix_timer, 0)
        self.assertFalse(self.game.vtd_active)
        self.game.toggle_pause()
        self.game.start_new_game()

    def test_classic_mode_uses_two_complete_bags(self):
        old_mode = self.game.figure_fall_mode
        old_enabled = self.game.character_enabled.copy()
        try:
            self.game.figure_fall_mode = "classic"
            self.game.character_enabled = {kind: True for kind in old_enabled}
            self.game.classic_piece_queue = []
            self.game.classic_piece_signature = ()
            self.game.spawn_history = []
            self.assertEqual(self.game.figure_fall_label(), "КЛАССИК")
            sequence = [self.game.random_piece() for _ in range(14)]
            expected = set(old_enabled)
            self.assertEqual(set(sequence[:7]), expected)
            self.assertEqual(set(sequence[7:]), expected)
            self.assertEqual(len(set(sequence[:7])), 7)
            self.assertEqual(len(set(sequence[7:])), 7)
            self.assertNotEqual(sequence[6], sequence[7])
        finally:
            self.game.figure_fall_mode = old_mode
            self.game.character_enabled = old_enabled
            self.game.classic_piece_queue = []
            self.game.classic_piece_signature = ()

    def test_menu_voice_and_room_layers(self):
        self.assertEqual(self.game.menu_voice_paths, [])
        self.assertEqual(self.game.pause_voice_paths, [])
        self.assertIsNotNone(self.game.phobos_room_outside)
        self.game.phobos_room_stage = "room"
        self.game.phobos_room_tick = 0
        self.game.draw_phobos_room()
        first = pygame.image.tostring(self.game.canvas.subsurface((123, 155, 62, 111)), "RGB")
        self.game.phobos_room_tick = 330
        self.game.draw_phobos_room()
        second = pygame.image.tostring(self.game.canvas.subsurface((123, 155, 62, 111)), "RGB")
        self.assertNotEqual(first, second)

    def test_phobos_room_has_six_clean_seated_poses(self):
        self.assertEqual(len(self.game.phobos_room_emotions), 6)
        for pose in self.game.phobos_room_emotions:
            with self.subTest(size=pose.get_size()):
                pixels = pygame.mask.from_surface(pose, 8).count()
                self.assertGreater(pixels, pose.get_width() * pose.get_height() * 0.45)
                self.assertLess(pixels, pose.get_width() * pose.get_height() * 0.90)
        self.assertTrue((ROOT / "assets/cutscenes/phobos_room/background_v2.png").is_file())

    def test_room_variants_and_action_frames_draw(self):
        self.game.ensure_story100_assets()
        self.assertEqual(len(self.game.story200_action_frames), 14)
        self.game.phobos_room_stage = "room"
        self.game.phobos_room_layout = "table"
        self.game.draw_phobos_room()


if __name__ == "__main__":
    unittest.main()
