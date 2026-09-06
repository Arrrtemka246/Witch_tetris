"""Music-clock ending, rendered from the user's original sprite sheets.

All coordinates refer to a 1280x720 stage. The stage is letterboxed inside
the portrait game canvas so the complete final artwork stays visible.
"""
from pathlib import Path
import math
import random
import pygame

ROOT = Path(__file__).resolve().parent
ART = ROOT / 'assets/cutscenes/ending'
TRACK = ROOT / 'assets/audio/music/ending/witch_end_outro.mp3'
DURATION = 28.656327
PROMPT_AT = DURATION + 2


def clamp(v):
    return max(0.0, min(1.0, v))


def prepared(name, count):
    """Load transparent sprites prepared once for the release build."""
    directory = ART / 'ready'
    frames = []
    for index in range(count):
        path = directory / f'{name}_{index:02d}.png'
        if not path.is_file():
            raise FileNotFoundError(f'Prepared ending sprite is missing: {path}')
        frames.append(pygame.image.load(str(path)).convert_alpha())
    return frames


class Ending:
    def __init__(self):
        self.stage = pygame.Surface((1280,720))
        counts = {'will': 6, 'cornelia': 12, 'taranee': 6, 'haylin': 6,
                  'irma': 6, 'caleb': 12, 'blunk': 6, 'will_heart': 8}
        self.frames = {name: prepared(name, count) for name, count in counts.items()}
        self.enemies = prepared('enemies', 6)
        self.cedric = prepared('cedric', 1)[0]
        self.bats = prepared('bats', 6)
        self.heart = prepared('heart', 24)
        self.art1 = pygame.transform.smoothscale(pygame.image.load(str(ART/'art_phobos.jpg')),(1280,720))
        self.art2 = pygame.transform.smoothscale(pygame.image.load(str(ART/'art_witch.jpg')),(1280,720))
        self.font = pygame.font.SysFont('DejaVu Sans',23)
        self.title = pygame.font.SysFont('DejaVu Sans',37,bold=True)
        self.prompt = pygame.font.SysFont('DejaVu Sans',22)
        self.credit_lines = []
        for line in (ROOT/'ending_credits.txt').read_text(encoding='utf-8').splitlines():
            words = line.split(); current = ''
            for word in words:
                candidate = (current+' '+word).strip()
                if self.font.size(candidate)[0]>650 and current:
                    self.credit_lines.append(current); current=word
                else:
                    current=candidate
            self.credit_lines.append(current)
        self.scaled = {}
        rng = random.Random(641)
        # Only the central Phobos silhouette disintegrates. Other image areas
        # cross-fade gently to the final composition supplied by the author.
        mask = pygame.Surface((1280,720)); mask.fill('black')
        pygame.draw.polygon(mask,'white',[(580,22),(670,22),(730,100),(850,145),
                            (855,300),(805,555),(650,620),(450,570),(425,350),(460,170)])
        self.tiles=[]
        for y in range(0,625,9):
            for x in range(420,865,9):
                if mask.get_at((x,y)).r:
                    rect=pygame.Rect(x,y,9,9)
                    self.tiles.append((self.art1.subsurface(rect).copy(),x,y,rng.random()*.5,rng.uniform(-130,130),rng.uniform(-220,-80)))
        self.started=0

    def start(self, game):
        game.save_record()
        game.cancel_secret_effects(restart_music=False)
        game.queued_voice=None
        for ch in (game.voice_channel,game.menu_voice_channel,game.vtd_channel,game.sfx_channel):
            if ch: ch.stop()
        game.music.stop(); game.music.special_lock=True
        game.mode='ending'; game.game_over=False; game.paused=False
        game.story_overlay=None; pygame.mouse.set_visible(False)
        self.started=pygame.time.get_ticks()
        if game.music.enabled and pygame.mixer.get_init():
            pygame.mixer.music.load(str(TRACK))
            pygame.mixer.music.set_volume(game.music.base_volume)
            pygame.mixer.music.play(0)
        # Reset the clock after decoder setup so visuals match playback.
        self.started=pygame.time.get_ticks()

    def elapsed(self):
        return max(0,(pygame.time.get_ticks()-self.started)/1000)

    def key(self, game):
        if self.elapsed()<PROMPT_AT:
            return
        game.music.stop(); game.music.special_lock=False
        game.mode='menu'; game.story_overlay=None; game.game_over=False
        pygame.mouse.set_visible(True)
        game.music.set_phase(-1,force=True)

    def sprite(self, src, pos, height, alpha=255, flip=False):
        height=max(1,int(height)); key=(id(src),height,flip)
        if key not in self.scaled:
            size=(max(1,int(src.get_width()*height/src.get_height())),height)
            self.scaled[key]=pygame.transform.flip(pygame.transform.smoothscale(src,size),flip,False)
        image=self.scaled[key]
        if alpha!=255:
            image=image.copy(); image.set_alpha(max(0,min(255,int(alpha))))
        self.stage.blit(image,image.get_rect(midbottom=(int(pos[0]),int(pos[1]))))

    def center(self, text, y, font=None, color=(244,222,255)):
        im=(font or self.title).render(text,True,color)
        self.stage.blit(im,im.get_rect(center=(640,y)))

    def draw(self, canvas, t=None):
        t=self.elapsed() if t is None else t
        self.stage.fill('black')
        if t<14:
            self.sprite(self.heart[int(t*8)%24],(265,500),340)
            clip=self.stage.get_clip(); self.stage.set_clip((520,40,730,640))
            # The entire authored text traverses the viewport by 14 seconds.
            total=len(self.credit_lines)*34
            start=680-(total+700)*clamp(t/14)
            for i,line in enumerate(self.credit_lines):
                y=int(start+i*34)
                if -35<y<725:
                    im=self.font.render(line,True,(231,208,247))
                    self.stage.blit(im,(535,y))
            self.stage.set_clip(clip)
        elif t<24:
            self.battle(t)
        elif t<26:
            self.stage.blit(self.art1,(0,0))
        else:
            p=clamp((t-26)/2.1)
            self.stage.blit(self.art2,(0,0))
            if p<1:
                old=self.art1.copy(); old.set_alpha(int(255*(1-p)))
                self.stage.blit(old,(0,0))
                for tile,x,y,delay,vx,vy in self.tiles:
                    q=clamp((p-delay)/(1-delay))
                    if q<1:
                        tile.set_alpha(int(255*(1-q)))
                        self.stage.blit(tile,(int(x+vx*q),int(y+vy*q)))
        canvas.fill('black')
        width=canvas.get_width(); height=int(width*720/1280)
        top=(canvas.get_height()-height)//2-45
        canvas.blit(pygame.transform.smoothscale(self.stage,(width,height)),(0,top))
        if t>=28.1:
            text=self.title.render('СПАСИБО ЗА ИГРУ',True,(244,222,255))
            canvas.blit(text,text.get_rect(center=(width//2,top+height+55)))
        if t>=PROMPT_AT:
            for i,line in enumerate(('НАЖМИТЕ ЛЮБУЮ КЛАВИШУ,','ЧТОБЫ ВЕРНУТЬСЯ В МЕНЮ')):
                text=self.prompt.render(line,True,(191,173,207))
                canvas.blit(text,text.get_rect(center=(width//2,top+height+110+i*29)))

    def battle(self,t):
        targets={'will':(220,660),'irma':(350,670),'taranee':(485,675),
                 'caleb':(680,685),'haylin':(790,678),'cornelia':(905,665),'blunk':(405,690)}
        colors={'cornelia':(138,202,94),'irma':(75,169,255),'taranee':(255,113,36),'haylin':(207,244,252)}
        if t<20:
            for i,enemy in enumerate(self.enemies):
                x=1190-(t-14)*85+(i%3)*110
                y=270+(i//3)*245+12*math.sin(t*3+i)
                alpha=255*(1-clamp((t-19.3)/.7))
                self.sprite(enemy,(x,y),170,alpha)
            for i in range(8):
                x=1120-((t-14)*220+i*115)%950
                y=180+(i%3)*85+25*math.sin(t*8+i)
                self.sprite(self.bats[int(t*12+i)%len(self.bats)],(x,y),40,255*(1-clamp((t-19.5)/.5)))
        if 20<=t<22:
            self.sprite(self.cedric,(1015+20*math.sin(t*17),570),340,255*(1-clamp((t-21.65)/.35)))
        for i,name in enumerate(('will','irma','taranee','caleb','haylin','cornelia')):
            dest=targets[name]; fight=(150+i*115,620-(i%2)*85)
            if t<18:
                progress=clamp((t-16.6-i*.12)/1.0)
                x=-180+(fight[0]+180)*progress; y=fight[1]
                pose=1
            elif t<22:
                x=fight[0]+30*math.sin((t-18)*9+i); y=fight[1]-30*abs(math.sin(t*7+i))
                pose=(2,4,2,4)[int((t-18)*5+i)%4]
                if name=='caleb': pose=2 if int(t*5)%2 else 4
                if name=='cornelia': pose=4
            else:
                p=clamp((t-22)/2); p=p*p*(3-2*p)
                x=fight[0]+(dest[0]-fight[0])*p; y=fight[1]+(dest[1]-fight[1])*p
                pose=0
            frames=self.frames['will_heart'] if name=='will' and 20<=t<22 else self.frames[name]
            self.sprite(frames[pose%len(frames)],(x,y),310 if name!='caleb' else 365)
            if 18<=t<22 and name in colors:
                target=(1015,360) if t>=20 else (900+(i%2)*110,230+(i%3)*110)
                progress=((t-18)*3+i*.19)%1
                origin=(int(x+45),int(y-190))
                point=(int(origin[0]+(target[0]-origin[0])*progress),int(origin[1]+(target[1]-origin[1])*progress))
                color=colors[name]
                if name=='cornelia':
                    pygame.draw.polygon(self.stage,color,[(point[0]-15,point[1]+15),(point[0],point[1]-19),(point[0]+17,point[1]+12)])
                elif name=='haylin':
                    pygame.draw.ellipse(self.stage,color,(point[0]-30,point[1]-12,60,24),3)
                else:
                    pygame.draw.circle(self.stage,color,point,13 if name=='irma' else 18)
                if progress>.85:
                    pygame.draw.circle(self.stage,color,target,int(15+progress*15),3)
        if t<18:
            x=850-(t-14)*145; y=660-18*abs(math.sin(t*15)); pose=int(t*9)%6
        elif t<22:
            x=190; y=675; pose=3
        else:
            p=clamp((t-22)/2); x=190+(405-190)*p; y=690; pose=0
        self.sprite(self.frames['blunk'][pose],(x,y),150)
        if 21.55<t<22:
            flash=pygame.Surface((1280,720)); flash.fill((230,212,255))
            flash.set_alpha(int(150*math.sin((t-21.55)/.45*math.pi)))
            self.stage.blit(flash,(0,0))
