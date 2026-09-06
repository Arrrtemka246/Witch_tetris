"""Quick scene selector for the test build. Run main.py for normal startup."""
from __future__ import annotations
import argparse
import pygame
from main import Game,WINDOW_W,WINDOW_H
SCENES=[('treasure','Бланк и сокровища — Game A / B'),('hunter','Калеб против Охотника и летучих мышей'),('choice','Выбор победителя на 200+'),('room','Комната Фобоса — секретные коды'),('classic','CLASSIC — фигуры, ghost, фиксация'),('defeat','Поражение после выбора Фобоса'),('game','Полная игра с самого начала')]
def start_scene(game,scene):
    if scene=='game': game.mode='intro'; game.restart_intro(); return
    if scene=='treasure': game.start_minigame('BLUNK TREASURE ESCAPE'); return
    if scene=='hunter': game.start_minigame('CALEB — BAT HUNTER'); return
    game.start_new_game(); game.phobos_deleted_win=False; game.record_saved=True
    if scene=='classic':
        game.figure_fall_mode='classic'; game.classic_piece_queue=[]; game.classic_piece_signature=()
        game.next_kind=game.random_piece(); game.spawn_piece()
    elif scene=='choice':
        game.lines=200; game.story_seen.update((100,200)); game.story_overlay=200
        game.story200_stage='choice'; game.story200_tick=0; game.music.enter_special()
    elif scene in ('room','defeat'):
        game.lines=220; game.phobos_route=True; game.story_winner='phobos'; game.game_over=scene=='defeat'
        if scene=='defeat': game.update()
        else: game.enter_phobos_room('playtest')
def select_scene(game):
    pygame.mouse.set_visible(True)
    while True:
        game.canvas.fill((13,9,23))
        game.draw_wrapped_center('W.I.T.C.H. — ТЕСТОВАЯ СБОРКА',100,WINDOW_W-60,game.font,(217,170,255))
        game.draw_wrapped_center('Выбери сцену мышью или клавишами 1–7',160,WINDOW_W-60,game.small)
        buttons=[]
        for i,(scene,label) in enumerate(SCENES):
            rect=pygame.Rect(55,240+i*100,WINDOW_W-110,76); buttons.append(rect)
            pygame.draw.rect(game.canvas,(39,25,58),rect,border_radius=10)
            pygame.draw.rect(game.canvas,(118,78,151),rect,2,border_radius=10)
            im=game.font.render(f'{i+1}. {label}',True,(241,228,250)); game.canvas.blit(im,im.get_rect(center=rect.center))
        game.draw_wrapped_center('ESC — выйти из тестового меню',925,WINDOW_W-80,game.small)
        ww,wh=game.window.get_size(); scale=min(ww/WINDOW_W,wh/WINDOW_H)
        frame=pygame.transform.scale(game.canvas,(int(WINDOW_W*scale),int(WINDOW_H*scale)))
        game.window.fill((0,0,0)); game.window.blit(frame,((ww-frame.get_width())//2,(wh-frame.get_height())//2)); pygame.display.flip()
        for event in pygame.event.get():
            if event.type==pygame.QUIT or (event.type==pygame.KEYDOWN and event.key==pygame.K_ESCAPE): return None
            if event.type==pygame.KEYDOWN and pygame.K_1<=event.key<=pygame.K_7: return SCENES[event.key-pygame.K_1][0]
            if event.type==pygame.MOUSEBUTTONDOWN and event.button==1:
                pos=game.window_to_canvas(event.pos)
                if pos is not None:
                    for rect,(scene,_) in zip(buttons,SCENES):
                        if rect.collidepoint(pos): return scene
        game.clock.tick(30)
if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--scene',choices=[s[0] for s in SCENES]); args=parser.parse_args()
    g=Game(); scene=args.scene or select_scene(g)
    if scene: start_scene(g,scene); g.run()
    else: g.music.stop(); pygame.quit()
