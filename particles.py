import pygame,os,sys
from time import *
from PIL import Image
import cv2 as cv
import numpy
from config import *
import random
from filter import *
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


def rp(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


class Particle(pygame.sprite.Sprite):
    def __init__(self,image,pos,duration,target,down=False,free=False,show=True,mother=None):
        super().__init__()
        self.image=get_value('images')[image][tuple()]
        self.pos=pos
        self.cnt, self.duration = 0, duration
        if not free:
            self.lane=target.lane
        self.free=free
        self.show=show
        self.mother=mother
        try:
            if not self.free:
                if get_value('state') != 'loading':
                    lane = get_value('lanes')
                    for key in ['obstacles','plants','zombies']:
                        if target in lane[self.lane-1][key]:
                            l=lane[self.lane-1][key]
                            inde=l.index(target)
                            if not down:
                                inde+=1
                            l.insert(inde,self)
                            lane[self.lane-1][key] = l
                            break
                    set_value('lanes', lane)
        except:
            pass

    def update(self, screen):
        self.cnt+=get_value('equivalent_frame')
        #blity(self.image,self.pos)
        if self.cnt>=self.duration:
            self.on_end()
            self.kill()
        if self.free:
            self.display()
    def display(self):
        if self.show:
            blity(self.image, self.pos)

    def on_end(self):
        try:
            if not self.free:
                lane = get_value('lanes')
                for key in ['plants','obstacles','zombies']:
                    if self in lane[self.lane-1][key]:
                        lane[self.lane-1][key].remove(self)
                        break
                set_value('lanes', lane)
            if self.mother:
                self.mother.particles.remove(self)
        except:
            pass




#particles used in a level
class Ready(Particle):
    def __init__(self):
        super().__init__('ready.png',(325,270),25,None,free=True)
    def on_end(self):
        get_value('particles_-2').add(Set())
        super().on_end()
class Set(Particle):
    def __init__(self):
        super().__init__('set.png',(325,270),25,None,free=True)
    def on_end(self):
        get_value('particles_-2').add(Go())
        super().on_end()
class Go(Particle):
    def __init__(self):
        super().__init__('get_rekt.png',(325,270),25,None,free=True)

class HugeWave(Particle):
    def __init__(self):
        super().__init__('huge_wave.png',(250,270),50,None,free=True)

class FinalWave(Particle):
    def __init__(self):
        super().__init__('final_wave.png',(250,270),75,None,free=True)

class HYNDZ(Particle):
    def __init__(self,pos):
        super().__init__('hyn,dz!.png',pos,50,None,free=True)
class QZNS(Particle):
    def __init__(self,pos):
        super().__init__('wq,yqznsl.png',pos,1,None,free=True)
        
class UglyDirt(Particle):
    def __init__(self,pos,target):
        super().__init__(r'ugly_dirt.png',pos,10,target,True)
class GraveDirt(Particle):
    def __init__(self,pos,target):
        super().__init__(r'grave_die.png',pos,10,target)
class Crack(Particle):
    def __init__(self,pos):
        super().__init__(r'crack.png',pos,50,None,free=True)

class PeaSplat(Particle):
    def __init__(self, pos,target):
        super().__init__(r'pea_splat.png', pos, 10,target)


class SnowpeaSplat(Particle):
    def __init__(self, pos,target):
        super().__init__(r'snowpea_splat.png', pos, 10,target)
class FireSplat(Particle):
    def __init__(self, pos,target):
        super().__init__(r'fire_splat.png', pos, 10,target)
class BlueFireSplat(Particle):
    def __init__(self, pos,target):
        super().__init__(r'blue_fire_splat.png', pos, 10,target)
class BlackFireSplat(Particle):
    def __init__(self, pos,target):
        super().__init__(r'black_fire_splat.png', pos, 10,target)

class MilkSplat(Particle):
    def __init__(self, pos,target):
        super().__init__(r'milk_splat.png', (pos[0]-10,pos[1]), 10,target)
class SweetSplat(Particle):
    def __init__(self, pos,target):
        super().__init__(r'sweet_splat.png', (pos[0]-10,pos[1]), 10,target)
class CatExplode(Particle):
    def __init__(self, pos,target):
        super().__init__(r'cat_explode.png', (pos[0],pos[1]), 25,target)
class GhostHit(Particle):
    def __init__(self, pos,target):
        super().__init__(r'ghost_arrow_particle.png', (pos[0]-20,pos[1]), 20,target)
        
class Frozen(Particle):
    def __init__(self, pos,duration,target):
        super().__init__(r'iced.png', (pos[0], pos[1]), duration,target,show=False,mother=target)

class MilkHeal(Particle):
    def __init__(self, pos,duration,target):
        super().__init__(r'milk_heal.png',pos, duration,target)
class Heal(Particle):
    def __init__(self, pos,duration,target):
        super().__init__(r'heal.png',pos, duration,target)

class Clash(Particle):
    def __init__(self,pos,target):
        super().__init__('clash.png',pos,25,target)

class Spudow(Particle):
    def __init__(self, pos, duration):
        super().__init__(r'spudow.png', pos, duration,get_value('zombies').sprites()[-1])
class Cherry(Particle):
    def __init__(self, pos, duration):
        super().__init__(r'cherry_explosion.png', pos, duration,None,free=True)
class PlanternLight(Particle):
    def __init__(self, pos, size=270,angle=0,duration=1):
        super().__init__(r'plantern_light.png', pos,duration,None,free=True)
        self.image=pygame.transform.scale(get_value('images')['plantern_light.png'][tuple()],(size,size))
        self.image,self.pos=rotate(self.image,angle,[pos[0]+135,pos[1]+135],pygame.math.Vector2())
class Sweeet(Particle):
    def __init__(self, pos, duration):
        super().__init__(r'sweet_particle.png', pos, duration,None,free=True)
class Icy(Particle):
    def __init__(self, pos, duration):
        super().__init__(r'icy_particle.png', pos, duration,None,free=True)
class Pepper(Particle):
    def __init__(self, pos, duration):
        super().__init__(r'pepper_particle.png', pos, duration,None,free=True)
class Hot(Particle):
    def __init__(self, pos, duration):
        super().__init__(r'fried_duck_explode.png', pos, duration,None,free=True)
class Disco(Particle):
    def __init__(self, pos, duration):
        super().__init__(r'disco.png', pos, duration,None,free=True)
class Fog(Particle):
    def __init__(self, pos, duration):
        super().__init__(r'fog.png', pos, duration,None,free=True)
def fogs(pos,duration,density):
    for a in range(density):
        get_value('particles_-2').add(Fog((pos[0]+random.randint(-20,20),pos[1]+random.randint(-20,20)),duration+random.randint(-10,10)))
class Snow(Particle):
    def __init__(self, pos, duration):
        super().__init__(r'snow.png', pos, duration,None,free=True)
    def update(self,screen):
        super().update(screen)
        self.pos=(self.pos[0],self.pos[1]+5)
def snow(duration,density):
    for a in range(density):
        get_value('particles_-1').add(Snow((random.randint(0,800),random.randint(-300,600)),duration+random.randint(-10,10)))
class Chill(Particle):
    def __init__(self, pos, duration=10):
        super().__init__(r'chill_bro.png', pos, duration,get_value('zombies').sprites()[-1])

class Zzz(Particle):
    def __init__(self, pos, duration=10):
        super().__init__(r'zzz.png', pos, duration,get_value('zombies').sprites()[-1])
class TLZDie(Particle):
    def __init__(self, pos):
        super().__init__(r'TLZ_dead.png', pos, 20)
class TheEmperorsNewParticle(Particle):
    def __init__(self, pos,target):
        super().__init__(r'nuthing.png', pos, 20,target)
class FlagHeal(Particle):
    def __init__(self,pos,target):
        super().__init__(r'smol_heal.png',pos,5,target,free=True)
class FlagRevive(Particle):
    def __init__(self, pos,target):
        super().__init__(r'legendary_heal.png', pos, 5,target,free=True)
class FlagShield(Particle):
    def __init__(self, pos,target):
        super().__init__(r'smol_shield.png', pos, 1,target,free=True)


class FlagTurbo(Particle):
    def __init__(self, pos,target):
        super().__init__(r'smol_wind.png', pos, 1,target)


class FlagAggro(Particle):
    def __init__(self, pos,target):
        super().__init__(r'smol_sword.png', pos, 1,target)
class FlagDeadly(Particle):
    def __init__(self, pos,target):
        super().__init__(r'smol_skeleton.png', pos, 1,target)
class Intoxicated(Particle):
    def __init__(self, pos,target):
        super().__init__(r'intoxicated.png', pos, 1,target)
class Overheat(Particle):
    def __init__(self, pos,target):
        super().__init__(r'overheat.png', pos, 1,target,free=True)
class EffectPowerflower(Particle):
    def __init__(self, pos,target):
        super().__init__(r'effect_powerflower.png', pos, 1,target,free=True)
class Fungus(Particle):
    def __init__(self, pos,target):
        super().__init__(r'fungus.png', pos, 1,target)
class Graftable(Particle):
    def __init__(self, pos,target):
        super().__init__(r'grafting_upgrade.png', pos, 1,target,free=True)
class Fire(Particle):
    def __init__(self, pos,target):
        super().__init__(r'fire.png', pos, 1,target,free=True)
class Fire_(Particle):
    def __init__(self,pos):
        super().__init__('fire.png',pos,75,None,free=True)
class Randomness(Particle):
    def __init__(self, pos,target):
        super().__init__(r'randomness_fume.png', pos, 1,target,free=True)
class PowerFume(Particle):
    def __init__(self, pos,target):
        super().__init__(r'power_fume.png', pos, 25,target,free=True)
class HolyMantle(Particle):
    def __init__(self, pos,target):
        super().__init__(r'holy_mantle.png', pos, 1,target,free=True)
class FullShield(Particle):
    def __init__(self, pos,target):
        super().__init__(r'shield_0.png', pos, 1,target,free=True)
class HalfShield(Particle):
    def __init__(self, pos,target):
        super().__init__(r'shield_1.png', pos, 1,target,free=True)
class BrokeShield(Particle):
    def __init__(self, pos,target):
        super().__init__(r'shield_2.png', pos, 1,target,free=True)
class Confusion(Particle):
    def __init__(self, pos,target):
        super().__init__(r'wha.png', pos, 1,target)
class Shadow(Particle):
    def __init__(self, pos,target):
        super().__init__(r'shadow.png', pos, 1,None,free=True)
class Glitched(Particle):
    def __init__(self, pos,target):
        super().__init__(r'glitched.png', pos, 10,target)
class Report(Particle):
    def __init__(self, pos,target):
        super().__init__(r'report.png', pos, 25,target)
class SeedPacketGlow(Particle):
    def __init__(self, pos):
        super().__init__(r'seed_packet_glow.png', pos, 1,None,free=True)
#tiles
class LavaTile(Particle):
    def __init__(self, pos):
        super().__init__(r'lava_tile.png', pos, 1,None,free=True)

class ObjectFall(pygame.sprite.Sprite):
    def __init__(self, mother,image_path, pos,end_time,effects,start_speed,speed_increase,rotate=False,rotate_start=0,rotate_end=0,rotate_speed=0,up=True):
        super().__init__()
        self.e=effects.copy()
        if 'hit' in self.e:
            self.e.remove('hit')
        self.image = get_value('images')[image_path][tuple(self.e)]
        self.pos = list(pos)
        self.end_timer=end_time
        self.yspeed=start_speed
        self.increase=speed_increase
        self.angle=rotate_start
        self.rotate=True
        self.rotate_speed=rotate_speed
        self.rotate_end=rotate_end
        self.rotate_ended = False
        self.lane = mother.lane
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
            set_value('lanes', lane)

    def update(self, screen):
        self.end_timer-=get_value('equivalent_frame')
        self.pos[1]+=self.yspeed*get_value('equivalent_frame')
        self.yspeed+=self.increase*get_value('equivalent_frame')
        #rotate
        if self.rotate:
            if not self.rotate_ended:
                self.angle+=self.rotate_speed
                if self.angle==self.rotate_end:
                    self.rotate_ended=True
            self.img,self.rect=rotate(self.image,self.angle, (self.pos[0]+self.image.get_width() //
               2, self.pos[1]+self.image.get_height()//2),pygame.math.Vector2(-20,-20))
        else:
            self.img=self.image
        if self.end_timer<=0:
            self.on_end()
            self.kill()
    def display(self):
        try:
            screen = get_value('screen')
            if self.rotate:
                blity(self.img, self.rect)
            else:
                blity(self.img, self.pos)
        except:
            pass

    def on_end(self):
        try:
            lane = get_value('lanes')
            for key in ['plants', 'obstacles', 'zombies']:
                if self in lane[self.lane-1][key]:
                    lane[self.lane-1][key].remove(self)
                    break
            set_value('lanes', lane)
        except:
            pass


class ObjectFly(pygame.sprite.Sprite):
    def __init__(self, mother,image_path, start_pos, end_time, effects, start_speeds, speed_increases, rotate=False, rotate_start=0, rotate_end=0, rotate_speed=0,up=True):
        super().__init__()
        self.e=effects.copy()
        if 'hit' in self.e:
            self.e.remove('hit')
        self.image = get_value('images')[image_path][tuple(self.e)]
        self.pos = list(start_pos)
        self.end_timer = end_time
        self.speeds = start_speeds
        self.increases = speed_increases
        self.angle = rotate_start
        self.rotate = True
        self.rotate_speed = rotate_speed
        self.rotate_end = rotate_end
        self.rotate_ended = False
        self.lane = mother.lane
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
            set_value('lanes', lane)

    def update(self, screen):
        self.end_timer -= get_value('equivalent_frame')
        self.pos[0]+=self.speeds[0]*get_value('equivalent_frame')
        self.pos[1] += self.speeds[1]*get_value('equivalent_frame')
        self.speeds[0] += self.increases[0]*get_value('equivalent_frame')
        self.speeds[1]+=self.increases[1]*get_value('equivalent_frame')
        #rotate
        if self.rotate:
            if not self.rotate_ended:
                self.angle += self.rotate_speed
                if self.angle == self.rotate_end:
                    self.rotate_ended = True
            self.img, self.rect = rotate(self.image, self.angle, (self.pos[0]+self.image.get_width() //
                                                                  2, self.pos[1]+self.image.get_height()//2), pygame.math.Vector2(-20, -20))
        else:
            self.img = self.image
        if self.end_timer <= 0:
            self.on_end()
            self.kill()
    def display(self):
        try:
            screen=get_value('screen')
            if self.rotate:
                blity(self.img, self.rect)
            else:
                blity(self.img, self.pos)
        except:
            pass
    def on_end(self):

        lane = get_value('lanes')
        for key in ['plants', 'obstacles', 'zombies']:
            if self in lane[self.lane-1][key]:
                lane[self.lane-1][key].remove(self)
                break
        set_value('lanes', lane)
        pass
