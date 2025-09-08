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
import pickle
#this py program is used to track and do things constantly that are too weird to fit in other files.
#minor.update() is run in the main loop in main.py
set_value('shakey',[0,0])
set_value('pos_shift2',[0,0])
def update(level=None):
    playing=True
    #checking the 全场光环持续时间
    specials=get_value('specials')
    for special in specials:
        if type(special)==type(list()):
            special[1]-=1
            if special[1]<=0:
                specials.remove(special)
    set_value('specials',specials)
    #getting the text typed
    events=get_value('events')
    for event in events:
        if event.type==pygame.KEYUP:
            if level and get_value('for_real?')=='ye':
                dev(event,level)
 
            set_value('key_press',get_value('key_press')+pygame.key.name(event.key))
        if event.type==pygame.QUIT:
            playing=False
    if get_value('key_press')[-11:]==get_value('dev_pass'):
        set_value('for_real?','ye')
        set_value('key_press','')
        sounds.play('mine_explode',10)
    if get_value('key_press')[-3:]=='sus':
        sounds.play('sus',1)
        set_value('key_press','')
    if get_value('key_press')[-8:]=='shameonu':
        set_value('for_real?','no')
        set_value('key_press','')
        sounds.play('select_seed',10)
    #shake
        
    #shake screen
    shake=get_value('shake')
    if shake>0:
        shake-=1
        set_value('shake',shake)
        if shake<=0:
            shake=0
        pos_shift2=get_value('pos_shift2')
        shakey=get_value('shakey')
        if pos_shift2[0]>=0:
            x=-random.random()*random.randint(3,10)
        else:
            x=random.random()*random.randint(3,10)
        if pos_shift2[1]>=0:
            y=-random.random()*random.randint(3,10)
        else:
            y=random.random()*random.randint(3,10)
        pos_shift2=list(pos_shift2)
        pos_shift2[0]+=x
        pos_shift2[1]+=y
        shakey[0]+=x
        shakey[1]+=y
        set_value('pos_shift2',pos_shift2)
        set_value('shakey',shakey)
        if shake==0:
            pos_shift2[0]-=shakey[0]
            pos_shift2[1]-=shakey[1]
            shakey=[0,0]
            set_value('pos_shift2',pos_shift2)
            set_value('shakey',shakey)
    #veil - [r,g,b,a,delta a]
    veil=get_value('veil')
    s=pygame.Surface((900,640))
    s.set_alpha(veil[3])
    s.fill(veil[0:3])
    blity(s,(0,0),True)
    veil[3]-=veil[4]
    if veil[3]<=0:
        veil=[0,0,0,0,0]
    set_value('veil',veil)
    return playing   

def dev(event,level):
    try:
        zombie_spawn_lane=int(get_value('key_press')[-1])
    except:
        zombie_spawn_lane=1
    if event.key == pygame.K_z:
        z=PaperZombie((840, 90+(zombie_spawn_lane-1)*90))
        level.zombies.add(z)
    if event.key == pygame.K_c:
        level.zombies.add(ConeheadZombie((840, 90+(zombie_spawn_lane-1)*90)))
    if event.key == pygame.K_b:
        level.zombies.add(BucketheadZombie((840, 90+(zombie_spawn_lane-1)*90)))
    if event.key == pygame.K_j:
        level.zombies.add(JeffZombie((840, 90+(zombie_spawn_lane-1)*90)))
    if event.key == pygame.K_f:
        level.zombies.add(FireArcherZombie((840, 90+(zombie_spawn_lane-1)*90)))
    if event.key == pygame.K_i:
        level.zombies.add(IceArcherZombie((840, 90+(zombie_spawn_lane-1)*90)))
    if event.key == pygame.K_n:
        level.zombies.add(NinjaImp((840, 90+(zombie_spawn_lane-1)*90)))
    #if event.key==pygame.K_d:
        #level.zombies.add(JeffZombie((-100,0)))
    if event.key == pygame.K_d:
        level.zombies.add(DiscoZombie((840, 90+(zombie_spawn_lane-1)*90)))
    if event.key == pygame.K_g:
        level.zombies.add(GhostArcher((840, 90+(zombie_spawn_lane-1)*90)))
    if event.key == pygame.K_m:
        level.zombies.add(Ghost((840, 90+(zombie_spawn_lane-1)*90)))
    if event.key == pygame.K_l:
        level.zombies.add(ReaperGhost((840, 90+(zombie_spawn_lane-1)*90)))
    if event.key == pygame.K_a:
        level.zombies.add(ArcherZombie((840, 90+(zombie_spawn_lane-1)*90)))
    #if event.key==pygame.K_i:
        #for target in level.zombies:
            #target.frozen=True
            #target.freezes=(True,1000)
    if event.key==pygame.K_k:
        for zombie in level.zombies:
            zombie.hp=-100000
        for obstacle in level.obstacles:
            obstacle.hp=-100000
    if event.key==pygame.K_s:
        set_value('sun',get_value('sun')+1000)
    if event.key==pygame.K_r:
        for seed in get_value('level').seeds:
            seed.recharge_countdown=0
    if event.key == pygame.K_p:
        level.zombies.add(PogoZombie(
                    (840, 90+(zombie_spawn_lane-1)*90)))
    if event.key == pygame.K_w:
        for grave in level.obstacles:
            get_value('particles_0').add(SpawnGraveZombie(grave.location,random.randint(1,3),lane=grave.lane))
