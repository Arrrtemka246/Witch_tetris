"""Discrete Octopus-style rules; independent of Snake and other mini-games."""
from __future__ import annotations
import math
import random
from dataclasses import dataclass

@dataclass
class Tentacle:
    target: int
    maximum: int
    length: int = 0
    direction: int = 1
    wait: int = 0

class TreasureOctopus:
    def __init__(self, game_b=False, rng=None):
        self.rng=rng or random.Random()
        self.game_b=game_b
        self.position=0
        self.bag=self.banked=self.score=self.tick=self.pause=self.flash=self.grab=0
        self.lives=3
        self.over=False
        self.message=''
        self.bonus_awarded=set()
        self.tentacles=[Tentacle(i+2,n,wait=i*2+2) for i,n in enumerate((5,4,3,2))]

    @property
    def step_frames(self):
        return max(9,(27 if self.game_b else 36)-(self.score%100)//5)

    def add_score(self,amount):
        old=self.score
        self.score+=amount
        for mark in range(old+1,self.score+1):
            if mark%1000 in (200,500) and mark not in self.bonus_awarded:
                self.bonus_awarded.add(mark)
                self.lives=3
                self.message='БЛАНКИ ВЕРНУЛИСЬ!'
                self.flash=90

    def collision(self):
        if self.over or self.pause or self.position<2:
            return False
        if any(t.target==self.position and t.length==t.maximum for t in self.tentacles):
            self.lives-=1
            self.bag=0
            self.pause=self.flash=75
            self.message='СЕДРИК ПОЙМАЛ БЛАНКА!'
            self.over=self.lives==0
            return True
        return False

    def press(self,direction):
        if self.over or self.pause or self.collision():
            return
        if direction>0:
            if self.position<5:
                self.position+=1
            else:
                self.bag+=1
                self.add_score(1)
                self.grab=12
        elif self.position>1:
            self.position-=1
        elif self.position==1 and self.bag:
            self.position=0
            self.banked+=self.bag
            self.bag=0
            self.add_score(3)
            self.message='+3 — ДОБЫЧА В ЛОДКЕ'
            self.flash=60
            self.pause=25
        self.collision()

    def update(self):
        if self.over:
            return
        self.tick+=1
        self.flash=max(0,self.flash-1)
        self.grab=max(0,self.grab-1)
        if self.pause:
            self.pause-=1
            if not self.pause and self.position!=0:
                self.position=0
                for i,t in enumerate(self.tentacles):
                    t.length=0; t.direction=1; t.wait=i*2+3
            return
        if self.tick%self.step_frames==0:
            for t in self.tentacles:
                if t.wait:
                    t.wait-=1
                    continue
                t.length+=t.direction
                if t.length>=t.maximum:
                    t.length=t.maximum; t.direction=-1; t.wait=self.rng.randint(0,1)
                elif t.length<=0:
                    t.length=0; t.direction=1; t.wait=self.rng.randint(1,3 if self.game_b else 5)
        self.collision()


def draw_treasure(game):
    import pygame
    state=game.treasure; canvas=game.canvas; arena=game.mg_arena
    def pt(x,y): return int(arena.left+x*arena.width),int(arena.top+y*arena.height)
    def label(text,pos,color=(233,218,161)):
        im=game.small.render(text,True,color); canvas.blit(im,im.get_rect(center=pt(*pos)))
    def sprite(src,center,height):
        if src is None: return
        scale=height/src.get_height()
        im=pygame.transform.scale(src,(max(1,int(src.get_width()*scale)),int(height)))
        canvas.blit(im,im.get_rect(midbottom=center))
    for y in range(arena.height):
        f=y/arena.height
        pygame.draw.line(canvas,(int(15+12*f),int(36+12*f),int(40+16*f)),(arena.left,arena.top+y),(arena.right-1,arena.top+y))
    for x in range(arena.left,arena.right,9):
        y=pt(0,.27)[1]+int(3*math.sin(x*.045))
        pygame.draw.line(canvas,(76,127,122),(x,y),(x+8,y),2)
    boat=[pt(.025,.22),pt(.265,.22),pt(.225,.29),pt(.065,.29)]
    pygame.draw.polygon(canvas,(84,52,30),boat)
    pygame.draw.polygon(canvas,(207,162,83),boat,3)
    pygame.draw.line(canvas,(207,162,83),pt(.09,.20),pt(.28,.30),4)
    pygame.draw.lines(canvas,(76,105,76),False,[pt(.02,.86),pt(.23,.87),pt(.36,.90),pt(.97,.90)],5)
    positions=[pt(.13,.22),pt(.18,.43),pt(.29,.76),pt(.46,.81),pt(.64,.82),pt(.83,.80)]
    origins=[(.68,.35),(.70,.39),(.74,.43),(.80,.45)]
    bends=[(.34,.47),(.43,.53),(.60,.59),(.84,.60)]
    for i,tentacle in enumerate(state.tentacles):
        start=pt(*origins[i]); bend=pt(*bends[i]); end=positions[tentacle.target]; end=(end[0],end[1]-45)
        points=[start]
        for segment in range(1,tentacle.maximum+1):
            t=segment/tentacle.maximum
            p=(int((1-t)**2*start[0]+2*(1-t)*t*bend[0]+t*t*end[0]),int((1-t)**2*start[1]+2*(1-t)*t*bend[1]+t*t*end[1]))
            if segment<=tentacle.length:
                pygame.draw.line(canvas,(8,24,18),points[-1],p,25)
                pygame.draw.line(canvas,(58,100,60),points[-1],p,19)
                pygame.draw.line(canvas,(188,178,103),points[-1],p,8)
                pygame.draw.circle(canvas,(143,39,47),(p[0]-7,p[1]-3),5)
            points.append(p)
        if tentacle.length:
            tip=points[tentacle.length]
            monster=game.mg_art.get(f'will_enemy_{i+1}')
            if monster:
                size=70
                scale=min(size/monster.get_width(),size/monster.get_height())
                head=pygame.transform.smoothscale(monster,(max(1,int(monster.get_width()*scale)),max(1,int(monster.get_height()*scale))))
                canvas.blit(head,head.get_rect(center=tip))
            else:
                pygame.draw.circle(canvas,(126,48,75),tip,18)
                pygame.draw.circle(canvas,(245,75,95),(tip[0]-6,tip[1]-3),3)
                pygame.draw.circle(canvas,(245,75,95),(tip[0]+6,tip[1]-3),3)
    body=getattr(game,'treasure_cedric',None)
    if getattr(game,'treasure_full_body',False):
        sprite(body,pt(.73,.60),arena.height*.51)
    else:
        # Recovery fallback: original repository portrait, with game-native
        # serpent coils. A supplied full-body image overrides this automatically.
        coil=[pt(.74,.35),pt(.77,.43),pt(.81,.51),pt(.90,.53),pt(.94,.47)]
        pygame.draw.lines(canvas,(9,28,23),False,coil,48)
        pygame.draw.lines(canvas,(46,92,65),False,coil,39)
        pygame.draw.lines(canvas,(179,179,115),False,coil,15)
        sprite(body,pt(.73,.405),arena.height*.30)
    chest=pygame.Rect(0,0,int(arena.width*.14),48); chest.midbottom=pt(.89,.89)
    pygame.draw.rect(canvas,(100,55,30),chest,border_radius=5)
    pygame.draw.rect(canvas,(216,174,70),chest,3,border_radius=5)
    pygame.draw.line(canvas,(216,174,70),chest.midtop,chest.midbottom,6)
    for i in range(6): pygame.draw.circle(canvas,(249,214,87),(chest.left+9+i*15,chest.top-5-(i%2)*5),6)
    blunk=game.intro_images.get('blunk_normal') or game.mg_art.get('blunk_face')
    for x,y in positions[1:]: pygame.draw.ellipse(canvas,(54,79,69),(x-17,y+2,34,6),1)
    bx,by=positions[state.position]
    if state.grab: bx+=8
    if not state.pause or state.position==0 or state.tick%12<7:
        sprite(blunk,(bx,by),82 if state.position else 65)
        if state.bag:
            pygame.draw.ellipse(canvas,(168,116,50),(bx+18,by-44,27,34))
            pygame.draw.circle(canvas,(244,206,80),(bx+31,by-44),6)
    for i in range(max(0,state.lives-1)): sprite(blunk,pt(.05+i*.065,.205),37)
    label(f"GAME {'B' if state.game_b else 'A'}     ДОБЫЧА {state.banked}     В МЕШКЕ {state.bag}",(.5,.035))
    label(state.message if state.flash else '← НАЗАД     → ВПЕРЁД / ВЗЯТЬ СОКРОВИЩЕ',(.5,.94))
    label('1 — GAME A    2 — GAME B',(.5,.975),(141,165,145))
