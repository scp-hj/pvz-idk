import pygame,math
from missles import *
from resources import *
from config import *
from particles import *
from filter import *
import sounds
import random
from events import *
import sys
import os
from PIL import Image
from pygame.freetype import Font
import cv2 as cv
import numpy
import math
def cv2_2_pillow(img: numpy.ndarray) -> Image:
    # return Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    return Image.fromarray(img)


def pillow_2_cv2(img: Image) -> numpy.ndarray:
    # return cv2.cvtColor(numpy.array(img), cv2.COLOR_RGB2BGR)
    i = numpy.array(img)
    red = i[:, :, 0].copy()
    i[:, :, 0] = i[:, :, 2].copy()
    i[:, :, 2] = red
    return i


def pillow_2_pygame(image):
    mode = image.mode
    size = image.size
    data = image.tobytes()
    return pygame.image.fromstring(data, size, mode)


def cv2_2_pygame(cv2Image):
    if cv2Image.dtype.name == 'uint16':
        cv2Image = (cv2Image / 256).astype('uint8')
    size = cv2Image.shape[1::-1]
    if len(cv2Image.shape) == 2:
        cv2Image = np.repeat(cv2Image.reshape(size[1], size[0], 1), 3, axis=2)
        format = 'RGB'
    else:
        format = 'RGBA' if cv2Image.shape[2] == 4 else 'RGB'
        cv2Image[:, :, [0, 2]] = cv2Image[:, :, [2, 0]]
    surface = pygame.image.frombuffer(cv2Image.flatten(), size, format)
    return surface.convert_alpha() if format == 'RGBA' else surface.convert()



PLANT_PLANTED = pygame.USEREVENT+2

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


class Plant(pygame.sprite.Sprite):
    def __init__(self, images,health, pos,cartoon_id,special_duration,missles,seed=False,cost=0,special_criteria=1,shoot_anim_name=None,costume_interval=0,traits=[],trait_configs=dict(),sleep_image='',plant_id=0,show=True,fast_reaction=False,keep_attack=False,start_frame=None):#special_crieteria:1=have something to attack the thelane
        super().__init__()
        if not seed:
            self.id_=get_value('plant_largest_id')
            set_value('plant_largest_id',self.id_+1)
        self.paths=images
        self.images = [get_value('images')[image][tuple()] for image in images]
        pos=list(pos)
        pos[0]=int(pos[0])
        pos[1]=int(pos[1])
        self.shifts=True
        if not seed:
            lanes=get_value('lanes')
            lane=lanes[pos[1]-1]['plants']
            lane.insert(0,self)
            lanes[pos[1]-1]['plants']=lane
            set_value('lanes',lanes)
        self.pos=pos
        self.x = pos[0]*90+20
        self.y = pos[1]*90+70
        self.skills=dict()
        self.mother=None #for planting plants
        #self.og_x = self.x
        #self.og_y = self.y
        self.lane = pos[1]
        self.show=show
        try:
            _=self.xshift,self.yshift
        except:
            self.xshift,self.yshift=0,0
        self.column=pos[0]
        self.traits=traits
        self.trait_configs=trait_configs
        self.pos=pos
        self.full_hp=health
        self.armor=0
        self.plant_id=plant_id
        self.hp=health
        self.special_num=0
        self.cartoon=cartoon_id
        self.duration=special_duration
        self.special_countdown=special_duration*0.3
        self.gn=get_value('images')['gn.png'][tuple()]
        self.missles=missles
        self.costume_countdown=0.5
        self.costume_cnt = 0
        self.seed=seed
        self.fast_reaction=fast_reaction
        self.keep_attack=keep_attack
        self.interval=costume_interval
        self.cost=cost
        self.growing=None
        self.protect=False
        self.sleeping=('sleep' in get_value('specials'))
        if 'awake' in self.traits:
            self.sleeping=False
        self.graftable=False
        self.resistance=1
        self.additional_animations=list()
        self.effect={'snowball':-1,'randomness':-1,'unselectable':-1,'coffee':-1,'wwm':-1,'chilled':-1,
                     'overheat':-1,'powerflower':-1}
        self.unselected=False
        #{'name':[[sprites_in_sequence],special_frame_name,special,special_criteria,(x,y),start_costume_timer,end_costume_timer]}
        if not self.seed:
            if (get_value('level').shroom_sleep and 'shroom' in self.traits) or ('skol' in get_value('level').gimmicks):
                self.sleeping=True
        self.hit_timer=-1
        self.effects=[]
        self.atk_frame=shoot_anim_name
        if self.cartoon==6:
            self.sleep_image=get_value('images')[sleep_image][tuple()]
        self.costume_num=0
        self.special_criteria=special_criteria
        self.head_countdown = 1
        self.change_head=False
        self.milks=False
        self.milked_cnt=0
        self.milk_end_countdown=0
        self.milked=False
        self.unselected=False
        self.atk_coefficient=1
        self.animation_coefficient=1
        self.start_frame=start_frame
        self.angle=[0,0] #[angle, delta angle]
        self.height_factor=1
        self.cnt=0
        self.last_effects=[]
        #list of plants (using class name) that it cannot be planted/grafted on
        self.banned_combo=[]
        #cartoon
        if self.cartoon == 1 or self.cartoon==5:
            self.root = [-20+50,-20+62]
            self.stem = [-20+50, -35+62]
            self.head = [-30+50, -53+62]
        elif self.cartoon == 2:
            self.root = [-20+50, -20+62]
            self.stem = [-20+50, -35+62]
            self.head = [-50+50, -53+62]
        elif self.cartoon == 3:
            self.hats = [[-12+50, -45+62+20+10], [5+35+5, -60+62+20+10],[5+35+5-20, -60+62+20+10-5]]
            self.heads = [[-12+50, -30+62+20+10],[5+35+5,-45+62+20+10],[5+35+5-20,-45+62+20+10-5]]
        elif self.cartoon==4 or self.cartoon==6:
            self.body = [-12+50, -30+62]
    #trais
        if 'revolution' in self.traits:
            self.revolution_timer=-1
        self.graft_id=-1
        for plants in get_value('plants'):
            if not plants is self and plants.column==self.column and plants.lane==self.lane:
                self.graft_id=plants.plant_id
    def update(self, screen,*args):
        if self.protect:
            if not 'ungraftable' in self.traits:
                self.traits.append('ungraftable')
        if self.cnt==1 and self.graft_id!=-1:
            p=PLANTS_WITH_ID[self.graft_id]()
            p.graft_effect(self)
            p.show=False
            p.on_destroy()
        self.relative_x,self.relative_y=self.x+get_value('pos_shift')[0],self.y+get_value('pos_shift')[1]
        if not self.seed and self.hit_timer<=0:
            self.cnt+=1
            if abs(self.angle[0]-self.angle[1])<abs(self.angle[1]):
                self.angle=[0,0]
            self.angle[0]+=self.angle[1]
            if self.shifts:
                self.height_factor+=math.sin(math.radians(self.cnt)*5)*0.0035
        #pre-plant
        if get_value('state')=='pre-planting':
            self.special_countdown=0.1
        self.special_countdown-=get_value('dt')*self.atk_coefficient
        self.costume_countdown-=get_value('dt')*self.animation_coefficient
        #skills
        for skill in self.skills:
            self.skills[skill][1]-=get_value('equivalent_frame')
            if self.skills[skill][1]<=0:
                self.skills[skill][1]=self.skills[skill][2]
                skill()
        #traits
        if 'revolution' in self.traits:
            self.revolution_timer-=get_value('equivalent_frame')
            if self.revolution_timer>0:
                get_value('particles_-1').add(Fire((self.x-40,self.y-60),self))
        #resistance
        self.resistance=1
        if 'revolution' in self.traits:
            if self.revolution_timer>0:
                self.resistance*=0.2
        #milk
        if self.milks:
            if self.milked_cnt<2:
                self.milks=False
                self.milk_end_countdown=5
                self.milked_cnt+=1
        if self.milk_end_countdown>0:
            self.milk_end_countdown-=get_value('dt')
            if self.milk_end_countdown<=0:
                self.milked_cnt-=get_value('equivalent_frame')
                if self.milked_cnt==0:
                    self.milk_end_countdown=0
                    self.milked=False
                else:
                    self.milk_end_countdown=5
        self.animation_coefficient=1+0.1*self.milked_cnt
        self.atk_coefficient=1+0.1*self.milked_cnt
        #effects
        self.unselected=False
        for effect in self.effect:
            if self.effect[effect]>=0:
                self.effect[effect]=self.effect[effect]-get_value('equivalent_frame')
                if effect=='snowball' or effect=='chilled':
                    self.animation_coefficient*=0.5
                    self.atk_coefficient*=0.5
                if effect=='powerflower':
                    self.animation_coefficient*=1.25
                    self.atk_coefficient*=1.25
                    get_value('particles_-1').add(
                        EffectPowerflower((self.x-10, self.y-60), self))
                if effect=='overheat':
                    self.animation_coefficient*=2
                    self.atk_coefficient*=2
                    get_value('particles_-1').add(
                        Overheat((self.x-10, self.y-60), self))
                    if abs(self.effect['overheat']//4*4-self.effect['overheat'])<=get_value('equivalent_frame')*0.5:
                        self.damage(10,None,'fire','homing')
                        
                if effect=='coffee':
                    self.animation_coefficient*=2
                    self.atk_coefficient*=2
                if effect=='unselectable':
                    self.unselected=True
                    
            if effect=='randomness' and self.effect[effect]==-100:
                get_value('particles_-1').add(Randomness((self.x-40,self.y-60),self))
            if effect=='wwm' and self.effect[effect]>=0:
                get_value('particles_-1').add(QZNS((self.x,self.y-60)))
        if self.armor>=6000:
            get_value('particles_-1').add(FullShield((self.x-40,self.y-60),self))
        elif self.armor>=2000:
            get_value('particles_-1').add(HalfShield((self.x-40,self.y-60),self))
        elif self.armor>0:
            get_value('particles_-1').add(BrokeShield((self.x-40,self.y-60),self))
        if self.costume_countdown <= 0 and not self.seed and (not self.cartoon==6 or not self.sleeping):
            self.next_costume()
            if self.cartoon==1:
                self.costume_countdown=1.1
            elif self.cartoon==2 or self.cartoon==3 or self.cartoon==5:
                self.costume_countdown = 0.3
            elif self.cartoon==4:
                self.costume_countdown=1.1
            elif self.cartoon==6:
                self.costume_countdown=self.interval
        #render effects
        self.effects=[]
        if self.hit_timer == 1 or self.hit_timer==2:
            #self.on_hit()
            self.effects.append('hit')
        else:
            if self.milked:
                self.effects.append('milk')
            if self.effect['snowball']>=0 or self.effect['chilled']>=0:
                self.effects.append('freeze')
            if self.unselected:
                self.effects.append('transparent')
        self.images=[get_value('images')[image][tuple(self.effects)] for image in self.paths]
        if self.cartoon == 4 or self.cartoon==6:
            self.images = [pygame.transform.scale(image, self.photo_size) for image in self.images]
                
        self.last_effects = self.effects
        self.hit_timer -= 1
        if not self.cartoon==6 and not self.sleeping:
            if self.special_criteria == 1:
                if get_obstacles_in(self.pos[0],10,self.pos[1],self.pos[1]) or get_zombies_in(self.pos[0],10,self.pos[1],self.pos[1]):
                    if self.special_countdown <= 0 and not self.seed:
                        self.special()
                else:
                    if 'revolution' in self.traits:
                        if self.revolution_timer>0:
                            self.revolution_timer=-1
            elif self.special_criteria==2:
                if self.special_countdown <= 0 and not self.seed:
                    self.special()
                else:
                    pass
            elif self.special_criteria==3:
                if get_obstacles_in(self.pos[0], self.pos[0]+4, self.pos[1], self.pos[1]) or get_zombies_in(self.pos[0], self.pos[0]+4, self.pos[1], self.pos[1]):
                    if self.special_countdown <= 0 and not self.seed:
                        self.special()
                else:
                    if 'revolution' in self.traits:
                        if self.revolution_timer>0:
                            self.revolution_timer=-1
            elif self.special_criteria==4:
                if len(get_zombies_in(1,10,1,get_value('level').lane_num))>0:
                    if self.special_countdown<=0 and not self.seed:
                        self.special()
                else:
                    if 'revolution' in self.traits:
                        if self.revolution_timer>0:
                            self.revolution_timer=-1
            elif self.special_criteria==6:
                if len(get_plants_at(self.column,self.lane))>1:
                    if self.special_countdown<=0 and not self.seed:
                        self.special()
                else:
                    if 'revolution' in self.traits:
                        if self.revolution_timer>0:
                            self.revolution_timer=-1
        #additional animations
        for av in self.additional_animations:
            av[6]-=get_value('equivalent_frame')
            if av[6]<=0:
                av[6]=av[7]+random.randint(-2,2)
                
                av[1]+=1
                if av[1]>=len(av[0]):
                    av[1]=0
                special_yes=False
                if av[0][av[1]]==av[2]:
                    if av[4] == 1:
                        if get_obstacles_in(self.pos[0], 9, self.pos[1], self.pos[1]) or get_zombies_in(self.pos[0], 9, self.pos[1], self.pos[1]):
                            
                            special_yes=True
                    elif av[4] == 2:
                            special_yes = True
                    elif av[4] == 3:
                        if get_obstacles_in(self.pos[0], self.pos[0]+3, self.pos[1], self.pos[1]) or get_zombies_in(self.pos[0], self.pos[0]+3, self.pos[1],self.pos[1]):

                            special_yes = True
                    elif av[4] == 4:
                        if len(get_value('zombies').sprites()) > 0:
                            special_yes = True
                    if special_yes:
                        av[3](av)
                    else:
                        av[1]=0
        #rect
        if self.cartoon==1 or self.cartoon==5:
            self.rect = pygame.Rect(
                self.x-50+self.head[0], self.y-62+self.head[1], 70, 75)
        elif self.cartoon==2:
            self.rect = pygame.Rect(
                self.x-50+self.head[0], self.y-62+self.head[1], 80, 75)
        elif self.cartoon==3:
            self.rect = pygame.Rect(
                self.x-50+self.hats[0][0], self.y-62+self.hats[0][1], 24,30)
        elif self.cartoon==4 or self.cartoon==6:
            self.rect = pygame.Rect(
                self.x-50+self.body[0], self.y-62+self.body[1], self.photo_size[0], self.photo_size[1])
        if self.head_countdown <= 0:
            if self.change_head:
                if len(self.images)==5 or len(self.images)==7:
                    self.images[2], self.images[3] = self.images[3], self.images[2]
                    self.paths[2], self.paths[3] = self.paths[3], self.paths[2]
                elif len(self.images) == 4:
                    self.images[1], self.images[2] = self.images[2], self.images[1]
                    self.paths[1], self.paths[2] = self.paths[2], self.paths[1]
                elif len(self.images) == 3:
                    self.images[0],self.images[1]=self.images[1],self.images[0]
                    self.paths[0], self.paths[1] = self.paths[1], self.paths[0]
                self.change_head = False
        if self.head_countdown>0:
            self.head_countdown-=get_value('dt')
        #grafting icon
        if not self.seed:
            if get_value('planting') and not 'non_graftable' in self.traits:
                planting=PLANTS_WITH_ID[get_value('planting_plant')[0]](seed=True)
                planting.show=False
                if planting.traits[-1]==self.traits[-1] or 'graft on everything' in planting.traits or 'everything graft on' in self.traits:
                    get_value('particles_-1').add(Graftable((self.x,self.y),self))
                    self.graftable=True
                else:
                    self.graftable=False
                #planting.on_destroy()
            else:
                self.graftable=False
        if self.seed:
            plant_below=None
            try:
                plant_below=get_plants_at((self.x+25-get_value('pos_shift')[0])//90, (self.y-60-get_value('pos_shift')[1])//90)[0]
            except:
                pass
            color='yellow'
            text=''
            if not plant_below:
                text='-'+str(self.cost)
                if get_value('sun')<self.cost:
                    color='red'
                else:
                    color='yellow'
            else:
                if plant_below.graftable:
                    if 'revolution' in self.traits:
                        get_value('particles_-1').add(Fire((self.x-40,self.y-60),self))
                    graft_cost=self.cost-math.ceil(plant_below.cost/4*3/5)*5
                    if get_value('sun')>graft_cost:
                        color='yellow'
                        if graft_cost>=0:
                            text='-'+str(graft_cost)
                        else:
                            text='+'+str(-graft_cost)
                    else:
                        color='red'
                        text='-'+str(graft_cost)
                else:
                    text=''
            if color=='yellow':
                color=(255,255,112)
            else:
                color=(220,20,60)
            set_value('sun_data',[text,color])
            screen=pygame.Surface((140,150),pygame.SRCALPHA)
            self.x,self.y=get_pos()
            if self.cartoon == 1 or self.cartoon==5:
                self.root = [-20+50, -20+62]
                self.stem = [-20+50, -35+62]
                self.head = [-30+50, -53+62]
            elif self.cartoon == 2:
                self.root = [-20+50, -20+62]
                self.stem = [-20+50, -35+62]
                self.head = [-50+50, -53+62]
            elif self.cartoon == 3:
                self.hats = [[-12+50, -45+62], [-5+35, -60+62]]
                self.heads = [[-12+50, -30+62],[5+35,-45+62]]
            elif self.cartoon==4 or self.cartoon==6:
                self.body = [-12+50, -30+62]
            if self.cartoon == 1 or self.cartoon == 2 or self.cartoon == 5:
                screen.blit(self.images[0], self.root)
                screen.blit(self.images[1], self.stem)
                screen.blit(self.images[2], self.head)
            elif self.cartoon == 3:
                if self.shroom_number >= 2:
                    screen.blit(self.images[0], self.hats[1])
                    screen.blit(self.images[1], self.heads[1])
                if self.shroom_number == 3:
                    screen.blit(self.images[0], self.hats[2])
                    screen.blit(self.images[1], self.heads[2])
                screen.blit(self.images[0], self.hats[0])
                screen.blit(self.images[1], self.heads[0])
            elif self.cartoon == 4:
                self.body = [50+self.xshift, 62+self.yshift]
                screen.blit(self.images[0], self.body)
            elif self.cartoon == 6:
                self.body = [50+self.xshift, 62+self.yshift]
                screen.blit(self.images[self.costume_num], self.body)
            for event in get_value('events'):
                if event.type == pygame.MOUSEBUTTONDOWN:
                    button=pygame.mouse.get_pressed()
                    if button[0]:
                        yes=False
                        for plant_ in get_plants_at((self.x+25-get_value('pos_shift')[0])//90, (self.y-60-get_value('pos_shift')[1])//90):
                            if 'can plant on' in plant_.traits and len(get_plants_at((self.x+25-get_value('pos_shift')[0])//90, (self.y-60-get_value('pos_shift')[1])//90))==1:
                                if find_plant_class(plant_) in self.banned_combo:
                                    yes=False
                                else:
                                    yes=True
                        if (not get_objects_at((self.x+25-get_value('pos_shift')[0])//90, (self.y-60-get_value('pos_shift')[1])//90)) or 'floating' in self.traits or yes:
                            if get_value('sun')>=self.cost and int((self.y-60-get_value('pos_shift')[1])//90) in get_value('level').available_lanes and (self.x+25-get_value('pos_shift')[0])//90<=9 and (self.x+25-get_value('pos_shift')[0])//90>=1:
                                class_=PLANTS_WITH_ID[get_value('planting_plant')[0]]
                                plant((self.x+25-get_value('pos_shift')[0])//90, (self.y-60)//90, get_value('plants'),
                                    class_, self.missles, get_value('particles_1'),cost=self.cost)
                                set_value('planting',False)
                                self.kill()
                                set_value('sun',get_value('sun')-self.cost)
                                if yes:
                                    get_value('newest_plant').xshift+=plant_.trait_configs['can plant on'][0]
                                    get_value('newest_plant').yshift+=plant_.trait_configs['can plant on'][1]
                                plant_=get_value('planting_plant')[0]
                                pygame.event.post(pygame.event.Event(PLANT_PLANTED))
                        else:
                            if not 'ungraftable' in self.traits:
                                for plants in get_plants_at((self.x+25-get_value('pos_shift')[0])//90, (self.y-60-get_value('pos_shift')[1])//90):
                                    if plants.graftable and get_value('sun')>=(self.cost-math.floor(plants.cost/4*3/5)*5) and int((self.y-60-get_value('pos_shift')[1])//90) in get_value('level').available_lanes and (self.y-60-get_value('pos_shift')[1])//90>=1 and (self.x+25-get_value('pos_shift')[0])//90<=9 and (self.x+25-get_value('pos_shift')[0])//90>=1:
                                        class_=PLANTS_WITH_ID[get_value('planting_plant')[0]]
                                        graft((self.x+25-get_value('pos_shift')[0])//90, (self.y-60)//90, get_value('plants'),
                                            class_, self.missles, get_value('particles_-1'),self.cost,plants)
                                        set_value('planting',False)
                                        self.kill()
                                        #plants.kill()
                                        #plants.show=False
                                        #get_value('plants').remove(plants)
                                        set_value('sun',get_value('sun')-(self.cost-math.ceil(plants.cost/4*3/5)*5))
                                        plant_=get_value('planting_plant')[0]
                                        pygame.event.post(pygame.event.Event(PLANT_PLANTED))
                                
                    elif button[2]:
                        set_value('planting',False)
                        self.kill()
            blity(get_value('images')['tile_highlight.png'][tuple()],((self.x+25-get_value('pos_shift')[0])//90*90-25, (self.y-60-get_value('pos_shift')[1])//90*90+35))
            blity(screen,(self.x-50,self.y-50),True)
    def graft_effect(self,plant):
        pass
    def display(self):
        if self.show:
            if self.protect:
                image=loady('bgs//tile_protect_plant.png')
                blity(image,(self.x-50,self.y-60))
            #pygame.draw.rect(get_value('screen'),(255,0,0),self.rect,3)
            screen=pygame.Surface((140,150),pygame.SRCALPHA)
            if self.cartoon == 1 or self.cartoon == 2 or self.cartoon == 5:
                if self.sleeping:
                    img = self.images[4]
                else:
                    img = self.images[2]
                screen.blit(self.images[0], self.root)
                screen.blit(self.images[1],self.stem)
                screen.blit(img,self.head)
            elif self.cartoon==3:
                if self.sleeping:
                    img=self.images[3]
                else:
                    img=self.images[1]
                if self.shroom_number>=2:
                    screen.blit(self.images[0], self.hats[1])
                    screen.blit(img, self.heads[1])
                if self.shroom_number==3:
                    screen.blit(self.images[0], self.hats[2])
                    screen.blit(img, self.heads[2])
                screen.blit(self.images[0], self.hats[0])
                screen.blit(img,self.heads[0])
            elif self.cartoon==4:
                if self.sleeping:
                    img=self.images[2]
                else:
                    img=self.images[0]
                self.body = [self.xshift+50, self.yshift+62]
                screen.blit(img, self.body)
            elif self.cartoon==6:
                if self.sleeping:
                    img=self.sleep_image
                else:
                    try:
                        img=self.images[self.costume_num]
                    except:
                        pass
                self.body = [self.xshift+50, self.yshift+62]
                screen.blit(img,self.body)
            if self.sleeping and not self.seed:
                screen.blit(self.gn,(70,0))
            if self.effect['coffee']>0:
                self.sleeping=False
                screen.blit(get_value('images')['!.png'][tuple()],(70,0))
            #[[sprites_in_sequence],costume_num,special_frame_name,special,special_criteria,(x,y),start_costume_timer,end_costume_timer,name]
            #draw additional animations
            for av in self.additional_animations:
                screen.blit(get_value('images')[av[0][av[1]]][tuple(self.effects)],(av[5][0]+50,av[5][1]+65))
            try:
                _=self.rect
            except:
                self.rect=self.images[0].get_rect()
            temp=math.floor(self.height_factor*1000)/1000
            screen=pygame.transform.smoothscale(screen,(140,150*temp))
            screen=pygame.transform.rotate(screen,self.angle[0])
            temp=(self.height_factor-1)*self.rect[3]
            temp=math.floor(temp/1)*1
            pos=(self.x-50-math.tan(math.radians(self.angle[0]))*50,self.y-60-temp-math.tan(math.radians(self.angle[0]))*self.rect[3])
            blity(screen,pos)
    def special(self):
        self.special_num+=1
        if len(self.images) == 5 or len(self.images)==7:
            self.images[2], self.images[3] = self.images[3], self.images[2]
            self.paths[2], self.paths[3] = self.paths[3], self.paths[2]
        elif len(self.images) == 4:
            self.images[1], self.images[2] = self.images[2], self.images[1]
            self.paths[1], self.paths[2] = self.paths[2], self.paths[1]
        elif len(self.images) == 3:
            self.images[0], self.images[1] = self.images[1], self.images[0]
            self.paths[0], self.paths[1] = self.paths[1], self.paths[0]
        self.head_countdown = 0.25
        if self.duration==5:
            self.head_countdown=0.5
        self.change_head=True
        self.special_countdown = self.duration+random.random()*random.uniform(-0.2, 0.2)
        if self.effect['snowball']>=0:
            self.effect['snowball']=-1
            get_value('missles').add(Snowball((self.x+25,self.y-38),self.x+40,self))
            return False
        return 1
            
    def revolution_effect(self):
        if self.sleeping and 'revolution' in self.traits:
            self.sleeping=False
            self.revolution_timer=0
    def on_hit(self,enemy):
        if self.hp<=0:
            self.on_destroy(enemy)
    def damage(self,damage,enemy=None,dmg_type=None,missle_kind=None,real=False):
        self.hit_timer=3
        if self.armor>0 and not real:
            self.armor-=damage*self.resistance
        else:
            self.hp-=damage*self.resistance
        self.on_hit(enemy)
    def on_destroy(self,enemy=None):
        lane=get_value('lanes')
        try:
            lane[self.lane-1]['plants'].remove(self)
            set_value('lanes',lane)
        except:
            pass
        if self.protect:
            get_value('level').die()
        self.kill()
    def next_costume(self):
        self.costume_cnt+=1
        if self.cartoon==1 or self.cartoon==2 or self.cartoon==5:
            temp=self.costume_cnt%4
            if self.cartoon==1 or self.cartoon==2:
                if len(self.paths)==5:
                    paths=[
                    'stem1.png','stem2.png', 'stem3.png','stem2.png']
                else:
                    paths=[self.paths[1],self.paths[5], self.paths[6],self.paths[5]]
                    
                imgs = [get_value('images')[image][tuple()] for image in paths]
            else:
                paths=['milkpea_stem1.png','milkpea_stem2.png', 'milkpea_stem3.png','milkpea_stem2.png']
                imgs = [get_value('images')[image][tuple()] for image in paths]                
            self.images[1]=imgs[temp]
            self.paths[1]=paths[temp]
        if self.cartoon==6 and not self.sleeping:
            self.costume_num+=1
            if self.costume_num>=len(self.paths):
                self.costume_num=0
            self.special_yes=False
            if not self.start_frame:
                self.start_frame=''
            if self.paths[self.costume_num]==self.start_frame or self.paths[self.costume_num]==self.atk_frame:
                if self.special_criteria == 1:
                    if get_obstacles_in(self.pos[0],10,self.pos[1],self.pos[1]) or get_zombies_in(self.pos[0],10,self.pos[1],self.pos[1]):
                        if not self.seed:
                            self.special_yes=True
                elif self.special_criteria==2:
                    if not self.seed:
                        self.special_yes=True
                elif self.special_criteria==3:
                    if get_obstacles_in(self.pos[0], self.pos[0]+3, self.pos[1], self.pos[1]) or get_zombies_in(self.pos[0], self.pos[0]+3, self.pos[1], self.pos[1]):
                        if not self.seed:
                            self.special_yes=True
                elif self.special_criteria==4:
                    if len(get_zombies_in(1,10,1,get_value('level').lane_num))>0:
                        if not self.seed:
                            self.special_yes=True
                elif self.special_criteria==5:
                    if not self.seed:
                        for zombie in get_value('zombies'):
                            if zombie.lane==self.lane and abs(zombie.x-self.x)<135 and self.x>=zombie.x:
                                self.special_yes=True
                        for zombie in get_value('obstacles'):
                            if zombie.lane==self.lane and abs(zombie.x-self.x)<135 and self.x>=zombie.x:
                                self.special_yes=True
                elif self.special_criteria==6:
                    if len(get_plants_at(self.column,self.lane))>1:
                        self.special_yes=True
                    else:
                        self.costume_num=0
                if self.special_yes:
                    if self.paths[self.costume_num]==self.atk_frame:
                        self.special()
                else:
                    self.costume_num=0
        if self.cartoon == 4 or (self.cartoon==6 and int(self.costume_cnt)%2==0):
            if self.change_head:
                self.costume_cnt -= 1
            else:
                if (self.cartoon==4 and self.costume_cnt%2==1) or (self.cartoon==6 and (self.costume_cnt%4==2)):
                    self.minus=True
                else:
                    self.minus=False
                if self.minus:
                    #self.photo_size=(self.photo_size[0],self.photo_size[1]+3)
                    #self.yshift-=3
                    pass
                else:
                    pass
                    #self.photo_size = (self.photo_size[0], self.photo_size[1]-3)
                    #self.yshift += 3
                self.images=[pygame.transform.scale(get_value('images')[image][tuple()],self.photo_size) for image in self.paths]
        if self.cartoon == 1 or self.cartoon==5:
            if temp == 0:
                self.head[0]=50-30+self.xshift
            elif temp==1 or temp==3:
                self.head[0]=50-32+self.xshift
            else:
                self.head[0]=50-34+self.xshift
        if self.cartoon == 2:
            if temp == 0:
                self.head[0] = 50-48+self.xshift
            elif temp == 1 or temp == 3:
                self.head[0] = 50-50+self.xshift
            else:
                self.head[0] = 50-52+self.xshift
        self.effects=[]
        if self.hit_timer == 1 or self.hit_timer==2:
            #self.on_hit()
            self.effects.append('hit')
        else:
            if self.milked:
                self.effects.append('milk')
            if self.effect['snowball']>=0 or self.effect['chilled']>=0:
                self.effects.append('freeze')
        self.images=[get_value('images')[image][tuple(self.effects)] for image in self.paths]
        if self.cartoon == 4 or self.cartoon==6:
            self.images = [pygame.transform.scale(image, self.photo_size) for image in self.images]
            if self.cartoon==6:
                if self.special_yes and self.keep_attack:
                    self.costume_num-=1
                    if self.costume_num<0:
                        self.costume_num=len(self.paths)-1
    def heal(self,hp):
        self.hp+=hp
        if self.hp>self.full_hp:
            self.hp=self.full_hp


class Peashooter(Plant):
    def __init__(self,pos=(0,0),missles=pygame.sprite.Group(),seed=False,cost=0):
        super().__init__(['leaves.png','stem1.png','pea_new.png','pea_wink.png','pea_sleep.png'],100,pos,1,1.4,missles,seed,cost,plant_id=1,traits=['pea'])
    def special(self):
        if super().special():
            self.angle=[10,-1.25]
            if self.effect['randomness']==-100:
                missle=random.choices(list(MISSLES_WITH_CHANCES.keys()),list(MISSLES_WITH_CHANCES.values()))[0]
            else:
                missle=Pea
            target=None
            for zombie in get_value('zombies'):
                if target:
                    if zombie.lane==self.lane:
                        if zombie.x<target.x:
                            target=zombie
                else:
                    target=zombie
            self.missles.add(missle((self.x-40,self.y-38),self.x+20,self))
            #self.missles.add(missle((self.x-40,self.y-38),self.x+20,self,dest_x=target.x-target.og_speed*25*target.speed_coefficient))
class SnowPea(Plant):
    def __init__(self, pos=(0, 0), missles=pygame.sprite.Group(), seed=False, cost=0):
        super().__init__(['leaves.png', 'stem1.png', 'snow_head.png',
                          'snow_wink.png','snow_sleep.png'], 200, pos,
                         1, 1.3, missles, seed, cost,plant_id=4,traits=['pea'])

    def special(self):
        if super().special():
            self.angle=[10,-1.25]
            if self.effect['randomness']==-100:
                missle=random.choices(list(MISSLES_WITH_CHANCES.keys()),list(MISSLES_WITH_CHANCES.values()))[0]
            else:
                missle=IcePea
            self.missles.add(missle((self.x-40,self.y-38),self.x+20,self))
class Repeater(Plant):
    def __init__(self, pos=(0, 0), missles=pygame.sprite.Group(), seed=False, cost=0):
        super().__init__(['leaves.png', 'stem1.png', r'repeat_head.png',
                          r'repeat_wink.png',r'repeat_sleep.png'], 200, pos, 1, 1.05,
                         missles, seed, cost,plant_id=3,traits=['pea'])

    def special(self):
        if super().special():
            self.angle=[20,-1.25]
            if self.effect['randomness']==-100:
                missle=random.choices(list(MISSLES_WITH_CHANCES.keys()),list(MISSLES_WITH_CHANCES.values()))[0]
            else:
                missle=Pea
            self.missles.add(missle((self.x-45, self.y-38),self.x+20,self))
            self.missles.add(missle((self.x-70,self.y-38),self.x+20,self))
            if self.special_num%5==0 and get_value('hard_mode'):
                peas=[Pea((self.x-40,self.y-38),self.x+20,self),Pea((self.x-40,self.y-38),self.x+20,self)]
                peas[0].velocity=(12,2)
                peas[1].velocity=(12,-2)
                self.missles.add(peas[0])
                self.missles.add(peas[1])

class Sunflower(Plant):
    def __init__(self, pos=(0, 0), resources=pygame.sprite.Group(), seed=False, cost=0):
        super().__init__(['leaves.png', 'stem1.png',
                          r'sunflower_head.png', r'sunflower_smile.png',
                          r'sunflower_sleep.png'], 600, pos, 2, 25, resources,
                         seed,cost,2,plant_id=2,traits=['flower'])
    def special(self):
        if super().special():
            self.missles.add(Sun((self.x-30,self.y-48),(self.x+20,self.y+20)))
class Puffshroom(Plant):
    def __init__(self,pos=(0,0),missles=pygame.sprite.Group(),seed=False,cost=0,traits=['shroom']):
        super().__init__(['puffshroom_hat.png','puffshroom_head.png',
                          'puffshroom_wink.png','puffshroom_sleep.png'],50,
                         pos,3,1.3,missles,seed,cost,3,traits=['grow','little','shroom'],plant_id=5)
        self.shroom_number=1
        self.attack_time=0
        self.shifts=False
    def special(self):
        if super().special():
            if self.effect['randomness']==-100:
                missle=random.choices(list(MISSLES_WITH_CHANCES.keys()),list(MISSLES_WITH_CHANCES.values()))[0]
            else:
                missle=Spore
            self.missles.add(missle((self.x-40,self.y+10),self.x+5,self))
            if self.shroom_number>=2:
                self.missles.add(missle((self.x-57, self.y-5), self.x+5,self))
            if self.shroom_number==3:
                self.missles.add(missle((self.x-87, self.y-10), self.x-25,self))
            self.attack_time += 1
            if self.shroom_number<=2 and self.attack_time%(25*self.shroom_number)==0:
                self.grow()
    def grow(self):
        if self.shroom_number==1:
            pos=(self.x-5,self.y-30)
        elif self.shroom_number==2:
            pos=(self.x-30,self.y-50)
        get_value('particles_1').add(PuffshroomGrow(pos,self))


class Sunshroom(Plant):
    def __init__(self, pos=(0, 0), resources=pygame.sprite.Group(), seed=False, cost=0,traits=['shroom']):
        self.xshift, self.yshift = -12, -15
        super().__init__(['sunshroom.png', 'sunshroom_smile.png','sunshroom_sleep.png'],
                         200, pos, 4, 26, resources, seed, cost, 2,traits=['grow','little','shroom'],plant_id=6)
        self.produce_time = 0
        self.photo_size=self.images[0].get_width(),self.images[0].get_height()
        self.shifts=False
        self.growing=False
        self.grown=False
    def special(self):
        if super().special():
            if self.produce_time==7 and not self.grown:
                self.grow()
            if not self.grown:
                self.missles.add(SmallSun((self.x, self.y-15), (self.x+20, self.y+20)))
            else:
                self.missles.add(Sun((self.x, self.y-15), (self.x+20, self.y+20)))
        self.produce_time+=1
    def on_destroy(self,enemy=None):
        super().on_destroy(enemy)
        try:
            if get_value('hard_mode') and self.hp<=0:
                enemy.toxic=True,700
        except:
            pass
    def grow(self):
        sounds.play('grow',0.5)
        self.special_duration=24
        self.growing=True
        self.shifts=True
        self.grown=True
        self.traits.remove('little')
    def next_costume(self):
        super().next_costume()
        if self.growing:
            self.photo_size = (
                    self.photo_size[0]+6, self.photo_size[1]+6)
            self.xshift-=3
            self.yshift-=6
            self.images = [pygame.transform.scale(get_value('images')[image][tuple()], self.photo_size) for image in self.paths]
            if self.photo_size[0]>=48 and self.photo_size[1]>=60:
                self.growing=False


class Fumeshroom(Plant):
    def __init__(self, pos=(0, 0), missles=pygame.sprite.Group(), seed=False, cost=0,traits=['shroom']):
        self.xshift, self.yshift = -24, -30
        super().__init__([r'fumeshroom.png', r'fumeshroom_attack.png',r'fumeshroom_sleep.png'],
                         200, pos, 4,3.3, get_value('missles'), seed, cost,traits=['shroom'],plant_id=7)
        self.photo_size=self.images[0].get_width(),self.images[0].get_height()
    def special(self):
        if super().special():
            self.angle=[-10,1.25]
            self.missles.add(Fume((self.x-self.xshift-5,self.y-self.yshift-35),mother=self))
class MilkPea(Plant):
    def __init__(self,pos=(0,0),missles=pygame.sprite.Group(),seed=False,cost=0):
        super().__init__(['milkpea_leaves.png','milkpea_stem1.png','milkpea_head.png',
                          'milkpea_wink.png','milkpea_sleep.png'],200,pos,5,1.25,
                         missles,seed,cost,plant_id=8,traits=['holy','pea'])
        self.special_cnt=0
    def special(self):
        if super().special():
            self.angle=[10,-1.25]
            self.special_cnt+=1
            if self.effect['randomness']==-100:
                missle=random.choices(list(MISSLES_WITH_CHANCES.keys()),list(MISSLES_WITH_CHANCES.values()))[0]
            else:
                missle=Milk
            self.missles.add(missle((self.x-40,self.y-38),self.x+20,self))
            if self.special_cnt%7==0:
                x,y=(self.x+25)//90,(self.y-60)//90
                plants=get_plants_in(x-1,x+1,y-1,y+1)
                if self in plants:
                    plants.remove(self)
                for plant in plants:
                    get_value('particles_0').add(MilkHeal((plant.x-30, plant.y-53),152,plant))
                    plant.full_hp+=50
                    plant.heal(400)
                    plant.milks = True
                    plant.milked=True
class GatlingPea(Plant):
    def __init__(self,pos=(0,0),missles=pygame.sprite.Group(),seed=False,cost=0,destroy=False):
        super().__init__(['leaves.png','stem1.png','gatling_pea_head.png',
                          'gatling_pea_attack.png','gatling_pea_sleep_what.png'],200,
                         pos,1,0.3,missles,seed,cost,plant_id=9,traits=['revolution','pea'],trait_configs={'revolution':125})
        self.pea_left=125
        self.pea_recovery_countdown=-1
        self.state=1# state1:attacking state2: no zombie and have peas left state3: no peas left
    def update(self,screen,*args):
        self.effects.append('e')
        super().update(screen,args)
        #states
        if self.state!=3:
            if self.pea_left>=1:
                if get_obstacles_in(self.pos[0],9,self.pos[1],self.pos[1]) or get_zombies_in(self.pos[0],9,self.pos[1],self.pos[1]):
                    self.state=1
                else:
                    self.state=2
            else:
                self.state=3
        else:
            if self.pea_left==100:
                self.state=1
        #pea recovery
        if self.pea_recovery_countdown==-1:
            if self.state==2 and self.pea_left<40:
                self.pea_recovery_countdown=-1
            elif self.state==3:
                self.pea_recovery_countdown=1
        if self.pea_recovery_countdown>0:
            self.pea_recovery_countdown-=1
        if self.pea_recovery_countdown==0:
            self.pea_left+=1
            if self.state==1:
                self.pea_recovery_countdown=-1
            elif self.state==2:
                self.pea_recovery_countdown=int(30/self.atk_coefficient)
            else:
                self.pea_recovery_countdown=int(3/self.atk_coefficient)
        #head change
        if self.state==3:
            self.paths[2]=r'gatling_pea_rest.png'
        else:
            if not self.change_head:
                self.paths[2] =r'gatling_pea_head.png'
                
            else:
                self.paths[2] =r'gatling_pea_attack.png'

    def special(self):
        if self.pea_left>0 and not self.state==3:
            if super().special():
                self.angle=[5,-1.25]
                self.pea_left-=1
                if self.revolution_timer<=0:
                    if self.effect['randomness']==-100:
                        missle=random.choices(list(MISSLES_WITH_CHANCES.keys()),list(MISSLES_WITH_CHANCES.values()))[0]
                    else:
                        missle=Pea
                    self.missles.add(missle((self.x+25,self.y-38),self.x+40,self))
                self.head_countdown=0.03333
                self.special_countdown=0.09999
                if self.revolution_timer>0:
                    peas=[FirePea((self.x+25,self.y-38),self.x+40,self),FirePea((self.x+25,self.y-38),self.x+40,self),RedFirePea((self.x+25,self.y-38),self.x+40,self)]
                    peas[0].velocity=(12,3)
                    peas[1].velocity=(12,-3)
                    self.missles.add(peas[0])
                    self.missles.add(peas[1])
                    self.missles.add(peas[2])
                
class Wallnut(Plant):
    def __init__(self,pos=(0,0),missles=pygame.sprite.Group(),seed=False,cost=0):
        self.xshift, self.yshift =-25,-35
        self.photo_size=(60,60)
        self.degrade=0
        self.eye=0
        super().__init__(['wallnut_0_0.png','wallnut_sleep.png','wallnut_sleep.png'],
                         4000,pos,4,15,missles,seed,cost,2,plant_id=10,traits=['nut'])
    def update(self,screen,*args):
        super().update(screen,args)
        #degrade
        if self.hp<=500:
            self.degrade=2
        elif self.hp<=2000:
            self.degrade=1
        else:
            self.degrade=0
        #change image
        if not self.sleeping:
            self.paths[0]=f'wallnut_{int(self.degrade)}_{int(self.eye%4)}.png'
        else:
            self.paths[0]=f'wallnut_sleep.png'
    def special(self):
        if super().special():
            #change eye
            self.eye+=1
class RootedMine(Plant):
    def __init__(self,pos=(0,0),missles=pygame.sprite.Group(),seed=False,cost=0):
        self.xshift, self.yshift =-30,-10
        self.photo_size=(60,40)
        self.up_cnt=400
        self.grown=False
        super().__init__([r'rooted_mine.png',r'rooted_mine.png',r'rooted_mine.png'],1,
                         pos,4,12,missles,seed,cost,2,plant_id=11,traits=['grow','little','root'])
    def update(self,screen,*args):
        super().update(screen,args)
        self.up_cnt-=get_value('equivalent_frame')
        if self.up_cnt<=0 and not self.grown:
            self.grow()
    def grow(self):
        self.grown=True
        get_value('particles_1').add(PotatoUp((self.x-30,self.y-10),self.pos))
        self.kill()
        self.on_destroy(self)
        
    def special(self):
        super().special()
class PotatoMine(Plant):
    def __init__(self,pos=(0,0),missles=pygame.sprite.Group(),seed=False,cost=0):
        self.xshift, self.yshift =-30,-10
        self.photo_size=(60,40)
        self.costume=0
        super().__init__([r'potato_mine_0.png',r'potato_mine_sleep.png',
                          r'potato_mine_sleep.png'],500,pos,4,1.5,missles,seed,cost,
                         2,plant_id=11,traits=['little','root'])
    def update(self,screen,*args):
        super().update(screen,args)
        for zombie in get_value('zombies'):
            if self.rect.colliderect(zombie.rect) and zombie.lane==self.pos[1] and zombie.move_state=='ground':
                sounds.play('mine_explode',1)
                get_value('particles_-1').add(Spudow((self.x-150,self.y-150),50))
                for z in get_value('zombies'):
                    if z.lane==self.pos[1] and abs(z.x-self.x)<=100:
                        z.hp-=2000
                self.kill()
                self.on_destroy(self)
    def special(self):
        if super().special():
            if self.costume==0:
                self.costume=1
            else:
                self.costume=0
            self.paths[0]=f'potato_mine_{self.costume}.png'


class Catail(Plant):
    def __init__(self, pos=(0, 0), missles=pygame.sprite.Group(), seed=False, cost=0):
        self.xshift, self.yshift = -35, -45
        self.photo_size = (90, 75)
        self.degrade = 0
        self.eye = 0
        super().__init__(['catail_0_0.png',  'catail_0_1.png', 'catail_0_2.png', 'catail_0_3.png',  'catail_0_2.png', 'catail_0_1.png','catail_1_0.png', 'catail_1_1.png', 'catail_1_0.png', 'catail_1_1.png'],
                         200, pos, 6, 1, missles, seed, cost, 4,'catail_1_0.png',
                         costume_interval=0.45,sleep_image='cattail_sleep.png',
                         plant_id=12,traits=['revolution','flower'],trait_configs={'revolution':100})

    def special(self):
        if super().special():
            if self.revolution_timer>0:
                self.missles.add(CatMissle((self.x,self.y-30),(0,0),self,'homing'))
            #change eye
            rnd=random.randint(1,4)
            if self.effect['randomness']==-100:
                missle=random.choices(list(MISSLES_WITH_CHANCES.keys()),list(MISSLES_WITH_CHANCES.values()))[0]
                print(missle)
            else:
                if rnd==4:
                    missle=ElectricSting
                else:
                    missle=Sting
            self.missles.add(missle((self.x-10,self.y-30),(0,0),self,'homing'))
class IcebergLettuce(Plant):
    def __init__(self, pos=(0, 0), missles=pygame.sprite.Group(), seed=False, cost=0):
        self.xshift, self.yshift = -10, -20
        self.photo_size = (40, 40)
        self.degrade = 0
        self.eye = 0
        super().__init__(['iceberg_lettuce_0.png','iceberg_lettuce_1.png'],
                         1, pos, 6, 1, missles, seed, cost, 4,'ur a sussy baka',
                         costume_interval=2,sleep_image='iceberg_lettuce_sleep.png',
                         plant_id=13,traits=['little','vegetable'])
        self.shifts=False
    def update(self,screen,*args):
        super().update(screen,args)
        for zombie in get_value('zombies'):
            if self.rect.colliderect(zombie.rect) and zombie.lane==self.pos[1] and zombie.move_state=='ground':
                sounds.play('snowpea_hit',3)
                get_value('particles_-1').add(Chill((self.x-10,self.y-10)))
                for z in get_value('zombies'):
                    if z.lane==self.pos[1] and abs(z.x-self.x)<=50:
                        z.chilled=True
                        z.chills=True,1000
                        z.frozen=True
                        z.freezes=(True,250)
                self.kill()
                self.on_destroy(self)

class MiniPear(Plant):
    def __init__(self, pos=(0, 0), missles=pygame.sprite.Group(), seed=False, cost=0):
        self.xshift, self.yshift = -20, -30
        self.photo_size = (50, 50)
        super().__init__(['mini_pear_0.png','mini_pear_1.png','mini_pear_shoot.png','mini_pear_2.png'],
                         200, pos, 6, 0.01, missles, seed, cost, 4,
                         'mini_pear_2.png',costume_interval=0.4,
                         sleep_image='mini_pear_ugly.png',plant_id=14,traits=['fruit'],keep_attack=True)
    def special(self):
        if super().special():
            self.angle=[5,-1.25]
        #shoot a bunch of 3 seeds
            seeds=[]
            if self.effect['randomness']==-100:
                missle=random.choices(list(MISSLES_WITH_CHANCES.keys()),list(MISSLES_WITH_CHANCES.values()))[0]
            else:
                missle=Pear
            for a in range(4):
                yspeed=-4+2*a+random.randint(-1,1)
                xspeed=15-abs(yspeed)
                m=missle((self.x-10+xspeed,self.y-6+yspeed),self.x,self)
                m.velocity=(xspeed,yspeed)
                seeds.append(m)
            for seed in seeds:
                self.missles.add(seed)

class Peapod(Plant):
    def __init__(self, pos=(0, 0), missles=pygame.sprite.Group(), seed=False, cost=0,traits=['pea']):
        self.xshift, self.yshift = -24, -30
        super().__init__([r'pea_pod.png', r'pea_pod.png',r'pea_pod.png'],
                         600, pos, 4,4.5, get_value('missles'), seed, cost,
                         traits=['grow','pea'],plant_id=15)
        self.photo_size=self.images[0].get_width(),self.images[0].get_height()
        self.skills[self.grow]=['growth',15,650]
        self.pea_cnt=0
    def special(self):
        super().special()
    def grow(self):
        if self.pea_cnt==0:
            x,y=0,4
        elif self.pea_cnt==1:
            x,y=0,-8
        elif self.pea_cnt==2:
            x,y=0,-20
        elif self.pea_cnt==3:
            x,y=-15,0
        elif self.pea_cnt==4:
            x,y=15,0
        else:
            return
        get_value('particles_0').add(PeaOut((self.x+x,self.y+y),self,(x,y)))
        self.pea_cnt+=1
    def pea(self,av):
        if self.effect['randomness']==-100:
            missle=random.choices(list(MISSLES_WITH_CHANCES.keys()),list(MISSLES_WITH_CHANCES.values()))[0]
        else:
            missle=Pea
        self.missles.add(missle((av[5][0]-40+self.x,av[5][1]+self.y),av[5][0]+self.x,self))
class Firepea(Plant):
    def __init__(self,pos=(0,0),missles=pygame.sprite.Group(),seed=False,cost=0):
        super().__init__(['fire_leaves.png','fire_stem1.png','fire_head.png','fire_wink.png','fire_sleep.png','fire_stem2.png','fire_stem3.png'],200,pos,1,1.4,missles,seed,cost,plant_id=16,traits=['pea'])
    def special(self):
        if super().special():
            self.angle=[10,-1.25]
            if self.effect['randomness']==-100:
                missle=random.choices(list(MISSLES_WITH_CHANCES.keys()),list(MISSLES_WITH_CHANCES.values()))[0]
            else:
                missle=FirePea
            self.missles.add(missle((self.x-30,self.y-45),self.x+20,self))
class ShadowShroom(Plant):
    def __init__(self, pos=(0, 0), missles=pygame.sprite.Group(), seed=False, cost=0):
        self.xshift, self.yshift = -30, -25
        self.photo_size = (50, 45)
        self.degrade = 0
        self.eye = 0
        super().__init__(['shadow_shroom_0.png','shadow_shroom_1.png','shadow_shroom_2.png','shadow_shroom_3.png'],
                         150, pos, 6, 1, missles, seed, cost, 4,'ur a sussy baka',
                         costume_interval=1,sleep_image='shadow_shroom_sleep.png',
                         plant_id=16,traits=['little','shroom'])
    def on_destroy(self,enemy=None):
        super().on_destroy(enemy)
        try:
            if enemy:
                if self.hp<=0 and not self.sleeping:
                    enemy.toxic=True,1000
        except:
            pass
class Buzzzton(Plant):
    def __init__(self,pos=(0,0),missles=pygame.sprite.Group(),seed=False,cost=0):
        self.xshift, self.yshift =-30,-30
        self.photo_size=(60,60)
        super().__init__(['buzzzton.png','buzzzton.png','buzzzton_sleep.png'],
                         1,pos,4,15,missles,seed,cost,2,plant_id=18,traits=['flower'])
    def on_destroy(self,enemy=None):
        super().on_destroy(enemy)
        if not self.seed:
            set_value('shake',10)
        try:
            if enemy:
                enemy.effect['confusion']=350
                enemy.stop_timer+=10
                
                get_value('particles_-1').add(Zzz((self.x-40,self.y-40)))
                sounds.play('electric_hit',1)
                get_value('particles_1').add(Glitched((enemy.x-10,enemy.y-10),enemy))
                enemy.damage(20,'electric','homing',real=True)
                zap_num=2
            zombies=get_value('zombies').sprites()
            random.shuffle(zombies)
            for zombie in zombies:
                if zap_num>0:
                    get_value('particles_1').add(Glitched((zombie.x-10,zombie.y-10),zombie))
                    zombie.damage(20,'electric','homing',real=True)
                    zombie.effect['confusion']=350
                    zap_num-=1
                    
        except:
            pass
                
class Tallnut(Plant):
    def __init__(self,pos=(0,0),missles=pygame.sprite.Group(),seed=False,cost=0):
        self.xshift, self.yshift =-25,-75
        self.photo_size=(60,100)
        self.degrade=0
        self.eye=0
        super().__init__(['tallnut_0.png','tallnut_2.png','tallnut_sleep.png'],
                         8000,pos,4,15,missles,seed,cost,2,plant_id=19,traits=['revolution','nut'],trait_configs={'revolution':250})

    def update(self,screen,*args):
        super().update(screen,args)
        #degrade
        if self.hp<=2000:
            self.degrade=2
        elif self.hp<=4000:
            self.degrade=1
        else:
            self.degrade=0
        #change image
        if not self.sleeping:
            self.paths[0]=f'tallnut_{int(self.degrade)}.png'
        else:
            self.paths[0]=f'tallnut_0.png'
    def revolution_effect(self):
        super().revolution_effect()
        self.armor=self.old_plant.full_hp+2000

class Magnolia(Plant):
    def __init__(self, pos=(0, 0), missles=pygame.sprite.Group(), seed=False, cost=0):
        self.xshift, self.yshift = -25, -45
        self.photo_size = (60, 70)
        super().__init__(['mag_2.png',  'mag_0.png', 'mag_1.png', 'mag_0.png',  'mag_2.png', 'mag_3.png','mag_4.png'],
                         1000, pos, 6, 0.8, missles, seed, cost, 2,'mag_4.png',
                         costume_interval=0.9,sleep_image='mag_3.png',
                         plant_id=20,traits=['flower'])

    def special(self):
        if super().special():
            for plant in get_value('plants'):
                if plant.lane==self.lane or plant.column==self.column:
                    plant.armor+=125

class CherryBomb(Plant):
    def __init__(self, pos=(0, 0), missles=pygame.sprite.Group(), seed=False, cost=0):
        self.xshift, self.yshift = -35, -45
        self.photo_size = (70, 70)
        super().__init__(['cherry_0.png','cherry_1.png','cherry_2.png','nuthing.png'],
                        10000, pos, 6, 0.8, missles, seed, cost, 2,'nuthing.png',
                         costume_interval=0.5,sleep_image='cherry_sleep.png',
                         plant_id=21,traits=['revolution','fruit'],trait_configs={'revolution':250})
        self.time=0
        self.exploded=False
    def special(self):
        if not self.exploded and not self.seed:
            sounds.play('explode',1)
            set_value('shake',50)
            get_value('particles_-1').add(Cherry((self.x-150,self.y-150),50))
            for zombie in get_value('zombies'):
                if abs(zombie.lane-self.lane)<=1 and abs(zombie.column-self.column)<=1:
                    zombie.damage(2000-300*self.time,'fire','homing',True)
            if self.revolution_timer<=0:
                self.on_destroy(self)
                self.exploded=True
            else:
                self.time+=1
class FriedDuck(Plant):
    def __init__(self,pos=(0,0),missles=pygame.sprite.Group(),seed=False,cost=0):
        self.xshift, self.yshift =-45,-45
        self.photo_size=(90,90)
        super().__init__(['fried_duck_0.png','fried_duck_1.png'],
                         1000,pos,6,15,missles,seed,cost,2,'nuthing.png',
                         costume_interval=1,sleep_image='cattail_sleep.png',
                         plant_id=-1,traits=['powerup','awake'])
    def update(self,screen,*args):
        super().update(screen,args)
        for z in get_value('zombies'):
            if abs(z.lane-self.lane)<=1 and not z.lane==self.lane and z.column-self.column<3 and z.column-self.column>=0:
                z.switch_lane(self.lane,10)
    def on_destroy(self,enemy=None):
        super().on_destroy(enemy)
        if not self.seed:
            set_value('shake',25)
            sounds.play('explode',1)
            get_value('particles_-1').add(Hot((self.x-150,self.y-150),50))
            for zombie in get_value('zombies'):
                if abs(zombie.lane-self.lane)<=1 and abs(zombie.column-self.column)<=1:
                    zombie.damage(500,'fire','homing',True)
class Sweetpea(Plant):
    def __init__(self,pos=(0,0),missles=pygame.sprite.Group(),seed=False,cost=0):
        super().__init__(['leaves.png','stem1.png','sweet_pea.png','sweet_wink.png','sweet_sleep.png','stem2.png','stem3.png'],200,pos,1,2.3,missles,seed,cost,plant_id=22,traits=['pea'])
    def special(self):
        if super().special():
            self.angle=[10,-1.25]
            if self.effect['randomness']==-100:
                missle=random.choices(list(MISSLES_WITH_CHANCES.keys()),list(MISSLES_WITH_CHANCES.values()))[0]
            else:
                missle=random.choice([Sweet,Peppermint,Icymint])
            self.missles.add(missle((self.x-30,self.y-45),self.x+20,self))
class Torchwood(Plant):
    def __init__(self, pos=(0, 0), missles=pygame.sprite.Group(), seed=False, cost=0):
        self.xshift, self.yshift = -35, -65
        self.photo_size = (60, 90)
        super().__init__(['torch_0_0.png','torch_0_1.png','torch_0_2.png'],
                         750, pos, 6, 0.8, missles, seed, cost, 2,'mag_4.png',
                         costume_interval=1,sleep_image='torch_sleep.png',
                         plant_id=23,traits=['tree'])
        self.temperature=1000
        if self.sleeping:
            self.temperature=0
    def special(self):
        pass
        
    def update(self,screen,*args):
        super().update(screen,args)
        if not self.seed:
            if self.temperature<=0:
                self.paths=['torch_dim.png']
            else:
                if self.temperature<=3500:
                    self.paths=['torch_0_0.png','torch_0_1.png','torch_0_2.png']
                    self.atk_frame='torch_0_2.png'
                elif self.temperature<=5000:
                    self.paths=['torch_1_0.png','torch_1_1.png','torch_1_2.png']
                    self.atk_frame='torch_1_2.png'
                else:
                    self.paths=['torch_2_0.png','torch_2_1.png','torch_2_2.png']
                    self.atk_frame='torch_2_2.png'
            for missle in get_value('missles'):
                if self.rect.colliderect(missle.rect) and missle.side==1 and missle.torched==False and missle.kind=='straight' and ((not missle.limited) or missle.lane==self.lane):
                    if missle.element=='fire':
                        self.temperature+=100
                    elif missle.element=='ice':
                        self.temperature-=200
                    new_level=missle.level
                    if self.temperature>0 and self.temperature<=3500:
                        new_level=missle.level+1
                    elif self.temperature>0 and self.temperature<=5000:
                        new_level=missle.level+2
                    elif self.temperature>0:
                        new_level=missle.level+3
                    if new_level>len(missle.family)-1:
                        new_level=len(missle.family)-1
                    try:
                        missle_=missle.family[new_level]((missle.x,missle.y),0,self)    
                        missle_.torched=True
                        missle_.velocity=missle.velocity
                    except:
                        pass
                    try:
                        lane=get_value('lanes')
                        lane[self.lane-1]['zombies'].remove(missle)
                        set_value('lanes',lane)
                        missle.kill()
                    except:
                        missle.kill()
                        missle.image=get_value('images')['nuthing.png'][tuple()]
                    get_value('missles').add(missle_)
    def on_hit(self,enemy):
        super().on_hit(enemy)
        if enemy:
            if self.temperature>0:
                self.temperature-=40
                #burn enemy
                enemy.damage(20,'fire','homing')

#fireweed
class FireWeed(Plant):
    def __init__(self, pos=(0, 0), missles=pygame.sprite.Group(), seed=False, cost=0):
        self.xshift, self.yshift = -35, -45
        self.photo_size = (70, 70)
        super().__init__(['fireweed_0.png','fireweed_1.png','fireweed_2.png','nuthing.png'],
                        400, pos, 6, 2, missles, seed, cost, 2,'nuthing.png',
                         costume_interval=0.5,sleep_image='fireweed_sleep.png',
                         plant_id=24,traits=['flower'])
        self.exploded=False
    def special(self):
        if not self.exploded:
            sounds.play('explode',0.5)
            set_value('shake',10)
            self.exploded=True
            #summon 60 lava droplets
            
            if super().special():
                seeds=[]
                if self.effect['randomness']==-100:
                    missle=random.choices(list(MISSLES_WITH_CHANCES.keys()),list(MISSLES_WITH_CHANCES.values()))[0]
                else:
                    missle=LavaDrop
                for a in range(60):
                    yspeed=-5+a*0.25+random.choice([-1,1])*random.random()*0.1
                    xspeed=8+random.randint(0,5)
                    m=missle((self.x-10+xspeed,self.y-6+yspeed),self.x,self)
                    m.velocity=(xspeed,yspeed)
                    seeds.append(m)
                for seed in seeds:
                    self.missles.add(seed)
                self.kill()
class CoffeeBean(Plant):
    def __init__(self, pos=(0, 0), missles=pygame.sprite.Group(), seed=False, cost=0):
        self.xshift, self.yshift = -30, -60
        self.photo_size = (64, 32)
        super().__init__(['coffee_0.png','coffee_1.png','coffee_2.png','nuthing.png'],
                        1, pos, 6, 0.8, missles, seed, cost, 2,'nuthing.png',
                         costume_interval=0.5,sleep_image='coffee_1.png',
                         plant_id=25,traits=['non_graftable','floating','awake'])
        self.time=0
    def special(self):
        sounds.play('grow',1)
        for plant in get_plants_at(self.column,self.lane):
            for effect in plant.effect:
                plant.effect[effect]=-1
            plant.sleeping=False
            plant.effect['coffee']=250
        self.on_destroy(self)
class WWM(Plant):
    def __init__(self, pos=(0, 0), missles=pygame.sprite.Group(), seed=False, cost=0):
        self.xshift, self.yshift = -35, -45
        self.photo_size = (70, 70)
        self.cnt_=100
        self.zombies=[]
        super().__init__(['wwm.png','wwm_wink.png','wwm_sleep.png'],
                        1000, pos, 4, 2.1, missles, seed, cost, 1,'nuthing.png',
                         costume_interval=0.5,sleep_image='wwm_sleep.png',
                         plant_id=26,traits=['revolution','pea'],trait_configs={'revolution':250})
        self.time=0
        self.summon_id=1
        self.plants=[]
        for plants in get_value('plants'):
            if not plants is self and plants.column==self.column and plants.lane==self.lane:
                self.summon_id=plants.plant_id
    def special(self):
        if super().special():
            self.angle=[20,-1.25]
            if self.effect['randomness']==-100:
                missle=random.choices(list(MISSLES_WITH_CHANCES.keys()),list(MISSLES_WITH_CHANCES.values()))[0]
            else:
                missle=GiantPea
            self.missles.add(missle((self.x-120,self.y-38),self.x+0,self))
    def update(self,screen,events=None):
        if self.time==0 and not self.seed:
            self.time+=1
            
            for a in [[self.lane,self.column-1],[self.lane,self.column+1],[self.lane-1,self.column],[self.lane+1,self.column]]:
                if a[1]>0 and a[1]<10 and a[0]>0 and a[0]<=get_value('level').lane_num and len(get_plants_at(a[1],a[0]))==0:
                    self.plants.append(plant(a[1],a[0],get_value('plants'),PLANTS_WITH_ID[self.summon_id],get_value('missles'),get_value('particles_0'),0))
            if self.revolution_timer>0:
                for plants in self.plants:
                    plants.full_hp+=400
                    plants.hp+=400
        self.cnt_-=get_value('equivalent_frame')*self.atk_coefficient
        super().update(screen,events)
        if not self.seed:
            for plants in get_value('plants'):
                if abs(plants.lane-self.lane)<=1 and abs(plants.column-self.column)<=1:
                    if plants.hit_timer>0 and self.effect['coffee']<=80:
                        self.effect['coffee']+=20
                        for plants_ in self.plants:
                            plants_.effect['coffee']+=20
            if self.cnt_<=0:
                self.cnt_=200
                zombies=get_value('zombies').sprites()
                random.shuffle(zombies)
                for zombie in zombies:
                    if not zombie in self.zombies and zombie.x<=850:
                        get_value('particles_1').add(Report((zombie.x-10,zombie.y-10),zombie))
                        get_value('particles_-1').add(HYNDZ((self.x,self.y-60)))
                        self.zombies.append(zombie)
                        sounds.play('report',1)
                        zombie.damage(200,'physical','homing')
                        effect=random.choice(['freeze','chill','confusion','stun','overheat','spore'])
                        if effect=='freeze':
                            zombie.frozen=True
                            zombie.freezes=(True,9999999999)
                        if effect=='chill':
                            zombie.chilled=True
                            zombie.chills=(True,9999999999)
                        if effect=='stun':
                            zombie.stop_timer=999999999999
                        if effect=='confusion':
                            zombie.effect['confusion']=9999999999
                        if effect=='overheat':
                            zombie.effect['overheat']=9999999999999
                        if effect=='spore':
                            zombie.effect['fungus']=999999999999
                        break
    def on_destroy(self,enemy=None):
        super().on_destroy(enemy)
        if self.hp<=0:
            zombies.spawn_grave((self.column,self.lane),'wwm')
            plants=get_value('plants').sprites()
            random.shuffle(plants)
            cnt=3
            for plant in plants:
                cnt-=1
                if cnt>=0:
                    plant.effect['wwm']=75
    def revolution_effect(self):
        super().revolution_effect()
class Chomper(Plant):
    def __init__(self, pos=(0, 0), missles=pygame.sprite.Group(), seed=False, cost=0):
        self.xshift, self.yshift = -35, -35
        self.photo_size = (80, 80)
        self.cnt_=100
        self.plants=[]
        super().__init__(['chomper_1.png','chomper_0.png','chomper_1.png'],
                        100, pos, 4, 10, missles, seed, cost, 6,'nuthing.png',
                         costume_interval=1,sleep_image='wwm_sleep.png',
                     plant_id=27,traits=['non_graftable','can plant on','flower'],trait_configs={'can plant on':(0,-15)})
    def special(self):
        if super().special() and self.show:
            sounds.play('chomp',1)
            for plant_ in get_plants_at(self.column,self.lane):
                if not plant_ is self:
                    self.full_hp+=plant_.full_hp*0.75
                    self.heal(plant_.full_hp)
                    plant_.kill()
                    plant_.show=False
                    self.plants.append(plant_)
    def update(self,screen,events=None):
        super().update(screen,events)
        if self.show:
            for plant_ in self.plants:
                plant_.update(screen,events)

class LittleSprout(Plant):
    def __init__(self, pos=(0, 0), resources=pygame.sprite.Group(), seed=False, cost=0,traits=['graft on everything','everything graft on']):
        self.xshift, self.yshift = -15, -10
        super().__init__(['little_sprout.png', 'little_sprout.png','little_sprout.png'],
                         1, pos, 4, 18, resources, seed, cost, 2,
                         traits=['grow','short','little','graft on everything','everything graft on','revolution'],plant_id=28,
                         trait_configs={'revolution':250})
        self.photo_size=self.images[0].get_width(),self.images[0].get_height()
        self.skills[self.grow]=['growth',25*30,999999999999]
        self.shifts=False
        self.grown=False
        self.yes=False
        self.banned_combo=[Chomper]
    def special(self):
        if self.revolution_timer>0 and not self.growing:
            self.grow()
            self.yes=True
        if self.grown:
            fogs((self.x-50,self.y-10),25,8)
            self.on_destroy()
            self.kill()
            sounds.play('magical',1)
            p=plant(self.column,self.lane,get_value('plants'),PLANTS_WITH_ID[random.randint(1,len(PLANTS_WITH_ID.keys()))],get_value('missles'),get_value('particles_0'),0)
            if self.yes:
                p.full_hp+=1000
                p.hp+=1000
    def grow(self):
        self.growing=True
        sounds.play('grow',0.5)
        self.grown=False
    def next_costume(self):
        super().next_costume()
        if self.growing:
            self.photo_size = (
                    self.photo_size[0]+6, self.photo_size[1]+6)
            self.xshift-=3
            self.yshift-=6
            self.images = [pygame.transform.scale(get_value('images')[image][tuple()], self.photo_size) for image in self.paths]
            if self.photo_size[0]>=48 and self.photo_size[1]>=60:
                self.growing=False
                self.grown=True
    def graft_effect(self,target):
        try:
            target.grow()
        except:
            pass
        target.sleeping=False
        target.full_hp+=500
        target.hp+=500
class Plantern(Plant):
    def __init__(self,pos=(0,0),missles=pygame.sprite.Group(),seed=True,cost=0):
        self.xshift, self.yshift =-25,-40
        self.photo_size=(50,75)
        super().__init__(['plantern_0.png','plantern_1.png','plantern_sleep.png'],
                         1,pos,4,10,missles,seed,cost,2,plant_id=29,traits=['holy','tree'])
        self.hp=500
        self.full_hp=500
        self.light_zones=[]
        if not self.seed:
            sounds.play('plantern',100)
            for x in range(self.column-1,self.column+2):
                for y in range(self.lane-1,self.lane+2):
                    self.light_zones.append(['light',[x,y],99999,0])
                    get_value('tile_modifiers').append(['light',[x,y],99999,0])
        self.light_size=270
        self.delta_size=0.5
        self.light_angle=0
    def update(self,screen,events=None):
        super().update(screen,events)
        get_value('particles_-1').add(PlanternLight((self.x-135-(self.light_size-270),self.y-125-(self.light_size-270)),self.light_size,self.light_angle))
        if not self.seed:
            #self.light_size+=self.delta_size
            if abs(self.light_size-270)>=10:
                self.delta_size=-self.delta_size
            self.light_angle+=0.5
    def on_destroy(self,enemy=None):
        super().on_destroy(enemy)
        for light in self.light_zones:
            get_value('tile_modifiers').remove(light)
        if enemy:
            sounds.play('plantern_die',1)
            for x in range(11):
                for y in range(get_value('level').lane_num+1):
                    get_value('tile_modifiers').append(['light',[x,y],125,1])
            get_value('particles_-1').add(PlanternLight((self.x-135,self.y-125),1000,self.light_angle,duration=100))
            set_value('veil',[245, 212, 105,225,2])
            for zombie in get_value('zombies'):
                zombie.stop_timer+=150

class Powerflower(Plant):
    def __init__(self, pos=(0, 0), resources=pygame.sprite.Group(), seed=False, cost=0):
        super().__init__(['leaves.png', 'stem1.png',
                          r'powerflower_head.png', r'powerflower_shoot.png',
                          r'powerflower_sleep.png'], 300, pos, 2, 32, resources,
                         seed,cost,2,plant_id=30,traits=['revolution','holy','flower'],trait_configs={'revolution':100})
    
        self.sun_spawned=0
    def update(self,screen,events=None):
        super().update(screen,events)
        if self.revolution_timer>=0:
            self.costume_countdown+=0.1
            self.special_countdown+=0.1
    def revolution_effect(self):
        super().revolution_effect()
        get_value('missles').add(PowerflowerBeam((self.x-20,self.y-58),-9999,self))
        sounds.play('power_beam',0.1)
    def special(self):
        if super().special():
            sounds.play('powerflower_magic',0.1)
            self.missles.add(BigSun((self.x-30,self.y-48),(self.x+20,self.y+20)))
            for plant in get_plants_in(self.column-1,self.column+1,self.lane-1,self.lane+1):
                if not plant==self and plant.effect['powerflower']<=9*25:
                    plant.effect['powerflower']=13*25
                get_value('particles_-1').add(PowerFume((plant.x-40,plant.y-60),plant))
    def hit(self):
        for plant in get_plants_in(self.column-1,self.column+1,self.lane-1,self.lane+1):
            if not plant==self:
                plant.effect['powerflower']+=15
                if self.sun_spawned<=40:
                    self.missles.add(SunPiece((plant.x-30,plant.y-48),(plant.x+20+random.randint(-5,5),plant.y+20+random.randint(-5,5))))
                    self.sun_spawned+=1
        
#animations
class Animation(pygame.sprite.Sprite):
    def __init__(self, images, pos, durations,up=False,mother=None,kind='plants',lane=1):
        super().__init__()
        self.images = [get_value('images')[image][tuple()] for image in images]
        self.pos = pos
        self.rect=self.images[0].get_rect()
        self.cnt, self.durations, self.pose = 0, durations, 0
        self.image = self.images[0]
        if mother:
            self.lane=mother.lane
            lane = get_value('lanes')
            for key in ['obstacles', 'plants', 'zombies']:
                if mother in lane[self.lane-1][key]:
                    l = lane[self.lane-1][key]
                    inde = l.index(mother)
                    if up:
                        inde += 1
                    l.insert(inde, self)
                    lane[self.lane-1][key] = l
                    break
            set_value('lanes',lane)
        else:

            self.lane = lane
            lane = get_value('lanes')
            l=lane[self.lane-1][kind]
            l.append(self)
            lane[self.lane-1][kind] = l
            set_value('lanes', lane)

    def update(self, screen):
        self.cnt += get_value('equivalent_frame')
        try:
            if self.cnt >= self.durations[self.pose]:
                self.cnt = 0
                self.pose += 1
                self.image = self.images[self.pose]
        except:
            self.on_end()
            self.kill()
    def display(self):
        screen=get_value('screen')
        blity(self.image, self.pos)

    def on_end(self):
        lane = get_value('lanes')
        for key in ['plants', 'obstacles', 'zombies']:
            if self in lane[self.lane-1][key]:
                lane[self.lane-1][key].remove(self)
                break
        set_value('lanes', lane)


class PuffshroomGrow(Animation):
    def __init__(self, pos,plant):
        super().__init__(['puffshroom_grow_0.png','puffshroom_grow_1.png',
        'puffshroom_grow_2.png'], pos, [10, 10, 10],lane=1)
        sounds.play('grow', 0.5)
        self.plant=plant
    def on_end(self):
        super().on_end()
        self.plant.shroom_number+=1
        self.plant.duration+=0.3


class PotatoUp(Animation):
    def __init__(self, pos,pos_):
        super().__init__(['rooted_mine.png', 'potato_finish_0.png',
                          'potato_finish_1.png'], pos, [10, 20, 20],lane=1)
        sounds.play('spawngrave', 0.5)
        self.pos_=pos_
    def on_end(self):
        super().on_end()
        get_value('plants').add(PotatoMine(self.pos_))
class Grafting(Animation):
    def __init__(self, pos,old_plant,new_plant,class_):
        super().__init__(['scissors_0.png', 'scissors_1.png'], pos, [20,20],lane=get_value('level').lane_num,up=True)
        sounds.play('scissors', 0.5)
        self.old=old_plant
        self.new=new_plant
        self.new.show=False
        self.class_=class_
        print(self.class_)
    def on_end(self):
        super().on_end()
        self.old.show=False
        self.old.kill()
        get_value('plants').remove(self.old)
        get_value('plants').add(self.new)
        self.new.show=True
        self.new.revolution_effect()
        if 'revolution' in self.new.traits:
            sounds.play('revolution',1)
        packet=find_packet(self.class_)
        packet.recharge_countdown=packet.recharge_countdown/2
        packet.highlight_timer=5

class PeaOut(Animation):
    def __init__(self,pos,mother,rel_pos):
        super().__init__(['smolpea_out.png'],pos,[20],lane=1)
        sounds.play('grow',0.5)
        self.mother=mother
        self.rel_pos=rel_pos
    def on_end(self):
        super().on_end()
        self.mother.additional_animations.append([['smolpea_head.png','smolpea_head.png','smolpea_head.png',
                                                   'smolpea_head.png','smolpea_head.png','smolpea_shoot.png'],1,'smolpea_shoot.png',self.mother.pea,1,self.rel_pos,20,10])
        #[[sprites_in_sequence],costume_num,special_frame_name,special,special_criteria,(x,y),start_costume_timer,end_costume_timer,name]
#functions
def plant(x,y,group,class_,group_,particles_,cost):
    c=class_((x,y),group_,seed=False)
    c.cost=cost
    c.old_plant=None
    group.add(c)
    particles_.add(UglyDirt((x*90-25, y*90+60),c))
    sounds.play('plant',0.5)
    set_value('newest_plant',c)
    return c
def graft(x,y,group,class_,group_,particles_,cost,old_plant):
    c=class_((x,y),group_,seed=False)
    c.cost=cost
    c.old_plant=old_plant
    if 'revolution' in c.traits:
        c.revolution_timer=c.trait_configs['revolution']
    particles_.add(Grafting((x*90+20, y*90+45),old_plant,c,class_))
    
def get_objects_at(x,y):
    objects=[]
    for plant in get_value('plants'):
        if (plant.x+25)//90==x and (plant.y-60)//90==y:
            objects.append(plant)
    for obstacle in get_value('obstacles'):
        if (obstacle.x+20)//90 == x and (obstacle.y-10)//90 == y:
            objects.append(obstacle)
    return objects


def get_plants_at(x, y,trait=None,exclude_trait=None,find_unselectable=True,effect=None):
    objects = []
    for plant in get_value('plants'):
        if (plant.x+25)//90 == x and (plant.y-60)//90 == y and (not plant.unselected or find_unselectable) and (trait in plant.traits or not trait) and (not exclude_trait in plant.traits or not exclude_trait) and (effect in plant.effect or not effect):
            objects.append(plant)
    return objects


def get_plants_in(xstart, xend, ystart, yend,trait=None,exclude_trait=None,find_unselectable=True,effect=None):
    xs = [x+1 for x in range(int(xstart-1), int(xend))]
    ys = [y+1 for y in range(int(ystart-1), int(yend))]
    objects = []
    for x in xs:
        for y in ys:
            objects.extend(get_plants_at(x, y,trait,exclude_trait,find_unselectable,effect))
    return objects
def get_a_plant_in(xstart,xend,ystart,yend,plant_id):
    xs = [x+1 for x in range(int(xstart-1), int(xend))]
    ys = [y+1 for y in range(int(ystart-1), int(yend))]
    objects = []
    for x in xs:
        for y in ys:
            for plant in get_plants_at(x,y):
                if plant.plant_id==plant_id:
                    objects.append(plant)
    return objects
    
def get_obstacles_at(x, y):
    objects = []
    for plant in get_value('obstacles'):
        if (plant.x+20)//90 == x and (plant.y-10)//90 == y:
            objects.append(plant)
    return objects


def get_obstacles_in(xstart, xend, ystart, yend):
    xs = [x+1 for x in range(xstart-1, xend)]
    ys = [y+1 for y in range(ystart-1, yend)]
    objects = []
    for x in xs:
        for y in ys:
            objects.extend(get_obstacles_at(x, y))
    return objects
def get_zombies_at(x, y):
    objects = []
    for plant in get_value('zombies'):
        if (plant.x+20)//90 == x and plant.lane == y+1 and not plant.unselected:
            objects.append(plant)
    return objects


def get_zombies_in(xstart, xend, ystart, yend):
    xs = [x for x in range(xstart-1, xend)]
    ys = [y for y in range(ystart-1, yend)]
    objects = []
    for x in xs:
        for y in ys:
            objects.extend(get_zombies_at(x, y))
    return objects
def find_packet(plant_class):

    for packet in get_value('seed_packets'):
        try:
            plant1=packet.plant_id
            plant2=plant_class()
            plant2.show=False
            if plant1==plant2.plant_id:
                return packet
            #plant1.on_destroy(None)
            plant2.on_destroy(None)
        except:
            return None
    return None
def find_plant_class(plant):

    for packet in PLANTS_WITH_ID:
        plant2=PLANTS_WITH_ID[packet]()
        plant2.show=False
        if type(plant)==type(plant2):
            return PLANTS_WITH_ID[packet]
        plant2.on_destroy(None)
    return None
#constants
PLANTS_WITH_ID={1:Peashooter,2:Sunflower,3:Repeater,4:SnowPea,5:Puffshroom,6:Sunshroom,7:Fumeshroom,
                8:MilkPea,9:GatlingPea,10:Wallnut,11:RootedMine,12:Catail,13:IcebergLettuce,14:MiniPear,
                15:Peapod,16:Firepea,17:ShadowShroom,18:Buzzzton,19:Tallnut,20:Magnolia,21:CherryBomb,22:Sweetpea,
                23:Torchwood,24:FireWeed,25:CoffeeBean,26:WWM,27:Chomper,28:LittleSprout,29:Plantern,30:Powerflower}

import zombies
