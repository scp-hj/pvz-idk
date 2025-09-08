
import system
import pygame,sys,os
from missles import *
import copy
from plants import *
from time import *
from resources import *
from system import *
from config import *
from particles import *
import sounds,random
from filter import *
from PIL import Image
import cv2 as cv
import numpy
def cv2_2_pillow(img: numpy.ndarray) -> Image:
    # return Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    return Image.fromarray(img)


def pillow_2_cv2(img: Image) -> numpy.ndarray:
    # return cv2.cvtColor(numpy.array(img), cv2.COLOR_RGB2BGR)
    i=numpy.array(img)
    red = i[:,:,0].copy(); i[:,:,0] = i[:,:,2].copy(); i[:,:,2] = red;
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
def rp(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def rotate(surface, angle, pivot, offset):
    """Rotate the surface around the pivot point.

    Args:
        surface (pygame.Surface): The surface that is to be rotated.
        angle (float): Rotate by this angle.
        pivot (tuple, list, pygame.math.Vector2): The pivot point.
        offset (pygame.math.Vector2): This vector is added to the pivot.
    """
    rotated_image = pygame.transform.rotozoom(surface, -angle, 1)  # Rotate the image.
    rotated_offset = offset.rotate(angle)  # Rotate the offset vector.
    # Add the offset vector to the center/pivot point to shift the rect.
    rect = rotated_image.get_rect(center=pivot+rotated_offset)
    return rotated_image, rect  # Return the rotated image and shifted rect.


class Grave(pygame.sprite.Sprite):
    def __init__(self,pos=(0,0),id_=1):
        super().__init__()
        self.x = pos[0]*90-20
        self.y = pos[1]*90+10
        self.lane=pos[1]
        self.column=pos[0]
        self.location=pos
        self.id_=id_
        self.full_hp=3000
        self.hp=self.full_hp
        if self.id_=='wwm':
            self.id_=5
            self.hp=300
        
        if get_value('state')!='loading':    
            lanes=get_value('lanes')
            lane=lanes[pos[1]-1]['obstacles']
            lane.append(self)
            lanes[pos[1]-1]['obstacles']=lane
            #set_value('lanes',lane)
        paths = [('grave_'+str(self.id_)+'_1.png'),
                 ('grave_'+str(self.id_)+'_2.png')]
        self.images = [get_value('images')[path][tuple()] for path in paths]
        self.hit_images=[get_value('images')[path][('hit',)] for path in paths]
        self.mask = pygame.mask.from_surface(self.images[0])
        self.rect = self.images[0].get_rect()
        self.image=self.images[0]
        self.hit_timer=-1
        self.fumes=[]
        self.milked=0
        #eradicate plants!!!
        eradicate_plants=get_plants_at(pos[0],pos[1])
        for plant in eradicate_plants:
            plant.hp=-1
            plant.on_hit(None)
    def update(self,screen):
        self.rect = pygame.Rect(
            self.x, self.y, self.image.get_width(), self.image.get_height())
        self.hit_timer-=1
        if self.hit_timer<0:
            if self.hp<self.full_hp//2:
                self.image=self.images[1]
            else:
                self.image=self.images[0]
        else:
            if self.hp < self.full_hp//2:
                self.image = self.hit_images[1]
            else:
                self.image = self.hit_images[0]
        if self.hp <= 0 or self.milked>=10:
            self.on_destroy()
    def display(self):
        blity(self.image, (self.x, self.y))

    def on_destroy(self):
        grave_ratio = get_value('grave_spots')
        grave_ratio.append(((self.x+20)//90,(self.y-10)//90))
        set_value('grave_spots',grave_ratio)
        get_value('particles_1').add(GraveDirt((self.x, self.y),self))
        sounds.play('grave_die', 1)
        if self.id_==4:
            get_value('resources').add(Sun((self.x,self.y),(self.x-40,self.y+10)))
            get_value('resources').add(
                Sun((self.x, self.y), (self.x+40, self.y+10)))
        if self.id_==5:
            get_value('zombies').add(ZOMBIE_CLASSES[random.choice(SPECIAL_ZOMBIES[get_value('level').scene])]((self.column*90, self.lane
                                                 * 90)))
        self.kill()        
        lane=get_value('lanes')
        lane[self.lane-1]['obstacles'].remove(self)
        set_value('lanes',lane)
class Cone(pygame.sprite.Sprite):
    def __init__(self,pos=(0,0)):
        super().__init__()
        self.x = pos[0]
        self.y = pos[1]
        self.lane=(pos[1]+20)//90
        self.column=(pos[0]-10)//90
        self.location=pos
        self.full_hp=650
        self.hp=self.full_hp     
        
        if get_value('state')!='loading':    
            lanes=get_value('lanes')
            lane=lanes[int(self.lane-1)]['obstacles']
            lane.append(self)
            lanes[int(self.lane-1)]['obstacles']=lane
            #set_value('lanes',lane)
        paths = [('roadcone_1.png'),
                 ('roadcone_2.png')]
        self.images = [pygame.transform.scale(get_value('images')[path][tuple()],(60,60)) for path in paths]
        self.hit_images=[pygame.transform.scale(get_value('images')[path][('hit',)],(60,60)) for path in paths]
        self.mask = pygame.mask.from_surface(self.images[0])
        self.rect = self.images[0].get_rect()
        self.image=self.images[0]
        self.hit_timer=-1
        self.fumes=[]
        self.milked=0
        self.up_timer=750
    def update(self,screen):
        self.up_timer-=1
        if self.up_timer<=0:
            get_value('zombies').add(ConeheadZombie((self.x, 90+(self.lane-1)*90)))
            self.on_destroy()
        self.rect = pygame.Rect(
            self.x, self.y, self.image.get_width(), self.image.get_height())
        self.hit_timer-=1
        if self.hit_timer<0:
            if self.hp<self.full_hp//2:
                self.image=self.images[1]
            else:
                self.image=self.images[0]
        else:
            if self.hp < self.full_hp//2:
                self.image = self.hit_images[1]
            else:
                self.image = self.hit_images[0]
        if self.hp <= 0 or self.milked>=10:
            self.on_destroy()
    def display(self):
        blity(self.image, (self.x, self.y))

    def on_destroy(self):
        sounds.play('grave_die', 1)
        self.kill()        
        lane=get_value('lanes')
        lane[int(self.lane-1)]['obstacles'].remove(self)
        set_value('lanes',lane)
#zombies
class Zombie(pygame.sprite.Sprite):
    def __init__(self, pos=(0, 0), full_hp=200, speed=0.6, images=['idk.png'], atk=40, atk_duration=15,resistents={'physical':1.0,'ice':1.0,'poison':1.0,'electric':1.0,'fire':1.0,'holy':1.0},can_eat=True,preview=False,skills=dict()):
        super().__init__()
        self.x,self.y=pos
        self.full_hp = full_hp
        self.hp = self.full_hp
        #self.images = [loady(rp(image)) for image in images]
        self.filter_index=0
        self.render_index=0
        self.paused=False
        self.render_flag=1
        self.preview=preview
        self.paths=images
        self.images=[get_value('images')[path][tuple()] for path in images]
        self.groan='groan_'+str(random.randint(0,7))+'.ogg'
        self.setup_rect()
        self.hit_timer = -1
        self.fumes = []
        self.traits=[]
        self.special_timer=-1
        self.special_recharge=0
        self.milked = 0
        self.destination=1
        self.switching=False
        self.switch_speed=0
        self.milks=False
        self.speed_coefficient=1
        self.atk_coefficient=1
        self.animation_coefficient=1
        self.speed=speed
        self.chilled=False
        self.chills=False,0
        self.chill_timer=0
        self.toxin=False
        self.toxic=False,0
        self.toxin_timer=0
        self.stop_timer=0
        self.effects=''
        self.effect={'confusion':-1,'overheat':-1,'fungus':-1,
                     'unselectable':-1,'haste':-1,'phantom':-1,'invincible':-1}
        #confusion: walk backwards, stun & dmg, spreads
        #overheat: speed up, high rate dmg
        #fungus: random speed (overall slower) spawns puffshroom when dead
        #unselectable: are not target by plants and not be hit by missiles
        #haste: ignores plants
        #phantom: does not trigger & get hurt by mower
        self.dont_move=False
        self.dont_eat=False
        self.moving=True
        self.eating=False
        self.atk=atk
        self.armors=[]
        self.insta_kill=False
        self.effects=[]
        self.move_state='ground'
        self.atk_duration=atk_duration
        self.atk_timer=atk_duration*0.5
        self.can_eat=can_eat
        self.resistents=resistents
        self.last_effects=['offfffff']
        self.reduce_dmg=0
        self.og_speed=speed
        self.og_atk=atk
        self.frozen=False
        self.freezes=False,0
        self.unselected=False
        self.particles=[]
        self.lane=(pos[1]-90)//90+1
        self.column=(pos[0])//90
        self.idk=False
        self.hover_time=0
        self.lore=False
        self.skills=dict()#{func_name:[current_timer,max_timer]}
    def render(self):
        self.renders[self.filters[self.filter_index]].append(cv2_2_pygame(
            pillow_pvz_filter(self.paths[self.render_index], self.filters[self.filter_index])))
        self.render_index+=1
        if self.render_index>=len(self.paths):
            self.filter_index+=1
            self.render_index=0

    def update(self, screen):
        if not self.idk:
            if get_value('state')!='loading' and self.preview==False:
                lanes=get_value('lanes')
                try:
                    lane=lanes[self.lane-1]['zombies']
                except:
                    get_value('zombies').remove(self)
                    return
                lane.append(self)
                lanes[self.lane-1]['zombies']=lane
                set_value('lanes',lanes)
            self.idk=True

        self.reduce_dmg=0
        self.column=int((self.x-50)//90)+1
        if self.switching and not self.preview:
            lane=get_value('lanes')
            lane[self.lane-1]['zombies'].remove(self)
            set_value('lanes',lane)
            self.lane=int(self.y//90)
            des_y=(self.destination)*90
            if abs(self.y-des_y)<=self.speed:
                self.y=des_y
                self.switching=False
                self.lane=(des_y-90)//90+1
            if self.y>des_y:
                self.y-=self.speed
            elif self.y<des_y:
                self.y+=self.speed
            lane=get_value('lanes')
            lane[self.lane-1]['zombies'].append(self)
            set_value('lanes',lane)
        #description box
        if self.preview and not self.paused:
            if self.rect.collidepoint((get_pos()[0]-get_value('pos_shift')[0],get_pos()[1])):
                if self.hover_time<10:
                    self.hover_time+=1
                if self.hover_time>=5:
                    if not self.lore:
                        get_value('uber_uis').add(system.ShortZombieLore(self))
                        self.lore=True
            else:
                if self.hover_time>0:
                    self.hover_time-=1
                if self.hover_time<=0:
                    self.lore=False
            
        #effects
        if self.preview:
            self.dont_eat=True
        for effect in self.effect:
            if self.effect[effect]>=0:
                self.effect[effect]=self.effect[effect]-get_value('equivalent_frame')
        self.speed=self.og_speed
        self.atk=self.og_atk
        self.speed_coefficient=1
        self.atk_coefficient=1
        self.animation_coefficient=1
        for special in get_value('specials'):
            if special=='flag_shield':
                self.reduce_dmg += get_value('difficulty')*3
            if special == 'flag_turbo':
                self.speed=self.og_speed*(1+get_value('difficulty')*0.3)
            if special=='flag_aggro':
                self.atk = self.og_atk*(1+get_value('difficulty')*0.5)
            if special=='flag_deadly':
                self.atk =9999999999
        if self.effect['overheat']>=0:
            self.speed_coefficient*=1.5
            self.animation_coefficient*=1.5
            self.atk_coefficient*=4
            if int(self.effect['overheat'])%5==0:
                self.damage(10,'fire','homing')
            for armor in self.armors:
                armor.flexibility=0
        if self.effect['fungus']>=0:
            self.speed_coefficient*=random.random()*1.3
            self.animation_coefficient*=random.random()
        if self.effect['unselectable']>=0:
            self.unselected=True
            for tile in get_value('tile_modifiers'):
                if list(tile[1])==[self.column,self.lane] and tile[0]=='light':
                    self.unselected=False
        else:
            self.unselected=False
        if self.effect['confusion']>=0:
            self.speed_coefficient*=0.55
            self.can_eat=False
            get_value('particles_1').add(Confusion((self.x+20,self.rect[1]+self.rect[3]-self.height-10-15),self))
            if abs(self.effect['confusion']-300)<=get_value('equivalent_frame')*0.5 or abs(self.effect['confusion']-200)<=get_value('equivalent_frame')*0.5 or abs(self.effect['confusion']-100)<=get_value('equivalent_frame')*0.5 or abs(self.effect['confusion']-0)<=get_value('equivalent_frame')*0.5:
                self.damage(10,'electric','homing',real=True)
                get_value('particles_1').add(Glitched((self.x-10,self.rect[1]+self.rect[3]-self.height-10-15+20),self))
                self.stop_timer+=10
                sounds.play('electric_hit',1)
                possible_victims=[]
                for zombie in get_value('zombies'):
                    if zombie!=self and zombie.effect['confusion']<75 and zombie.x<880:
                        possible_victims.append(zombie)
                if len(possible_victims)>=1 and random.randint(1,3)<2:
                    zombie=random.choice(possible_victims)
                    zombie.stop_timer+=10
                    zombie.effect['confusion']=225
                    zombie.damage(15,'electric','homing',real=True)
                    get_value('particles_1').add(Glitched((zombie.x-10,self.rect[1]+self.rect[3]-self.height-10-15+20),zombie))
        if self.milks:
            self.speed_coefficient+=0.6*self.milked
            self.atk_coefficient+=0.4*self.milked
            self.animation_coefficient+=0.6*self.milked
            self.milks=False
        if self.milked>0:

            self.speed_coefficient += abs(0.5*self.milked)
            self.atk_coefficient += abs(0.5*self.milked)
            self.animation_coefficient += abs(0.5*self.milked)

        if self.toxic[0]:
            self.toxin_timer = self.toxic[1]
            self.toxin = True
            self.toxic = False, 0
        if self.toxin:
            if self.toxin_timer%40==0:
                self.damage(20,'poison','homing',True)
        if self.toxin_timer == 0 and self.toxin:
            self.toxin = False
        if self.toxin_timer > 0:
            self.toxin_timer -= 1
            self.speed_coefficient*=0.8
        if self.chills[0]:
            self.speed_coefficient *= 0.5
            self.atk_coefficient *= 0.5
            self.animation_coefficient *= 0.5
            self.chill_timer=self.chills[1]
            self.chilled=True
            self.chills=False,0
        if self.chilled:
            self.speed_coefficient*=0.5
            self.atk_coefficient*=0.5
            self.animation_coefficient*=0.5
        if self.chill_timer==0 and self.chilled:
            self.chilled=False
        if self.chill_timer>0:
            self.chill_timer-=1
        if self.freezes[0]:
            self.stop_timer+=self.freezes[1]
            frozen=Frozen((self.x,self.y+80),self.freezes[1],self)
            self.particles.append(frozen)
            get_value('particles_0').add(frozen)
            self.freezes=False,0
            self.frozen=True
        if self.stop_timer<=0 and self.frozen:
            self.frozen=False
        if self.stop_timer<=0:
            self.stop_timer=0
            if self.moving and not self.preview and not self.dont_move:
                self.move()
        else:
            self.stop_timer-=get_value('equivalent_frame')
            self.speed=0
        #special
        if self.special_timer>=0 and self.stop_timer<=0 and not self.eating and self.special_criteria() and not self.preview:
            self.special_timer-=get_value('equivalent_frame')*self.atk_coefficient
            if self.special_timer<=0:
                self.special()
                self.special_timer=self.special_recharge
        self.effects=[]
        if self.hit_timer == 1:
            self.effects.append('hit')
        if self.milked > 0:
            self.effects.append('milk')
        if self.chilled:
            self.effects.append('freeze')
        if self.unselected:
            self.effects.append('transparent')
        if self.hp>0:
            if self.toxin:
                get_value('particles_0').add(
                        Intoxicated((self.x, self.rect[1]+self.rect[3]-self.height-10-15), self))
            if self.effect['overheat']>0:
                get_value('particles_0').add(
                        Overheat((self.x, self.rect[1]+self.rect[3]-self.height-10-15), self))
            if self.effect['fungus']>0:
                get_value('particles_0').add(
                        Fungus((self.x, self.rect[1]+self.rect[3]-self.height-10-15), self))
        for armor in self.armors:
            armor.update()
        #recharge skills
        if self.can_eat:
            for skill in self.skills:
                self.skills[skill][0]-=get_value('equivalent_frame')
                if self.skills[skill][0]<=0:
                    skill()
                    self.skills[skill][0]=self.skills[skill][1]
        #change images
        if self.last_effects!=self.effects:
            self.images=[get_value('images')[path][tuple(self.effects)] for path in self.paths]
        self.last_effects=self.effects
        if self.stop_timer!=0 or self.dont_eat:
            self.can_eat=False
        else:
            self.can_eat=True
        self.hit_timer -= 1
        if self.hp <= 0 or self.milked >= 5:
            self.on_death(screen)
        if random.randint(0,4000)==53:
            sounds.play(self.groan,1)
        #eat plants
        if self.can_eat and self.effect['haste']<=0 and not self.preview and not self.switching:
            for plant in get_value('plants'):
                try:
                    _=plant.rect
                except:
                    break
                if pygame.Rect.colliderect(self.rect,plant.rect) and not plant.unselected and plant.lane==self.lane and not 'short' in plant.traits:
                    if self.insta_kill:
                        plant.hp=-9999999
                        plant.on_destroy(self)
                        self.insta_kills(plant)
                    else:
                        self.moving=False
                        self.eating=True
                        self.speed=0
                        self.atk_timer-=get_value('equivalent_frame')
                        if self.atk_timer<=0:
                            if plant.hp>=self.atk*self.atk_coefficient:
                                sounds.play('chomp_'+str(random.randint(0,3))+'.ogg',0.5)
                            else:
                                sounds.play(
                                    'chomp_finish', 0.5)
                            self.atk_timer = self.atk_duration-random.random()*5
                            plant.damage(self.atk*self.atk_coefficient,self)
                    break
                self.moving=True
                self.eating=False
        if not get_value('plants') or self.effect['haste']>0:
            self.moving=True
            self.eating = False
        if self.hp>0:
            for special in get_value('specials'):
                if special == 'flag_shield':
                    get_value('particles_0').add(
                        FlagShield((self.x, self.rect[1]+self.rect[3]-self.height-10-15), self))
                if special == 'flag_turbo':
                    get_value('particles_0').add(
                        FlagTurbo((self.x, self.rect[1]+self.rect[3]-self.height-10-15), self))
                if special == 'flag_aggro':
                    get_value('particles_0').add(
                        FlagAggro((self.x, self.rect[1]+self.rect[3]-self.height-10-15), self))
                if special == 'flag_deadly':
                    get_value('particles_0').add(
                        FlagDeadly((self.x, self.rect[1]+self.rect[3]-self.height-10-15), self))
        if self.preview:
            self.display()
    def display(self):
        pass
    def insta_kills(self,plant):
        pass
    def move(self):
        if not self.dont_move:
            if self.effect['confusion']>=0:
                if self.x<=850:
                    self.x+=self.speed*self.speed_coefficient*get_value('equivalent_frame')
            else:
                self.x-=self.speed*self.speed_coefficient*get_value('equivalent_frame')
            
    def damage(self,dmg,dmg_type,missle_kind,real=False):
        if self.effect['invincible']>0:
            return
        actual_dmg = dmg*self.resistents[dmg_type]-self.reduce_dmg
        if actual_dmg<=0:
            actual_dmg=0
        if real:
            self.hp-=actual_dmg
            self.hit_timer=2
            return
        #melting
        if dmg_type=='fire':
            if self.frozen:
                self.frozen=False
                self.chilled=False
                self.hp-=60
                self.stop_timer=0
            elif self.chilled:
                self.chilled=False
                self.hp-=30
        if dmg_type=='ice':
            if self.effect['overheat']>0:
                self.effect['overheat']=-1
                self.hp-=30
        if self.armors:
            st=False
            for armor in self.armors:
                if armor.kind=='horizontal' and not armor.accessory:
                    st=True
                    if missle_kind=='straight':
                        armor.damage(actual_dmg,dmg_type,missle_kind)
                        return
                    break
            if st:
                for armor in self.armors:
                    if not armor.kind=='horizontal' and not armor.flag and not armor.accessory:
                        armor.damage(actual_dmg,dmg_type,missle_kind)
                        return
                self.hp-=actual_dmg
                    
            else:
                for armor in self.armors:
                    if not armor.flag and not armor.accessory:
                        armor.damage(actual_dmg,dmg_type,missle_kind)
                        return
                self.hp-=actual_dmg
        else:
            self.hp-=actual_dmg
        self.hit_timer=2
        self.on_hit()
    def setup_rect(self):
        pass
    def on_hit(self):
        pass
    def special(self):
        pass
    def blit(self):
        for armor in reversed(self.armors):
            armor.display()#add at the end of display func
        for particle in self.particles:
            blity(particle.image,particle.pos)
    def on_death(self,screen):
        self.skills=dict()
        if not self.preview:
            if random.randint(1,20)==1:
                get_value('resources').add(Coin((self.x+20,self.y+40),(self.x+1,self.y+61),1))
            elif random.randint(1,40)==1:
                get_value('resources').add(Coin((self.x+20,self.y+40),(self.x+1,self.y+61),4))
            elif random.randint(1,100)==1:
                get_value('resources').add(Coin((self.x+20,self.y+40),(self.x+1,self.y+61),10))
            elif random.randint(1,2000)==1:
                get_value('resources').add(Coin((self.x+20,self.y+40),(self.x+1,self.y+61),69))
            if self.effect['fungus']>0:
                if not get_objects_at(self.column,self.lane):
                    plant(self.column,self.lane, get_value('plants'),
                                    Puffshroom, get_value('missles'), get_value('particles_1'),cost=0)
                    
        if not self.preview:
            for armor in self.armors:
                armor.on_break()
            lane=get_value('lanes')
            if self in lane[self.lane-1]['zombies']:
                lane[self.lane-1]['zombies'].remove(self)
            set_value('lanes',lane)
        self.kill()
        for particles in self.particles:
            particles.kill()
            particles.on_end()
    def heal(self,amount):
        if self.hp+amount>=self.full_hp:
            self.hp=self.full_hp
        else:
            self.hp+=amount
    def special_criteria(self):
        return True
    def switch_lane(self,destination,speed):
        if not self.switching:
            self.destination=destination
            if not self.destination>get_value('level').lane_num and not self.destination<=0:
                self.switching=True
                self.switch_speed=speed
class Ghost(Zombie):
    def __init__(self,pos=(0,0)):
        super().__init__(pos)
    def setup_rect(self):
        self.mask = pygame.mask.from_surface(self.images[0])
        self.rect = self.images[0].get_rect()
    def blit(self,screen,effects):
        self.rect=pygame.Rect(int(self.x),int(self.y),36,105)
        blity(self.images[0],(self.x-5,self.y-20))

    def on_death(self, screen):
        sounds.play('limbs_pop',3)
        self.kill()
        get_value('particles_0').add(TLZDie((self.x,self.y+60)))
#animation classes
class Basics(Zombie):
    def __init__(self, pos=(0,0),images=['zombie_head_1.png','zombie_head_2.png','zombie_body_0.png','zombie_body_1.png','zombie_hand_left.png','zombie_hand_right.png','zombie_leg_left.png','zombie_leg_right.png'],resistents={'physical':1.0,'ice':1.0,'poison':1.0,'electric':1.0,'fire':1.0,'holy':1.0},lift_left_hand=False):
        super().__init__(pos,images=images,resistents=resistents)
        self.lift_left_hand=lift_left_hand
        self.big_head=False
    def setup_rect(self):
        self.mask = pygame.mask.from_surface(self.images[0])
        self.rect = self.images[0].get_rect()
        #animation things
        self.left_leg_shift, self.right_leg_shift =-1,1
        self.left_hand_angle,self.right_hand_angle=20,10
        self.mouth_image_index=0
        self.mouth_countdown=10
        self.step_countdown = 10
        self.arm_fallen,self.arm_fall_hp=False,100
        self.left_hand_direction,self.right_hand_direction=1,0
        self.height=115
        self.force_left_hand=False
        self.left_hand_angle_=0
        self.death=ZombieDie
        self.yshift=random.randint(-10,10)
        self.step=1 #1:left down right up -1: left up right down
        self.step_countdown=random.randint(2,5)
        self.og_yshift=self.yshift
        self.angle=[0,0]
    def display(self):
        effects=self.effects
        #particles
        get_value('particles_1').add(Shadow((self.x+5,self.y+70+self.yshift),self))
        for armor in self.armors:
            armor.show=False
        self.rect = pygame.Rect(int(self.x), int(self.y), 36, 105)
        screen=pygame.Surface((36+15+10,105+28+10+10),pygame.SRCALPHA)
        #step
        if self.moving and self.stop_timer==0 and not self.dont_move:
            if abs(self.angle[0]-self.angle[1])<abs(self.angle[1]):
                self.angle=[0,0]
            self.angle[0]+=self.angle[1]
            #print(self.yshift)
            self.step_countdown -= self.animation_coefficient*0.2
            if self.step==1:
                self.left_leg_shift,self.right_leg_shift=5-self.step_countdown,self.step_countdown
                if self.left_leg_shift>2.5:
                    self.yshift-=self.animation_coefficient*0.2
                elif self.left_leg_shift<2.5:
                    self.yshift+=self.animation_coefficient*0.2
            else:
                self.left_leg_shift,self.right_leg_shift=self.step_countdown,5-self.step_countdown
                if self.right_leg_shift>2.5:
                    self.yshift-=self.animation_coefficient*0.2
                elif self.right_leg_shift<2.5:
                    self.yshift+=self.animation_coefficient*0.2
            if abs(self.yshift-self.og_yshift)>=2.5:
                if self.yshift>=self.og_yshift:
                    self.yshift=self.og_yshift+2.5
                else:
                    self.yshift=self.og_yshift-2.5
            if self.step_countdown<=0:
                self.step_countdown=5
                self.step=-self.step
        #eating
        if not self.eating or not self.can_eat:
            self.mouth_image_index=0
            self.left_hand_direction, self.right_hand_direction = -1, 0
            self.left_hand_angle,self.right_hand_angle=20,10
        else:
            self.mouth_countdown -= 1
            if self.mouth_countdown == 0:
                if self.mouth_image_index==0:
                    self.mouth_image_index=1
                else:
                    self.mouth_image_index=0
                self.mouth_countdown =int( 10/self.animation_coefficient)
            if self.left_hand_angle<=20:
                self.left_hand_direction=4
                if self.right_hand_angle!=10:
                    self.right_hand_direction=-4
            if self.left_hand_angle>=100:
                self.left_hand_direction=-4
                self.right_hand_direction=4
            if self.stop_timer==0:
                if self.animation_coefficient>1:
                    self.left_hand_angle+=self.left_hand_direction*round(self.animation_coefficient)
                    self.right_hand_angle+=self.right_hand_direction*round(self.animation_coefficient)
                else:
                    self.left_hand_angle += self.left_hand_direction * \
                        self.animation_coefficient
                    self.right_hand_angle += self.right_hand_direction * \
                        self.animation_coefficient
        #arm fall
        if self.hp<=self.full_hp//2:
            if not self.arm_fallen:
                sounds.play('limbs_pop', 3)
                get_value('particles_0').add(ObjectFall(
                    self,self.paths[5], (self.x+30, self.y+32), 15, self.effects,0.5,0.5,))
            self.arm_fallen=True
        #rotate hands
        rotated_left_hand,left_hand_rect = rotate(self.images[4], self.left_hand_angle,(15-3+12+10,28+18+10),pygame.math.Vector2((0,+18.5)))
        if self.lift_left_hand:
            rotated_left_hand, left_hand_rect = rotate(self.images[4], 60, (15-3+12+10, 28+18+10), pygame.math.Vector2((0, +18.5)))
        if self.force_left_hand:
            rotated_left_hand, left_hand_rect = rotate(self.images[4],self.left_hand_angle_, (15-3+12+10, 28+18+10), pygame.math.Vector2((0, +18.5)))
        rotated_right_hand, right_hand_rect = rotate(
            self.images[5], self.right_hand_angle, (15+13+8+10, 28+18+10), pygame.math.Vector2((0, +18.5)))
        #left hand
        screen.blit(rotated_left_hand, left_hand_rect)
        #left leg
        screen.blit(self.images[6],(15+4+10,28+53+10+self.left_leg_shift))
        #right leg
        screen.blit(self.images[7], (15+17+10, 28+53+10+self.right_leg_shift))
        #body
        if self.arm_fallen:    img=self.images[3]
        else:    img=self.images[2]
        screen.blit(img,(5+10,28+17+10))
        #head
        if self.big_head:
            screen.blit(self.images[self.mouth_image_index], (10, 10))
        else:
            screen.blit(self.images[self.mouth_image_index], (20, 20))
        #right hand
        if not self.arm_fallen:
            screen.blit(rotated_right_hand,right_hand_rect)
        #draw armor
        for armor in self.armors:
            try:
                _=armor.image
            except:
                continue
            screen.blit(armor.image,[armor.pos_shift[0]+15+10,armor.pos_shift[1]+38])
            
        screen=pygame.transform.rotate(screen,self.angle[0])
        pos=(self.x-20-math.tan(math.radians(self.angle[0]))*self.rect[2],self.y-38+self.yshift-math.tan(math.radians(self.angle[0]))*self.rect[3])
        blity(screen,pos)
        super().blit()
    def on_death(self, screen):
        if not self.preview:
            sounds.play('limbs_pop', 3)
            get_value('particles_0').add(ObjectFall(
                self,self.paths[0], (self.x-5, self.y-20), 15, self.effects, 0.5, 0.5))
            get_value('particles_0').add(self.death((self.x-5, self.y-20), self.effects,self))
        super().on_death(screen)
class Imps(Zombie):
    def __init__(self, pos=(0,0),images=['imp_head_1.png','imp_head_2.png','imp_body_0.png','imp_body_1.png','imp_hand.png','imp_hand.png','imp_leg.png','imp_leg.png'],resistents={'physical':1.0,'ice':1.0,'poison':1.0,'electric':1.0,'fire':1.0,'holy':1.0},lift_left_hand=False):
        super().__init__(pos,images=images,resistents=resistents)
        self.lift_left_hand=lift_left_hand
    def setup_rect(self):
        self.mask = pygame.mask.from_surface(self.images[0])
        self.rect = self.images[0].get_rect()
        #animation things
        self.left_leg_shift, self.right_leg_shift =-1,1
        self.left_hand_angle,self.right_hand_angle=20,10
        self.mouth_image_index=0
        self.mouth_countdown=10
        self.step_countdown = 10
        self.arm_fallen,self.arm_fall_hp=False,50
        self.left_hand_direction,self.right_hand_direction=1,0
        self.height=50
        self.death=ImpDie
    def display(self):
        screen=get_value('screen')
        effects=self.effects
        self.rect = pygame.Rect(int(self.x), int(self.y+60), 36, 105-70)
        #step
        if self.moving and self.stop_timer==0:
            self.step_countdown -= 1
            if self.step_countdown==0:
                self.left_leg_shift,self.right_leg_shift=self.right_leg_shift,self.left_leg_shift
                self.step_countdown=int(10/self.animation_coefficient)
        #eating
        if not self.eating or not self.can_eat:
            self.mouth_image_index=0
            self.left_hand_direction, self.right_hand_direction = -1, 0
            self.left_hand_angle,self.right_hand_angle=20,10
        else:
            self.mouth_countdown -= 1
            if self.mouth_countdown == 0:
                if self.mouth_image_index==0:
                    self.mouth_image_index=1
                else:
                    self.mouth_image_index=0
                self.mouth_countdown =int( 10/self.animation_coefficient)
            if self.left_hand_angle<=20:
                self.left_hand_direction=4
                if self.right_hand_angle!=10:
                    self.right_hand_direction=-4
            if self.left_hand_angle>=100:
                self.left_hand_direction=-4
                self.right_hand_direction=4
            if self.stop_timer==0:
                if self.animation_coefficient>1:
                    self.left_hand_angle+=self.left_hand_direction*round(self.animation_coefficient)
                    self.right_hand_angle+=self.right_hand_direction*round(self.animation_coefficient)
                else:
                    self.left_hand_angle += self.left_hand_direction * \
                        self.animation_coefficient
                    self.right_hand_angle += self.right_hand_direction * \
                        self.animation_coefficient
        #arm fall
        if self.hp<=self.full_hp//2:
            if not self.arm_fallen:
                sounds.play('limbs_pop', 3)
                get_value('particles_0').add(ObjectFall(
                    self,self.paths[5], (self.x+30, self.y+80), 15, self.effects,0.5,0.5,))
            self.arm_fallen=True
        #rotate hands
        rotated_left_hand,left_hand_rect = rotate(self.images[4], self.left_hand_angle,(self.x-3+25-5,self.y+68),pygame.math.Vector2((0,+10)))
        if self.lift_left_hand:
            rotated_left_hand, left_hand_rect = rotate(self.images[4], 60, (self.x-3+35-5, self.y+68), pygame.math.Vector2((0, +10)))
        rotated_right_hand, right_hand_rect = rotate(
            self.images[5], self.right_hand_angle, (self.x+25+8-5, self.y+68), pygame.math.Vector2((0, +10)))
        #left hand
        blity(rotated_left_hand, left_hand_rect)
        #left leg
        blity(self.images[6],(self.x+10,self.y+77+self.left_leg_shift))
        #right leg
        blity(self.images[7], (self.x+10+11, self.y+77+self.right_leg_shift))
        #body
        if self.arm_fallen:    img=self.images[3]
        else:    img=self.images[2]
        blity(img,(self.x+7,self.y+57+10+2))
        #head
        blity(self.images[self.mouth_image_index], (self.x+5, self.y+30+10+3))
        #right hand
        if not self.arm_fallen:
            blity(rotated_right_hand,right_hand_rect)

        super().blit()
    def on_death(self, screen):
        if not self.preview:
            sounds.play('limbs_pop', 3)
            get_value('particles_0').add(ObjectFall(
                self,self.paths[0], (self.x+5, self.y+30+11), 15, self.effects, 0.5, 0.5))
            get_value('particles_0').add(self.death((self.x+7, self.y+57+2), self.effects,self))
        super().on_death(screen)

class Running(Zombie):
    def __init__(self, pos=(0,0),images=['zombie_head_1.png','zombie_head_2.png','zombie_body_0.png','zombie_body_1.png','football_hand_left.png','football_hand_left.png','zombie_leg_left.png','zombie_leg_right.png'],resistents={'physical':1.0,'ice':1.0,'poison':1.0,'electric':1.0,'fire':1.0,'holy':1.0}):
        super().__init__(pos,images=images,resistents=resistents,can_eat=True)
        self.lane=(pos[1]-90)//90+1
        self.og_speed=1.7
        self.speed=1.7
        self.height=115
    def setup_rect(self):
        self.mask = pygame.mask.from_surface(self.images[0])
        self.rect = self.images[0].get_rect()
        #animation things
        self.left_leg_shift, self.right_leg_shift =-2,2
        self.left_hand_angle,self.right_hand_angle=20,10
        self.mouth_image_index=0
        self.mouth_countdown=10
        self.arm_fallen,self.arm_fall_hp=False,100
        self.left_hand_direction,self.right_hand_direction=1,0
        self.jump_height=2
        self.initial_y=self.y
        self.yspeed = -self.jump_height
        self.hand_ceiling=50
        self.left_hand_xshift,self.left_hand_yshift=0,0
        self.right_hand_xshift,self.right_hand_yshift=0,0
        self.death=FootballDie
    def display(self):
        screen=get_value('screen')
        effects=self.effects
        self.rect = pygame.Rect(int(self.x), int(self.y), 36, 105)
        #run
        if not get_value('paused'):
            if self.stop_timer==0:
                if self.moving:
                    self.y+=self.yspeed
                    self.yspeed+=0.25
                    if self.y>=self.initial_y:
                        self.yspeed=-self.jump_height                
                        self.left_leg_shift,self.right_leg_shift=self.right_leg_shift,self.left_leg_shift
                else:
                    if not self.y==self.initial_y:
                        self.y += self.yspeed
                        self.yspeed += 0.25
                        if abs(self.y-self.initial_y)<self.yspeed:
                            self.y=self.initial_y
                    else:
                        self.yspeed = -self.jump_height
        if self.switching:
            des_y=(self.destination)*90
            if self.y>des_y:
                self.initial_y-=self.speed
                
            elif self.y<des_y:
                self.initial_y+=self.speed
            if abs(self.initial_y-des_y)<=self.speed:
                self.initial_y=des_y
        #eating
        if not self.eating or not self.can_eat:
            self.mouth_image_index = 0
            self.left_hand_direction, self.right_hand_direction = -1, 0
            self.left_hand_angle, self.right_hand_angle = 20, 10
            self.left_hand_xshift,self.left_hand_yshift=0,0
            self.right_hand_xshift,self.right_hand_yshift=0,0
        else:
            self.mouth_countdown -= 1
            if self.mouth_countdown == 0:
                if self.mouth_image_index == 0:
                    self.mouth_image_index = 1
                else:
                    self.mouth_image_index = 0
                self.mouth_countdown = int(10/self.animation_coefficient)
            if self.left_hand_angle <= 20:
                self.left_hand_direction = 4
                if self.right_hand_angle != 10:
                    self.right_hand_direction = -4
            if self.left_hand_angle >= 100:
                self.left_hand_direction = -4
                self.right_hand_direction = 4
            if self.left_hand_direction==4:
                self.left_hand_yshift+=0.5*self.animation_coefficient
                self.left_hand_xshift+=1*self.animation_coefficient
            else:
                self.left_hand_xshift-=1*self.animation_coefficient
                self.left_hand_yshift -= 0.5*self.animation_coefficient

            if self.right_hand_direction == 4:
                self.right_hand_yshift +=0.1*self.animation_coefficient
                self.right_hand_xshift += 1*self.animation_coefficient
            elif self.right_hand_direction == -4:
                self.right_hand_xshift -= 1*self.animation_coefficient
                self.right_hand_yshift -= 0.1*self.animation_coefficient
            if self.stop_timer==0:
                if self.animation_coefficient > 1:
                    self.left_hand_angle += self.left_hand_direction * \
                        round(self.animation_coefficient)
                    self.right_hand_angle += self.right_hand_direction * \
                        round(self.animation_coefficient)
                else:
                    self.left_hand_angle += self.left_hand_direction * \
                        self.animation_coefficient
                    self.right_hand_angle += self.right_hand_direction * \
                        self.animation_coefficient
        #arm fall
        if self.hp<=self.full_hp//2:
            if not self.arm_fallen:
                sounds.play('limbs_pop', 3)
                get_value('particles_0').add(ObjectFall(
                    self,self.paths[5], (self.x+30, self.y+32), 15, self.effects,0.5,0.5))
            self.arm_fallen=True
        #rotate hands
        rotated_left_hand,left_hand_rect = rotate(self.images[4], self.left_hand_angle,(self.x+self.left_hand_xshift,self.y+15+self.left_hand_yshift),pygame.math.Vector2((0,+18.5)))
        rotated_right_hand, right_hand_rect = rotate(
            self.images[5], self.right_hand_angle, (self.x+13+8+self.right_hand_xshift, self.y+18+self.right_hand_yshift), pygame.math.Vector2((0, +18.5)))
        #left hand
        blity(rotated_left_hand, left_hand_rect)
        #left leg
        blity(self.images[6],(self.x+4,self.y+56+self.left_leg_shift))
        #right leg
        blity(self.images[7], (self.x+17, self.y+56+self.right_leg_shift))
        #body
        if self.arm_fallen:    img=self.images[3]
        else:    img=self.images[2]
        blity(img,(self.x-10,self.y+17))
        #head
        blity(self.images[self.mouth_image_index], (self.x-5, self.y-20))
                #right hand
        if not self.arm_fallen:
            blity(rotated_right_hand,right_hand_rect)
        super().blit()

    def on_death(self, screen):
        if not self.preview:
            sounds.play('limbs_pop', 3)
            get_value('particles_0').add(ObjectFall(
                self,self.paths[0], (self.x-5, self.y-20), 15, self.effects, 0.5, 0.5))
            get_value('particles_0').add(self.death((self.x-5, self.y-20), self.effects,self))
        super().on_death(screen)

class Bouncing(Zombie):
    def __init__(self, pos=(0,0),initial_jump_height=0 ,images=['pogo_zombie.png','pogo_zombie_rip.png','pogo_stick.png'], resistents={'physical': 1.0, 'ice': 1.0, 'poison': 1.0,'electric':1.1,'fire':1.0,'holy':1.0}):
        self.real_y=pos[1]
        self.jump_height=initial_jump_height
        super().__init__(pos, images=images, resistents=resistents)
        self.y=pos[1]
        self.og_speed=1.2
        self.lane = (pos[1]-90)//90+1
        self.can_eat=False
        self.height=100
    def update(self,screen):
        if self.freezes[0]:
            self.freezes=(False,0)
        super().update(screen)
    def setup_rect(self):
        self.mask = pygame.mask.from_surface(self.images[0])
        self.rect = self.images[0].get_rect()
        #animation things
        self.left_leg_shift, self.right_leg_shift = -1, 1
        self.left_hand_angle, self.right_hand_angle = 20, 10
        self.mouth_image_index = 0
        self.mouth_countdown = 10
        self.step_countdown = 10
        self.arm_fallen, self.arm_fall_hp = False, 100
        self.left_hand_direction, self.right_hand_direction = 1, 0
        self.yspeed=-self.jump_height
    def display(self):
        screen=get_value('screen')
        effects=self.effects
        self.rect = pygame.Rect(int(self.x), int(self.y), 40, 120-(self.y-self.real_y)-30)
        self.eating=False
        self.moving=True
        self.atk_timer=10000000000000
        #run
        if not get_value('paused'):
            if self.stop_timer==0:
                self.real_y+=self.yspeed
                self.yspeed+=1
            if self.yspeed==self.jump_height+1:
                self.yspeed=-self.jump_height
                self.move_state='ground'
                if self.stop_timer<=0:
                    sounds.play('pogo',0.5)
                    self.on_bounce()
            else:
                self.move_state='air'
        blity(self.images[0],(self.x,self.real_y))
        if self.switching:
            try:
                des_y=(self.destination)*90
                if self.y>des_y:
                    self.real_y-=self.speed
                    
                elif self.y<des_y:
                    self.real_y+=self.speed
                if abs(self.initial_y-des_y)<=self.speed:
                    self.initial_y=des_y
            except:
                pass
        super().blit()
    def on_death(self, screen):
        self.skills=dict()
        if not self.preview:
            sounds.play('pogo', 3)
            get_value('particles_0').add(ObjectFall(
                self,self.paths[2], (self.x-5, self.real_y+60), 18, self.effects, 0, 0,True,0,180,10))
            get_value('particles_0').add(ObjectFly(
                self,self.paths[1], (self.x-5, self.real_y+30), 100, self.effects, [10,-15], [0.25,0.5], True, 0, 180, 5))
        super().on_death(screen)
    def on_bounce(self):
        pass

class Levitating(Zombie):
    def __init__(self, pos=(0,0),images=['ghost_zombie.png'], resistents={'physical': 1.0, 'ice': 1.0, 'poison': 1.0,'electric':1.0,'fire':1.0,'holy':1.0}):
        self.real_y=pos[1]+15
        super().__init__(pos, images=images, resistents=resistents)
        self.y=pos[1]+15
        self.og_speed=1.2
        self.lane = (pos[1]-90)//90+1
        self.can_eat=False
        self.height=100
        self.yspeed=-5
        self.sincere=False
    def update(self,screen):
        if self.freezes[0]:
            self.freezes=(False,0)
        if self.stop_timer>0:
            self.stop_timer=0
        super().update(screen)
    def setup_rect(self):
        self.mask = pygame.mask.from_surface(self.images[0])
        self.rect = self.images[0].get_rect()
        #animation things
        self.left_leg_shift, self.right_leg_shift = -1, 1
        self.left_hand_angle, self.right_hand_angle = 20, 10
        self.mouth_image_index = 0
        self.mouth_countdown = 10
        self.step_countdown = 10
        self.arm_fallen, self.arm_fall_hp = False, 100
        self.left_hand_direction, self.right_hand_direction = 1, 0
        self.levitate_direction=0 #0: upwards 1: downwards
    def display(self):
        screen=get_value('screen')
        effects=self.effects
        self.rect = pygame.Rect(int(self.x), int(self.y), 40, 120-(self.y-self.real_y)-30)
        self.eating=False
        self.moving=True
        self.atk_timer=10000000000000
        self.move_state='air'
        if not get_value('paused') and not self.sincere:
            if self.stop_timer==0:
                self.real_y+=self.yspeed
                if self.levitate_direction==0:
                    self.yspeed+=0.5
                    if self.yspeed>=5:
                        self.levitate_direction=1
                else:
                    self.yspeed-=0.5
                    if self.yspeed<=-5:
                        self.levitate_direction=0
        blity(self.images[0],(self.x,self.real_y))
        if self.switching:
            self.switching=False
        super().blit()
    def on_death(self, screen):
        super().on_death(screen)
        get_value('particles_0').add(GhostDie((self.x-5, self.real_y), self.effects,self))
        
class BasicZombie(Basics):
    def __init__(self,pos=(0,0)):
        self.zombie_id=1
        super().__init__(pos)
        self.hp=200
        self.full_hp=200
        self.speed,self.og_speed=1.0,1.0
        self.atk,self.og_atk=40,40
class Imp(Imps):
    def __init__(self,pos=(0,0)):
        self.zombie_id=8
        super().__init__(pos)
        self.hp=160
        self.full_hp=160
        self.speed,self.og_speed=1.5,1.5
        self.atk,self.og_atk=40,40
class PaperImp(Imps):
    def __init__(self,pos=(0,0)):
        self.zombie_id=12
        super().__init__(pos)
        self.hp=120
        self.full_hp=120
        self.speed,self.og_speed=1.5,1.5
        self.atk,self.og_atk=40,40
        self.armors.append(PaperBox(self))
class DiscoZombie(Basics):
    def __init__(self,pos=(0,0)):
        self.zombie_id=13
        super().__init__(pos,images=['disco_head_1.png','disco_head_1.png','disco_body_0.png','disco_body_1.png','disco_hand_left.png','disco_hand_right.png','disco_leg_left.png','disco_leg_right.png'],resistents={'physical':1.0,'ice':1.0,'poison':1.0,'electric':1.0,'fire':1.0,'holy':1.0})
        self.hp=600
        self.full_hp=600
        self.speed,self.og_speed=2.5,2.5
        self.atk,self.og_atk=40,40
        self.death=NinjaImpDie
        self.special_timer=125
        self.death=DiscoDie
        self.special_recharge=225
        self.summoning=-1
        self.big_head=True
        self.specialed=False
        self.dancers={'up':None,'down':None,'left':None,'right':None}
    def special(self):
        get_value('particles_-1').add(Disco((self.x-240,self.y-240),75))
        sounds.play('disco',3)
        self.force_left_hand=True
        self.left_hand_angle=100
        fogs((self.x-50,self.y+20),25,8)
        self.og_speed,self.speed=0,0
        self.summoning=75
        self.specialed=True
        self.heal_=True
        for direction in self.dancers.keys():
            if not self.dancers[direction]:
                self.heal_=False
                if direction=='up':
                    if self.lane<=1:
                        continue
                    pos=(self.x,self.y-90)
                elif direction=='down':
                    if self.lane>=get_value('level').lane_num:
                        continue
                    pos=(self.x,self.y+90)
                elif direction=='left':
                    pos=(self.x-90,self.y)
                else:
                    pos=(self.x+90,self.y)
                dancer=DancerZombie(pos)
                dancer.direction=direction
                dancer.mother=self
                self.dancers[direction]=dancer
                get_value('zombies').add(dancer)
        if self.heal_:
            for zombie in get_value('zombies'):
                if abs(zombie.lane-self.lane)<=1 and abs(zombie.column-self.column)<=1:
                    zombie.heal(100)
                    get_value('particles_-1').add(Heal((zombie.x-30,zombie.y),25,zombie))
            sounds.play('grow',0.5)
    def update(self,screen):
        if self.specialed:
            self.og_speed=0.5
        for dancer in self.dancers:
            if self.dancers[dancer]:
                if self.dancers[dancer].speed<self.og_speed:
                    self.og_speed=self.dancers[dancer].speed
        if self.og_speed==0.5:    
            for dancer in self.dancers:
                if self.dancers[dancer]:
                    if self.dancers[dancer].speed>self.og_speed:
                        self.og_speed=self.dancers[dancer].speed
            
        if self.summoning>=0:
            self.summoning-=get_value('equivalent_frame')
            self.og_speed,self.speed=0,0
            self.force_left_hand=True
            self.left_hand_angle_=80
            if self.summoning<=0:
                self.left_hand_angle_=20
                self.force_left_hand=False
        super().update(screen)
        if self.can_eat and self.effect['haste']<=0 and not self.preview:
            for plant in get_value('plants'):
                try:
                    _=plant.rect
                except:
                    break
                if pygame.Rect.colliderect(self.rect,plant.rect) and plant.lane==self.lane and not plant.unselected:
                    if not self.specialed:
                        self.special()
                        self.special_timer=self.special_recharge
        for direction in self.dancers:
            if direction=='up':
                pos=(self.x,self.y-90)
            elif direction=='down':
                pos=(self.x,self.y+90)
            elif direction=='left':
                pos=(self.x-90,self.y)
            else:
                pos=(self.x+90,self.y)
            if self.dancers[direction]:
                self.dancers[direction].x=pos[0]
                self.dancers[direction].y=pos[1]
class DancerZombie(Basics):
    def __init__(self,pos=(0,0)):
        super().__init__(pos,images=['dancer_head_1.png','dancer_head_1.png','dancer_body_0.png','dancer_body_0.png','dancer_hand_left.png','dancer_hand_right.png','dancer_leg_left.png','dancer_leg_right.png'],resistents={'physical':1.0,'ice':1.0,'poison':1.0,'electric':1.0,'fire':1.0,'holy':1.0})
        self.hp=250
        self.full_hp=250
        self.speed,self.og_speed=0.5,0.5
        self.atk,self.og_atk=40,40
        self.death=DancerDie
    def on_death(self,screen):
        super().on_death(screen)
        self.mother.dancers[self.direction]=None

class NinjaImp(Imps):
    def __init__(self,pos=(0,0)):
        self.zombie_id=9
        super().__init__(pos,images=['ninja_imp_head.png','ninja_imp_head.png','ninja_imp_body.png','ninja_imp_body.png','ninja_imp_hand.png','ninja_imp_hand.png','ninja_imp_leg.png','ninja_imp_leg.png'],resistents={'physical':1.0,'ice':1.0,'poison':0.8,'electric':1.0,'fire':1.0,'holy':1.0})
        self.hp=180
        self.full_hp=180
        self.speed,self.og_speed=1.3,1.3
        self.atk,self.og_atk=60,60
        self.death=NinjaImpDie
        self.special_timer=random.randint(150,350)
        self.special_recharge=-1
    def special(self):
        self.lift_left_hand=True
        fogs((self.x-50,self.y+20),25,8)
        self.effect['unselectable']=175
        self.effect['haste']=175
        self.og_speed,self.speed=2,2
    def update(self,screen):
        super().update(screen)
        if self.can_eat and self.effect['haste']<=0 and not self.preview:
            for plant in get_value('plants'):
                try:
                    _=plant.rect
                except:
                    break
                if pygame.Rect.colliderect(self.rect,plant.rect) and plant.lane==self.lane and not plant.unselected:
                    if self.special_timer>-1:
                        self.special()
                        self.special_timer=self.special_recharge
                        self.can_move=True
        if self.effect['unselectable']>=0:
            self.lift_left_hand=True
            self.atk,self.og_atk=180,180
            self.og_speed,self.speed=2.1,2.1
            if self.effect['unselectable']==0:
                fogs((self.x-60,self.y+40),25,8)
        else:
            self.lift_left_hand=False
            self.og_speed,self.speed=1.3,1.3
            self.atk,self.og_atk=80,80
class ConeheadZombie(Basics):
    def __init__(self, pos=(0,0), images=['zombie_head_1.png', 'zombie_head_2.png', 'zombie_body_0.png', 'zombie_body_1.png','zombie_hand_left.png', 'zombie_hand_right.png', 'zombie_leg_left.png', 'zombie_leg_right.png'],is_special=False):
        self.zombie_id=2
        if random.randint(1,500)==1 or is_special:
            self.is_special=True
            images=['lawnmower.png', 'lawnmower.png', 'zombie_body_0.png', 'zombie_body_1.png', 'zombie_hand_left.png', 'zombie_hand_right.png', 'zombie_leg_left.png', 'zombie_leg_right.png']
        else:
            self.is_special=False
            
        super().__init__(pos, images)
        self.hp = 200
        self.full_hp=200
        self.armors.append(RoadCone(self))
        if self.is_special:
            self.atk,self.og_atk=99999999999999,99999999999999
            self.speed,self.og_speed=3,3
            sounds.play('lawnmower',2)
            self.insta_kill=True
    def on_death(self,_):
        super().on_death(_)
        if not self.preview and self.hp>-50 and not self.is_special:
            get_value('obstacles').add(Cone((self.x,self.y+30)))
        

class BucketheadZombie(Basics):
    def __init__(self, pos=(0,0), images=['zombie_head_1.png', 'zombie_head_2.png', 'zombie_body_0.png', 'zombie_body_1.png', 'zombie_hand_left.png', 'zombie_hand_right.png', 'zombie_leg_left.png', 'zombie_leg_right.png']):
        self.zombie_id=3
        super().__init__(pos, images)
        self.hp = 200
        self.full_hp = 200
        self.armors.append(Bucket(self))
    def on_death(self,_):
        super().on_death(_)
        if not self.preview:
            
            self.lane=int((self.x-90)//90+1)
            self.column=int((self.y)//90)
            for zombie in get_zombies_in(self.lane-1,self.lane+1,self.column-1,self.column+1):
                fogs((zombie.x,zombie.y),25,3)
                zombie.armors.append(Bucket(zombie))
                
class PaperZombie(Basics):
    def __init__(self, pos=(0,0), images=['zombie_head_1.png', 'zombie_head_2.png', 'paper_zombie_body_0.png', 'paper_zombie_body_1.png', 'paper_zombie_hand_left.png', 'paper_zombie_hand_right.png', 'zombie_leg_left.png', 'zombie_leg_right.png']):

        self.zombie_id=11
        super().__init__(pos, images)
        self.hp = 200
        self.full_hp = 200
        self.armors.append(PaperHat(self))
        self.death=PaperZombieDie
        self.special_timer=10
        self.special_recharge=60
        self.shooting=-1
        self.og_speed=0.7
        self.shot=False
    def special_criteria(self):
        if self.x<=900 and len(get_plants_in(self.column-4,self.column,self.lane,self.lane,None,'little',False))>=1:
            return True
        return False
    def update(self,screen):
        if self.shooting>=0:
            if abs(self.shooting-20)<=get_value('equivalent_frame')*0.5 or (self.shooting<=0 and self.shot==False):
                get_value('missles').add(Paper((self.x-30,self.y+5),-1000,self))
                self.shot=True
            self.shooting-=1*self.animation_coefficient*get_value('equivalent_frame')
            self.dont_move=True
            self.dont_eat=True
            self.force_left_hand=True
            if self.shooting>=20:
                self.left_hand_angle_+=2
            else:
                self.left_hand_angle_-=4
        else:
            self.dont_move=False
            self.dont_eat=False
            self.force_left_hand=False
            self.left_hand_angle_=20
        super().update(screen)
    def special(self):
        self.shooting=60
        self.left_hand_angle_=20
        self.shot=False

class PogoZombie(Bouncing):
    def __init__(self, pos=(0,0),initial_jump_height=13,is_special=False):
        self.zombie_id=4
        super().__init__(pos,initial_jump_height)
        self.full_hp = 400
        self.hp = 400
        self.jump_height=13
        self.is_special=is_special
        if random.randint(1,300)==1:
            self.is_special=True
        if self.is_special:
            
            self.jump_height=13
            self.og_speed=1.4
            self.images[0]=get_value('images')['pogo_zombie_mutant.png'][tuple()]
            self.paths[0]='pogo_zombie_mutant.png'
    def on_bounce(self):
        self.jump_height+=0
        if self.is_special:
            self.switch_lane(random.randint(self.lane-1,self.lane+1),720)
            for plant in get_value('plants'):
                try:
                    _=plant.rect
                except:
                    break
                if pygame.Rect.colliderect(self.rect,plant.rect) and plant.lane==self.lane:
                    plant.hp=-9999999
                    plant.on_destroy(self)
                    self.insta_kills(plant)
                    sounds.play('lawnmower',2)

class FootballZombie(Running):
    def __init__(self, pos=(0,0), images=['zombie_head_1.png', 'zombie_head_2.png', 'football_body.png', 'football_body.png', 'football_hand_left.png', 'football_hand_left.png', 'football_leg_left.png', 'football_leg_right.png']):

        self.zombie_id=5
        super().__init__(pos, images)
        self.hp = 300
        self.full_hp = 300
        self.armors.append(Football(self))
        self.atk,self.og_atk=80,80
class BlueFootballZombie(Running):
    def __init__(self, pos=(0,0), images=['zombie_head_1.png', 'zombie_head_2.png', 'blue_football_body.png', 'blue_football_body.png', 'blue_football_hand_left.png', 'blue_football_hand_left.png', 'blue_football_leg_left.png', 'blue_football_leg_right.png']):
        self.zombie_id=10
        super().__init__(pos, images)
        self.hp = 200
        self.full_hp = 200
        self.armors.append(BlueFootball(self))
        self.atk,self.og_atk=120,120
        self.og_speed=3.2
        self.speed=3.2
        self.insta_kill=True
        self.death=BlueFootballDie
    def insta_kills(self,_):
        self.insta_kill=False
        self.og_speed=0.8
        self.speed=0.8
        get_value('particles_-2').add(Clash((self.x-40,self.y+20),self))
        sounds.play('pea_hit',2)
    

class JeffZombie(Basics):
    def __init__(self, pos=(0,0), images=['zombie_head_1.png', 'zombie_head_2.png', 'zombie_body_0.png', 'zombie_body_1.png', 'zombie_hand_left.png', 'zombie_hand_right.png', 'zombie_leg_left.png', 'zombie_leg_right.png'],lift_left_hand=True):
        self.zombie_id=6
        super().__init__(pos, images)
        self.hp = 200
        self.full_hp = 200
        self.speed=0.25
        self.atk=200
        self.armors.extend([ScreenDoor(self),Football(self),Bucket(self),RoadCone(self)])
class ScreendoorZombie(Basics):
    def __init__(self, pos=(0,0), images=['zombie_head_1.png', 'zombie_head_2.png', 'zombie_body_0.png', 'zombie_body_1.png', 'zombie_hand_left.png', 'zombie_hand_right.png', 'zombie_leg_left.png', 'zombie_leg_right.png'],lift_left_hand=True):

        self.zombie_id=7
        super().__init__(pos, images)
        self.hp = 200
        self.full_hp = 200
        self.speed=0.7
        self.armors.extend([ScreenDoor(self)])


class FlagZombie(Basics):
    def __init__(self, pos=(0,0),kind='summon_', images=['zombie_head_1.png', 'zombie_head_2.png', 'zombie_body_0.png', 'zombie_body_1.png', 'zombie_hand_left.png', 'zombie_hand_right.png', 'zombie_leg_left.png', 'zombie_leg_right.png']):
        super().__init__(pos, images)
        self.hp = 500
        self.full_hp = 500
        self.armors.append(Flag(self,kind))
        #self.armors.append(Bucket(self))
        #self.armors.append(ScreenDoor(self))
        self.speed,self.og_speed=0.9,0.9

class Ghost(Levitating):
    def __init__(self, pos=(0,0), images=['ghost_zombie.png'],sincere=False):
        self.zombie_id=14
        super().__init__(pos, images)
        self.hp = 200
        self.full_hp = 200
        self.speed=1.05
        self.atk=0
        self.entered=False
        self.cnt=0
        self.sincere=False
        self.effect['unselectable']=1
        self.reveal=False
        if sincere:
            self.sincere=True
    def update(self,screen):
        super().update(screen)
        self.cnt+=get_value('equivalent_frame')
        if not self.reveal:
            self.effect['unselectable']=20
            self.effect['haste']=20
        if self.unselected and not self.reveal:
            self.effect['phantom']=1
            self.effect['invincible']=1
        else:
            self.effect['phantom']=-1
            self.effect['invincible']=-1
        if not self.entered and self.x<=800:
            self.entered=True
            sounds.play('ghost_appear',1)
class ReaperGhost(Ghost):
    def __init__(self,pos=(0,0)):
        super().__init__(pos,sincere=True)
        self.armors.append(ReaperCloak(self))
        self.zombie_id=15
class GhostArcher(Ghost):
    def __init__(self,pos=(0,0)):
        super().__init__(pos,sincere=True,images=['ghost_archer.png'])
        self.special_timer=10
        self.special_recharge=100
        self.speed,self.og_speed=0.4,0.4
        self.cnt_=0
        self.zombie_id=16
        self.yandoubuyanle=False
        self.shoot=False
        self.bow=BowAnimation((-35,0),mother=self)
    def special_criteria(self):
        if self.x<=850 and len(get_plants_in(0,self.column,self.lane,self.lane,None,'little',False))>=1:
            self.reveal=True
            self.yandoubuyanle=False
            return True
        elif self.x<=850 and len(get_plants_in(0,self.column,self.lane,self.lane,None,'little',True,'unselectable'))==len(get_plants_in(0,self.column,self.lane,self.lane,None,'little',True)) and not len(get_plants_in(0,self.column,self.lane,self.lane,None,None,True))==0:
            self.yandoubuyanle=True
            return True
        self.reveal=False
        self.speed,self.og_speed=0.4,0.4
        return False
    def display(self):
        super().display()
        if not self.yandoubuyanle:
            self.bow.draw()
    def update(self,screen):
        super().update(screen)
        if self.cnt_>0 and self.shoot:
            self.cnt_-=1
            if self.cnt_==0:
                if self.yandoubuyanle:
                    sounds.play('ghost_beam',1)
                    get_value('missles').add(GhostBeam((60-(900-self.x),self.y-10),-1000,self))

                else:
                    sounds.play('bow_release',1)
                    get_value('missles').add(GhostArrow((self.x-5,self.y+20),-1000,self))
                self.shoot=False
    def special(self):
        if not self.shoot:
            self.bow.stretch_timer=20
            self.cnt_=20
            self.shoot=True
            self.speed,self.og_speed=0,0
            sounds.play('bow_load',1)
class ArcherZombie(Basics):
    def __init__(self, pos=(0,0), images=['zombie_head_1.png', 'zombie_head_2.png', 'archer_body_0.png', 'archer_body_1.png', 'archer_hand_left.png', 'archer_hand_right.png', 'archer_leg_left.png', 'archer_leg_right.png'],lift_left_hand=True):
        self.zombie_id=17
        super().__init__(pos, images)
        self.special_timer=10
        self.special_recharge=75
        self.hp = 250
        self.full_hp = 250
        self.speed=0.6
        self.atk=40
        self.cnt_=-1
        self.death=ArcherDie
        self.shoot=False
        self.armors.extend([ArcherHat(self)])
        self.bow=BowAnimation((-65,10),arrow_img='normal_arrow.png',mother=self)
    def special_criteria(self):
        if self.x<=850 and len(get_plants_in(0,self.column,self.lane,self.lane,None,'little',False))>=1:
            return True
        self.speed,self.og_speed=0.6,0.6
        self.dont_move=False
        self.dont_eat=False
        return False
    def display(self):
        super().display()
        self.bow.draw()
    def update(self,screen):
        super().update(screen)
        if self.cnt_>0 and self.shoot:
            self.cnt_-=1
            self.dont_move=True
            self.dont_eat=True
            if self.cnt_==0:
                sounds.play('bow_release',1)
                get_value('missles').add(NormalArrow((self.x-15,self.y+30),-1000,self))
                self.shoot=False
    def special(self):
        if not self.shoot:
            self.bow.stretch_timer=20
            self.cnt_=20
            self.shoot=True
            self.speed,self.og_speed=0,0
            sounds.play('bow_load',1)
class FireArcherZombie(Basics):
    def __init__(self, pos=(0,0), images=['zombie_head_1.png', 'zombie_head_2.png', 'archer_body_0.png', 'archer_body_1.png', 'archer_hand_left.png', 'archer_hand_right.png', 'archer_leg_left.png', 'archer_leg_right.png'],lift_left_hand=True):
        self.zombie_id=18
        super().__init__(pos, images)
        self.special_timer=10
        self.special_recharge=100
        self.death=ArcherDie
        self.hp = 250
        self.full_hp = 250
        self.speed=0.6
        self.atk=40
        self.cnt_=-1
        self.shoot=False
        self.armors.extend([FireArcherHat(self)])
        self.bow=BowAnimation((-65,10),arrow_img='fire_arrow.png',mother=self)
    def special_criteria(self):
        if self.x<=850 and len(get_plants_in(0,self.column,self.lane,self.lane,None,'little',False))>=1:
            return True
        self.speed,self.og_speed=0.6,0.6
        self.dont_move=False
        self.dont_eat=False
        return False
    def display(self):
        super().display()
        self.bow.draw()
    def update(self,screen):
        super().update(screen)
        if self.cnt_>0 and self.shoot:
            self.cnt_-=1
            self.dont_move=True
            self.dont_eat=True
            if self.cnt_==0:
                sounds.play('bow_release',1)
                get_value('missles').add(FireArrow((self.x-15,self.y+30),-1000,self))
                self.shoot=False
    def special(self):
        if not self.shoot:
            self.bow.stretch_timer=20
            self.cnt_=20
            self.shoot=True
            self.speed,self.og_speed=0,0
            sounds.play('bow_load',1)
class IceArcherZombie(Basics):
    def __init__(self, pos=(0,0), images=['zombie_head_1.png', 'zombie_head_2.png', 'archer_body_0.png', 'archer_body_1.png', 'archer_hand_left.png', 'archer_hand_right.png', 'archer_leg_left.png', 'archer_leg_right.png'],lift_left_hand=True):
        self.zombie_id=19
        super().__init__(pos, images)
        self.special_timer=10
        self.special_recharge=75
        self.hp = 250
        self.full_hp = 250
        self.speed=0.6
        self.death=ArcherDie
        self.atk=40
        self.cnt_=-1
        self.shoot=False
        self.armors.extend([IceArcherHat(self)])
        self.bow=BowAnimation((-65,10),arrow_img='ice_arrow.png',mother=self)
    def special_criteria(self):
        if self.x<=850 and len(get_plants_in(0,self.column,self.lane,self.lane,None,'little',False))>=1:
            return True
        self.speed,self.og_speed=0.6,0.6
        self.dont_move=False
        self.dont_eat=False
        return False
    def display(self):
        super().display()
        self.bow.draw()
    def update(self,screen):
        super().update(screen)
        if self.cnt_>0 and self.shoot:
            self.cnt_-=1
            self.dont_move=True
            self.dont_eat=True
            if self.cnt_==0:
                sounds.play('bow_release',1)
                get_value('missles').add(IceArrow((self.x-15,self.y+30),-1000,self))
                self.shoot=False
    def special(self):
        if not self.shoot:
            self.bow.stretch_timer=20
            self.cnt_=20
            self.shoot=True
            self.speed,self.og_speed=0,0
            sounds.play('bow_load',1)
#armors
class Armors():#kind: normal:just normal lol horizontal:can only block horizontal missles verticle:can only block verticle
    def __init__(self, mother=None,hp=400, kind='normal', resistents={
        'physical': 0.9, 'ice': 1, 'poison': 1, 'electric': 1,'fire':1,'holy':1.0},images={400:'roadcone_0.png',250:'roadcone_1.png',100:'roadcone_2.png'},pos_shift=(-5,-50),angle=-20,effect_resistents=[],
                 flexibility=0.5):
        self.hp=hp
        self.kind=kind
        self.resistents=resistents
        self.images=images
        self.paths=images
        self.image=get_value('images')[self.paths[self.hp]][tuple()]
        self.healths=list(self.images.keys())
        self.pos_shift=pos_shift
        self.angle=angle
        self.mother=mother
        self.hit=False
        self.effect_resistents=effect_resistents
        self.flag=False
        self.filter_index=0
        self.render_index=0
        self.flexibility=flexibility
        self.effects=[]
        self.show=True
        self.accessory=False
    def render(self):
        self.renders[self.filters[self.filter_index]][list(self.paths.keys())[self.render_index]]=cv2_2_pygame(pillow_pvz_filter(self.paths[list(self.paths.keys())[self.render_index]], self.filters[self.filter_index]))
        self.render_index += 1
        if self.render_index >= len(list(self.paths.keys())):
            self.filter_index += 1
            self.render_index = 0
    def update(self):
        #resistents to effects
        for effect in self.effect_resistents:
            if effect=='freeze' and 'freeze' in self.mother.effects:
                self.mother.effects.remove('freeze')
                self.mother.speed_coefficient=1
                self.mother.animation_coefficient=1
                self.mother.atk_coefficient=1
                self.mother.chilled=False
            elif effect=='milk' and 'milk' in self.mother.effects:
                self.mother.effects.remove('milk')
                self.mother.speed_coefficient = 1
                self.mother.animation_coefficient = 1
                self.mother.atk_coefficient = 1
                self.mother.milked = 0

    def display(self):
        try:
            self.effects = self.mother.effects.copy()
        except:
            pass
        if 'hit' in self.effects:
            self.effects.remove('hit')
        if self.hit:
            self.effects.insert(0,'hit')
            self.hit=False
        self.images = dict()
        for a in self.paths:
            self.images[a] = get_value('images')[self.paths[a]][tuple(self.effects)]
        for key in reversed(self.healths):
            if self.hp <= key:
                if self.angle!=0:
                    self.image = pygame.transform.rotate(self.images[key], self.angle)
                else:
                    self.image=self.images[key]
                break
        if self.show:
            blity(self.image, (self.mother.x + self.pos_shift[0], self.mother.y+self.pos_shift[1]))

    def damage(self,dmg,dmg_type,missle_type):
        self.hp-=self.resistents[dmg_type]*dmg
        self.hit=True
        if self.hp<=0:
            self.on_break()
            self.mother.armors.remove(self)
            self.mother.damage(abs(self.hp)*(1-self.flexibility),dmg_type,missle_type)
    def on_break(self):
        get_value('particles_0').add(ObjectFall(
            self.mother,self.paths[self.healths[-1]], (self.pos_shift[0]+self.mother.x,self.pos_shift[1]+self.mother.y), 20, self.effects, 0.5, 0.5, rotate=True, rotate_start=-20, rotate_end=-180, rotate_speed=-10))
class RoadCone(Armors):
    def __init__(self,mother):
        super().__init__(mother)
class Bucket(Armors):
    def __init__(self,mother):
        super().__init__(mother, 600, resistents={
            'physical': 0.7, 'ice': 1, 'poison': 1, 'electric': 1.1,'fire':1.0,'holy':1.0},
                         images={600: 'bucket_0.png', 400: 'bucket_1.png',
                                 200: 'bucket_2.png'}, pos_shift=(-20, -45),angle=-20,flexibility=0.7)


class Football(Armors):
    def __init__(self, mother):
        super().__init__(mother, 800, resistents={
            'physical': 0.5, 'ice': 0.8, 'poison': 0.9, 'electric': 1.2,'fire':1.0,'holy':1.0},
                         images={800: 'football_helmet_0.png',
                                 400: 'football_helmet_1.png',
                                 200: 'football_helmet_2.png'}, pos_shift=(-5, -25), angle=0,flexibility=0.3)
class PaperHat(Armors):
    def __init__(self, mother):
        super().__init__(mother, 200, resistents={
            'physical': 0.95, 'ice': 1, 'poison': 1, 'electric': 1,'fire':1.75,'holy':1.0},
                         images={200: 'paperhat_0.png',
                                 100: 'paperhat_1.png'}, angle=0,flexibility=0)
class PaperBox(Armors):
    def __init__(self, mother):
        super().__init__(mother, 200, resistents={
            'physical': 0.95, 'ice': 1, 'poison': 1, 'electric': 1,'fire':2,'holy':1.0},
                         images={200: 'paper_box_0.png',
                                 100: 'paper_box_1.png'}, angle=0,flexibility=0,pos_shift=(-10,33))
        
class BlueFootball(Armors):
    def __init__(self, mother):
        super().__init__(mother, 500, resistents={
            'physical': 0.7, 'ice': 0.9, 'poison': 1, 'electric': 1.1,'fire':1.0,'holy':1.0},
                         images={500: 'blue_football_helmet_0.png',
                                 250: 'blue_football_helmet_1.png',
                                 100: 'blue_football_helmet_2.png'}, pos_shift=(-5, -25), angle=0,flexibility=0.3)
class ScreenDoor(Armors):
    def __init__(self, mother):
        super().__init__(mother, 1500, kind='horizontal', resistents={
            'physical': 0.7, 'ice': 0.8, 'poison': 0.1, 'electric': 1.3,'fire':1.0,'holy':1.0},
                         images={1500: 'screen_door_0.png',
                                 900: 'screen_door_1.png',
                                 300: 'screen_door_2.png'},
                         pos_shift=(-15, 10), angle=0,effect_resistents=['freeze'],flexibility=1)
        self.mother.lift_left_hand=True
    def on_break(self):
        self.mother.lift_left_hand=False
        super().on_break()
class ReaperCloak(Armors):
    def __init__(self, mother):
        super().__init__(mother, 200, resistents={
            'physical': 0.95, 'ice': 0.9, 'poison': 0.5, 'electric': 1.0,'fire':1.5,'holy':1.0},
                         images={200: 'reaper_cloak.png',
                                 100: 'reaper_cloak_1.png'},
                         pos_shift=(-10, -10), angle=0,flexibility=0)
    def on_break(self):
        super().on_break()
        self.mother.sincere=False
    def update(self):
        super().update()
        for plant in get_value('plants'):
            try:
                _=plant.rect
            except:
                break
            if pygame.Rect.colliderect(self.mother.rect,plant.rect) and plant.lane==self.mother.lane:
                if 'holy' in plant.traits:
                    self.mother.damage(2,'poison','piercing',True)
                    get_value('particles_0').add(HolyMantle((plant.x-50,plant.y-60),plant))
                else:
                    self.mother.x+=0.5
                    plant.damage(2,None,real=True)
                    plant.hit_timer=1
class ArcherHat(Armors):
    def __init__(self, mother):
        super().__init__(mother, 1, resistents={
            'physical': 1, 'ice': 1, 'poison': 1, 'electric': 1,'fire':1.5,'holy':1.0},
                         images={1:'archer_hat_green.png'}, pos_shift=(-10,-35),angle=0,flexibility=0.3)
        self.accessory=True
class FireArcherHat(Armors):
    def __init__(self, mother):
        super().__init__(mother, 1, resistents={
            'physical': 1, 'ice': 1, 'poison': 1, 'electric': 1,'fire':1.5,'holy':1.0},
                         images={1:'archer_hat_orange.png'}, pos_shift=(-10,-35),angle=0,flexibility=0.3)
        self.accessory=True
class IceArcherHat(Armors):
    def __init__(self, mother):
        super().__init__(mother, 1, resistents={
            'physical': 1, 'ice': 1, 'poison': 1, 'electric': 1,'fire':1.5,'holy':1.0},
                         images={1:'archer_hat_blue.png'}, pos_shift=(-10,-35),angle=0,flexibility=0.3)
        self.accessory=True
    
class Flag():
    def __init__(self, mother, kind):
        self.mother = mother
        self.hit = False
        self.filter_index = 0
        self.kind=kind
        self.flag=True
        self.pole=get_value('images')['stic.png'][tuple()]
        self.flag=get_value('images')[''+kind+'flag.png'][tuple()]
        #self.image=pygame.Surface((36+15+10,105+28+10+10),pygame.SRCALPHA)
        self.paths=['stic.png',''+kind+'flag.png']
        self.effects=[]
        self.special_cnt=999999
        self.max_cnt=999999
        if self.kind=='taunt_':
            set_value('specials',get_value('specials')+['flag_shield'])
        elif self.kind=='heal_' or self.kind=='revive_':
            self.special_cnt,self.max_cnt=30,30
            self.mother.skills[self.skill]=[30,30]
        elif self.kind=='revive_':
            self.special_cnt,self.max_cnt=60,90
            self.mother.skills[self.skill]=[60,90]
        elif self.kind=='summon_' or self.kind=='grave_':
            self.special_cnt,self.max_cnt=50,500/get_value('difficulty')
            self.mother.skills[self.skill]=[50,500/get_value('difficulty')]
        elif self.kind=='turbo_':
            set_value('specials', get_value('specials')+['flag_turbo'])
        elif self.kind == 'aggro_':
            set_value('specials', get_value('specials')+['flag_aggro'])
        elif self.kind == 'deadly_':
            set_value('specials', get_value('specials')+['flag_deadly'])
        elif self.kind == 'crowd_':
            set_value('specials', get_value('specials')+['flag_crowd'])
    def update(self):
        pass

    def render(self):
        self.renders[self.filters[self.filter_index]] = [cv2_2_pygame(
            pillow_pvz_filter(self.paths[0], self.filters[self.filter_index])), cv2_2_pygame(pillow_pvz_filter(self.paths[1], self.filters[self.filter_index]))]
        self.filter_index+=1

    def display(self):
        self.mother.lift_left_hand = True
        self.effects = self.mother.effects.copy()
        self.pole=get_value('images')[self.paths[0]][tuple(self.effects)]
        self.flag=get_value('images')[self.paths[1]][tuple(self.effects)]
        blity(self.pole, (self.mother.x-20 , self.mother.y-50))
        blity(self.flag,(self.mother.x-15,self.mother.y-50))
    def skill(self):
        if self.kind=='heal_':
            for zombie in get_value('zombies'):
                zombie.heal(10*get_value('difficulty'))
                get_value('particles_0').add(FlagHeal((zombie.x,zombie.y-30),zombie))
        elif self.kind=='revive_':
            for zombie in get_value('zombies'):
                zombie.heal(999999999999)
                get_value('particles_0').add(FlagRevive((zombie.x,zombie.y-30),zombie))     
        elif self.kind=='summon_':
            zombie=copy.deepcopy(SPECIAL_ZOMBIES)[get_value('level').scene]
            if not get_value('hard_mode'):
                zombie=list(set(zombie)-set(HARD_MODE_EXCLUSIVE))
            x=random.randint(6,9)
            y=random.randint(1,get_value('level').lane_num)
            get_value('particles_0').add(SpawnGraveZombie((x,y),random.choice(zombie),self.mother,lane=y))
        elif self.kind=='grave_':
            spawn_random_graves(1)

    def on_break(self):
        specials=get_value('specials')
        if self.kind == 'taunt_':
            specials.remove('flag_shield')
        elif self.kind == 'turbo_':
            specials.remove('flag_turbo')
        elif self.kind == 'aggro_':
            specials.remove('flag_aggro')
        elif self.kind == 'deadly_':
            specials.remove('flag_deadly')
        elif self.kind == 'crowd_':
            specials.remove('flag_crowd')
        self.mother.skills=dict()
        set_value('specials',specials)


        get_value('particles_0').add(ObjectFall(
            self.mother,self.paths[1], (self.mother.x-60, self.mother.y-60), 20, self.effects, 0.5, 0.5, rotate=True, rotate_start=-20, rotate_end=-90, rotate_speed=-5))
        get_value('particles_0').add(ObjectFall(
            self.mother,self.paths[0], (self.mother.x-30, self.mother.y-60), 20, self.effects, 0.5, 0.5, rotate=True, rotate_start=-20, rotate_end=-180, rotate_speed=-10))
    def damage(self):
        pass
#animations
class Animation(pygame.sprite.Sprite):
    def __init__(self, images=[], pos=(0,0), durations=[],effects=[],up=False,mother=None,kind='obstacles',lane=1,free=False):
        super().__init__()
        self.e = effects.copy()
        self.mother=mother
        self.shake=False
        self.free=free
        if not free:
            if mother:
                self.lane=mother.lane
                if get_value('state')!='loading': 
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
            else:
                
                if get_value('state')!='loading': 
                    self.lane = lane
                    lane = get_value('lanes')
                    l=lane[self.lane-1][kind]
                    l.append(self)
                    set_value('lanes', lane)
        if 'hit' in self.e:
            self.e.remove('hit')
        #self.images = []
        self.pos = pos
        self.cnt, self.durations,self.pose = 0, durations,0
        self.paths=images
        self.images=[get_value('images')[path][tuple(self.e)] for path in self.paths]
        self.image = self.images[0]
    def update(self, screen):
        self.cnt += get_value('equivalent_frame')
        try:
            if self.cnt>=self.durations[self.pose]:
                self.cnt=0
                self.pose+=1
                self.image=self.images[self.pose]
        except:
            self.on_end()
            self.kill()
        if self.free:
            if self.shake:
                blity(self.image, [self.pos[0]+random.randint(-5,5),self.pos[1]+random.randint(-5,5)])
            else:
                blity(self.image, self.pos)
            
    def display(self):
        screen=get_value('screen')
        if self.shake:
            blity(self.image, [self.pos[0]+random.randint(-5,5),self.pos[1]+random.randint(-5,5)])
        else:
            blity(self.image, self.pos)

    def on_end(self):
        lane = get_value('lanes')
        if not self.free:
            for key in ['plants', 'obstacles', 'zombies']:
                if self in lane[self.lane-1][key]:
                    lane[self.lane-1][key].remove(self)
                    break
            set_value('lanes', lane)
class SpawnGrave(Animation):
    def __init__(self, pos=(0,0), id_=2,lane=0):
        wwm=False
        if id_=='wwm' or 'random graves' in get_value('specials'):
            print('wwm')
            id_=5
            wwm=True
        print(id_)
        super().__init__([f'spawngrave_{id_}_1.png', f'spawngrave_{id_}_2.png',
                          f'spawngrave_{id_}_3.png'], pos, [10, 10, 10],lane=lane)
        if wwm:
            id_='wwm'
        self.id_ = id_
        sounds.play('spawngrave', 0.5)

    def on_end(self):
        super().on_end()
        x = (self.pos[0]+20)//90
        y = (self.pos[1]-10)//90
        get_value('obstacles').add(Grave((x, y), self.id_))


class SpawnGraveZombie(pygame.sprite.Sprite):
    def __init__(self, pos=(0,0), id_=1,mother=None,up=False,lane=1,kind='obstacles'):
        super().__init__()
        self.id_=id_
        self.x,self.y=pos
        self.cnt=50
        self.image=get_value('images')['zombie_hand_left.png'][tuple()]
        self.angle=random.randint(171,189)
        self.rotate_speed = -1
        self.mother=mother
        sounds.play('spawngrave', 0.3)
        if mother:
            if get_value('state')!='loading': 
                self.lane = mother.lane
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
        else:
            
            if get_value('state')!='loading': 
                self.lane = lane
                lane = get_value('lanes')
                l = lane[int(self.lane-1)][kind]
                l.append(self)
                lane[int(self.lane-1)][kind] = l
                set_value('lanes', lane)
                set_value('lanes', lane)

    def update(self, screen):
        self.rotated_hand, self.hand_rect = rotate(
             self.image, self.angle, (self.x*90+25, self.y*90+97), pygame.math.Vector2((8, 18.5)))
        self.angle+=self.rotate_speed
        if self.angle==170 or self.angle==190:
            self.rotate_speed=-self.rotate_speed
        self.cnt-=1
        if self.cnt==0:
            self.on_end()
            self.kill()
        if not self.mother:
            blity(self.rotated_hand,self.hand_rect)

    def display(self):
        screen=get_value('screen')
        try:
            blity(self.rotated_hand,self.hand_rect)
        except:
            pass
    def on_end(self):
        lane = get_value('lanes')
        for key in ['plants', 'obstacles', 'zombies']:
            if self in lane[int(self.lane-1)][key]:
                lane[int(self.lane-1)][key].remove(self)
                break
        set_value('lanes',lane)
        get_value('zombies').add(
            ZOMBIE_CLASSES[self.id_]((90*self.x, self.y*90)))

class ZombieDie(Animation):
    def __init__(self, pos=(0,0),effects=[],mother=None):
        super().__init__([f'zombie_die_0.png', f'zombie_die_1.png',
                          f'zombie_die_2.png'], pos, [20, 15, 15],effects,mother=mother)
class PaperZombieDie(Animation):
    def __init__(self, pos=(0,0),effects=[],mother=None):
        super().__init__([f'paper_zombie_die_0.png', f'paper_zombie_die_1.png',
                          f'paper_zombie_die_2.png'], pos, [20, 15, 15],effects,mother=mother)

class FootballDie(Animation):
    def __init__(self, pos=(0,0), effects=[],mother=None):
        super().__init__([f'football_die_0.png', f'football_die_1.png',
                          f'football_die_2.png'], pos, [20, 15, 15], effects,mother=mother)
class BlueFootballDie(Animation):
    def __init__(self, pos=(0,0), effects=[],mother=None):
        super().__init__([f'blue_football_die_0.png', f'blue_football_die_1.png',
                          f'blue_football_die_2.png'], pos, [20, 15, 15], effects,mother=mother)
class ImpDie(Animation):
    def __init__(self, pos=(0,0), effects=[],mother=None):
        super().__init__([f'imp_die_1.png', f'imp_die_2.png',
                          f'imp_die_3.png'], pos, [20, 15, 15], effects,mother=mother)
class NinjaImpDie(Animation):
    def __init__(self, pos=(0,0), effects=[],mother=None):
        super().__init__([f'ninja_imp_die_1.png', f'ninja_imp_die_2.png',
                          f'ninja_imp_die_3.png'], pos, [20, 15, 15], effects,mother=mother)
class DiscoDie(Animation):
    def __init__(self, pos=(0,0), effects=[],mother=None):
        super().__init__([f'disco_zombie_die_0.png', f'disco_zombie_die_1.png',
                          f'disco_zombie_die_2.png'], pos, [20, 15, 15], effects,mother=mother)
class ArcherDie(Animation):
    def __init__(self, pos=(0,0), effects=[],mother=None):
        super().__init__([f'archer_zombie_die_0.png', f'archer_zombie_die_1.png',
                          f'archer_zombie_die_2.png'], pos, [20, 15, 15], effects,mother=mother)
class DancerDie(Animation):
    def __init__(self, pos=(0,0), effects=[],mother=None):
        super().__init__([f'dancer_zombie_die_0.png', f'dancer_zombie_die_1.png',
                          f'dancer_zombie_die_2.png'], pos, [20, 15, 15], effects,mother=mother)
class GhostDie(Animation):
    def __init__(self, pos=(0,0), effects=[],mother=None):
        super().__init__([f'ghost_death_0.png'], pos, [160], effects,mother=mother,free=True)
        self.shake=True
        sounds.play('ghost_die',0.05)
class BowAnimation():
    def __init__(self,pos=(0,0),arrow_img='ghost_arrow.png',mother=None,stretch_time=20):
        self.pos,self.og_pos=pos,pos
        self.image=get_value('images')['bow.png'][tuple()]
        self.arrow_img=get_value('images')[arrow_img][tuple()]
        self.stretch_time=20
        self.stretch_timer=-1
        self.mother=mother
    def draw(self):
        if self.mother:
            self.image=get_value('images')['bow.png'][tuple(self.mother.effects)]
            self.pos=[self.og_pos[0]+self.mother.x,self.og_pos[1]+self.mother.y]
        if self.stretch_timer<0:
            self.mid_point=(68,32)
        else:
            self.stretch_timer-=1
            self.mid_point=(68+32*(self.stretch_time-self.stretch_timer)/self.stretch_time,32)
        blity(self.image,self.pos)
        pygame.draw.line(get_value('screen'),(141,141,141),(self.pos[0]+69,self.pos[1]+7),(self.pos[0]+self.mid_point[0],self.pos[1]+self.mid_point[1]))
        pygame.draw.line(get_value('screen'),(141,141,141),(self.pos[0]+self.mid_point[0],self.pos[1]+self.mid_point[1]),(self.pos[0]+67,self.pos[1]+57))
        if self.stretch_timer>0:
            blity(self.arrow_img,(self.pos[0]+28+28*(self.stretch_time-self.stretch_timer)/self.stretch_time,self.pos[1]+20))
#group
class StupidOrderedGroup(pygame.sprite.Group):

    def by_y(self, spr):
        return spr.lane

    def draw(self, surface):
        sprites = self.sprites()
        for spr in sorted(sprites, key=self.by_y):
            spr.update(surface)
        self.lostsprites = []
#functions
def spawn_grave(pos,id_):
    x = pos[0]*90-20
    y = pos[1]*90+10
    lane=pos[1]
    pos=[x,y]
    get_value('particles_0').add(SpawnGrave(pos,id_,lane=lane))
def spawn_random_graves(number):
    for a in range(number):
        if get_value('grave_spots') and get_value('grave_num')<get_value('level').max_grave:
            set_value('grave_num',get_value('grave_num')+1)
            spots = get_value('grave_spots')
            location = random.choice(spots)
            spots.remove(location)
            set_value('grave_spots', spots)
            spawn_grave(location, random.choice(
                get_value('grave_ratio')))


def get_obstacles_at(x, y):
    objects = []
    for plant in get_value('obstacles'):
        if (plant.x+20)//90 == x and (plant.y-10)//90 == y:
            objects.append(plant)
    return objects
def get_obstacles_in(xstart,xend,ystart,yend):
    xs=[x+1 for x in range(xstart-1,xend)]
    ys = [y+1 for y in range(ystart-1, yend)]
    objects=[]
    for x in xs:
        for y in ys:
            objects.extend(get_obstacles_at(x,y))
    return objects


def get_zombies_at(x, y):
    objects = []
    for plant in get_value('zombies'):
        if (plant.x+20)//90 == x and plant.lane == y and plant.effect['unselectable']<=0:
            objects.append(plant)
    return objects


def get_zombies_in(xstart, xend, ystart, yend):
    xs = [x+1 for x in range(xstart-1, xend)]
    ys = [y+1 for y in range(ystart-1, yend)]
    objects = []
    for x in xs:
        for y in ys:
            objects.extend(get_zombies_at(x, y))
    return objects
#constants part 2
HARD_MODE_EXCLUSIVE=[6]
ZOMBIE_CLASSES={1:BasicZombie,2:ConeheadZombie,4:PogoZombie,3:BucketheadZombie,5:FootballZombie,6:JeffZombie,7:ScreendoorZombie,
                8:Imp,9:NinjaImp,10:BlueFootballZombie,11:PaperZombie,12:PaperImp,13:DiscoZombie,14:Ghost,
                15:ReaperGhost,16:GhostArcher,17:ArcherZombie,18:FireArcherZombie,19:IceArcherZombie}

SPECIAL_ZOMBIES={'void':[4,5,6,7,9,10,11,13,17,18,19],'lawn_day':[4,5,6,7,10,11],'lawn_night':[4,5,6,7,9,10,11,12,13,14],'lawn_day_1':[4,5,6,7,10,11],'lawn_night_1':[4,5,6,7,9,10,11,12,13,14]}
