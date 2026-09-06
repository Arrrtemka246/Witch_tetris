from __future__ import annotations

import os
import unittest
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")


class DialogueBankTests(unittest.TestCase):
    def test_supplied_dialogue_bank_is_complete_and_parseable(self):
        from phobos_dialogue import load_phobos_dialogue
        root=Path(__file__).resolve().parents[1]
        bank=load_phobos_dialogue(root/"assets/cutscenes/phobos_room/spec/PHOBOS_VTD_DIALOGUE_BANK_RU_v2.md")
        self.assertEqual(len(bank["intros"]),10)
        self.assertEqual(len(bank["random"]),10)
        self.assertGreaterEqual(len(bank["vtd"]),24)


class V639IntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import pygame
        from main import Game
        cls.pygame=pygame
        cls.game=Game()

    @classmethod
    def tearDownClass(cls):
        cls.pygame.quit()

    def test_collection_has_xxx_gallery_but_no_phobos_room(self):
        self.game.collection_page="CUTSCENES"
        self.assertNotIn("PHOBOS ROOM",self.game.collection_current_items())
        self.game.collection_page="DEVELOPMENT ARCHIVE"
        self.assertIn("XXX",self.game.collection_current_items())

    def test_hunter_spawns_and_caleb_can_strike_a_bat(self):
        self.game.start_minigame("CALEB — BAT HUNTER")
        self.game.mg_tick=39
        self.game.update_minigame()
        self.assertTrue(self.game.mg_objects)
        bat=self.game.mg_objects[0]
        bat.update({"x":self.game.mg_player[0],"y":self.game.mg_player[1],"hp":1,"max_hp":1})
        before=self.game.mg_score
        self.game.handle_minigame_key(self.pygame.K_SPACE)
        self.assertNotIn(bat,self.game.mg_objects)
        self.assertGreater(self.game.mg_score,before)
        self.game.leave_minigame()

    def test_minigame_keeps_pointer_visible(self):
        self.game.start_minigame("CALEB — BAT HUNTER")
        self.assertTrue(self.pygame.mouse.get_visible())
        self.game.leave_minigame()
