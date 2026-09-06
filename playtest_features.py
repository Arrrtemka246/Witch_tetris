"""Test-build scenes, local room codes and Classic conveniences."""
from __future__ import annotations
import json
import math
import random
from pathlib import Path
import pygame
ROOT=Path(__file__).resolve().parent
FPS=60
CLEAR_CODES={'guardians','witch','стражницы','стражничы','чародейки','витч','кондракар','kandrakar'}
ROOM_GUARDIANS={'guardians','witch','will','irma','tarani','taranee','haylin','cornelia','стражницы','стражничы','чародейки','витч','вилл','ирма','тарани','хайлин','корнелия'}
ROOM_LETTERS=set('ijltozs')
PHOBOS_CODES={'phobos','фобос'}
VTD_CODES={'vtd','втд','валентин'}
ROOM_REACTIONS=['Их здесь больше нет.','Бесполезно.','Ха-ха-ха. Я победил.','Они распались на пиксели. Хотя я сохранил их фотографии. Можешь посмотреть их в коллекции.']
VICTORY_LINES={
 'will':['Мы снова вместе!','Сердце Кондракара снова с нами!'],
 'irma':['Ура! Можно наконец выдохнуть!','Ну что, кто теперь смеётся?'],
 'taranee':['Мы справились!','Вместе мы сильнее!'],
 'cornelia':['Вот теперь порядок.','Победа за нами!'],
 'haylin':['Ура! Мы свободны!','Я знала, что у нас получится!'],
 'caleb':['Меридиан свободен!','Мы победили. Вместе.'],
 'blunk':['Бланк тоже герой!','Бланк знал: мы победим!']}
NAMES={'will':'ВИЛЛ','irma':'ИРМА','taranee':'ТАРАНИ','cornelia':'КОРНЕЛИЯ','haylin':'ХАЙ ЛИН','caleb':'КАЛЕБ','blunk':'БЛАНК'}

class PlaytestFeatures:
    def reset_playtest(self):
        self.room_code_buffer=''
        self.room_code_idle=self.room_vtd_count=self.room_vtd_timer=0
        self.room_vtd_line=''
        self.cheat_notice=0
        self.classic_lock_frames=self.classic_lock_resets=0
        self.classic_das_direction=self.classic_das_frames=0
        self.victory_speaker=None
        self.victory_line=''
        self.victory_laughed=False
        self.room_vtd_sequence=[]
        self.room_vtd_index=0
        self.room_vtd_entry=None
        self.room_vtd_silent=False
        self.room_vtd_matrix=False

    def phobos_laugh(self):
        path=self.voice_paths.get('brilliant_laugh')
        return self.play_external_voice(path,force=True) if path else False

    def silence_for_vtd(self):
        for channel in (self.voice_channel,self.menu_voice_channel):
            if channel: channel.stop()
        self.queued_voice=None
        self.queued_voice_delay=0
        self.pause_voice_pending=None
        self.pause_voice_delay=0
        self.vtd_locked=False

    def room_say(self,text):
        self.room_say_lines([text] if text else [])

    def room_say_lines(self,lines):
        self.phobos_room_intro_pending=False
        self.phobos_room_reaction=None
        self.phobos_room_chain={'id':'secret_reaction','lines':list(lines)} if lines else None
        self.phobos_room_line=0
        self.phobos_room_type_started_ms=pygame.time.get_ticks()
        self.phobos_room_type_complete=False
        self.phobos_room_wait_until=0
        self.phobos_room_next_ms=10**12

    def room_code(self,code):
        self.room_code_buffer=''; self.room_code_idle=0
        if code in PHOBOS_CODES:
            self.room_say('Спасибо')
        elif code in ROOM_GUARDIANS or code in ROOM_LETTERS:
            self.room_say(random.choice(ROOM_REACTIONS))
        elif code in VTD_CODES:
            self.room_vtd_count+=1
            if self.room_vtd_count==1:
                self.room_say('Я не знаю, кто это.')
            elif self.room_vtd_count==2:
                self.room_say('Не понимаю, о чём ты.')
            elif self.room_vtd_count==3:
                self.room_say_lines([])
                self.room_vtd_silent=True
                self.room_vtd_timer=FPS*2
                self.phobos_room_intro_pending=False
            elif self.room_vtd_count<=11:
                pool=list(getattr(self,'phobos_dialogue',{}).get('vtd',[]))
                recent=set(getattr(self,'phobos_vtd_recent',[])[-4:])
                eligible=[entry for entry in pool if entry.get('id') not in recent] or pool
                if eligible:
                    if random.random()<.05:
                        self.room_vtd_entry={'id':'matrix-combo','lines':['The Matrix Has You...','Матрицу вы будете показывать?','Спойлер: нет.'],
                                             'reply':['Ха-ха-ха!','Теперь я понимаю ещё меньше, чем после первого «VTD».']}
                        self.room_vtd_matrix=True
                    else:
                        self.room_vtd_entry=random.choice(eligible)
                        self.room_vtd_matrix='matrix' in self.room_vtd_entry.get('id','')
                    self.phobos_vtd_recent=(getattr(self,'phobos_vtd_recent',[])+[self.room_vtd_entry.get('id')])[-4:]
                    self.room_vtd_sequence=list(self.room_vtd_entry.get('lines',[]))
                    self.room_vtd_index=0
                    self.room_vtd_line=self.room_vtd_sequence[0] if self.room_vtd_sequence else ''
                    self.room_vtd_timer=max(FPS*2,len(self.room_vtd_line)*3)
                    self.room_vtd_silent=False
                    self.phobos_room_intro_pending=False
                    if self.voice_channel: self.voice_channel.stop()
                    self.queued_voice=None
                    if pygame.mixer.get_init(): pygame.mixer.music.stop()
                else:
                    self.room_say('Код сработал, но банк реплик не найден.')
            else:
                self.room_say('Мне надоело играть в это.')

    def feed_room_code(self,text):
        if self.room_vtd_timer or self.phobos_room_stage!='room':
            return bool(self.room_vtd_timer)
        aliases=PHOBOS_CODES|ROOM_GUARDIANS|VTD_CODES
        consumed=False
        for ch in text.lower():
            if not ch.isalpha(): continue
            self.room_code_buffer=(self.room_code_buffer+ch)[-24:]
            self.room_code_idle=0; consumed=True
            matches=[code for code in aliases if self.room_code_buffer.endswith(code)]
            if matches:
                self.room_code(max(matches,key=len)); return True
            prefixes=[self.room_code_buffer[i:] for i in range(len(self.room_code_buffer)) if any(code.startswith(self.room_code_buffer[i:]) for code in aliases) or self.room_code_buffer[i:] in ROOM_LETTERS]
            self.room_code_buffer=max(prefixes,key=len) if prefixes else ''
        return consumed

    def update_room_code(self):
        if self.room_vtd_timer:
            self.room_vtd_timer-=1
            if not self.room_vtd_timer:
                if self.room_vtd_silent:
                    self.room_vtd_silent=False
                    self.phobos_room_next_ms=pygame.time.get_ticks()+40000
                elif self.room_vtd_index+1<len(self.room_vtd_sequence):
                    self.room_vtd_index+=1
                    self.room_vtd_line=self.room_vtd_sequence[self.room_vtd_index]
                    self.room_vtd_timer=max(FPS*2,len(self.room_vtd_line)*3)
                else:
                    reply=list((self.room_vtd_entry or {}).get('reply',[]))
                    if not reply:
                        reactions=getattr(self,'phobos_dialogue',{}).get('reactions',[])
                        reply=[random.choice(reactions)] if reactions else []
                    self.room_vtd_sequence=[]; self.room_vtd_entry=None
                    self.room_say_lines(reply)
                    room_track=ROOT/'assets/audio/music/phobos_room/PhobosthemeDark.mp3'
                    if room_track.exists() and pygame.mixer.get_init():
                        try:
                            pygame.mixer.music.load(str(room_track)); pygame.mixer.music.play(-1); pygame.mixer.music.set_volume(.68)
                        except pygame.error: pass
            return True
        if self.room_code_buffer:
            self.room_code_idle+=1
            if self.room_code_idle>=36:
                if self.room_code_buffer in ROOM_LETTERS: self.room_code(self.room_code_buffer)
                elif self.room_code_idle>=FPS*3: self.room_code_buffer=''
        return False

    def draw_room_cameo(self):
        if not self.room_vtd_timer or self.room_vtd_silent: return False
        self.canvas.fill((0,0,0))
        if self.room_vtd_matrix:
            veil=pygame.Surface(self.canvas.get_size(),pygame.SRCALPHA); veil.fill((0,80,20,75)); self.canvas.blit(veil,(0,0))
            for i in range(36):
                x=(i*73+self.room_vtd_timer*3)%self.canvas.get_width(); y=(i*131+self.room_vtd_timer*5)%self.canvas.get_height()
                self.canvas.blit(self.small.render(str(i%2),True,(40,145,65)),(x,y))
        if self.vtd_observer: self.draw_story100_sprite(self.vtd_observer,(self.canvas.get_width()//2,460),650)
        self.draw_wrapped_center('ВАЛЕНТИН',90,self.canvas.get_width()-100,self.font,(150,235,165))
        if self.room_vtd_line: self.draw_wrapped_center(self.room_vtd_line,865,self.canvas.get_width()-100,self.font)
        return True

    def prepare_victory(self):
        self.ensure_story100_assets()
        self.victory_laughed=False
        self.victory_speaker=self.pick_active_character()
        self.victory_line=random.choice(VICTORY_LINES[self.victory_speaker]) if self.victory_speaker else ''
        self.story200_stage=('guardians_win' if self.guardians_route else 'phobos_win' if self.horror_piece_mode else 'phobos_split')
        self.story200_tick=0
        self.queued_voice=None
        if self.voice_channel: self.voice_channel.stop()
        self.victory_tiles=[]
        source=self.story100_assets.get('phobos_action') or self.phobos_resistance_body
        if source:
            h=640; w=max(1,int(source.get_width()*h/source.get_height()))
            im=pygame.transform.scale(source,(w,h))
            rng=random.Random(638); left=(self.canvas.get_width()-w)//2
            for y in range(0,h,14):
                for x in range(0,w,14):
                    rect=pygame.Rect(x,y,min(14,w-x),min(14,h-y))
                    frag=im.subsurface(rect).copy()
                    if pygame.mask.from_surface(frag,8).count():
                        self.victory_tiles.append((frag,left+x,170+y,rng.randrange(-400,1260),rng.randrange(-300,1250),rng.random()*.25))

    def update_victory(self):
        if self.story200_stage not in ('guardians_win','phobos_win'): return False
        if self.phobos_route and self.story200_tick>=FPS*2.5 and not self.victory_laughed:
            self.victory_laughed=True; self.phobos_laugh()
        if self.story200_tick>=FPS*7 and not (self.voice_channel and self.voice_channel.get_busy()):
            self.continue_after_story200()
        return True

    def draw_victory(self):
        if self.story200_stage not in ('guardians_win','phobos_win'): return False
        width=self.canvas.get_width(); t=self.story200_tick/FPS
        if self.phobos_route:
            progress=min(1,t/2.5)
            for frag,x,y,sx,sy,delay in self.victory_tiles:
                local=max(0,min(1,(progress-delay)/max(.01,1-delay))); ease=1-(1-local)**3
                self.canvas.blit(frag,(int(sx+(x-sx)*ease),int(sy+(y-sy)*ease)))
            self.draw_wrapped_center('ФОБОС ПОБЕДИЛ',95,width-80,self.big,(245,160,211))
            if t>=2.5: self.draw_wrapped_center('Ха-ха-ха! Власть над Меридианом снова моя!',845,width-100,self.font)
        else:
            self.draw_wrapped_center('СТРАЖНИЦЫ ПОБЕДИЛИ',110,width-60,self.big,(229,194,255))
            active=self.active_intro_characters(); count=len(active)
            for i,ch in enumerate(active):
                x=int(width*(i+1)/(count+1)); jump=int(45*max(0,math.sin(t*5-i*.55)))
                source=self.story100_assets.get(ch+'_action') or self.intro_images.get(ch+'_normal')
                if source:
                    height=min(330,(width/(count+1)-10)*source.get_height()/source.get_width())
                    self.draw_story100_sprite(source,(x,570-jump),height)
            if active: self.draw_wrapped_center('Ура! Победа!',735,width-100,self.font,(250,223,134))
            if t>=2 and self.victory_speaker: self.draw_wrapped_center(NAMES[self.victory_speaker]+': '+self.victory_line,830,width-100,self.font)
        self.draw_wrapped_center('SPACE — продолжить',980,width-80,self.small,(179,166,192))
        return True

    def reset_classic_lock(self):
        self.classic_lock_frames=self.classic_lock_resets=0
        if self.figure_fall_mode=='classic': self.frame_counter=0

    def classic_adjusted(self,was_grounded):
        if self.figure_fall_mode=='classic' and was_grounded and self.classic_lock_resets<15:
            self.classic_lock_frames=0; self.classic_lock_resets+=1

    def classic_update(self,keys):
        if self.figure_fall_mode!='classic' or self.current is None: return
        direction=int(keys[pygame.K_RIGHT] or 7 in self.held_scancodes)-int(keys[pygame.K_LEFT] or 4 in self.held_scancodes)
        if direction!=self.classic_das_direction: self.classic_das_direction=direction; self.classic_das_frames=0
        if direction:
            self.classic_das_frames+=1
            if self.classic_das_frames>=10 and (self.classic_das_frames-10)%3==0: self.move(direction,0)
        if self.collides(self.current['x'],self.current['y']+1,self.current['rot']):
            self.classic_lock_frames+=1
            if self.classic_lock_frames>=30: self.lock_piece()
        else: self.classic_lock_frames=0

    def draw_classic_ghost(self):
        if self.figure_fall_mode!='classic' or self.current is None or self.pending_clear: return
        y=self.current['y']
        while not self.collides(self.current['x'],y+1,self.current['rot']): y+=1
        if y==self.current['y']: return
        for dx,dy in self.shape():
            rect=pygame.Rect(30+(self.current['x']+dx)*50+4,30+(y+dy)*50+4,42,42)
            pygame.draw.rect(self.canvas,(125,155,185),rect,2)
