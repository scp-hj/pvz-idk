import pygame
import sounds,sys,os,random
from config import *
from particles import *
from filter import *
from sympy.abc import x
from sympy import solve,solveset
def rp(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


class Missle(pygame.sprite.Sprite):
    def __init__(self,image,kind,velocity,damage,side,pos,show_x,hit_sound,particle,mother,dmg_type='physical',size=20,piercing=False,volumn=0.5,dest_x=0):
        super().__init__()
        if size:
            self.image=pygame.transform.scale(get_value('images')[image][tuple()],(size,size))
        else:
            self.image=get_value('images')[image][tuple()]
        self.kind=kind
        self.velocity=list(velocity)
        self.dmg=damage
        self.side=side
        self.mother=mother
        self.volumn=volumn
        self.x=pos[0]
        self.y=pos[1]
        self.life=-99999999
        self.mask=pygame.mask.from_surface(self.image)
        self.rect=self.image.get_rect()
        self.particle=particle
        self.show=show_x
        self.sound=hit_sound
        self.dmg_type=dmg_type
        self.zombie=None
        self.fps = 0
        self.lane=self.mother.lane
        lanes = get_value('lanes')
        lane = lanes[self.lane-1]['zombies']
        lane.append(self)
        lanes[self.lane-1]['zombies'] = lane
        self.piercing = piercing
        self.done=False
        self.hitted=False
        self.hit_again=False
        self.hit_cds=[] # [cd1,cd2,cd3,...]
        self.hit_cd=0
        self.number=random.randint(1,1000000)
        self.factor=0
        self.limited=False
        self.hits=[]      # [1, 2, 3]
        self.torched=False
        self.hit_unselectable=False
        self.hit_little=True
        if self.kind=='homing':
            self.new_target('distance')
        if self.kind=='thrown':
            self.velocity[0]=self.velocity[0]*(dest_x-self.x)/700
            self.velocity[1]=float(min(solveset((-x/get_value('gravity'))*self.velocity[0]-(dest_x-self.x)//2,x)))
            print(self.velocity)
            print((self.velocity[1]/get_value('gravity'))*self.velocity[0])
            print(dest_x)
    def display(self):
        screen=get_value('screen')
        if self.kind == 'straight':
            if self.x > self.show:
                blity(self.image, (self.x, self.y))
        else:
            blity(self.image, (self.x, self.y))

    def update(self, screen):
        for i in range(len(self.hit_cds)):
            self.hit_cds[i]-=get_value('equivalent_frame')
        self.relative_x,self.relative_y=self.x+get_value('pos_shift')[0],self.y+get_value('pos_shift')[1]
        self.rect = pygame.Rect(self.x, self.y, self.image.get_width(), self.image.get_height())
        self.life-=get_value('equivalent_frame')
        if self.life<=0 and self.life>-5:
            self.done=True
            lane=get_value('lanes')
            if self in lane[self.lane-1]['zombies']:
                lane[self.lane-1]['zombies'].remove(self)
            set_value('lanes',lane)
            self.kill()
        #move
        if self.kind=='straight':
            self.x=self.x+self.velocity[0]*get_value('equivalent_frame')
            self.y=self.y+self.velocity[1]*get_value('equivalent_frame')
        elif self.kind=='thrown':
            self.x+=self.velocity[0]*get_value('equivalent_frame')
            self.y+=self.velocity[1]*get_value('equivalent_frame')
            self.velocity[1]+=get_value('gravity')*get_value('equivalent_frame')
            self.limited=True
        elif self.kind=='homing':
            if len(get_value('zombies').sprites())>0:
                if not self.hitted:
                    self.new_target('distance')
                if self.zombie and not self.hitted:
                    self.x_dif=self.zombie.rect[0]-self.x
                    self.y_dif=self.zombie.rect[1]-self.y+20
                    #normalise
                    try:
                        self.factor=self.velocity[0]*(1/(abs(self.x_dif)+abs(self.y_dif)))
                    except:
                        pass
                try:
                    self.x_speed=self.x_dif*self.factor
                    self.y_speed=self.y_dif*self.factor
                    if self.x_speed==0 and self.y_speed==0:
                        lane = get_value('lanes')                            
                        if self in lane[self.lane-1]['zombies']:
                            lane[self.lane-1]['zombies'].remove(self)
                        set_value('lanes', lane)
                        self.kill()
                except:
                    self.kill()
                    
            #move
            try:
                self.x=self.x+self.x_speed*get_value('equivalent_frame')
                self.y=self.y+self.y_speed*get_value('equivalent_frame')
            except:
                lane = get_value('lanes')                            
                if self in lane[self.lane-1]['zombies']:
                    lane[self.lane-1]['zombies'].remove(self)
                set_value('lanes', lane)
                self.kill()
        #self.x,self.y=self.x+get_value('pos_shift')[0],self.y+get_value('pos_shift')[1]
        if self.x-self.image.get_width() > 900 or self.x < -self.image.get_width() or self.y-self.image.get_height() >640 or self.y < -self.image.get_height():
            lane = get_value('lanes')                            
            if self in lane[self.lane-1]['zombies']:
                lane[self.lane-1]['zombies'].remove(self)
            set_value('lanes', lane)
            self.kill()
        yes=False
        if self.kind != 'homing' and self.kind!='fume':
            if self.x > self.show:
                yes=True
        else:
            yes=True
        if yes:
            if (self.piercing=='rng' and self.fps%5==0) or (self.piercing!='rng') and not self.done:
                if self.side==1:
                    for obstacle in get_value('obstacles'):
                        if self.kind=='fume':
                            if self.rect.colliderect(obstacle.rect) and ((not self.limited) or self.lane==obstacle.lane):
                                if not self in obstacle.fumes:
                                    obstacle.fumes.append(self)
                                    obstacle.hp -= self.dmg
                                    obstacle.hit_timer = 1
                                    sounds.play(self.sound,self.volumn)
                                    continue
                                else:
                                    continue
                            else:
                                continue
                        else:
                            if self.collide_with(obstacle) and ((not self.limited) or self.lane==obstacle.lane):
                                hit_again=False
                                if self.hit_again:
                                    if obstacle in self.hits:
                                        if self.hit_cds[self.hits.index(obstacle)]<=0:
                                            hit_again=True
                                if not obstacle in self.hits or hit_again:
                                    obstacle.hp-=self.dmg
                                    self.on_hit(obstacle,'obstacle')
                                    obstacle.hit_timer=1
                                    if self.hit_again:
                                        if not obstacle in self.hits:
                                            self.hit_cds.append(self.hit_cd)
                                        else:
                                            self.hit_cds[self.hits.index(obstacle)]=self.hit_cd
                                    if not obstacle in self.hits:
                                        self.hits.append(obstacle)
                                    sounds.play(self.sound,self.volumn)
                                    if self.particle:
                                        get_value('particles_0').add(self.particle((self.x-20,self.y),obstacle))
                                if not self.piercing:
                                    try:
                                        lane=get_value('lanes')
                                        lane[self.lane-1]['zombies'].remove(self)
                                        set_value('lanes',lane)
                                        self.kill()
                                    except:
                                        self.kill()
                                        self.image=get_value('images')['nuthing.png'][tuple()]
                                break
                if self.side==1:
                    target=get_value('zombies')
                else:
                    target=get_value('plants')
                for obstacle in target:
                    if (not obstacle.unselected or self.hit_unselectable) and (not 'little' in obstacle.traits or self.hit_little):
                        if self.kind == 'fume':
                            if self.rect.colliderect(obstacle.rect) and ((not self.limited) or self.lane==obstacle.lane):
                                if not self in obstacle.fumes:
                                    obstacle.fumes.append(self)
                                    obstacle.damage(self.dmg,dmg_type=self.dmg_type,missle_kind=self.kind)
                                    sounds.play(self.sound, self.volumn)
                                    continue
                                else:
                                    continue
                            else:
                                continue
                        else:
                            try:
                                if self.rect.colliderect(obstacle.rect) and ((not self.limited) or self.lane==obstacle.lane):
                                    hit_again=False
                                    if self.hit_again:
                                        if obstacle in self.hits:
                                            if self.hit_cds[self.hits.index(obstacle)]<=0:
                                                hit_again=True
                                    if not obstacle in self.hits or hit_again:
                                        obstacle.damage(self.dmg,dmg_type=self.dmg_type,missle_kind=self.kind)
                                        self.on_hit(obstacle, 'zombie')
                                        if self.hit_again:
                                            if not obstacle in self.hits:
                                                self.hit_cds.append(self.hit_cd)
                                            else:
                                                self.hit_cds[self.hits.index(obstacle)]=self.hit_cd
                                        if not obstacle in self.hits:
                                            self.hits.append(obstacle)

                                        sounds.play(self.sound, self.volumn)
                                        if self.particle:
                                            get_value('particles_0').add(
                                            self.particle((self.x-20, self.y),obstacle))
                                        #splash dmg
                                        if self.dmg_type=='electric':
                                            for zombie in get_value('zombies'):
                                                if self.distance_to_zombie(zombie)<=100:
                                                    zombie.damage(0.3*self.dmg,self.dmg_type,self.kind)
                                                    self.on_hit(zombie,'zombie')
                                        self.hitted=True
                                        self.zombie=None
                                    if not self.piercing:
                                        self.done=True
                                        lane=get_value('lanes')
                                        if self in lane[self.lane-1]['zombies']:
                                            lane[self.lane-1]['zombies'].remove(self)
                                        set_value('lanes',lane)
                                        self.kill()
                                    
                                        return
                            except:
                                pass
        self.fps+=1

    def collide_with(self, x):
        return pygame.sprite.collide_mask(self,x)
    def on_hit(self,target,kind):
        pass
    def distance_to_zombie(self,zombie):
        if zombie.move_state=='air':
            return (abs(self.x-zombie.rect[0])**2+abs(self.y-zombie.rect[2])**2)**0.5
        return (abs(self.x-zombie.x)**2+abs(self.y-zombie.y)**2)**0.5
    def new_target(self,how):
        if how=='distance':
            if self.fps % 10 == 0:
                self.nearest_dist = 9999
                for zombie in get_value('zombies'):
                    if not zombie.effect['unselectable']>=0:
                        if self.distance_to_zombie(zombie) <= self.nearest_dist:
                            self.zombie = zombie
                            self.nearest_dist = self.distance_to_zombie(zombie)
                            return self.zombie
                self.zombie=None
                return 0
        elif how=='random':
            self.zombie=random.choice(get_value('zombies').sprites())
class Pea(Missle):
    def __init__(self,pos,show,mother,kind='straight',dest_x=0):
        super().__init__(r'pea.png',kind,(12,0),20,1,pos,show,'pea_hit',PeaSplat,mother,'physical',dest_x=dest_x)
        self.level=0
        self.family=[Pea,FirePea,BlueFirePea,RedFirePea,BlackFirePea]
        self.element='physical'
class Paper(Missle):
    def __init__(self,pos,show,mother,kind='straight'):
        super().__init__(r'paper_bullet.png',kind,(-12,-0.05),30,2,pos,show,'pea_hit',None,mother,'physical',size=None)
        self.level=0
        self.family=[Paper]
        self.element='physical'
        self.og_y=self.y

    def update(self,screen):
        super().update(screen)
        if self.velocity[1]<=4:
            self.velocity=(self.velocity[0],self.velocity[1]+0.15)
        if self.y>=self.og_y+100:
            self.done=True
            lane=get_value('lanes')
            if self in lane[self.lane-1]['zombies']:
                lane[self.lane-1]['zombies'].remove(self)
            set_value('lanes',lane)
            self.kill()
class GhostArrow(Missle):
    def __init__(self,pos,show,mother,kind='straight'):
        super().__init__(r'ghost_arrow.png',kind,(-10,0),40,2,pos,show,'ghost_appear',GhostHit,mother,'poison',size=None)
        self.level=0
        self.family=[GhostArrow]
        self.limited=True
        self.element='poison'
        self.hit_little=False
    def on_hit(self, target, kind):
        if kind == 'zombie':
            target.effect['unselectable']=750
class NormalArrow(Missle):
    def __init__(self,pos,show,mother,kind='straight'):
        super().__init__(r'normal_arrow.png',kind,(-15,0),80,2,pos,show,'pea_hit',None,mother,'physical',size=None)
        self.level=0
        self.family=[NormalArrow]
        self.limited=True
        self.element='physical'
        self.hit_little=False
class FireArrow(Missle):
    def __init__(self,pos,show,mother,kind='straight'):
        super().__init__(r'fire_arrow.png',kind,(-17,0),40,2,pos,show,'fire',None,mother,'fire',size=None)
        self.level=0
        self.family=[FireArrow]
        self.limited=True
        self.element='fire'
        self.hit_little=False
    def on_hit(self, target, kind):
        if kind == 'zombie':
            if target.effect['overheat']<100:
                target.effect['overheat']=100
class IceArrow(Missle):
    def __init__(self,pos,show,mother,kind='straight'):
        super().__init__(r'ice_arrow.png',kind,(-13,0),60,2,pos,show,'snowpea_hit',None,mother,'ice',size=None)
        self.level=0
        self.family=[IceArrow]
        self.limited=True
        self.element='ice'
        self.hit_little=False
    def on_hit(self, target, kind):
        if kind == 'zombie':
            if target.effect['chilled']<500:
                target.effect['chilled']=500
class GhostBeam(Missle):
    def __init__(self,pos,show,mother,kind='straight'):
        super().__init__(r'ghost_beam.png',kind,(0,0),200,2,pos,show,'ghost_beam',GhostHit,mother,'poison',size=None,piercing=True)
        self.life=40
        self.limited=True
        self.hit_unselectable=True
    def on_hit(self, target, kind):
        if kind == 'zombie':
            self.mother.max_hp+=50
            self.mother.heal(99999)
class PowerflowerBeam(Missle):
    def __init__(self,pos,show,mother,kind='straight'):
        super().__init__(r'powerflower_beam.png',kind,(0,0),50,1,pos,show,'pea_hit',TheEmperorsNewParticle,mother,'holy',size=None,piercing=True)
        self.life=115
        self.limited=True
        self.hit_again=True
        self.hit_cd=25
    def on_hit(self, target, kind):
        if kind == 'zombie':
            self.mother.hit()
class Pear(Missle):
    def __init__(self,pos,show,mother,kind='straight'):
        super().__init__(r'pear_seed.png',kind,(15,0),5,1,pos,show,'pear_hit',TheEmperorsNewParticle,mother,'physical',size=None,volumn=0.05)
        self.element='physical'
        self.level=0
        self.family=[Pear,FirePear]
class FirePear(Missle):
    def __init__(self,pos,show,mother,kind='straight'):
        super().__init__(r'fire_pear_seed.png',kind,(15,0),6,1,pos,show,'pear_hit',FireSplat,mother,'fire',size=None)
        self.element='physical'
        self.level=1
        self.family=[Pear,FirePear]
    def on_hit(self, target, kind):
        if kind == 'zombie':
            for zombie in get_value('zombies'):
                if zombie.lane==target.lane and abs(zombie.x-target.x)<=25 and zombie.x<=840:
                    zombie.damage(2,'fire','fume')
                    zombie.x+=0.6

class GiantPea(Missle):
    def __init__(self,pos,show,mother,kind='straight'):
        super().__init__(r'giant_pea.png',kind,(15,0),100,1,pos,show,'pea_hit',PeaSplat,mother,'physical',size=None)
        self.element='physical'
        self.level=0
        self.family=[GiantPea,FireGiantPea]
        self.limited=True
    def on_hit(self, target, kind):
        if kind == 'zombie':
            for zombie in get_value('zombies'):
                if zombie.lane==target.lane and abs(zombie.x-target.x)<=35 and zombie.x<=840:
                    zombie.x+=20
class FireGiantPea(Missle):
    def __init__(self,pos,show,mother,kind='straight'):
        super().__init__(r'fire_giant_pea.png',kind,(15,0),150,1,pos,show,'fire',FireSplat,mother,'fire',size=None)
        self.element='physical'
        self.level=1
        self.family=[GiantPea,FireGiantPea]
        self.limited=True
    def on_hit(self, target, kind):
        if kind == 'zombie':
            for zombie in get_value('zombies'):
                if zombie.lane==target.lane and abs(zombie.x-target.x)<=45 and zombie.x<=820:
                    zombie.damage(60,'fire','fume')
                    zombie.x+=40
class IcePea(Missle):
    def __init__(self,pos,show,mother,kind='straight'):
        super().__init__(r'snow_pea.png',kind,(11,0),20,1,pos,show,'snowpea_hit',SnowpeaSplat,mother,'ice')
        self.element='ice'
        self.level=0
        self.family=[IcePea,IceFirePea,FrostPea,GhostFirePea]
    def on_hit(self, target, kind):
        if kind == 'zombie':
            if not target.chilled:
                target.chilled=True
                target.chills=True,800
class IceFirePea(Missle):
    def __init__(self,pos,show,mother,kind='straight'):
        super().__init__(r'blue_fire_pea.png',kind,(11,0),30,1,pos,show,'snowpea_hit',BlueFireSplat,mother,'fire',size=False)
        self.level=1
        self.family=[IcePea,IceFirePea,FrostPea,GhostFirePea]
        self.element='ice'

    def on_hit(self, target, kind):
        if kind == 'zombie':
            for zombie in get_value('zombies'):
                if zombie.lane==target.lane and abs(zombie.x-target.x)<=30:
                    zombie.damage(10,'ice','fume')
                    if not zombie.chilled:
                        zombie.chilled=True
                        zombie.chills=True,800
class FrostPea(Missle):
    def __init__(self,pos,show,mother,kind='straight'):
        super().__init__(r'frost_pea.png',kind,(11,0),50,1,pos,show,'snowpea_hit',BlueFireSplat,mother,'fire',size=False)
        self.level=2
        self.family=[IcePea,IceFirePea,FrostPea,GhostFirePea]
        self.element='ice'

    def on_hit(self, target, kind):
        if kind == 'zombie':
            for zombie in get_value('zombies'):
                if zombie.lane==target.lane and abs(zombie.x-target.x)<=37.5:
                    zombie.damage(20,'ice','fume')
                    if not zombie.chilled:
                        zombie.chilled=True
                        zombie.chills=True,800
                    if not target.frozen:
                        zombie.frozen=True
                        zombie.freezes=(True,25)
class GhostFirePea(Missle):
    def __init__(self,pos,show,mother,kind='straight'):
        super().__init__(r'ghost_fire_pea.png',kind,(11,0),70,1,pos,show,'snowpea_hit',BlueFireSplat,mother,'fire',size=False)
        self.level=3
        self.family=[IcePea,IceFirePea,FrostPea,GhostFirePea]
        self.element='ice'

    def on_hit(self, target, kind):
        if kind == 'zombie':
            for zombie in get_value('zombies'):
                if zombie.lane==target.lane and abs(zombie.x-target.x)<=45:
                    zombie.damage(30,'ice','fume')
                    if not zombie.chilled:
                        zombie.chilled=True
                        zombie.chills=True,800
                    if not target.frozen:
                        zombie.frozen=True
                        zombie.freezes=(True,75)
class FirePea(Missle):
    def __init__(self,pos,show,mother,kind='straight'):
        super().__init__(r'fire_pea.png',kind,(13,0),40,1,pos,show,'fire',FireSplat,mother,'fire',size=False)
        self.level=1
        self.family=[Pea,FirePea,BlueFirePea,RedFirePea,BlackFirePea]
        self.element='fire'
        self.limited=True

    def on_hit(self, target, kind):
        if kind == 'zombie':
            for zombie in get_value('zombies'):
                if not zombie==target and zombie.lane==target.lane and abs(zombie.x-target.x)<=30:
                    zombie.damage(15,'fire','fume')
class BlueFirePea(Missle):
    def __init__(self,pos,show,mother,kind='straight'):
        super().__init__(r'blue_fire_pea.png',kind,(13,0),60,1,pos,show,'fire',BlueFireSplat,mother,'fire',size=False)
        self.level=1
        self.family=[Pea,FirePea,BlueFirePea,RedFirePea,BlackFirePea]
        self.element='fire'

    def on_hit(self, target, kind):
        if kind == 'zombie':
            for zombie in get_value('zombies'):
                if not zombie==target and zombie.lane==target.lane and abs(zombie.x-target.x)<=37.5:
                    zombie.damage(30,'fire','fume')
class Icymint(Missle):
    def __init__(self,pos,show,mother,kind='straight'):
        super().__init__(r'icymint.png',kind,(11,0),30,1,pos,show,'snowpea_hit',SnowpeaSplat,mother,'ice',size=False)
        self.level=0
        self.family=[Icymint,IcePepperMint,FrostPepperMint,GhostPepperMint]
        self.element='ice'

    def on_hit(self, target, kind):
        get_value('particles_-1').add(Icy((target.column*90-90,target.lane*90-90),25))
        if kind == 'zombie':
            if not target.chilled:
                target.chilled=True
                target.chills=True,1000
            if not target.frozen:
                target.frozen=True
                target.freezes=(True,60)
        for z in get_value('zombies'):
            if abs(z.lane-target.lane)<=1 and abs(z.column-target.column)<=1 and not z==target:
                z.damage(10,'ice','fume')
                if not z.chilled:
                    z.chilled=True
                    z.chills=True,1000
class Peppermint(Missle):
    def __init__(self,pos,show,mother,kind='straight'):
        super().__init__(r'peppermint.png',kind,(13,0),80,1,pos,show,'fire',FireSplat,mother,'fire',size=False)
        self.level=0
        self.family=[Peppermint,IcePepperMint,FrostPepperMint,GhostPepperMint]
        self.element='fre'

    def on_hit(self, target, kind):
        get_value('particles_-1').add(Pepper((target.column*90-90,target.lane*90-90),25))
        for z in get_value('zombies'):
            if abs(z.lane-target.lane)<=1 and abs(z.column-target.column)<=1 and not z==target:
                z.damage(40,'fire','fume')
class IcePepperMint(Missle):
    def __init__(self,pos,show,mother,kind='straight'):
        super().__init__(r'icypep.png',kind,(11,0),40,1,pos,show,'snowpea_hit',SnowpeaSplat,mother,'fire',size=False)
        self.level=1
        self.family=[Icymint,IcePepperMint,FrostPepperMint,GhostPepperMint]
        self.element='fire'

    def on_hit(self, target, kind):
        get_value('particles_-1').add(Icy((target.column*90-90,target.lane*90-90),25))
        get_value('particles_-1').add(Pepper((target.column*90-90,target.lane*90-90),25))
        if kind == 'zombie':
            if not target.chilled:
                target.chilled=True
                target.chills=True,1000
            if not target.frozen:
                target.frozen=True
                target.freezes=(True,150)
        for z in get_value('zombies'):
            if abs(z.lane-target.lane)<=1 and abs(z.column-target.column)<=1 and not z==target:
                z.damage(20,'ice','fume')
                if not z.chilled:
                    z.chilled=True
                    z.chills=True,1000
                if not z.frozen:
                    target.frozen=True
                    target.freezes=(True,75)
class FrostPepperMint(Missle):
    def __init__(self,pos,show,mother,kind='straight'):
        super().__init__(r'frostpep.png',kind,(11,0),60,1,pos,show,'snowpea_hit',SnowpeaSplat,mother,'fire',size=False)
        self.level=2
        self.family=[Icymint,IcePepperMint,FrostPepperMint,GhostPepperMint]
        self.element='fire'

    def on_hit(self, target, kind):
        get_value('particles_-1').add(Icy((target.column*90-90,target.lane*90-90),25))
        get_value('particles_-1').add(Pepper((target.column*90-90,target.lane*90-90),25))
        if kind == 'zombie':
            if not target.chilled:
                target.chilled=True
                target.chills=True,1000
            if not target.frozen:
                target.frozen=True
                target.freezes=(True,250)
        for z in get_value('zombies'):
            if abs(z.lane-target.lane)<=1 and abs(z.column-target.column)<=1 and not z==target:
                z.damage(30,'ice','fume')
                if not z.chilled:
                    z.chilled=True
                    z.chills=True,1000
                if not z.frozen:
                    target.frozen=True
                    target.freezes=(True,150)
class GhostPepperMint(Missle):
    def __init__(self,pos,show,mother,kind='straight'):
        super().__init__(r'ghostpep.png',kind,(11,0),80,1,pos,show,'snowpea_hit',SnowpeaSplat,mother,'fire',size=False)
        self.level=3
        self.family=[Icymint,IcePepperMint,FrostPepperMint,GhostPepperMint]
        self.element='fire'

    def on_hit(self, target, kind):
        get_value('particles_-1').add(Icy((target.column*90-90,target.lane*90-90),25))
        get_value('particles_-1').add(Pepper((target.column*90-90,target.lane*90-90),25))
        if kind == 'zombie':
            if not target.chilled:
                target.chilled=True
                target.chills=True,1000
            if not target.frozen:
                target.frozen=True
                target.freezes=(True,250)
        for z in get_value('zombies'):
            if abs(z.lane-target.lane)<=1 and abs(z.column-target.column)<=1 and not z==target:
                z.damage(60,'fire','fume')
                if not z.chilled:
                    z.chilled=True
                    z.chills=True,1000
                if not z.frozen:
                    target.frozen=True
                    target.freezes=(True,150)
class Sweet(Missle):
    def __init__(self,pos,show,mother,kind='straight'):
        super().__init__(r'sweet.png',kind,(13,0),40,1,pos,show,'pear_hit',SweetSplat,mother,'physical',size=False)
        self.level=0
        self.family=[Sweet]
        self.element='physical'
    def on_hit(self, target, kind):
        get_value('particles_-1').add(Sweeet((target.column*90-90,target.lane*90-90),25))
        if kind == 'zombie':
            if target.stop_timer==0:
                target.stop_timer=75
        for z in get_value('zombies'):
            if abs(z.lane-target.lane)<=1 and abs(z.column-target.column)<=2 and not z==target:
                z.switch_lane(self.lane,10)
class RedFirePea(Missle):
    def __init__(self,pos,show,mother,kind='straight'):
        super().__init__(r'red_fire_pea.png',kind,(13,0),60,1,pos,show,'fire',FireSplat,mother,'fire',size=False)
        self.level=3
        self.family=[Pea,FirePea,BlueFirePea,RedFirePea,BlackFirePea]
        self.element='fire'

    def on_hit(self, target, kind):
        if kind == 'zombie':
            for zombie in get_value('zombies'):
                if not zombie==target and zombie.lane==target.lane and abs(zombie.x-target.x)<=37.5:
                    zombie.damage(40,'fire','fume')
class BlackFirePea(Missle):
    def __init__(self,pos,show,mother,kind='straight'):
        super().__init__(r'black_fire_pea.png',kind,(13,0),80,1,pos,show,'fire',BlackFireSplat,mother,'fire',size=False)
        self.level=4
        self.family=[Pea,FirePea,BlueFirePea,RedFirePea,BlackFirePea]
        self.element='fire'

    def on_hit(self, target, kind):
        if kind == 'zombie':
            for zombie in get_value('zombies'):
                if not zombie==target and zombie.lane==target.lane and abs(zombie.x-target.x)<=45:
                    zombie.damage(60,'fire','fume')
class IceArrow_(Missle):
    def __init__(self,pos,show,mother,kind='straight'):
        super().__init__(r'ice_arrow.png',kind,(11,0),40,1,pos,show,'snowpea_hit',SnowpeaSplat,mother,'ice',size=None)

    def on_hit(self, target, kind):
        if kind == 'zombie':
            if not target.chilled:
                target.chilled=True
                target.chills=True,800
            if not target.frozen:
                target.frozen=True
                target.freezes=(True,150)
class Snowball(Missle):
    def __init__(self,pos,show,mother,kind='straight'):
        super().__init__(r'snowball.png',kind,(9,0),40,1,pos,show,'snowpea_hit',SnowpeaSplat,mother,'ice',size=None,piercing=True)
        

    def on_hit(self, target, kind):
        if kind == 'zombie':
            if not target.chilled:
                target.chilled=True
                target.chills=True,1000
            if not target.frozen:
                target.frozen=True
                target.freezes=(True,125)
class Spore(Missle):
    def __init__(self, pos, show,mother,kind='straight'):
        super().__init__(r'spore.png', kind, (10,0),
                         20, 1, pos, show, 'spore_hit', None, mother, 'poison', 6)
        self.element='poison'
        self.level=0
        self.family=[Spore,SuperSpore]
class SuperSpore(Missle):
    def __init__(self, pos, show,mother,kind='straight'):
        super().__init__(r'spore.png', kind, (10,0),
                         40, 1, pos, show, 'spore_hit', None, mother, 'poison', 12)
        self.element='poison'
        self.level=1
        self.family=[Spore,SuperSpore]

    def on_hit(self, target, kind):
        if kind == 'zombie':
            target.effect['fungus']=1000


class Fume(Missle):
    def __init__(self, pos, show=0,mother=None,kind='fume'):
        super().__init__(r'ugly_purple_fume.png', 'fume', (0,0),
                         35, 1, pos, show, 'spore_hit', None, mother, 'poison', 6)
        self.image = pygame.transform.scale(get_value('images')['ugly_purple_fume.png'][tuple()], (90,5))
        self.next_timer=0
        self.disappear_timer=10
        self.newed=False
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect()
    def update(self, screen):
        super().update(screen)
        self.next_timer-=1
        self.disappear_timer-=1
        if self.disappear_timer<=0:
            lane=get_value('lanes')                            
            if self in lane[self.lane-1]['zombies']:
                lane[self.lane-1]['zombies'].remove(self)
            set_value('lanes',lane)
            self.kill()
        if not self.newed:
            if self.next_timer <= 0:
                if (self.x-20)//90<=10:
                    get_value('missles').add(Fume((self.x+90,self.y),89,self))
                    self.newed=True


class Milk(Missle):
    def __init__(self, pos, show,mother,kind='straight'):
        super().__init__(r'milk.png', kind,
                         (24,0), -100, 1, pos, show, 'butter', MilkSplat, mother,'poison',size=30)
        self.level=0
        self.family=[Milk,Lava]
        self.element='physical'
    def on_hit(self, target,kind):
        target.full_hp += 50
        target.hp+=50
        target.milked+=1
        sounds.play('grow',0.5)
        if kind == 'zombie':
            target.milks=True
        else:
            get_value('particles_0').add(MilkHeal((target.x, target.y),20,target))
class Lava(Missle):
    def __init__(self,pos,show,mother,kind='straight'):
        super().__init__(r'lava.png',kind,(24,0),5,1,pos,show,'fire',FireSplat,mother,'fire',size=30)
        self.level=1
        self.family=[Milk,Lava]
        self.element='fire'

    def on_hit(self, target, kind):
        if not find_layer('lava',[target.column,target.lane])>=5:
            get_value('tile_modifiers').append(['lava',[target.column,target.lane],250,1])
        if kind == 'zombie':
            for zombie in get_value('zombies'):
                if zombie.lane==target.lane and abs(zombie.x-target.x)<=55:
                    zombie.damage(5,'fire','fume')
                    zombie.effect['overheat']=21
                    if kind == 'zombie':
                        target.milks=True
class LavaDrop(Missle):
    def __init__(self,pos,show,mother,kind='straight'):
        super().__init__(r'lava_droplet.png',kind,(24,0),8,1,pos,show,'fire',FireSplat,mother,'fire',size=None)
        self.level=1
        self.family=[LavaDrop]
        self.element='fire'

    def on_hit(self, target, kind):
        if not find_layer('lava',[target.column,target.lane])>=5:
            get_value('tile_modifiers').append(['lava',[target.column,target.lane],50,1])
        if kind == 'zombie':
            if target.effect['overheat']>=0:
                target.effect['overheat']+=6
            else:
                target.effect['overheat']=26


class Sting(Missle):
    def __init__(self, pos, show,mother,kind='straight'):
        super().__init__(r'sting.png', kind,
                         (9,0), 30, 1, pos, show, 'sting_hit',TheEmperorsNewParticle,mother, 'physical', size=None)
class CatMissle(Missle):
    def __init__(self, pos, show,mother,kind='straight'):
        super().__init__(r'cat_missle.png', kind,
                         (18,0), 300, 1, pos, show, 'explode',TheEmperorsNewParticle,mother, 'electric', size=None)

    def on_hit(self,target,kind):
        if kind=='zombie' and not self.done:
            target.stop_timer+=200
            get_value('particles_0').add(CatExplode((target.x-135,target.y-135),target))
            for zombie in get_value('zombies'):
                if zombie!=target:
                    if abs(zombie.x-target.x)<=135 and abs(zombie.y-target.y)<=135:
                        zombie.stop_timer+=100
                        zombie.damage(100,'electric','homing')
class ElectricSting(Missle):
    def __init__(self, pos, show,mother,kind='straight'):
        super().__init__(r'electric_sting.png', kind,
                         (10,0), 30, 1, pos, show, 'electric_hit', TheEmperorsNewParticle,mother, 'electric', size=None,piercing=True,volumn=0.05)

    def on_hit(self, target, kind):
        if kind == 'zombie':
            if target.stop_timer==0:
                target.stop_timer=30
#constants
LEGAL_MISSLES=[Pea,Pear,IcePea,FirePea,RedFirePea,IceArrow_,Snowball,Spore,Milk,Sting,ElectricSting,CatMissle,Fume]
MISSLES_WITH_LEVELS={Pea:5,Pear:6,IcePea:4,FirePea:4,RedFirePea:3,IceArrow_:3,
                     Snowball:3,Spore:5,Milk:4,Sting:4,ElectricSting:3,CatMissle:1,Fume:3,
                     Lava:4,LavaDrop:5,SuperSpore:4,BlackFirePea:2,Sweet:2,GhostPepperMint:1,FrostPepperMint:1,
                     BlueFirePea:3,IcePepperMint:1,Peppermint:2,Icymint:2,FirePear:4}
print(list(MISSLES_WITH_LEVELS.values()))
N=1/sum(list(MISSLES_WITH_LEVELS.values()))
MISSLES_WITH_CHANCES=dict()
for missle in MISSLES_WITH_LEVELS:
    MISSLES_WITH_CHANCES[missle]=MISSLES_WITH_LEVELS[missle]*N

def find_layer(effect,tile):
    #find the number of a specific effect on a certain tile
    cnt=0
    for tile in get_value('tile_modifiers'):
        if tile[1]==tile and tile[1]==effect:
            cnt+=1
    return cnt
