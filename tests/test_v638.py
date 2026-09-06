from __future__ import annotations
import os, random, unittest
from unittest.mock import patch
from collections import defaultdict
os.environ.setdefault('SDL_VIDEODRIVER','dummy'); os.environ.setdefault('SDL_AUDIODRIVER','dummy')
from treasure_octopus import TreasureOctopus

class OctopusTests(unittest.TestCase):
 def test_scoring(self):
  g=TreasureOctopus()
  for _ in range(5): g.press(1)
  self.assertEqual((g.bag,g.score),(0,0))
  for _ in range(7): g.press(1)
  for _ in range(5): g.press(-1)
  self.assertEqual((g.position,g.bag,g.banked,g.score),(0,0,7,10))
 def test_empty_return(self):
  g=TreasureOctopus(); g.press(1); g.press(-1); self.assertEqual(g.position,1)
 def test_four_targets(self):
  for tindex in range(4):
   g=TreasureOctopus(); t=g.tentacles[tindex]; t.length=t.maximum; g.position=1
   self.assertFalse(g.collision()); g.position=t.target; self.assertTrue(g.collision()); self.assertEqual(g.lives,2); self.assertFalse(g.collision())
 def test_entering_danger(self):
  g=TreasureOctopus(); g.position=1; g.tentacles[0].length=g.tentacles[0].maximum; g.press(1); self.assertEqual(g.lives,2)
  for _ in range(75): g.update()
  self.assertEqual((g.position,g.lives),(0,2))
 def test_last_life(self):
  g=TreasureOctopus(); g.lives=1; g.position=2; g.tentacles[0].length=g.tentacles[0].maximum; g.collision(); self.assertTrue(g.over)
 def test_bonus_lives(self):
  for score in (199,499):
   g=TreasureOctopus(); g.score=score; g.lives=1; g.add_score(1); self.assertEqual(g.lives,3)
 def test_speed(self):
  g=TreasureOctopus(); start=g.step_frames; self.assertLess(TreasureOctopus(True).step_frames,start)
  g.score=99; self.assertLess(g.step_frames,start); g.add_score(1); self.assertEqual(g.step_frames,start)
 def test_extensions(self):
  g=TreasureOctopus(rng=random.Random(0)); seen=[set() for _ in g.tentacles]
  for _ in range(1400):
   g.update()
   for i,t in enumerate(g.tentacles): seen[i].add(t.length)
  for t,s in zip(g.tentacles,seen): self.assertEqual(s,set(range(t.maximum+1)))

class IntegratedTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  import pygame
  from main import Game
  cls.pygame=pygame; cls.g=Game()
 @classmethod
 def tearDownClass(cls): cls.pygame.quit()
 def setUp(self):
  self.g.start_new_game(); self.g.record_saved=True; self.g.character_enabled={k:True for k in self.g.character_enabled}
 def room(self):
  self.g.enter_phobos_room('test'); self.g.phobos_room_stage='room'; self.g.phobos_room_intro_pending=False
 def test_inventory(self):
  expected=['SNAKE — BLUNK/CEDRIC/PHOBOS','WILL MAZE','HAY LIN FLIGHT','CALEB RUNNER','CALEB — BAT HUNTER','HEART BREAKER','TARANEE FIRE SHOT','CORNELIA EARTH GARDEN','BLUNK WASHING','IRMA BUBBLE TROUBLE','IRMA WHIRLPOOL','BLUNK TREASURE ESCAPE','CORNELIA STONE COVERS','IRMA DARK WATER PANIC','PHOBOS TETRIS ???']
  self.assertEqual(self.g.minigame_names,expected)
  for name in expected:
   self.g.start_minigame(name)
   for _ in range(5): self.g.update_minigame()
   self.g.draw_minigame(); self.g.leave_minigame()
 def test_clear_codes(self):
  from playtest_features import CLEAR_CODES
  for code in CLEAR_CODES:
   self.g.secret_cooldown=0; self.g.secret_buffer=''; self.g.board[-1]=[{'kind':'T','surface':None}]*10
   self.g.pending_clear={'frames':1,'rows':[19],'kind':'T'}; self.g.score=321; self.g.lines=117
   self.g.feed_secret_char(code.upper()); self.assertTrue(all(c is None for r in self.g.board for c in r),code)
   self.assertIsNone(self.g.pending_clear); self.assertEqual((self.g.score,self.g.lines),(321,117))
 def test_names_not_cheats(self):
  from playtest_features import ROOM_GUARDIANS,CLEAR_CODES,ROOM_LETTERS
  for code in (ROOM_GUARDIANS-CLEAR_CODES)|ROOM_LETTERS:
   self.g.secret_buffer=''; self.g.secret_cooldown=0; self.g.board[-1][0]={'kind':'T','surface':None}
   self.g.feed_secret_char(code); self.assertIsNotNone(self.g.board[-1][0],code)
 def test_room_codes(self):
  from playtest_features import ROOM_GUARDIANS,ROOM_LETTERS,ROOM_REACTIONS
  self.room()
  for code in ROOM_GUARDIANS|ROOM_LETTERS:
   self.g.room_code_buffer=''
   for char in code.upper(): self.g.feed_room_code(char)
   for _ in range(36): self.g.update_room_code()
   self.assertIn(self.g.phobos_room_chain['lines'][0],ROOM_REACTIONS,code)
  for code in ('phobos','фобос'):
   self.g.feed_room_code(code); self.assertEqual(self.g.phobos_room_chain['lines'],['Спасибо'])
 def test_vtd_room(self):
  self.room()
  for n in range(1,13):
   self.g.feed_room_code(('vtd','втд','валентин')[(n-1)%3]); self.assertEqual(self.g.room_vtd_count,n)
   if n==1: self.assertEqual(self.g.phobos_room_chain['lines'],['Я не знаю, кто это.'])
   elif n==2: self.assertEqual(self.g.phobos_room_chain['lines'],['Не понимаю, о чём ты.'])
   elif n==3:
    self.assertTrue(self.g.room_vtd_silent)
    while self.g.room_vtd_timer: self.g.update_room_code()
   elif n<=11:
    self.assertGreater(self.g.room_vtd_timer,0); self.g.draw_phobos_room()
    while self.g.room_vtd_timer: self.g.update_room_code()
    self.assertTrue(self.g.phobos_room_chain['lines'])
   else: self.assertEqual(self.g.phobos_room_chain['lines'],['Мне надоело играть в это.'])
 def test_vtd_voice(self):
  self.g.start_secret('vtd'); self.assertTrue(self.g.vtd_active); self.assertFalse(self.g.vtd_locked)
  p=self.g.voice_paths['brilliant_laugh']; self.assertFalse(self.g.play_external_voice(p,True))
  self.assertFalse(self.g.play_voice('brilliant_laugh',True)); self.assertFalse(self.g.play_voice_if_idle('brilliant_laugh'))
  self.g.queue_external_voice(p); self.assertIsNone(self.g.queued_voice)
  self.g.vtd_channel.stop(); self.g.update(); self.assertFalse(self.g.vtd_active); self.assertTrue(self.g.play_external_voice(p,True))
 def test_guardians_victory(self):
  self.g.character_enabled={k:k=='S' for k in self.g.character_enabled}; self.g.story_overlay=200; self.g.winner_choice=0; self.g.choose_story_winner()
  self.assertEqual(self.g.victory_speaker,'irma'); self.g.story200_tick=180; self.g.draw_story200()
  self.g.story200_tick=421; self.g.update(); self.assertIsNone(self.g.story_overlay); self.assertTrue(self.g.guardians_route)
 def test_phobos_defeat(self):
  self.g.story_overlay=200; self.g.winner_choice=1; self.g.choose_story_winner(); self.assertTrue(self.g.victory_tiles)
  for tick in (1,75,150,250): self.g.story200_tick=tick; self.g.draw_story200()
  self.g.continue_after_story200(); self.g.game_over=True; self.g.update(); self.assertEqual(self.g.story_overlay,300); self.assertFalse(self.g.game_over)
 def test_existing_split(self):
  self.g.story_overlay=200; self.g.winner_choice=1
  with patch('main.random.random',return_value=.95): self.g.choose_story_winner()
  self.assertEqual(self.g.story200_stage,'phobos_split'); self.g.story200_tick=180; self.g.update(); self.assertEqual(self.g.story200_stage,'phobos_win')
 def test_classic_bag_boundary(self):
  self.g.figure_fall_mode='classic'; self.g.classic_piece_queue=[]; calls=0
  def shuffle(bag):
   nonlocal calls
   bag.sort()
   if calls==1: bag.insert(0,bag.pop())
   calls+=1
  with patch('main.random.shuffle',shuffle): seq=[self.g.random_piece() for _ in range(14)]
  self.assertEqual(seq[6],seq[7]); self.assertEqual(set(seq[:7]),set(seq[7:]))
 def test_lock_delay(self):
  self.g.figure_fall_mode='classic'; self.g.current={'kind':'O','rot':0,'x':3,'y':18}; self.g.reset_classic_lock(); keys=defaultdict(bool)
  for _ in range(29): self.g.classic_update(keys)
  self.assertTrue(all(c is None for r in self.g.board for c in r)); self.g.classic_update(keys); self.assertIsNotNone(self.g.board[19][3])
  self.g.classic_lock_resets=15; self.g.classic_lock_frames=20; self.g.classic_adjusted(True); self.assertEqual(self.g.classic_lock_frames,20)
