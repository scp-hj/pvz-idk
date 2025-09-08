
import pygame
from missles import *
from plants import *
from time import *
from resources import *
from system import *
from config import *
from particles import *
from zombies import *
from filter import *
import sounds
import random,json
import sys,os
from levels import *
import minor_stuff as minor
from powerups import *
from pygame.locals import *
pygame.init()
last=time()
dt,DT=0,0
x,y=0,6
LEVEL_START=pygame.USEREVENT+69
SWITCH_SCENE=pygame.USEREVENT+71
SCREEN_SIZE=(900,640)
WIDTH_TO_HEIGHT=900/640
HEIGHT_TO_WIDTH=640/900
clock=pygame.time.Clock()
#window displays
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)
pygame.display.init()
icon = pygame.image.load(resource_path('icon_.ico'))
pygame.display.set_icon(icon)
import os
os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (30,30)
window = pygame.display.set_mode((900, 640),RESIZABLE)
set_value('screen',window)
pygame.display.set_caption('pvz idk | a pvz fangame')
screen=pygame.Surface(SCREEN_SIZE)
load_game()
zombie_spawn_lane=1
#level = Level('alpha 0.1.2 is patched!')
playing = True
full_bool=[False,False]
next_frame = perf_counter() + DT
last = perf_counter()
while playing:
    if get_value('turbo'):
        DT=0.025
        dt=0.025
        set_value('dt',clock.tick(60)/1000*1.5)
    else:
        DT=0.04
        dt=0.04
        set_value('dt',clock.tick(45)/1000)
    set_value('equivalent_frame',get_value('dt')/0.04)
    window=check_full(window,full_bool,pygame.display.get_surface().get_size())
    events = pygame.event.get()
    if get_value('on_scene')[0]=='level':
        set_value('level',get_value('scene'))
        level=get_value('scene')
    else:
        level=None
    get_value('scene').update(events,screen)
    set_value('screen',screen)
    #make assets and whatever
    pygame.display.update()
    playing=minor.update(level)
    #now=time()
    #print(now-last)
    #if abs(DT-(now-last))>=0.005:
    #    if now-last<DT:
     #       dt+=abs(DT-(now-last))
    #    elif now-last>DT:
    #        dt-=abs(DT-(now-last))
    #print(dt)
    #last=time()
    
    w, h = pygame.display.get_surface().get_size()
    w,h=w/SCREEN_SIZE[0],h/SCREEN_SIZE[1]
    if w>h:
        w=SCREEN_SIZE[0]*h
        h*=SCREEN_SIZE[1]
        y=0
        x=(pygame.display.get_surface().get_size()[0]-w)//2
    else:
        h=SCREEN_SIZE[1]*w
        w*=SCREEN_SIZE[0]
        x=0
        y=(pygame.display.get_surface().get_size()[1]-h)//2
        
    set_value('window size',[w,h])
    set_value('window pos shift',[x,y])
    set_value('factors',(w/SCREEN_SIZE[0],h/SCREEN_SIZE[1]))
    screen_=pygame.transform.smoothscale(screen,(w,h))
    sounds.update(events)
    window.blit(screen_,(x,y))
    if not dt<0:
        sleep(dt)
        pass
    else:
        dt=0
    for event in events:
        if event.type==pygame.QUIT:
            playing=False
        if event.type==LEVEL_START:
            switch_scene(('level',get_value('request_object')))
        if event.type==SWITCH_SCENE:
            switch_scene(get_value('request_object'))
            
        if event.type==pygame.KEYUP:
            if event.key==K_F11:
                full_bool[0]=not full_bool[0]
                full_bool[1] = True
    set_value('full screen',full_bool[0])
                
pygame.quit()
