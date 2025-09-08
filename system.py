import math
import zombies
from plants import *
import pygame
import time
from pygame.freetype import Font
from config import *
from events import *
from filter import *
import sys,os,json,random
import sounds
from datetime import datetime
from powerups import *
LEVEL_START=pygame.USEREVENT+69
LEVEL_END=pygame.USEREVENT+70
SWITCH_SCENE=pygame.USEREVENT+71
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

#classes that dont fit

class LevelEnd(pygame.sprite.Sprite):
    def __init__(self,pos,img,level):
        super().__init__()
        self.x,self.y=pos
        self.x1,self.y1=pos
        self.image=img
        self.img=img
        self.state=0
        self.level=level
        self.ratio=1
        self.coin=0
    def update(self, screen, events):
        if self.state==1:
            self.image = pygame.transform.scale(self.img, (self.img.get_width()*self.ratio, self.img.get_height()*self.ratio))
            self.ratio+=0.1*get_value('equivalent_frame')
            self.cnt+=get_value('equivalent_frame')
            self.x1=self.x-self.img.get_width()*self.ratio//2
            self.y1=self.y-self.img.get_height()*self.ratio//2
            if self.cnt>=100:
                self.level.win()
        self.rect = self.image.get_rect(
            center=(self.x+self.image.get_width()//2, self.y+self.image.get_height()//2))
        blity(self.image,(self.x1,self.y1))
        if self.state==0:
            for event in events:
                if (event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(get_pos())):
                    for a in range(self.coin):
                        c=Coin((self.x+20,self.y+20),(self.x+random.randint(21,100),self.y+21),random.choice([1,1,1,1,4]))
                        c.on_collect()
                        get_value('resources').add(c)
                    sounds.play('win',1)
                    self.state=1
                    self.cnt=0
class SunBank(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image=get_value('images')['sun_bank.png'][tuple()]
        self.pos=(10,10)
        self.font=Font(resource_path(f'fonts/{get_value("language")}.ttf'), 15)
    def update(self,screen,_):
        blity(self.image,self.pos,True)
        self.font.render_to(screen,(15,50),str(get_value('sun')),(255,255,255))
        if get_value('planting'):   
            self.font.render_to(screen,(55,50),get_value('sun_data')[0],get_value('sun_data')[1])
class ProgressBar(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image=get_value('images')['progress_bar.png'][tuple()]
        self.flag=get_value('images')['progress_flag.png'][tuple()]
        self.pos=(280,590)

    def update(self,screen,_):
        if get_value('level').progressing:
            blity(self.image,self.pos,True)
            pygame.draw.rect(screen,(200,180,70),(286,596,get_value('level').wave/len(get_value('level').zombies_)*90,14))
            
            for a in range(len(get_value('level').zombies_)//get_value('level').big_wave):
                blity(self.flag,(295+75/(len(get_value('level').zombies_)/get_value('level').big_wave)*(a+1),580))
class ChromaCount(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image=get_value('images')['chroma_count.png'][tuple()]
        self.pos=(20,580)
        self.font=Font(resource_path(f'fonts/{get_value("language")}.ttf'), 15)
    def update(self,screen,_):
        blity(self.image,self.pos,True)
        self.font.render_to(screen,(53,587),str(get_value('data')['chromas']),(255,255,255))
class CoinCount(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image=get_value('images')['coin_count.png'][tuple()]
        self.pos=(20,580)
        self.font=Font(resource_path(f'fonts/{get_value("language")}.ttf'), 15)
    def update(self,screen,_):
        blity(self.image,self.pos,True)
        self.font.render_to(screen,(53,587),str(get_value('money')),(255,255,255))
class LawnMower(pygame.sprite.Sprite):
    def __init__(self,lane):
        super().__init__()
        self.lane=lane
        print('lawnmower',lane)
        self.x,self.y=0,lane*90+40
        self.image=get_value('images')['lawnmower.png'][tuple()]
        self.moving = False
        self.done=False

        self.stall_timer=0
    def display(self):
        
        blity(self.image,self.pos)
    def update(self, screen):
        if not self.done:
            try:
                if get_value('state') != 'loading':
                    lanes = get_value('lanes')
                    lane = lanes[self.lane-1]['zombies']
                    lane.append(self)
                    lanes[self.lane-1]['zombie'] = lane
                    self.done=True
            except:
                self.done=False
        if self.stall_timer>0:
            self.stall_timer-=1
        self.pos=(self.x,self.y)
        self.rect = self.image.get_rect(
            center=(self.x+self.image.get_width()//2, self.y+self.image.get_height()//2))
        for zombie in get_value('zombies'):
            if self.rect.colliderect(zombie.rect) and zombie.lane==self.lane and zombie.effect['phantom']<=0:
                if type(zombie)==type(zombies.ConeheadZombie()):
                    if zombie.is_special:
                        self.x=10000000
                    else:
                        zombie.hp=-999999
                else:
                    zombie.hp=-99999999
                if self.stall_timer<=0:
                    if not self.moving:
                        sounds.play('lawnmower',0.5)
                    self.moving=True
                else:
                    self.moving=False
        if self.moving:
            self.x+=5
        for event in get_value('events'):
            if event.type==LEVEL_END and not self.moving:
                self.kill()
                if random.randint(1,5)==1:
                    c=Coin((self.x+20,self.y+20),(self.x+21,self.y+21),4)
                else:
                    c=Coin((self.x+20,self.y+20),(self.x+21,self.y+21),1)
                c.on_collect()
                get_value('resources').add(c)

#basic classes
class Gadget(pygame.sprite.Sprite):
    def __init__(self,image,mother=None,kind='select_plant'):
        super().__init__()
        self.image=get_value('images')[image][tuple()]
        self.width,self.height=self.image.get_width(),self.image.get_height()
        self.x,self.y=get_pos()
        self.kind=kind
        self.mother=mother
    def update(self,screen,events):
        self.x,self.y=get_pos()[0]-self.width//2,get_pos()[1]-self.height//2
        blity(self.image,(self.x,self.y))
        if self.kind=='select_plant':
            self.tile=(self.x//90,self.y//90)
            if len(get_plants_at(self.x//90,self.y//90))>0:
                self.target=get_plants_at(self.x//90,self.y//90)[0]
            else:
                self.target=None
            blity(get_value('images')['tile_select.png'][tuple()],(self.tile[0]*90-90+75,self.tile[1]*90-90+100))
        if self.kind=='place_stuff':
            self.tile=(int(self.x//90),int(self.y//90))
            if len(get_plants_at(self.x//90,self.y//90))<=0 and len(get_obstacles_at(self.x//90,self.y//90))<=0:
                self.location=self.tile
                blity(get_value('images')['tile_select.png'][tuple()],(self.tile[0]*90-90+75,self.tile[1]*90-90+100))
            else:
                self.location=None
        for event in events:
            if event.type==pygame.MOUSEBUTTONDOWN:
                if pygame.mouse.get_pressed()[0]:
                    if self.kind=='select_plant':
                        if self.target:
                            self.effect(self.target)
                        else:
                            return
                    elif self.kind=='place_stuff':
                        if not self.location:
                            return
                        else:
                            self.effect(self.location)
                    self.kill()
                    if self.mother:
                        self.mother.recharge_countdown=self.mother.recharge
                        self.mother.use_chance-=1
                else:
                    self.kill()
    def effect(self):
        pass
class Button(pygame.sprite.Sprite):
    def __init__(self,pos,image,select_effect,activate_effect,activate_event=None,singular=True):
        super().__init__()
        self.x,self.y=pos
        self.images=[get_value('images')[image][tuple()]]
        if '.png' in select_effect:
            self.images.append(get_value('images')[select_effect][tuple()])
        else:
            self.images.append(get_value('images')[image][(select_effect,)])
        if '.png' in activate_effect:
            self.images.append(get_value('images')[activate_effect][tuple()])
        else:
            self.images.append(get_value('images')[image][(activate_effect,)])
        self.image=self.images[0]
        self.rect = self.image.get_rect(
            center=(self.x+self.image.get_width()//2, self.y+self.image.get_height()//2))
        self.activated=False
        self.play_sound=True
        self.locked=False
        self.singular=singular
        self.visible=True
        self.event=activate_event
        self.dialogue=False
    def update(self, screen,events):
        if self.visible:
            blity(self.image,(self.x,self.y),self.singular)
        if not self.singular:
            self.rect = self.image.get_rect(
            center=(self.x+self.image.get_width()//2+get_value('pos_shift')[0], self.y+self.image.get_height()//2+get_value('pos_shift')[1]))

            
        if self.rect.collidepoint(get_pos()) and not self.locked:
            self.image=self.images[1]
            if self.play_sound:
                sounds.play('select',0.5)
                self.play_sound=False
        else:
            self.play_sound=True
            if self.activated:
                self.image=self.images[2]
            else:
                self.image=self.images[0]
        for event in events:
            if not get_value('in_dialogue') or self.dialogue:
                if (event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(get_pos())) and not get_value('planting') and not self.locked:
                    self.activated=not self.activated
                    self.on_clicked()
                    break

                if self.event:
                    if event.type == pygame.KEYDOWN and not self.locked:
                        if event.key==self.event and not get_value('planting'):
                            self.activated = not self.activated
                            self.on_clicked()
                    break

    def on_clicked(self):
        pass
class NPC(pygame.sprite.Sprite):
    def __init__(self,pos,image,activate_effect,activate_sound,dialogues=[],dialogue_color=(0,0,0),activate_pause=50,singular=False):
        super().__init__()
        self.x,self.y=pos
        self.images=[get_value('images')[image][tuple()]]
        self.image=self.images[0]
        self.rect = self.image.get_rect(
            center=(self.x+self.image.get_width()//2, self.y+self.image.get_height()//2))
        self.activated=False
        self.play_sound=True
        self.sound=activate_sound
        self.idle_dialogues=dialogues[0][get_value('language')]
        self.select_dialogues=dialogues[1][get_value('language')]
        self.activate_dialogues=dialogues[2][get_value('language')]
        if '.png' in activate_effect:
            self.images.append(get_value('images')[activate_effect][tuple()])
        else:
            self.images.append(get_value('images')[image][(activate_effect,)])
        self.locked=False
        self.singular=singular
        self.visible=True
        self.activate_timer=activate_pause
        self.new_dialogue_timer=-1
        self.pause=activate_pause
        self.dialogue_timer=-1
        self.dialogue_text=''
        self.color=dialogue_color
        self.rng=0
    def update(self, screen,events):
        if self.activated:
            if len(self.images)>=2:
                self.image=self.images[1]
            self.activate_timer-=get_value('equivalent_frame')
            if self.activate_timer<=0:
                self.on_activated()
        else:
            self.image=self.images[0]
        if self.new_dialogue_timer>0:
            self.new_dialogue_timer-=get_value('equivalent_frame')
        if self.dialogue_timer<=0:
            if self.new_dialogue_timer<=0:
                self.rng=random.randint(1,150)
                if len(self.idle_dialogues)>0:
                    if self.rng==1:
                        self.set_dialogue(random.choice(self.idle_dialogues))
        else:
            self.dialogue_timer-=get_value('equivalent_frame')
            blity(self.dialogue_surface,(self.x+10+self.image.get_width(), self.y))            
        if self.visible:
            blity(self.image,(self.x,self.y),self.singular)
        if not self.singular:
            self.rect = self.image.get_rect(
            center=(self.x+self.image.get_width()//2+get_value('pos_shift')[0], self.y+self.image.get_height()//2+get_value('pos_shift')[1]))

        for event in events:
            if not get_value('in_dialogue'):
                if (event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(get_pos())) and not get_value('planting') and not self.locked:
                    self.activated=not self.activated
                    self.locked=False
                    self.on_clicked()
                    break

    def on_clicked(self):
        self.activate_timer=self.pause
        self.activated=True
        self.locked=True
        self.set_dialogue(random.choice(self.activate_dialogues),self.pause)
        sounds.play(self.sound,1)
    def set_dialogue(self,dialogue,duration=50):
        self.dialogue_timer=duration
        self.dialogue_text=dialogue
        self.dialogue_surface=render(self.dialogue_text,Font(resource_path(f'fonts/{get_value("language")}.ttf'), 15),self.color)
        
        self.new_dialogue_timer=2*duration
    def on_activated(self):
        self.activated=False
        self.locked=False
class Dialogue(pygame.sprite.Sprite):
    def __init__(self,character,sprite_id,name,dialogue,font_size=20,char_per_line=40,gap_per_line=25,colour=(255,255,255),side=0,move=False,other_sprite=None,queue=[],choices=None):
        super().__init__()
        self.image=get_value('images')[character+'_'+sprite_id+'.png'][tuple()]
        self.bg=loady(resource_path(f'bgs//dialogue_frame_{side}.png'))
        self.full_text=dialogue
        self.side=side
        self.cnt=0
        self.real_cnt=0
        self.move=move
        self.queue=queue
        self.choices=choices
        self.choice_shown=False
        self.choice_buttons=[]
        self.other=other_sprite
        set_value('in_dialogue',True)
        if self.other:
            self.other=get_value('images')[other_sprite][('black',)]
        if self.side==0 and move:
            self.x=-100
        elif self.side==1 and move:
            self.x=100
        else:
            self.x=0
        if get_value('language')=='chinese':
            char_per_line=34
        else:
            char_per_line=45
        self.text_obj=SmartText('',[150-100,452],font_size,char_per_line,gap_per_line)
        name_=name
        self.name=SmartText(name_,[190-100,418],20,char_per_line,gap_per_line)
        self.completed=False
    def update(self,screen,events):
        if self.x<0:
            self.x+=25
        elif self.x>0:
            self.x-=25
        blity(self.bg,(self.x,380),True)
        blity(self.image,(self.x+750*self.side,400),True)
        if self.other:
            if self.side==0:
                blity(self.other,(750,400),True)
            else:
                blity(self.other,(0,400),True)
        self.name.pos[0]=self.x+190+(540-190)*self.side
        self.text_obj.pos[0]=self.x+150
        if self.cnt>=len(self.full_text)-1:
            self.text_obj.text=self.full_text
            self.x=0
        else:
            self.text_obj.text+=self.full_text[self.cnt]
        self.text_obj.update(screen,events)
        self.name.update(screen,events)
        for button in self.choice_buttons:
            button.update(screen,events)
        if not self.completed:
            self.cnt+=1
            if self.cnt==len(self.full_text):
                self.completed=True
        if self.completed and not self.choice_shown:
            if self.choices:
                for a in range(len(self.choices)):
                    if get_value('language')=='chinese':
                        if len(self.choices[a][0])<=4:
                            font=20
                        elif len(self.choices[a][0])<=9:
                            font=15
                        else:
                            font=10
                    else:
                        if len(self.choices[a][0])<=6:
                            font=20
                        elif len(self.choices[a][0])<=15:
                            font=15
                        else:
                            font=10
                        
                    self.choice_buttons.append(DialogueChoiceButton((self.x+140+(a*150),380+160),self.choices[a][0],self.choices[a][1],self,font=font))
                self.choice_shown=True
        for event in events:
            if (event.type == pygame.MOUSEBUTTONDOWN):
                if not self.completed:
                    self.text_obj.text=self.full_text
                    self.cnt=len(self.full_text)-1
                else:
                    if not self.choices:
                        self.complete()
    def complete(self):
        self.kill()
        sounds.play('select',1)
        if len(self.queue)>0:
            new=self.queue[0]
            self.queue.remove(new)
            queue=self.queue
            if len(new)>=8:
                choice=new[7:]
            else:
                choice=None
            get_value('uber_uis').add(Dialogue(new[0],new[1],new[2],new[3],side=new[4],move=new[5],other_sprite=new[6],queue=queue,choices=choice))

        else:
            set_value('in_dialogue',False)
class Window(pygame.sprite.Sprite):#                          [['text',text_pos(relative),text_size,text_color],...]
    def __init__(self,pos,size,border_width,color,border_color,texts,attach_buttons,attach_buttons_pos,language=None):
        super().__init__()
        self.x,self.y=pos
        self.inner_rect=pygame.rect.Rect(self.x+border_width,self.y+border_width,size[0]-border_width,size[1]-border_width)
        self.outer_rect=pygame.rect.Rect(self.x,self.y,size[0]+border_width,size[1]+border_width)
        self.inner_color=color
        self.outer_color=border_color
        self.texts=texts
        self.language=language
        #buttons
        self.buttons=[]
        for a in range(len(attach_buttons)):
            pos = attach_buttons_pos[a]
            new_pos=pos[0]+self.x,pos[1]+self.y
            button = attach_buttons[a](new_pos)
            button.mother=self
            self.buttons.append(button)
    def update(self,screen,events):
        #draw window
        pygame.draw.rect(screen,self.outer_color,self.outer_rect)
        pygame.draw.rect(screen,self.inner_color,self.inner_rect)
        #blit texts
        for text in self.texts:
            relative_pos=text[1]
            real_pos=relative_pos[0]+self.x,relative_pos[1]+self.y
            if not self.language:
                Font(resource_path(f'fonts/{get_value("language")}.ttf'), text[2]).render_to(screen,real_pos,text[0],text[3])
        
            else:
                Font(resource_path(f'fonts/{self.language}.ttf'), text[2]).render_to(screen,real_pos,text[0],text[3])
        #update buttons
        for button in self.buttons:
            button.update(screen,events)
class FancyWindow(pygame.sprite.Sprite):#                          [['text',text_pos(relative),text_size,text_color],...]
    def __init__(self,pos,img,texts,attach_buttons,attach_buttons_pos,language=None):
        super().__init__()
        self.x,self.y=pos
        self.image=loady(resource_path(f'bgs//{img}'))
        self.texts=texts
        #buttons
        self.buttons=[]
        self.language=language
        for a in range(len(attach_buttons)):
            pos = attach_buttons_pos[a]
            new_pos=pos[0]+self.x,pos[1]+self.y
            button = attach_buttons[a](new_pos,self)
            button.mother=self
            self.buttons.append(button)
    def update(self,screen,events):
        #draw window
        blity(self.image,(self.x,self.y),True)
        #blit texts
        for text in self.texts:
            relative_pos=text[1]
            real_pos=relative_pos[0]+self.x,relative_pos[1]+self.y
            if not self.language:
                Font(resource_path(f'fonts/{get_value("language")}.ttf'), text[2]).render_to(screen,real_pos,text[0],text[3])
        
            else:
                Font(resource_path(f'fonts/{self.language}.ttf'), text[2]).render_to(screen,real_pos,text[0],text[3])
        #update buttons
        for button in self.buttons:
            button.update(screen,events)
class SmartText(pygame.sprite.Sprite):
    def __init__(self,text,pos,font_size,char_per_line,gap_per_line,colour=(255,255,255)):
        super().__init__()
        self.texts=[]
        self.pos=pos
        self.gap_per_line=gap_per_line
        self.char_per_line=char_per_line
        self.font_size=font_size
        self.colour=colour
        line=''
        char_cnt=0
        for char in text:
            char_cnt+=1
            line+=char
            if char_cnt>=char_per_line and (get_value('language')=='chinese' or char==' '):
                self.texts.append(line)
                line=''
                char_cnt=0
        self.texts.append(line+' ')
        #print(self.texts)
        self.texts=[Font(resource_path(f'fonts/{get_value("language")}.ttf'), font_size).render(line,colour) for line in self.texts]
        #print(self.texts)
        self.last_text=text
        self.text=text
    def update(self,screen,events):
        if self.text!=self.last_text:
            self.texts=[]
            self.last_text=self.text
            line=''
            char_cnt=0
            for char in self.text:
                char_cnt+=1
                line+=char
                if char_cnt>=self.char_per_line and (get_value('language')=='chinese' or char==' '):
                    self.texts.append(line)
                    line=''
                    char_cnt=0
            self.texts.append(line+' ')
            #print(self.texts)
            self.texts=[Font(resource_path(f'fonts/{get_value("language")}.ttf'), self.font_size).render(line,self.colour) for line in self.texts]
            #print(self.texts)
        for a in range(len(self.texts)):
            screen.blit(self.texts[a][0],(self.pos[0],self.pos[1]+self.gap_per_line*a))
#buttons
class TurboButton(Button):
    def __init__(self):
        super().__init__((700,10),'turbo.png','black','turbo_activated.png',pygame.K_t)
    def on_clicked(self):
        sounds.play('activate',1.0)
        if self.activated:
            set_value('turbo',True)
            return
        set_value('turbo',False)

class SpecialIcon(Button):
    def __init__(self,name,pos,cnt):
        super().__init__(pos,f'special_{name}.png','hit',f'special_{name}.png')
        self.locked=False
        self.name=name
        self.cnt=cnt
        self.hover_time=0
        self.x=800
        self.y=480-self.cnt*70
        self.lore=False
    def update(self,screen,event):
        super().update(screen,event)
        self.x=800
        self.y=480-self.cnt*70
        self.rect = self.image.get_rect(
            center=(self.x+self.image.get_width()//2, self.y+self.image.get_height()//2))
        if not get_value('level').level_start or get_value('paused'):
            if self.rect.collidepoint(get_pos()):
                self.hover_time+=1
                if self.hover_time>=3 and not self.lore:
                    get_value('uber_uis').add(SpecialLore(self))
                    self.lore=True
            else:
                self.hover_time=0
                self.lore=False
        else:
            self.hover_time=0
            self.lore=False
    def on_clicked(self):
        if get_value('level').level_start and not get_value('paused'):
            sounds.play('activate',1.0)
            set_value('paused',not get_value('paused'))
            if get_value('paused'):
                get_value('uis').add(PauseMenu())

class PauseButton(Button):
    def __init__(self):
        super().__init__((800,10),'pause.png','black','pause.png',pygame.K_SPACE)
    def on_clicked(self):
        sounds.play('activate',1.0)
        set_value('paused',not get_value('paused'))
        if get_value('paused'):
            get_value('uis').add(PauseMenu())

class ShovelButton(Button):
    def __init__(self):
        super().__init__((600, 10),'shovel_button.png','hit', 'black',pygame.K_s)
    def update(self,screen,events):
        super().update(screen,events)
        for event in events:
            if event.type==SHOVEL_BACK:
                self.activated=False
    def on_clicked(self):
        sounds.play('shovel_pick', 1.0)
        get_value('uis').add(Shovel())


class HelpButton(Button):
    def __init__(self):
        super().__init__((800, 10),'help_button.png', 'hit', 'black')

    def on_clicked(self):
        sounds.play('click2', 1.0)
        get_value('uis').add(HelpWindow())
class CloseButton(Button):
    def __init__(self,pos,mother):
        super().__init__(pos,'no.png', 'hit', 'black')
        self.mother=mother
    def on_clicked(self):
        sounds.play('click2', 1.0)
        self.mother.kill()
class Arrow(Button):
    def __init__(self,pos,mother,direction,cycle=False):
        if direction=='left':
            path='left_arrow.png'
        else:
            path='right_arrow.png'
        super().__init__(pos,path, 'hit', path)
        self.direction=direction
        self.cycle=cycle
        self.mother=mother
    def update(self,screen,events):
        super().update(screen,events)
        self.rect = self.image.get_rect(
            center=(self.x+self.image.get_width()//2, self.y+self.image.get_height()//2))
        for event in events:
            if event.type==pygame.KEYUP:
                if event.key==pygame.K_LEFT and self.direction=='left':
                    self.on_clicked()
                elif event.key==pygame.K_RIGHT and self.direction=='right':
                    self.on_clicked()
    def on_clicked(self):
        sounds.play('select_seed', 1.0)
        self.mother.last_pressed=self.direction
        if self.direction=='left':
            self.mother.value-=1
            if self.mother.value<0:
                if self.cycle:
                    self.mother.value=self.mother.max_value
                else:
                    self.mother.value=0
        elif self.direction=='right':
            self.mother.value+=1
            if self.mother.value>self.mother.max_value:
                if self.cycle:
                    self.mother.value=0
                else:
                    self.mother.value=self.mother.max_value

class Expand(Button):
    def __init__(self,pos,mother,direction):
        if direction=='up':
            path='expand_arrow.png'
            alt='extract_arrow.png'
        else:
            path='extract_arrow.png'
            alt='expand_arrow.png'
        super().__init__(pos,path, 'hit', path)
        self.direction=direction
        self.mother=mother
        self.alt_images=[get_value('images')[alt][tuple()]]
        self.alt_images.append(get_value('images')[alt][('hit',)])
        self.alt_images.append(get_value('images')[alt][tuple()])
        self.temp=[]
    def update(self,screen,events):
        super().update(screen,events)
        self.rect = self.image.get_rect(
            center=(self.x+self.image.get_width()//2, self.y+self.image.get_height()//2))
    def on_clicked(self):
        sounds.play('activate', 1.0)
        self.temp=self.images
        self.images=self.alt_images
        self.alt_images=self.temp
        if self.direction=='up':
            self.mother.up()
            self.direction='down'
        elif self.direction=='down':
            self.mother.down()
            self.direction='up'
class LetsRock(Button):
    def __init__(self,pos,level):
        super().__init__(pos,'rockkkkkk.png','rockk.png','rockk.png')
        self.level=level
    def on_clicked(self):
        self.level.level_start=True
        set_value('state','leveling')
        self.level.level_can_start=True
        self.kill()
class SussyImposter(Button):
    def __init__(self,pos):
        super().__init__(pos,'invisible_imposter.png','invisible_imposter.png','yellow.png')
    def on_clicked(self):
        sounds.play('sussy',1)
class LevelSelectButton(Button):
    def __init__(self,pos,level_name):
        if 'void_' in level_name:
            super().__init__(pos,'void_portal.png','hit','void_portal.png',singular=False)
        else:
            super().__init__(pos,'level_button_0.png','hit','level_button_1.png',singular=False)
        self.level_timer=0
        self.level=level_name
        self.hover_time=0
        self.shaking=False
        self.theta=0
        self.x_,self.y_=pos
        if not self.level in get_value('data')['unlocked_levels']:
            self.visible=False
            self.locked=True
    def update(self,screen,events):
        super().update(screen,events)
        if 'void_' in self.level:
            if self.shaking:
                set_value('map_veil',[20,0,75,200-self.level_timer])
                self.x=self.x_+random.randint(-20,20)
                self.y=self.y_+random.randint(-20,20)
            else:
                self.y=self.y_+math.sin(self.theta)*25
                self.theta+=0.1*get_value('equivalent_frame')
        if self.rect.collidepoint(get_pos()) and not self.locked:
            if self.hover_time<10:
                self.hover_time+=1
            if self.hover_time>=5:
                try:
                    if not self.lore:
                        get_value('uber_uis').add(LevelLore(self))
                        self.lore=True
                except:
                    pass
        else:
            if self.hover_time>0:
                self.hover_time-=1
            if self.hover_time<=0:
                self.lore=False
        if not self.level in get_value('data')['unlocked_levels']:
            self.visible=False
            self.locked=True
        elif not self.activated:
            self.visible=True
            self.locked=False
        if self.activated:
            self.level_timer-=get_value('equivalent_frame')
            if self.level_timer<=0:
                pygame.event.post(pygame.event.Event(LEVEL_START))
                set_value('request_object',self.level)
    def on_clicked(self):
        sounds.play('click2',1)
            
        self.locked=True
        self.level_timer=100
        if 'void_' in self.level:
            self.shaking=True
            sounds.play('void_portal',1)
            set_value('map_veil',[20,0,75,100])
        import levels
        if levels.get_level_setup(self.level)['scene'] in levels.NIGHT_SCENES:
            levels.change_and_save('time','night')
        else:
            levels.change_and_save('time','day')
class Goooooo(Button):
    def __init__(self,pos,mother):
        super().__init__(pos,'goooooo.png','hit','black',singular=False)
        self.mother=mother
    def update(self,screen,events):
        super().update(screen,events)
        if len(self.mother.mother.selected_seeds.sprites())<self.mother.mother.selected_seeds.max_seeds:
            self.visible=False
            self.locked=True
        elif self.mother.move_state==-1:
            self.visible=True
            self.locked=False
    def on_clicked(self):
        sounds.play('click2',1)
        self.locked=True
        self.mother.move_state=1
        self.mother.mother.fugging_end_this()
class BackToGame(Button):
    def __init__(self,pos,mother):
        super().__init__(pos,'back_to_game.png','hit','black',singular=False)
        self.mother=mother
    def on_clicked(self):
        sounds.play('click2',1)
        self.locked=True
        self.mother.kill()
        set_value('paused',False)
class BackToMenu(Button):
    def __init__(self,pos,mother):
        super().__init__(pos,'back_to_menu.png','hit','black',singular=False)
        self.mother=mother
        self.scene=False
    def on_clicked(self):
        sounds.play('click2',1)
        import levels
        if not self.scene:
            self.scene=get_value('last_scene')
        set_value('paused',False)
        levels.switch_scene(self.scene)
class Language(Button):
    def __init__(self):
        super().__init__((780,20),f'lang_{get_value("language")}.png','hit','black')
        self.fuck=False
    def update(self,screen,events):
        super().update(screen,events)
        
        if get_value('new')==True:
            self.fuck=True
            set_value('new',False)
        if self.fuck:
            self.fuck=False
            self.on_clicked()
    def on_clicked(self):
        sounds.play('click2',1)
        get_value('uber_uis').add(LanguageSelection())
        self.kill()
class EngCheckBox(Button):
    def __init__(self,pos,mother):
        super().__init__(pos,f'unchecked.png','checked.png','checked.png')
        self.mother=mother
        if get_value('language')=='english':
            self.activated=True
        else:
            self.activated=False
    def update(self,screen,events):
        super().update(screen,events)
        if get_value('language')=='chinese':
            self.activated=False
        else:
            self.activated=True
    def on_clicked(self):
        sounds.play('click2',1)
        self.activated=True
        set_value('language','english')
        data=get_value('data')
        data['language']='english'
        save(data)
class ChinCheckBox(Button):
    def __init__(self,pos,mother):
        super().__init__(pos,f'unchecked.png','checked.png','checked.png')
        self.mother=mother
        if get_value('language')=='chinese':
            self.activated=True
        else:
            self.activated=False
    def update(self,screen,events):
        super().update(screen,events)
        if get_value('language')=='english':
            self.activated=False
        else:
            self.activated=True
    def on_clicked(self):
        sounds.play('click2',1)
        self.activated=True
        set_value('language','chinese')
        data=get_value('data')
        data['language']='chinese'
        save(data)
class DailyChallenge(Button):
    def __init__(self):
        if get_value('completed_daily'):
            super().__init__((130,250),f'checked.png','hit','black')
        else:
            super().__init__((130,250),f'unchecked.png','hit','black')
        self.fuck=False
    def update(self,screen,events):
        super().update(screen,events)
    def on_clicked(self):
        sounds.play('click2',1)
        pygame.event.post(pygame.event.Event(LEVEL_START))
        set_value('request_object',[None,random_level()])
class BackMainMenu(Button):
    def __init__(self,pos,scene):
        super().__init__(pos,'goooooo.png','hit','black',singular=False)
        self.scene=scene
    def on_clicked(self):
        sounds.play('click2',1)
        #pygame.event.post(pygame.event.Event(SWITCH_SCENE))
        import levels
        if not self.scene:
            self.scene=get_value('last_scene')
        levels.switch_scene(self.scene)
        #set_value('request_object',('level_select','the_void'))
class Return(Button):
    def __init__(self,pos,scene=None):
        super().__init__(pos,f'btn_return.png','hit','black')
        self.scene=scene
    def update(self,screen,events):
        super().update(screen,events)
    def on_clicked(self):
        sounds.play('click2',1)
        import levels
        if not self.scene:
            self.scene=get_value('last_scene')
        levels.switch_scene(self.scene)
class ShopButton(Button):
    def __init__(self):
        super().__init__((690,20),f'shop_icon.png','hit','black')
    def update(self,screen,events):
        super().update(screen,events)
    def on_clicked(self):
        sounds.play('click2',1)
        import levels
        levels.switch_scene(['shop'])
class PurchaseButton(Button):
    def __init__(self,pos,price,item,currency):# item: ['plant',9] # currency: 'money' 'chromas'
        super().__init__(pos,f'price_tag.png','hit','price_tag.png')
        self.price=price
        self.item=item
        self.currency=currency
        self.text=SmartText('$'+str(price),(pos[0]+2,pos[1]+6),12,999,999,colour=(255,255,255))
    def update(self,screen,events):
        super().update(screen,events)
        self.text.update(screen,events)
    def on_clicked(self):
        if not self.item[0]=='feature':
            money=get_value('data')[self.currency]
            if money >= self.price:
                import levels
                levels.change_and_save(self.currency,money-self.price)
                set_value(self.currency,money-self.price)
                if self.item[0]=='plant':
                    category='unlocked_plants'
                elif self.item[0]=='powerup':
                    category='unlocked_powerups'
                list_=get_value('data')[category]
                list_.append(self.item[1])
                levels.change_and_save(category,list_)
                sounds.play('purchase',0.5)
                get_value('scene').refresh()
            else:
                sounds.play('wrong',0.5)
        else:
            if self.item[1]=='more_packets':
                money=get_value('data')[self.currency]
                if money >= self.price:
                    import levels
                    levels.change_and_save(self.currency,money-self.price)
                    set_value(self.currency,money-self.price)
                    limit=get_value('data')['seed_limit']+1
                    levels.change_and_save('seed_limit',limit)
                    set_value('max_seeds',limit)
                    sounds.play('purchase',0.5)
                    get_value('scene').refresh()
                else:
                    sounds.play('wrong',0.5)
class DialogueChoiceButton(Button):
    def __init__(self,pos,text,next_dialogue,mother,font=10):
        super().__init__(pos,f'dialogue_choice.png','hit','dialogue_choice.png')
        self.next=next_dialogue
        self.mother=mother
        if get_value('language')=='chinese':
            self.text=SmartText(text,(pos[0]+2,pos[1]+6),font,15,15,colour=(255,255,255))
        else:
            self.text=SmartText(text,(pos[0]+2,pos[1]+6),font,20,20,colour=(255,255,255))
        self.dialogue=True
    def update(self,screen,events):
        super().update(screen,events)
        self.text.update(screen,events)
    def on_clicked(self):
        self.mother.kill()
        import levels
        if self.next=='0' or self.next==0:
            set_value('in_dialogue',False)
            return
        levels.start_dialogue(self.next)
#gadgets
class TLG(Gadget):
    def __init__(self,mother):
        super().__init__('TLZ.png',mother)
    def effect(self,target):
        pass

class NutCracker(Gadget):
    def __init__(self,mother):
        super().__init__('nut_cracker.png',mother)
    def effect(self,target):
        for zombie in get_value('zombies'):
            zombie.stop_timer+=int(125+target.hp*0.06)
        target.hp=-999999
        target.on_destroy()
        get_value('particles_-1').add(Crack((self.tile[0]*90,self.tile[1]*90)))
        sounds.play('nut_crack',0.75+target.hp*0.0002)

class PlantFood(Gadget):
    def __init__(self,mother):
        super().__init__('plant_food.png',mother)
    def effect(self,target):
        sounds.play('grow',1)
        packet=find_packet(find_plant_class(target))
        if packet:
            packet.recharge_countdown=0
            packet.highlight_timer=5

class RandomnessWand(Gadget):
    def __init__(self,mother):
        super().__init__('randomness_wand.png',mother)
    def effect(self,target):
        sounds.play('grow',1)
        target.effect['randomness']=-100

class FriedChick(Gadget):
    def __init__(self,mother):
        super().__init__('fried_duck_0.png',mother,'place_stuff')
    def effect(self,target):
        plant(target[0],target[1],get_value('plants'),FriedDuck,get_value('plants'),get_value('particles_0'),0)

class Glove(Gadget):
    def __init__(self,mother):
        super().__init__('glove.png',mother)
    def effect(self,target):
        sounds.play('activate',1)
        get_value('uis').add(GlovePlace(target))
class GlovePlace(Gadget):
    def __init__(self,plant):
        super().__init__('glove.png',None,'place_stuff')
        self.plant=plant
    def effect(self,target):
        lane=get_value('lanes')
        try:
            lane[self.plant.lane-1]['plants'].remove(self.plant)
            set_value('lanes',lane)
        except:
            return
        self.plant.lane=target[1]
        self.plant.column=target[0]
        self.plant.x = target[0]*90+20
        self.plant.y = target[1]*90+70
        self.plant.pos=list(target)
        lanes=get_value('lanes')
        lane=lanes[target[1]-1]['plants']
        lane.insert(0,self.plant)
        lanes[target[1]-1]['plants']=lane
        set_value('lanes',lane)
#windows
class HelpWindow(Window):
    def __init__(self):  # [['text',text_pos,text_size,text_color],...]
        texts = [['Pvz idk made by SCPHJ alpha 0.1.2',
                 (10, 30), 15, (255, 255, 0)],
                 ['press "g" to spawn a random grave on screen',
                     (10, 60), 10, (255, 255, 255)],
                 ['press 1-6 to select lane and then press "z" to spawn a zombie', (10, 80), 10, (255, 255, 255)],
                 ['press "c" to spawn conehead, "b" for buckethead and "p" for pogo',
                     (10, 100), 10, (255, 255, 255)],
                 ['press "w" to spawn one zombie from every grave',
                     (10, 120), 10, (255, 255, 255)],
                 ['Alpha 0.0.9 updates:', (10, 140), 10, (255, 255, 255)],
                 ['-add one plant and two zombies: potato, football and pogo', (20, 160), 10, (255, 255, 255)],
                 ['-add a test level that automatically starts', (20, 180), 10, (255, 255, 255)],
                 ['-minor plant changes', (20, 200), 10, (255, 255, 255)]]
        super().__init__((300, 100), (400, 400), 3, (0, 50, 50), (0, 0, 0),
                         texts, [CloseButton], [(385,-15)])

class Lore(Window):
    def __init__(self,t,mother):
        self.mother=mother
        texts=[]
        for a in range(len(t)):
            if get_value('language')=='chinese':
                texts.append([t[a],(5,10+15*a),14,(0,0,0)])
            else:
                texts.append([t[a],(5,10+12*a),10,(0,0,0)])
    
        self.pos=mother.x-70,mother.y+45
        if get_value('language')=='chinese':
            size=(400,25+a*15)
        else:
            size=(400,20+a*12)
        super().__init__(self.pos,size,3,(248, 255, 209),(107, 63, 0),texts,[],[])
    def update(self,screen,events):
        super().update(screen,events)
        if self.mother.hover_time<=0:
            self.kill()
class ShortPlantLore(Window):
    def __init__(self,mother):
        self.plant_id=mother.plant_id
        self.pos=mother.x-70,mother.y+50
        self.mother=mother
        with open(resource_path(f'lore//{get_value("language")}//plants//short//{self.plant_id}.txt'),encoding="utf8") as t:
            self.pos=mother.x-70,mother.y+50
            t=t.readlines()
            texts=[]
            for a in range(len(t)):
                if get_value('language')=='chinese':
                    texts.append([t[a],(5,10+15*a),14,(0,0,0)])
                else:
                    texts.append([t[a],(5,10+12*a),10,(0,0,0)])
        
        self.pos=mother.x-70,mother.y+45
        if get_value('language')=='chinese':
            size=(400,25+a*15)
        else:
            size=(400,20+a*12)
        super().__init__(self.pos,size,3,(248, 255, 209),(107, 63, 0),texts,[],[])
    def update(self,screen,events):
        super().update(screen,events)
        if self.mother.hover_time<=0:
            self.kill()
class ShortPowerLore(Window):
    def __init__(self,mother):
        self.power_id=mother.power_id
        self.pos=mother.x-100,mother.y+30
        self.mother=mother
        with open(resource_path(f'lore//{get_value("language")}//gadgets//short//{self.power_id}.txt'),encoding="utf8") as t:
            t=t.readlines()
            texts=[]
            for a in range(len(t)):
                if get_value('language')=='chinese':
                    texts.append([t[a],(5,10+15*a),14,(0,0,0)])
                else:
                    texts.append([t[a],(5,10+12*a),10,(0,0,0)])
        if get_value('language')=='chinese':
            size=(400,25+a*15)
        else:
            size=(400,20+a*12)
        super().__init__(self.pos,size,3,(248, 255, 209),(107, 63, 0),texts,[],[])
    def update(self,screen,events):
        super().update(screen,events)
        if self.mother.hover_time<=0:
            self.kill()
class ShortZombieLore(Window):
    def __init__(self,mother):
        self.plant_id=mother.zombie_id
        self.pos=mother.x-120+get_value('pos_shift')[0],mother.y+30+get_value('pos_shift')[1]
        self.mother=mother
        with open(resource_path(f'lore//{get_value("language")}//zombies//short//{self.mother.zombie_id}.txt'),encoding="utf8") as t:
            t=t.readlines()
            texts=[]
            for a in range(len(t)):
                if get_value('language')=='chinese':
                    texts.append([t[a],(5,10+15*a),14,(0,0,0)])
                else:
                    texts.append([t[a],(5,10+12*a),10,(0,0,0)])
        if get_value('language')=='chinese':
            size=(400,25+a*15)
        else:
            size=(400,20+a*12)
        super().__init__(self.pos,size,3,(248, 255, 209),(107, 63, 0),texts,[],[])
    def update(self,screen,events):
        super().update(screen,events)
        if self.mother.hover_time<=0:
            self.kill()
class LevelLore(Window):
    def __init__(self,mother):
        self.level=mother.level
        self.pos=mother.x-120+get_value('pos_shift')[0],mother.y+30+get_value('pos_shift')[1]
        self.mother=mother
        with open(resource_path(f'lore//{get_value("language")}//levels//{self.level}.txt'),encoding="utf8") as t:
            t=t.readlines()
            texts=[]
            for a in range(len(t)):
                if get_value('language')=='chinese':
                    texts.append([t[a],(5,10+15*a),14,(0,0,0)])
                else:
                    texts.append([t[a],(5,10+12*a),10,(0,0,0)])
        if get_value('language')=='chinese':
            size=(400,25+a*15)
        else:
            size=(400,20+a*12)
        super().__init__(self.pos,size,3,(248, 255, 209),(107, 63, 0),texts,[],[])
    def update(self,screen,events):
        super().update(screen,events)
        if self.mother.hover_time<=0:
            self.kill()
class SpecialLore(Window):
    def __init__(self,mother):
        self.name=mother.name
        level_start=get_value('level').level_start
        if not level_start:
            self.pos=mother.x-300+get_value('pos_shift')[0],mother.y-50+get_value('pos_shift')[1]
        else:
            self.pos=mother.x-350+get_value('pos_shift')[0],mother.y-50+get_value('pos_shift')[1]
        self.mother=mother
        with open(resource_path(f'lore//{get_value("language")}//specials//{self.name}.txt'),encoding="utf8") as t:
            t=t.readlines()
            texts=[]
            for a in range(len(t)):
                if get_value('language')=='chinese':
                    texts.append([t[a],(5,10+15*a),14,(0,0,0)])
                else:
                    texts.append([t[a],(5,10+12*a),10,(0,0,0)])
        if get_value('language')=='chinese':
            size=(450,25+a*15)
        else:
            size=(450,20+a*12)
        super().__init__(self.pos,size,3,(248, 255, 209),(107, 63, 0),texts,[],[])
    def update(self,screen,events):
        super().update(screen,events)
        if self.mother.hover_time<=0:
            self.kill()

#NPCs
class Unicorn(NPC):
    def __init__(self):
        if get_value('completed_daily'):
            image='npc_unicorn_1.png'
            image_='npc_unicorn_1_wink.png'
            dialogue=NPC_DIALOGUES['unicorn_1']
        else:
            image='npc_unicorn_0.png'
            image_='npc_unicorn_0_wink.png'
            dialogue=NPC_DIALOGUES['unicorn_0']
        super().__init__((1600,60),image,image_,'magical',dialogue,[255, 0, 239])
        self.theta=0
        self.omega=0.03
        self.amplitude=25
        self.og_y=60
    def update(self,screen,events):
        super().update(screen,events)
        if not self.activated:
            self.y=self.og_y+self.amplitude*math.sin(self.theta)
            self.theta+=self.omega*get_value('equivalent_frame')
    def on_activated(self):
        super().on_activated()
        import levels
        levels.switch_scene(['daily'])
        #pygame.event.post(pygame.event.Event(LEVEL_START))
        #set_value('request_object',[None,random_level()])
class ShopUnicorn(NPC):
    def __init__(self):
        image='npc_unicorn_1.png'
        image_='npc_unicorn_1_wink.png'
        dialogue=NPC_DIALOGUES['unicorn_shop']
        super().__init__((200,480),image,image_,'magical',dialogue,[255, 0, 239])
        self.theta=0
        self.omega=0.05
        self.amplitude=25
        self.og_y=480
    def update(self,screen,events):
        super().update(screen,events)
        if not self.activated:
            self.y=self.og_y+self.amplitude*math.sin(self.theta)
            self.theta+=self.omega*get_value('equivalent_frame')
    def on_activated(self):
        super().on_activated()
        import levels
        levels.start_dialogue('7')
        #pygame.event.post(pygame.event.Event(LEVEL_START))class ShopUnicorn(NPC):
    def __init__(self):
        image='npc_unicorn_1.png'
        image_='npc_unicorn_1_wink.png'
        dialogue=NPC_DIALOGUES['unicorn_shop']
        super().__init__((200,480),image,image_,'magical',dialogue,[255, 0, 239])
        self.theta=0
        self.omega=0.05
        self.amplitude=25
        self.og_y=480
    def update(self,screen,events):
        super().update(screen,events)
        if not self.activated:
            self.y=self.og_y+self.amplitude*math.sin(self.theta)
            self.theta+=self.omega*get_value('equivalent_frame')
    def on_activated(self):
        super().on_activated()
        import levels
        levels.start_dialogue('7')
        #pygame.event.post(pygame.event.Event(LEVEL_START))
        #set_value('request_object',[None,random_level()])
class JHPCS(NPC):
    def __init__(self):
        image='npc_jhpcs_smile.png'
        image_='npc_jhpcs_wink.png'
        dialogue=NPC_DIALOGUES['jhpcs1']
        super().__init__((2550,445),image,image_,'magical',dialogue,[255, 0, 239])
        self.theta=0
        self.omega=0.05
        self.amplitude=20
        self.og_y=445
    def update(self,screen,events):
        super().update(screen,events)
        if not self.activated:
            self.y=self.og_y+self.amplitude*math.sin(self.theta)
            self.theta+=self.omega*get_value('equivalent_frame')
    def on_activated(self):
        super().on_activated()
        import levels
        levels.start_dialogue('41')
class Sprout(NPC):
    def __init__(self):
        image='little_sprout.png'
        image_='little_sprout.png'
        dialogue=NPC_DIALOGUES['sprout']
        super().__init__((780,455),image,image_,'magical',dialogue,[255, 0, 239])
    def on_activated(self):
        super().on_activated()
        import levels
        levels.start_dialogue('47')
        plants=get_value('data')['unlocked_plants']
        plants.append(28)
        levels.change_and_save('unlocked_plants',plants)
        self.kill()
        #pygame.event.post(pygame.event.Event(LEVEL_START))
class PauseMenu(FancyWindow):
    def __init__(self):
        super().__init__((200,70),'pause_menu.png',[[random.choice(get_value('pause_texts')),(137,240),12,(255, 230, 45)]],[BackToGame,BackToMenu],[[35,350],[170,275]])
        self.zombie=random.choice(list(zombies.ZOMBIE_CLASSES.values()))((137+300,200))
        self.zombie.preview=True
        self.zombie.paused=True
    def update(self,screen,events):
        super().update(screen,events)
        self.zombie.update(screen)
        self.zombie.display()
        if get_value('paused')==False:
            self.kill()

class LanguageSelection(FancyWindow):
    def __init__(self):
        super().__init__((200,120),'language_selection.png',[['Select your language',(70,30),20,(255, 230, 45)],
                                                             ['选择显示语言',(70,50),20,(255, 230, 45)],
                                                             ['English',(70,100),20,(255, 230, 45)],
                                                             ['英文',(70,130),20,(255, 230, 45)],
                                                             ['中文',(290,100),20,(255, 230, 45)],
                                                             ['Chinese',(290,130),20,(255, 230, 45)]],
                                                             [CloseButton,EngCheckBox,ChinCheckBox],
                                                             [(475,-15),(100,310),(340,310)],
                                                             language='chinese')
    def kill(self):
        super().kill()
        data=get_value('data')
        data['language']=get_value('language')
        save(data)
        get_value('uis').add(Language())
class Shovel(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.x, self.y = get_pos()
        self.image=get_value('images')['shovel.png'][tuple()]
    def update(self,screen,events):
        self.x, self.y = get_pos()
        self.x-=30
        self.y-=30
        blity(self.image,(self.x,self.y),True)
        for event in get_value('events'):
            if event.type == pygame.MOUSEBUTTONDOWN:
                button = pygame.mouse.get_pressed()
                if button[0]:
                    pygame.event.post(pygame.event.Event(SHOVEL_BACK))
                    sounds.play('plant',0.5)
                    for plant in get_plants_at((self.x-30)//90+1, (self.y-90)//90+1):
                        plant.hp=-1
                        plant.on_destroy(None)
                        #plant.kill()
                        #lane=get_value('lanes')
                        #lane[plant.lane-1]['plants'].remove(plant)
                        #set_value('lanes',lane)
                    self.kill()
class SeedPackets(pygame.sprite.Group):
    def __init__(self,seeds=[],max_seeds=10):
        super().__init__()
        self.cnt=0
        self.max_seeds=max_seeds
        self.left_seed=0
        for seed in seeds:
            self.cnt+=1
            s=seed((50+50*self.cnt,10))
            s.seed_id=self.cnt-1
            s.real_id=self.cnt-1
            if self.cnt>10:
                s.seed_id=-1
            self.add(s)
    def update(self,screen,events):
        for seed in self:
            seed.update(screen,events)
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    pygame.event.post(pygame.event.Event(SEED_PACKET[0]))
                elif event.key == pygame.K_2:
                    pygame.event.post(pygame.event.Event(SEED_PACKET[1]))
                elif event.key == pygame.K_4:
                    pygame.event.post(pygame.event.Event(SEED_PACKET[3]))
                elif event.key == pygame.K_5:
                    pygame.event.post(pygame.event.Event(SEED_PACKET[4]))
                elif event.key == pygame.K_6:
                    pygame.event.post(pygame.event.Event(SEED_PACKET[5]))
                elif event.key == pygame.K_7:
                    pygame.event.post(pygame.event.Event(SEED_PACKET[6]))
                elif event.key == pygame.K_8:
                    pygame.event.post(pygame.event.Event(SEED_PACKET[7]))
                elif event.key == pygame.K_9:
                    pygame.event.post(pygame.event.Event(SEED_PACKET[8]))
                elif event.key == pygame.K_0:
                    pygame.event.post(pygame.event.Event(SEED_PACKET[9]))
                elif event.key==pygame.K_LEFT:
                    if self.left_seed>0:
                        self.left_seed-=1
                        self.shift_seeds()
                elif event.key==pygame.K_RIGHT:
                    if self.left_seed<self.max_seeds-10:
                        self.left_seed+=1
                        self.shift_seeds()

    def add_seed(self, seed):
        self.cnt+=1
        self.add(seed((50+50*self.cnt,10)))
        seed.seed_id=self.cnt-1
    def shift_seeds(self):
        for seed in self:
            try:
                seed.seed_id=seed.real_id-self.left_seed
                if seed.seed_id<0 or seed.seed_id>9:
                    seed.seed_id=-1
                    seed.visible=False
                    seed.disabled=True
                seed.x=50+50*(seed.seed_id+1)
            except:
                pass

class SeedPacket(pygame.sprite.Sprite):
    def __init__(self,image1,image2,plant,group1,group2,pos,sun_needed,recharge,start_recharge,id_,recharge_per_plant=0):
        super().__init__()
        self.image1=get_value('images')[image1][tuple()]
        self.image2=get_value('images')[image1][('black',)]
        self.image=self.image1
        self.recharge_countdown=start_recharge
        self.recharge=recharge
        self.plant_type=plant
        self.plant_id=id_
        p=plant(seed=True)
        self.plant_traits=p.traits
        p.on_destroy(None)
        self.plant_group=group1
        self.produce_group=group2
        self.x,self.y=pos
        self.highlight_timer=-1
        if get_value('language')=='chinese':
            self.disable_text,self.recharge_text,self.sun_text='禁用','冷却中','阳光不足'
        else:
            self.disable_text,self.recharge_text,self.sun_text='disabled','loading','no sun'
        self.font=Font(resource_path(f'fonts/{get_value("language")}.ttf'), 10)
        self.rect = self.image.get_rect(
            center=(self.x+self.image.get_width()//2, self.y+self.image.get_height()//2))
        self.cost=sun_needed
        self.recharge_per_plant=recharge_per_plant
        self.disabled=False
        self.visible=True
        self.available=False
    def update(self, screen, events):
        min_cost=self.cost
        #print(self.seed_id)
        self.available=True
        for plants in get_value('plants'):
            if plants.traits[-1]==self.plant_traits[-1] or 'everything graft on' in plants.traits or 'graft on everything' in self.plant_traits:
                if (self.cost-math.ceil(plants.cost/4*3/5)*5)<=min_cost:
                    min_cost=(self.cost-math.ceil(plants.cost/4*3/5)*5)
        if self.x<100 or self.x>550:
            self.visible=False
            self.disabled=True
        else:
            self.visible=True
            self.disabled=False
        if get_value('state')=='pre-planting':
            self.recharge_countdown=0
            if self.cost==0 or self.plant_id in SUN_PRODUCING_PLANTS:
                self.recharge_countdown=1
                self.disabled=True
        self.recharge_countdown-=get_value('dt')
        cd=True
        for special in get_value('specials'):
            if type(special)==type(list()):
                if special[0]=='no recharge' and special[1]>0:
                    cd=False
                    self.highlight_timer=1
        self.rect = self.image.get_rect(
            center=(self.x+self.image.get_width()//2, self.y+self.image.get_height()//2))
        if self.recharge_countdown>0 or self.disabled or get_value('sun')<min_cost:
            self.image=self.image2
            self.available=False
        else:
            self.image=self.image1
        if self.highlight_timer>=0:
            self.highlight_timer-=1
            self.image=self.image1
        if self.visible:
            blity(self.image,(self.x,self.y),True)
        if self.highlight_timer>=0:
            blity(get_value('images')['seed_packet_glow.png'][tuple()],(self.x-5,self.y-5))
        if self.visible:
            if self.disabled:
                self.font.render_to(screen,(self.x+4,self.y+5),self.disable_text,(255,255,255))
            elif self.recharge_countdown>0:
                if self.recharge_countdown>0:
                    self.font.render_to(screen,(self.x+4,self.y+5),self.recharge_text,(255,255,255))
                    self.font.render_to(screen,(self.x+10,self.y+25),str(round(self.recharge_countdown,2)),(255,255,255))
            elif get_value('sun')<min_cost:
                if self.recharge_countdown<0:
                    self.font.render_to(screen,(self.x+4,self.y+5),self.sun_text,(255,255,255))
                    #last stand level
        for event in events:
            if not get_value('in_dialogue'):
                if not self.disabled and self.available and (event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(get_pos())) or event.type==SEED_PACKET[self.seed_id]:
                    if not get_value('planting'):
                        if self.recharge_countdown<=0:
                            set_value('planting',True)
                            set_value('planting_plant',[self.plant_id,self])
                            p=self.plant_type(((self.x+25)//90,(self.y-10)//90),self.produce_group,True,self.cost)
                            p.mother=self
                            get_value('seed_packets').add(p)
                            sounds.play('select_seed',1.0)
                if event.type==PLANT_PLANTED:
                    if cd:
                        id_,packet=get_value('planting_plant')
                        if id_==self.plant_id and packet is self:
                            if self.recharge_per_plant!=0:
                                num=len(get_a_plant_in(0,9,0,9,self.plant_id))
                                self.recharge_countdown=self.recharge+self.recharge_per_plant*num
                            else:
                                self.recharge_countdown=self.recharge
                
class PeaSeed(SeedPacket):
    def __init__(self,pos):
        super().__init__('pea_seed.png','black_pea_seed.png',Peashooter,get_value('seed_packets'),get_value('missles'),pos,75,5,10,1)

class SunflowerSeed(SeedPacket):
    def __init__(self, pos):
        super().__init__('sunflower_seed.png','black_sunflower_seed.png', Sunflower,
                         get_value('seed_packets'), get_value('resources'), pos,50,15,1,2)


class RepeaterSeed(SeedPacket):
    def __init__(self, pos):
        super().__init__('repeater_seed.png','black_repeater_seed.png', Repeater,
                         get_value('seed_packets'), get_value('missles'), pos,200,10,10,3)


class SnowPeaSeed(SeedPacket):
    def __init__(self, pos):
        super().__init__('snowpea_seed.png','black_snowpea_seed.png', SnowPea,
                         get_value('seed_packets'), get_value('missles'), pos,175,10,10,4)
class PuffshroomSeed(SeedPacket):
    def __init__(self, pos):
        super().__init__('puffshroom_seed.png', 'black_puffshroom_seed.png', Puffshroom,
                         get_value('seed_packets'), get_value('missles'), pos,0, 14, 2, 5)


class SunshroomSeed(SeedPacket):
    def __init__(self, pos):
        super().__init__('sunshroom_seed.png', 'black_sunshroom_seed.png', Sunshroom,
                         get_value('seed_packets'), get_value('resources'), pos, 25, 15, 2, 6)


class FumeshroomSeed(SeedPacket):
    def __init__(self, pos):
        super().__init__('fumeshroom_seed.png', 'black_fumeshroom_seed.png', Fumeshroom,
                         get_value('seed_packets'), get_value('resources'), pos, 150, 10, 10, 7)


class MilkPeaSeed(SeedPacket):
    def __init__(self, pos):
        super().__init__('milkpea_seed.png', 'black_milkpea_seed.png', MilkPea,
                         get_value('seed_packets'), get_value('missles'), pos, 200, 30, 10, 8)


class GatlingPeaSeed(SeedPacket):
    def __init__(self, pos):
        super().__init__('gatling_seed.png', 'black_gatling_seed.png', GatlingPea,
                         get_value('seed_packets'), get_value('missles'), pos, 425, 60, 30, 9)


class WallnutSeed(SeedPacket):
    def __init__(self, pos):
        super().__init__('wallnut_seed.png', 'black_wallnut_seed.png', Wallnut,
                         get_value('seed_packets'), get_value('missles'), pos, 50, 45, 30, 10)


class PotatoMineSeed(SeedPacket):
    def __init__(self, pos):
        super().__init__('potato_seed.png', 'black_potato_seed.png', PotatoMine,
                         get_value('seed_packets'), get_value('missles'), pos, 25, 25, 10, 11)


class CatailSeed(SeedPacket):
    def __init__(self, pos):
        super().__init__('catail_seed.png', 'catail_seed.png', Catail,
                         get_value('seed_packets'), get_value('missles'), pos, 225, 60, 30, 12)
class IcebergSeed(SeedPacket):
    def __init__(self, pos):
        super().__init__('iceberg_seed.png', 'catail_seed.png', IcebergLettuce,
                         get_value('seed_packets'), get_value('missles'), pos, 0, 35, 10, 13)
class MiniPearSeed(SeedPacket):
    def __init__(self, pos):
        super().__init__('minipear_seed.png', 'catail_seed.png', MiniPear,
                         get_value('seed_packets'), get_value('missles'), pos, 150, 20, 10, 14)
class PeapodSeed(SeedPacket):
    def __init__(self, pos):
        super().__init__('peapod_seed.png', 'catail_seed.png',Peapod,
                         get_value('seed_packets'), get_value('missles'), pos, 200, 10, 10, 15)
class FirepeaSeed(SeedPacket):
    def __init__(self, pos):
        super().__init__('firepea_seed.png', 'catail_seed.png',Firepea,
                         get_value('seed_packets'), get_value('missles'), pos, 175, 10, 10, 16)
class ShadowShroomSeed(SeedPacket):
    def __init__(self, pos):
        super().__init__('shadow_shroom_seed.png', 'catail_seed.png',ShadowShroom,
                         get_value('seed_packets'), get_value('missles'), pos, 0, 30, 5, 17)
class BuzzztonSeed(SeedPacket):
    def __init__(self, pos):
        super().__init__('buzzzton_seed.png', 'catail_seed.png',Buzzzton,
                         get_value('seed_packets'), get_value('missles'), pos, 75, 60, 10, 18)
class TallnutSeed(SeedPacket):
    def __init__(self, pos):
        super().__init__('tallnut_seed.png', 'catail_seed.png',Tallnut,
                         get_value('seed_packets'), get_value('missles'), pos, 125, 45, 30, 19)
class MagnoliaSeed(SeedPacket):
    def __init__(self, pos):
        super().__init__('mag_seed.png', 'catail_seed.png',Magnolia,
                         get_value('seed_packets'), get_value('missles'), pos, 100, 10, 10, 20)
class CherrySeed(SeedPacket):
    def __init__(self, pos):
        super().__init__('cherry_seed.png', 'catail_seed.png',CherryBomb,
                         get_value('seed_packets'), get_value('missles'), pos, 150, 45, 30, 21)

class SweetpeaSeed(SeedPacket):
    def __init__(self, pos):
        super().__init__('sweet_pea_seed.png', 'black_milkpea_seed.png', Sweetpea,
                         get_value('seed_packets'), get_value('missles'), pos, 200, 30, 10, 22)
class TorchSeed(SeedPacket):
    def __init__(self, pos):
        super().__init__('torch_seed.png', 'black_milkpea_seed.png', Torchwood,
                         get_value('seed_packets'), get_value('missles'), pos, 225, 20, 30, 23)
class FireWeedSeed(SeedPacket):
    def __init__(self, pos):
        super().__init__('fireweed_seed.png', 'black_milkpea_seed.png', FireWeed,
                         get_value('seed_packets'), get_value('missles'), pos, 50, 20, 10, 24)
class CoffeeBeanSeed(SeedPacket):
    def __init__(self, pos):
        super().__init__('coffee_seed.png', 'black_milkpea_seed.png', CoffeeBean,
                         get_value('seed_packets'), get_value('missles'), pos, 50, 20, 10, 25)
class WWMSeed(SeedPacket):
    def __init__(self, pos):
        super().__init__('wwm_seed.png', 'black_milkpea_seed.png', WWM,
                         get_value('seed_packets'), get_value('missles'), pos, 777, 300, 60, 26)
class ChomperSeed(SeedPacket):
    def __init__(self, pos):
        super().__init__('chomper_seed.png', 'black_milkpea_seed.png', Chomper,
                         get_value('seed_packets'), get_value('missles'), pos, 222, 300, 60, 27)
class SproutSeed(SeedPacket):
    def __init__(self, pos):
        super().__init__('sprout_seed.png', 'black_milkpea_seed.png', LittleSprout,
                         get_value('seed_packets'), get_value('missles'), pos, 100, 12.5, 10, 28)
class PlanternSeed(SeedPacket):
    def __init__(self, pos):
        super().__init__('plantern_seed.png', 'black_milkpea_seed.png', Plantern,
                         get_value('seed_packets'), get_value('missles'), pos, 50, 45, 30, 29)
class PowerflowerSeed(SeedPacket):
    def __init__(self, pos):
        print('hello')
        super().__init__('powerflower_seed.png', 'black_milkpea_seed.png', Powerflower,
                         get_value('seed_packets'), get_value('resources'), pos, 150, 60, 2, 30)
#power-ups
class PowerUp(pygame.sprite.Sprite):
    def __init__(self,image1,pos,recharge,start_recharge,use_chance,power_id,sun_needed=0,kind='gadget',gadget=None):
        super().__init__()
        self.image1=get_value('images')[image1][tuple()]
        self.image2=get_value('images')[image1][('black',)]
        self.image=self.image1
        self.recharge_countdown=start_recharge
        self.recharge=recharge
        self.x,self.y=pos
        self.use_chance=use_chance
        self.kind=kind
        self.gadget=gadget
        self.power_id=power_id
        if get_value('language')=='chinese':
            self.disable_text,self.recharge_text='禁用','冷却中'
        else:
            self.disable_text,self.recharge_text='disabled','loading'
        self.font=Font(resource_path(f'fonts/{get_value("language")}.ttf'), 10)
        self.large_font=Font(resource_path(f'fonts/{get_value("language")}.ttf'), 20)
        self.rect = self.image.get_rect(
            center=(self.x+self.image.get_width()//2, self.y+self.image.get_height()//2))
        self.cost=sun_needed

        
        self.disabled=False
        self.visible=True
        if not 2 in get_value('data')['unlocked_features']:
            self.disabled=True
            self.visible=False
    def update(self, screen, events):
        if get_value('state')=='pre-planting':
            self.recharge_countdown=0
            if self.cost==0:
                self.recharge_countdown=1
        self.recharge_countdown-=get_value('dt')
        self.rect = self.image.get_rect(
            center=(self.x+self.image.get_width()//2, self.y+self.image.get_height()//2))
        if self.recharge_countdown<0 and not self.disabled and not self.use_chance<=0:
            self.image=self.image1
        else:
            self.image=self.image2
        if self.visible:
            blity(self.image,(self.x,self.y),True)
        if self.visible:
            if self.disabled:
                self.font.render_to(screen,(self.x+15,self.y+7),self.disable_text,(255,255,255))
            elif not (get_value('sun') >= self.cost and self.recharge_countdown<0):
                if self.recharge_countdown>0:
                    self.font.render_to(screen,(self.x+15,self.y+7),self.recharge_text,(255,255,255))
                    self.font.render_to(screen,(self.x+21,self.y+27),str(round(self.recharge_countdown,2)),(255,255,255))
        if self.visible:
            self.large_font.render_to(screen,(self.x+60,self.y+60),str(self.use_chance),(255,255,255))                    
        #last stand level
        for event in events:
            if not self.disabled and (event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(get_pos())):
                if not get_value('planting') and self.use_chance>0:
                    if self.recharge_countdown<=0:
                        if self.kind=='gadget':
                            get_value('uis').add(self.gadget(self))
                            sounds.play('select_seed',1.0)
                        else:
                            self.effect()
                            self.use_chance-=1
                            self.recharge_countdown=self.recharge
class Nut(PowerUp):
    def __init__(self):
        super().__init__('nut_cracker_powerup.png',(495+163,535+6),60,10,3,0,gadget=NutCracker)
class Blizzard(PowerUp):
    def __init__(self):
        super().__init__('blizzard_powerup.png',(495+163,535+6),10,60,3,1,kind='instant')
    def effect(self):
        snow(100,100)
        set_value('veil',[2, 43, 122,200,50/25])
        for plant in get_value('plants'):
            plant.effect['snowball']=1000
class PlantFoodPacket(PowerUp):
    def __init__(self):
        super().__init__('plant_food_powerup.png',(495+163,535+6),10,30,5,2,gadget=PlantFood)
class MagicalRandomness(PowerUp):
    def __init__(self):
        super().__init__('magical_randomness_powerup.png',(495+163,535+6),0,75,1,3,gadget=RandomnessWand)
class FriedChicken(PowerUp):
    def __init__(self):
        super().__init__('fried_duck_powerup.png',(495+163,535+6),40,15,3,4,gadget=FriedChick)
class LastStand(PowerUp):
    def __init__(self):
        super().__init__('last_stand_powerup.png',(495+163,535+6),0,60,1,5,kind='instant')
    def effect(self):
        set_value('shake',200)
        set_value('veil',[89,35,13,200,20/25])
        for plant in get_value('plants'):
            get_value('particles_-2').add(Fire_((plant.x-40,plant.y-60)))
            for a in range(plant.cost//25+1):
                sun=Sun((plant.x-40+random.randint(-10,10),plant.y-60+random.randint(-10,10)),(20,20))
                sun.on_collect()
                get_value('resources').add(sun)
            plant.on_destroy()
        #refresh recharge of seedpackets
        for seed in get_value('seed_packets'):
            seed.recharge_countdown=0
        specials=get_value('specials')
        specials.append(['no recharge',250])

class GardeningGlove(PowerUp):
    def __init__(self):
        super().__init__('glove_powerup.png',(495+163,535+6),1,1,100,6,gadget=Glove)
class ShopPacket(pygame.sprite.Sprite):
    def __init__(self,pos):
        super().__init__()
        self.image1=loady(resource_path('images//seed.png'))
        self.image=self.image1
        self.x,self.y=pos
        self.hover_time=0
        self.lore=False
    def update(self, screen, events):
        self.rect = self.image.get_rect(
            center=(self.x+self.image.get_width()//2, self.y+self.image.get_height()//2))
        blity(self.image,(self.x,self.y),True)
        if self.rect.collidepoint(get_pos()):
            if self.hover_time<5:
                self.hover_time+=1
            if self.hover_time>=5:
                if not self.lore:
                    if get_value('language')=='chinese':
                        t=['将选卡上限增加至'+str(get_value('data')['seed_limit']+1)+'。']
                    else:
                        t=['Allows you to pick '+str(get_value('data')['seed_limit']+1)+' plants.']
                    get_value('uber_uis').add(Lore(t,self))
                    self.lore=True
        else:
            if self.hover_time>0:
                self.hover_time-=1
            if self.hover_time<=0:
                self.lore=False
class ShopSeed(pygame.sprite.Sprite):
    def __init__(self,pos,plant_id):
        super().__init__()
        see_=SEEDS_WITH_ID[plant_id]((10000,100000))
        image=see_.image1
        self.image1=image
        self.image=self.image1
        self.plant_id=plant_id
        self.x,self.y=pos
        self.hover_time=0
        self.lore=False
    def update(self, screen, events):
        self.rect = self.image.get_rect(
            center=(self.x+self.image.get_width()//2, self.y+self.image.get_height()//2))
        blity(self.image,(self.x,self.y),True)
        if self.rect.collidepoint(get_pos()):
            if self.hover_time<5:
                self.hover_time+=1
            if self.hover_time>=5:
                if not self.lore:
                    get_value('uber_uis').add(ShortPlantLore(self))
                    self.lore=True
        else:
            if self.hover_time>0:
                self.hover_time-=1
            if self.hover_time<=0:
                self.lore=False
class ShopPower(pygame.sprite.Sprite):
    def __init__(self,pos,powerup_id):
        super().__init__()
        see_=POWERUPS_WITH_ID[powerup_id]()
        image=see_.image1
        self.image1=image
        self.image=self.image1
        self.power_id=powerup_id
        self.x,self.y=pos
        self.hover_time=0
        self.lore=False
    def update(self, screen, events):
        self.rect = self.image.get_rect(
            center=(self.x+self.image.get_width()//2, self.y+self.image.get_height()//2))
        blity(self.image,(self.x,self.y),True)
        if self.rect.collidepoint(get_pos()):
            if self.hover_time<5:
                self.hover_time+=1
            if self.hover_time>=5:
                if not self.lore:
                    get_value('uber_uis').add(ShortPowerLore(self))
                    self.lore=True
        else:
            if self.hover_time>0:
                self.hover_time-=1
            if self.hover_time<=0:
                self.lore=False
#seed select
class SelectingSeed(pygame.sprite.Sprite):
    def __init__(self,pos,image,packet,selected_seeds,plant_id=0):
        super().__init__()
        self.image1=image
        self.image=self.image1
        self.disabled=False
        self.seed_id=-1
        self.plant_id=plant_id
        self.selected=False
        self.selected_seeds=selected_seeds
        self.x,self.y=pos
        self.og_x,self.og_y=pos
        self.packet=packet
        self.hover_time=0
        self.lore=False
        if 'last_stand' in get_value('level').gimmicks and self.plant_id in SUN_PRODUCING_PLANTS:
            print('im disabled')
            self.disabled=True
    def update(self, screen, events):
        self.rect = self.image.get_rect(
            center=(self.x+self.image.get_width()//2, self.y+self.image.get_height()//2))
        if not self.disabled:
            blity(self.image,(self.x,self.y),True)
        if self.rect.collidepoint(get_pos()) and not self.disabled:
            if self.hover_time<5:
                self.hover_time+=1
            if self.hover_time>=5:
                if not self.lore:
                    get_value('uber_uis').add(ShortPlantLore(self))
                    self.lore=True
        else:
            if self.hover_time>0:
                self.hover_time-=1
            if self.hover_time<=0:
                self.lore=False
        for event in events:
            if (event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(get_pos())):
                if not self.disabled:
                    if not self.selected:
                        if self.selected_seeds.cnt<self.selected_seeds.max_seeds:
                            self.selected=True
                            self.selected_seeds.add_seed(self)
                            sounds.play('select_seed',1)
                            events.remove(event)
                    else:
                        self.selected=False
                        self.selected_seeds.remove_seed(self)
                        sounds.play('select_seed',1)
                        events.remove(event)
class SelectedSeeds(pygame.sprite.Group):
    def __init__(self,seeds=[],max_seeds=8):
        super().__init__()
        self.cnt=0
        self.max_seeds=max_seeds
        self.left_seed=0
        for seed in seeds:
            self.cnt+=1
            self.add(seed((50+50*self.cnt,10)))
            seed.seed_id=self.cnt-1
            seed.real_id=self.cnt-1
            if self.cnt>10:
                seed.seed_id=-1
    def update(self,screen,events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key==pygame.K_LEFT:
                    if self.left_seed>0:
                        self.left_seed-=1
                        self.shift_seeds()
                elif event.key==pygame.K_RIGHT:
                    if self.left_seed<self.max_seeds-10:
                        self.left_seed+=1
                        self.shift_seeds()

    def add_seed(self, seed):
        self.cnt+=1
        seed.x=50+50*self.cnt
        seed.y=10
        self.add(seed)
        seed.seed_id=self.cnt-1
        seed.real_id=self.cnt-1-self.left_seed
    def remove_seed(self,seed):
        self.cnt-=1
        seed.seed_id=-1
        seed.x=seed.og_x
        seed.y=seed.og_y
        self.remove(seed)
        for seed_ in self:
            if seed_.real_id>seed.real_id:
                seed_.real_id-=1
                self.shift_seeds()
    def shift_seeds(self):
        for seed in self:
            try:
                seed.seed_id=seed.real_id-self.left_seed
                if seed.seed_id<0 or seed.seed_id>9:
                    seed.seed_id=-1
                    seed.visible=False
                    seed.disabled=True
                seed.x=50+50*(seed.seed_id+1)
            except:
                pass
class SelectingSeeds(pygame.sprite.Group):
    def __init__(self,seeds,width,max_seeds=None):
        super().__init__()
        if not max_seeds:
            max_seeds=get_value('max_seeds')
        self.selected_seeds=SelectedSeeds(max_seeds=max_seeds)
        self.menu=SeedMenu(self)
        self.seeds=seeds
        self.width=width
        self.done_seeds=None
    def update(self,screen,events):
        self.selected_seeds.update(screen,events)
        self.menu.update()
        for seed in self:
            seed.update(screen,events)
        if abs(int(get_value('level').idk)-77)<=2:
                
            self.cnt=0
            self.cct=0
            for seed in self.seeds:
                if seed in get_value('data')['unlocked_plants']:
                    self.cnt+=1
                    see_=SEEDS_WITH_ID[seed]((10000,100000))
                    seed=SelectingSeed((50+50*self.cnt,100+self.cct*60),see_.image1,SEEDS_WITH_ID[seed],self.selected_seeds,plant_id=seed)
                    if not 'double power' in get_value('scene').gimmicks:
                        time.sleep(0.005)
                        print(seed)
                    self.add(seed)
                    if self.cnt%self.width==0:
                        self.cnt=0
                        self.cct+=1
            print(self)
    def fugging_end_this(self):
        self.done_seeds=[]
        for seed in self.selected_seeds:
            self.done_seeds.append(seed.plant_id)
        for seed in self:
            seed.kill()
class SeedMenu(pygame.sprite.Sprite):
    def __init__(self,mother):
        super().__init__()
        self.x=80
        self.y=640
        self.image=loady(resource_path('bgs//card_selection.png'))
        self.move_state=-1
        self.button=Goooooo((self.x+180,self.y+400),self)
        self.mother=mother
        if 2 in get_value('data')['unlocked_features']:
            self.gadgets=PowerSelection(self)
        else:
            self.gadgets=None
    def update(self):
        blity(self.image,(self.x,self.y),True)
        self.button.x=self.x+400
        self.button.y=self.y+530
        self.button.update(get_value('screen'),get_value('events'))
        if self.gadgets:
            self.gadgets.update()
        if self.y<0:
            self.y=0
        if self.y>0 and self.move_state!=1:
            self.y-=25.6*get_value('equivalent_frame')
        if self.move_state==1 and self.y<640:
            self.y+=25.6*get_value('equivalent_frame')
        elif self.move_state==1 and self.y>=640:
            self.kill()
            for seed in self.mother:
                seed.kill()
            set_value('seed_selection',None)
            get_value('level').seed_selection=None
class PowerSelection(pygame.sprite.Sprite):
    def __init__(self,mother):
        super().__init__()
        self.x,self.y=495,640
        self.image=loady(resource_path('bgs//powerup_menu.png'))
        self.mother=mother
        self.arrows=[Arrow((self.x+17,self.y+65),self,'left',True),Arrow((self.x+103,self.y+65),self,'right',True)
                     ,Expand((self.x+189,self.y+80),self,'up')]
        self.value=0
        self.max_value=5
        self.powerups=[]
        self.last_pressed=None
        cnt=0
        self.data=get_value('data')
        for key in POWERUPS_WITH_ID:
            if key in self.data['unlocked_powerups']:
                seed=SelectingPowerup((0,0),POWERUPS_WITH_ID[key],self)
                seed.powerup_id=key
                self.powerups.append(seed)
                cnt+=1
    def update(self):
        if not self.value in self.data['unlocked_powerups']:
            if not self.last_pressed or self.last_pressed=='left':
                while not self.value in self.data['unlocked_powerups']:
                    self.arrows[0].on_clicked()
            else:
                while not self.value in self.data['unlocked_powerups']:
                    self.arrows[1].on_clicked()
        blity(self.image,(self.x,self.y),True)
        self.circles=[]
        self.circles=[(self.x+15+a%4*90,self.y+121+a//4*90) for a in range(12)]
        for bruh in self.circles:
            blity(get_value('images')['gadget_slot.png'][tuple()],bruh,True)
        if self.y>640-105:
            self.y-=4.2
        if self.mother.move_state!=1:
            self.arrows[0].x=self.x+132
            self.arrows[0].y=self.y+65
            self.arrows[1].x=self.x+217
            self.arrows[1].y=self.y+65
            self.arrows[2].x=self.x+189
            self.arrows[2].y=self.y+80
            self.arrows[0].update(get_value('screen'),get_value('events'))
            self.arrows[1].update(get_value('screen'),get_value('events'))
            self.arrows[2].update(get_value('screen'),get_value('events'))
            
        else:
            try:
                self.arrows[0].kill()
                self.arrows[1].kill()
                self.arrows[2].kill()
                for power in self.powerups:
                    power.kill()
                    self.powerups.remove(power)
            except:
                pass
        for power in self.powerups:
            power.update(get_value('screen'),get_value('events'))
            
    def up(self):
        self.y=640-400
    def down(self):
        self.y=640-105
class SelectingPowerup(pygame.sprite.Sprite):
    def __init__(self,pos,powerup,menu):
        super().__init__()
        self.disabled=False
        self.powerup_id=-1
        self.selected=False
        self.menu=menu
        self.x,self.y=pos
        self.og_x,self.og_y=pos
        self.powerup=powerup
        self.image=powerup().image1
        self.power_id=powerup().power_id
        self.hover_time=0
    def update(self, screen, events):
        self.og_x,self.og_y=self.menu.x+16+self.powerup_id%4*90,self.menu.y+122+self.powerup_id//4*90
        self.rect = self.image.get_rect(
            center=(self.x+self.image.get_width()//2, self.y+self.image.get_height()//2))
        if self.rect.collidepoint(get_pos()) and not self.disabled:
            if self.hover_time<10:
                self.hover_time+=1
            if self.hover_time>=5:
                if not self.lore:
                    get_value('uber_uis').add(ShortPowerLore(self))
                    self.lore=True
        else:
            self.hover_time=0
            self.lore=False
        if self.powerup_id==self.menu.value:
            self.selected=True
        else:
            self.selected=False
        if self.selected:
            self.x,self.y=self.menu.x+163,self.menu.y+6
        else:
            self.x,self.y=self.og_x,self.og_y
            
        if not self.disabled:
            blity(self.image,(self.x,self.y),True)
        for event in events:
            if (event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(get_pos())):
                if not self.disabled:
                    if not self.selected:
                        self.menu.value=self.powerup_id
                        sounds.play('select_seed',1)
#functions
def find_packet(plant_class):

    for packet in get_value('seed_packets'):
        try:
            plant1=packet.plant_type(seed=True)
        except:
            continue
        plant1.show=False
        plant2=plant_class(seed=True)
        plant2.show=False
        if type(plant1)==type(plant2):
            return packet
        plant1.on_destroy(None)
        plant2.on_destroy(None)
    return None



def find_plant_class(plant):

    for packet in PLANTS_WITH_ID:
        plant2=PLANTS_WITH_ID[packet](seed=True)
        plant2.show=False
        if type(plant)==type(plant2):
            return PLANTS_WITH_ID[packet]
        plant2.on_destroy(None)
    return None
#save file
def save(new_data):
    #load or create save file
    newpath = r'C:\ProgramData\pvzidk'
    if not os.path.exists(newpath):
        os.makedirs(newpath)
    with open(r'C:\ProgramData\pvzidk\beta_data.idk','a+') as f:
        pass
    with open(r'C:\ProgramData\pvzidk\beta_data.idk','w') as f:
        json.dump(new_data,f)
    set_value('data',new_data)
#generate a random level for daily challenge
ZOMBIE_POWER_LEVELS={1:[1],
                     2:[2,11,12,8],
                     3:[3,9,14,15,16,17,18,19,4,7],
                     4:[10,13],
                     5:[6,5]}
def random_level():
    #select one zombie from each power level
    random.seed(datetime.now().year*366+datetime.now().month*31+datetime.now().day)
    level=dict()
    zombies=[random.choice(ZOMBIE_POWER_LEVELS[power]) for power in range(1,6)]
    #add one zombie from a random power level
    zombies.append(random.choice(ZOMBIE_POWER_LEVELS[random.randint(1,5)]))
    level['start_sun']=50*random.randint(2,4)
    level['lanes']=[1,2,3,4,5]
    level['scene']=random.choice(['lawn_night','lawn_day','void'])
    level['sun_fall']=random.randint(0,1)
    if level['start_sun']<=50:
        level['sun_fall']=1
    if level['scene']=='lawn_night':
        level['sun_fall']=0
    level['wave_duration']=[random.randint(10,13)*100,
                            random.randint(11,13)*50,300]
    level['gimicks']=[]
    level['level']=['Daily challenge!','每日挑战！']
    if level['scene']=='lawn_night' or level['scene']=='void':
        level['shroom_sleep']=0
    else:
        level['shroom_sleep']=1
    level['opening_grave']=random.randint(0,5)
    level['grave_danger']=random.randint(0,1)
    if level['grave_danger']>0:
        level['gimicks'].append('grave')
    if level['shroom_sleep']==0:
        level['wave_duration'][0]+=100
    level['max_grave']=random.randint(5,20)
    level['grave_area']=[random.randint(4,7),10]
    level['sun_fall_duration']=[300,random.randint(8,18)*50]
    level['big_wave']=random.randint(1,2)*5
    if not get_value('data')['completed_daily']:
        if datetime.now().weekday()>=5:
            level['unlocks']=['False','False','False','False',2]
        else:
            level['unlocks']=['False','False','False','False',1]
    else:
        level['unlocks']=['False','False','False']
    level['zombie_spawn']=generate_level(zombies)
    return(level)
def generate_level(zombies):
    # Choose total number of waves randomly
    total_waves = random.choice([10, 15, 20, 25,30])
    
    waves = []
    
    for wave_idx in range(total_waves):
        # Calculate progression through the level (0 to 1)
        progression = wave_idx / (total_waves - 1) if total_waves > 1 else 0.0
        total_weight=int(1+wave_idx*0.5+(progression*8)*2/4)
        total_weight=random.randint(total_weight-1,total_weight+1)
        
        wave = []
            # Calculate weights for regular zombies (first 5 elements)
        weights = [
            (5 - k) * (1 - progression) + (k + 1) * progression
            for k in range(5)
        ]
        while total_weight>0:
            sum_weight = sum(weights)
            rand_val = random.uniform(0, sum_weight)
            
            # Select zombie type based on weights
            cumulative = 0
            for k in range(5):
                cumulative += weights[k]
                if rand_val <= cumulative:
                    if k+1<=total_weight:
                        wave.append(zombies[k])
                        total_weight-=k+1
                        break
                        
        
        waves.append(wave)
    for wave in waves:
        if random.random()<=0.1:
            wave.append(zombies[-1])
    return waves

def save(new_data):
    import os,json,getpass
    #load or create save file
    newpath = rf'C:\Users\{getpass.getuser()}\AppData\Local\pvzidk'
    if not os.path.exists(newpath):
        os.makedirs(newpath)
    with open(rf'{newpath}\beta_data.idk','a+') as f:
        pass
    with open(rf'{newpath}\beta_data.idk','w') as f:
        json.dump(new_data,f)
    set_value('data',new_data)
#constants
SEEDS_WITH_ID={1:PeaSeed,2:SunflowerSeed,3:RepeaterSeed,4:SnowPeaSeed,5:PuffshroomSeed,6:SunshroomSeed,7:FumeshroomSeed,
                8:MilkPeaSeed,9:GatlingPeaSeed,10:WallnutSeed,11:PotatoMineSeed,12:CatailSeed,13:IcebergSeed,14:MiniPearSeed,
                15:PeapodSeed,16:FirepeaSeed,17:ShadowShroomSeed,18:BuzzztonSeed,19:TallnutSeed,20:MagnoliaSeed,21:CherrySeed,
               22:SweetpeaSeed,23:TorchSeed,24:FireWeedSeed,25:CoffeeBeanSeed,26:WWMSeed,27:ChomperSeed,28:SproutSeed,
               29:PlanternSeed,30:PowerflowerSeed}
POWERUPS_WITH_ID={0:Nut,1:Blizzard,2:PlantFoodPacket,3:MagicalRandomness,4:FriedChicken,5:LastStand,6:GardeningGlove}
SUN_PRODUCING_PLANTS=[2,6,30]
NPC_DIALOGUES={'unicorn_0':
               [{'chinese':['每日关卡，等你挑战~☆','星虹代币等待着它的主人~☆'],
                 'english':['Daily level awaiting~☆','Come claim your chroma credit~☆']},
                {'chinese':['来吧~☆'],
                 'english':['Come in~☆']},
                {'chinese':['挑战，开始~☆'],
                 'english':['The challenge begins~☆']}],
               'unicorn_1':
               [{'chinese':['兑换强力星虹植物~☆','明天再来啊~☆','阳光彩虹小白马~☆'],
                 'english':['Buy strong chromatic plants~☆','Come again tomorrow~☆']},
                {'chinese':['进来吧~☆'],
                 'english':['Come in~☆']},
                {'chinese':['阳光彩虹小白马~☆'],
                 'english':['The power of rainbow~☆']}],
               'unicorn_shop':
               [{'chinese':['兑换强力星虹植物~☆','无聊的话点击我聊会天~','阳光彩虹小白马~☆','圣灵啊...'],
                 'english':['Buy strong chromatic plants~☆','Click on me to talk to me if you bored~','The holy rainbow...']},
                {'chinese':['进来吧~☆'],
                 'english':['Come in~☆']},
                {'chinese':['阳光洋溢在你的脸庞~☆','今天天气真好~'],
                 'english':['Your face shines bright~','Great weather~']}],
               'jhpcs1':
               [{'chinese':['……','天外有天……','虚空裂痕……','小芽……'],
                 'english':['...','The void rift...','Lil sprout...','The vast Cosmos...']},
                {'chinese':['进来吧~☆'],
                 'english':['Come in~☆']},
                {'chinese':['你好呀，伙伴！'],
                 'english':["Oh, you're here!",'Hello, my friend!']}],
               'sprout':
               [{'chinese':['','','',''],
                 'english':['']},
                {'chinese':['进来吧~☆'],
                 'english':['Come in~☆']},
                {'chinese':[''],
                 'english':['']}]
               }
REPEATED_DIALOGUES=[7,8,9,10,11,12,16,17,41,42,43,44,45,46]
