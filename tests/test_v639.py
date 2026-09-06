from __future__ import annotations

import os
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

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

    def test_updated_opening_bank_has_nine_intros_and_escape_event(self):
        from phobos_dialogue import load_phobos_dialogue
        root=Path(__file__).resolve().parents[1]
        bank=load_phobos_dialogue(
            root/"assets/cutscenes/phobos_room/spec/PHOBOS_VTD_DIALOGUE_BANK_RU_v2.md",
            root/"assets/cutscenes/phobos_room/spec/PHOBOS_ROOM_OPENING_CHAINS_RU_v2.md",
        )
        self.assertEqual(len(bank["intros"]),9)
        self.assertEqual(len(bank["intros"][0]["lines"]),7)
        self.assertEqual(len(bank["escape"]),7)


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

    def test_minigame_hides_pointer_and_restores_it_on_exit(self):
        self.game.start_minigame("CALEB — BAT HUNTER")
        self.assertFalse(self.pygame.mouse.get_visible())
        self.game.leave_minigame()
        self.assertTrue(self.pygame.mouse.get_visible())

    def test_wasd_and_russian_physical_keys_duplicate_arrows(self):
        from main import SC_D
        self.game.start_minigame("CALEB — BAT HUNTER")
        start=self.game.mg_player[0]
        self.game.handle_minigame_key(self.pygame.K_a)
        self.assertLess(self.game.mg_player[0],start)
        moved=self.game.mg_player[0]
        self.game.handle_minigame_key(0,SC_D)
        self.assertGreater(self.game.mg_player[0],moved)
        self.game.leave_minigame()

    def test_grown_garden_vine_can_be_uprooted_by_its_stem(self):
        self.game.start_minigame("CORNELIA EARTH GARDEN")
        self.game.mg_player=[400.0,780.0]
        mature=[400.0,float(self.game.mg_arena.top+190),"vine",0,1,1]
        self.game.mg_objects=[mature]
        self.game.mg_garden_color=0; self.game.mg_garden_pulse=0
        self.game.handle_minigame_key(self.pygame.K_SPACE)
        self.assertNotIn(mature,self.game.mg_objects)
        self.game.leave_minigame()

    def test_music_collection_has_all_music_but_no_voice_or_sfx(self):
        tracks=self.game.scan_collection_music()
        paths=[str(path).replace("\\","/") for _,path in tracks]
        self.assertGreaterEqual(len(paths),70)
        self.assertTrue(any("/user_music/hunter/" in path for path in paths))
        self.assertFalse(any("/voice/" in path or "/sfx/" in path for path in paths))
        self.assertFalse(any(path.endswith("phobos_type_tick.wav") for path in paths))

    def test_empty_collection_entries_are_not_shown(self):
        self.game.collection_page="DEVELOPMENT ARCHIVE"
        self.assertNotIn("FACTS & NOTES",self.game.collection_current_items())

    def test_opening_collection_does_not_restart_menu_music(self):
        with patch.object(self.game.music,"set_phase") as set_phase, patch.object(self.pygame.mixer.music,"stop") as stop:
            self.game.open_collection()
        set_phase.assert_not_called(); stop.assert_not_called()

    def test_room_vtd_pauses_and_resumes_the_same_music_stream(self):
        self.game.enter_phobos_room("test")
        self.game.phobos_room_stage="room"; self.game.phobos_room_intro_pending=False
        self.game.room_vtd_count=3
        with patch.object(self.pygame.mixer.music,"get_busy",return_value=True), patch.object(self.pygame.mixer.music,"pause") as pause:
            self.game.room_code("vtd")
        pause.assert_called_once(); self.assertTrue(self.game.room_vtd_music_paused)
        self.game.room_vtd_timer=1; self.game.room_vtd_index=max(0,len(self.game.room_vtd_sequence)-1)
        with patch.object(self.pygame.mixer.music,"unpause") as unpause, patch.object(self.pygame.mixer.music,"load") as load:
            self.game.update_room_code()
        unpause.assert_called_once(); load.assert_not_called()

    def test_record_reset_writes_a_valid_empty_json_list(self):
        with tempfile.TemporaryDirectory() as directory:
            target=Path(directory)/"records.json"; target.write_text('[{"lines": 20, "score": 500}]',encoding="utf-8")
            with patch("main.RECORDS_PATH",target): self.game.reset_records()
            self.assertEqual(json.loads(target.read_text(encoding="utf-8")),[])
