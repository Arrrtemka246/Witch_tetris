import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
from pathlib import Path
import unittest
from unittest.mock import patch
import pygame
from main import Game
from ending import Ending, PROMPT_AT, TRACK

class EndingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.g=Game()
        cls.scene=Ending()
        cls.g.ending=cls.scene

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_assets_and_every_scene_boundary(self):
        self.assertTrue(TRACK.is_file())
        self.assertEqual(len(list((TRACK.parents[3] / 'cutscenes' / 'ending' / 'ready').glob('*.png'))), 99)
        self.assertEqual(len(self.scene.heart),24)
        self.assertEqual(len(self.scene.enemies),6)
        for t in (0,7,13.9,14,17.9,18,20,21.8,22,23.9,24,26,27,28.66,31):
            self.scene.draw(self.g.canvas,t)

    def test_numpy_is_not_a_runtime_dependency(self):
        requirements = (TRACK.parents[4] / 'requirements.txt').read_text(encoding='utf-8')
        self.assertNotIn('numpy', requirements.lower())

    def test_guardian_loss_enters_ending_and_preserves_record(self):
        g=self.g; g.mode='game'; g.guardians_route=True
        g.story_winner='guardians'; g.game_over=True
        with patch.object(g,'save_record') as save:
            g.update()
        save.assert_called_once()
        self.assertEqual(g.mode,'ending')
        self.assertFalse(g.game_over)

    def test_any_key_waits_until_prompt_then_returns_to_menu(self):
        g=self.g; g.mode='ending'
        with patch.object(self.scene,'elapsed',return_value=PROMPT_AT-.01):
            g.handle_keydown(pygame.K_ESCAPE)
        self.assertEqual(g.mode,'ending')
        with patch.object(self.scene,'elapsed',return_value=PROMPT_AT+.01):
            g.handle_keydown(pygame.K_a)
        self.assertEqual(g.mode,'menu')
        self.assertFalse(g.music.special_lock)

    def test_new_game_always_starts_with_authored_track(self):
        g=self.g; g.phobos_enabled=True; g.music.enabled=True
        for _ in range(2):
            g.start_new_game()
            self.assertEqual(g.music.current.stem.lower(),'arrogant_prince_of_the_obsidian_court')

    def test_escape_first_chain_is_not_repeated(self):
        g=self.g; g.enter_phobos_room('test')
        g.react_phobos_room_key(pygame.K_ESCAPE)
        first=g.phobos_room_chain['lines']
        g.react_phobos_room_key(pygame.K_ESCAPE)
        self.assertNotEqual(first,g.phobos_room_chain['lines'])

    def test_break_voice_runs_once_before_choice(self):
        g=self.g; g.reset(); g.mode='game'; g.story_overlay=200
        g.story200_stage='cinematic_break'; g.break_voice_played=False
        with patch.object(g,'play_external_voice') as voice:
            g.update(); g.update()
        voice.assert_called_once_with(g.voice_paths['cant_end'],force=True)

    def test_launch_warning_precedes_intro_and_any_key_continues(self):
        g=self.g; g.restart_intro(show_boot=True)
        self.assertTrue(g.intro_boot_active)
        g.draw_intro()
        g.handle_keydown(pygame.K_a)
        self.assertFalse(g.intro_boot_active)
        self.assertEqual(g.intro_scene,0)

    def test_story200_matrix_code_starts_video_and_quits(self):
        g=self.g; g.reset(); g.mode='game'; g.story_overlay=200; g.story200_stage='choice'
        with patch.object(g,'begin_meta_video') as begin:
            for char in 'matrix':
                g.handle_keydown(pygame.K_UNKNOWN,char)
        begin.assert_called_once_with('matrix','matrix_quit')

        g.running=True; g.meta_video_after='matrix_quit'; g.meta_video_music_state={}
        with patch.object(g.music,'leave_special') as leave:
            g.finish_meta_video()
        leave.assert_called_once_with(restart=False)
        self.assertFalse(g.running)
        g.running=True

    def test_story200_porn_code_starts_video_and_returns_confirmation(self):
        g=self.g; g.reset(); g.mode='game'; g.story_overlay=200; g.story200_stage='choice'
        with patch.object(g,'begin_meta_video') as begin:
            for char in 'porn':
                g.handle_keydown(pygame.K_UNKNOWN,char)
        begin.assert_called_once_with('porn','porn_confirm')

        g.meta_video_after='porn_confirm'; g.meta_video_music_state={'paused':True}
        with patch.object(g.music,'leave_special'):
            g.finish_meta_video()
        self.assertEqual(g.story_overlay,200)
        self.assertEqual(g.story200_stage,'porn_confirm')

    def test_line100_music_waits_for_any_key(self):
        g=self.g; g.mode='game'; g.story_overlay=100; g.story100_stage='wait_key'
        with patch.object(g,'play_cutscene_music') as play:
            g.handle_keydown(pygame.K_a)
        play.assert_called_once_with('lines100')
        self.assertEqual(g.story100_stage,'after_key')

    def test_phobos_route_keeps_line_clear_sfx_without_voice(self):
        from unittest.mock import Mock
        g=self.g; g.start_new_game(); g.phobos_route=True; g.story_winner='phobos'
        sound, channel = Mock(), Mock()
        g.line_clear_sfx=[sound]; g.heart_sfx=None; g.sfx_channel=channel
        g.board[-1]=[None,None]+[{'kind':'T','surface':None} for _ in range(8)]
        g.current={'kind':'O','rot':0,'x':0,'y':18}
        g.lock_piece()
        channel.play.assert_called_once_with(sound)

if __name__=='__main__': unittest.main()
