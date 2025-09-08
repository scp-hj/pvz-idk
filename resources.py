import pygame,sys,os
from config import *
import sounds
from filter import *
import random
def rp(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)
class Resource(pygame.sprite.Sprite):
    def __init__(self,images,location,destination,speed,effect='rotate',disappear=True,collect_sound='sun',size=1,duration=25,sound_volume=1):
        super().__init__()
        images=[loady(rp(image)) for image in images]
        x,y=int(images[0].get_rect()[2]*size),int(images[0].get_rect()[3]*size)
        self.images=[pygame.transform.scale(image,(x,y)) for image in images]
        self.destination=destination
        self.effect='rotate'
        self.x,self.y=location
        self.cnt=0
        self.speed=speed
        self.duration=duration
        self.sound_volume=sound_volume
        self.costume_duration,self.duration=int(duration*random.random()),duration
        self.costume_id=0
        coefficient=self.speed*(1/(abs(self.destination[0]-self.x)+abs(self.destination[1]-self.y)))
        self.xspeed=(self.destination[0]-self.x)*coefficient
        self.yspeed=(self.destination[1]-self.y)*coefficient
        self.rect = self.images[0].get_rect(
            center=(self.x+self.images[0].get_width()//2, self.y+self.images[0].get_height()//2))
        self.effect=effect
        self.angle=0
        self.collected=False
        self.sound=collect_sound
        if disappear:
            self.disappear_cnt=10
        else:
            self.disappear_cnt=99999999999999
    def update(self,screen,events=None,*args,**kwargs):
        self.cnt+=get_value('equivalent_frame')
        events=get_value('events')
        if self.cnt>=75 and not self.collected:
            self.on_collect()
        if self.effect=='rotate':
            self.angle+=3*get_value('equivalent_frame')
        if abs(self.x-self.destination[0]) > 20 or abs(self.y-self.destination[1]) > 20:
            self.x+=self.xspeed*get_value('equivalent_frame')
            self.y+=self.yspeed*get_value('equivalent_frame')
        elif self.collected:
            self.on_received()
        self.rect = self.images[0].get_rect(
            center=(self.x+get_value('pos_shift')[0]+self.images[0].get_width()//2, self.y+get_value('pos_shift')[1]+self.images[0].get_height()//2))
        if self.effect=='rotate':
            new_image=pygame.transform.rotate(self.images[self.costume_id],self.angle)
            new_rect = new_image.get_rect(center=self.rect.center)
            blity(new_image,new_rect,True)
        else:
            blity(self.images[self.costume_id],(self.x,self.y),True)
            
        self.disappear_cnt-=get_value('dt')
        self.costume_duration-=get_value('equivalent_frame')
        if self.costume_duration<=0:
            self.costume_id+=1
            self.costume_duration=self.duration
            if self.costume_id>=len(self.images):
                self.costume_id=0
        if self.disappear_cnt<=0:
            self.kill()
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(get_pos()) and not self.collected and not get_value('planting'):
                self.on_collect()
        self.rect=self.images[0].get_rect(center=(self.x+self.images[0].get_width()//2,self.y+self.images[0].get_height()//2))
    def add_new_location(self,pos):
        self.destination = pos
        coefficient=self.speed*(1/(abs(self.destination[0]-self.x)+abs(self.destination[1]-self.y)))
        self.xspeed=(self.destination[0]-self.x)*coefficient
        self.yspeed=(self.destination[1]-self.y)*coefficient
        self.rect = self.images[0].get_rect(
            center=(self.x+self.images[0].get_width()//2, self.y+self.images[0].get_height()//2))
        if self.y>self.destination[1]:
            self.yspeed=-abs(self.yspeed)
        if self.x>self.destination[0]:
            self.xspeed=-abs(self.xspeed)
    def on_collect(self):
        sounds.play(self.sound,self.sound_volume)
        self.collected=True
    def on_received(self):
        self.kill()
class Sun(Resource):
    def __init__(self,location,destination):
        super().__init__(['images/sun.png'],location,destination,16)
    def on_collect(self):
        super().on_collect()
        self.add_new_location((20,20))
    def on_received(self):
        super().on_received()
        set_value('sun',get_value('sun')+25)
        

class SmallSun(Resource):
    def __init__(self, location, destination):
        super().__init__(['images/sun.png'], location, destination, 20,size=0.6)

    def on_collect(self):
        self.xspeed=-8
        super().on_collect()
        self.add_new_location((20, 20))

    def on_received(self):
        super().on_received()
        set_value('sun', get_value('sun')+15)

class BigSun(Resource):
    def __init__(self, location, destination):
        super().__init__(['images/sun.png'], location, destination, 12,size=1.5)

    def on_collect(self):
        self.xspeed=-8
        super().on_collect()
        self.add_new_location((20, 20))

    def on_received(self):
        super().on_received()
        set_value('sun', get_value('sun')+50)

class SunPiece(Resource):
    def __init__(self, location, destination):
        super().__init__(['images/sun.png'], location, destination, 20,size=0.25,sound_volume=0.01)

    def on_collect(self):
        self.xspeed=-8
        super().on_collect()
        self.add_new_location((20, 20))

    def on_received(self):
        super().on_received()
        set_value('sun', get_value('sun')+5)
class Coin(Resource):
    def __init__(self,location,destination,value):#copper-1 silver-4 gold - 10 legendary - 69
        if value==1:
            image='copper_coin_'+str(random.randint(0,3))
        elif value==4:
            image='silver_coin_'+str(random.randint(0,3))
        elif value==10:
            image='gold_coin_'+str(random.randint(0,2))
        elif value==69:
            image='legendary_coin_0'
        super().__init__(['images/'+image+'.png','images/'+image[:-1]+'flip.png'],location,destination,25,effect=None,collect_sound='coin',disappear=False)
        self.value=value
    def on_collect(self):
        super().on_collect()
        self.add_new_location((20,600))
    def on_received(self):
        super().on_received()
        set_value('money',get_value('money')+self.value)
