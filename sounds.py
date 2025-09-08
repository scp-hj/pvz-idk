import pygame,sys,os
from config import *
from events import *
pygame.mixer.init()
NEXT=pygame.USEREVENT+1


def rp(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


sounds = {'plant': pygame.mixer.Sound(rp('sounds//plant.ogg')), 'select_seed': pygame.mixer.Sound(rp('sounds//seedlift.ogg')), 'select': pygame.mixer.Sound(rp('sounds//select.ogg')),
    'activate': pygame.mixer.Sound(rp('sounds//activate.ogg')), 'sun': pygame.mixer.Sound(rp('sounds//sun.ogg')),
    'spawngrave':pygame.mixer.Sound(rp('sounds//spawngrave.ogg')),'grave_die':pygame.mixer.Sound(rp('sounds//grave_break.ogg')),
    'pea_hit': pygame.mixer.Sound(rp('sounds//pea_hit.ogg')), 'snowpea_hit': pygame.mixer.Sound(rp('sounds//snowpea_hit.ogg')),
    'spore_hit':pygame.mixer.Sound(rp('sounds//puff.ogg')),'grow':pygame.mixer.Sound(rp('sounds//plantgrow.ogg')),'butter':pygame.mixer.Sound(rp('sounds//butter.ogg')),
    'limbs_pop':pygame.mixer.Sound(rp('sounds//limbs_pop.ogg')),'chomp_finish':pygame.mixer.Sound(rp('sounds//chomp_finish.ogg')),
    'shovel_pick':pygame.mixer.Sound(rp('sounds//shovel_pick.ogg')),'click2':pygame.mixer.Sound(rp('sounds//click2.ogg')),'pogo':pygame.mixer.Sound(rp('sounds//pogo_zombie.ogg')),
          'mine_explode': pygame.mixer.Sound(rp('sounds//potato_mine.ogg')), 'sting_hit': pygame.mixer.Sound(rp('sounds//something_hit.ogg')), 'electric_hit': pygame.mixer.Sound(rp('sounds//electric_hit.ogg')),
          'lawnmower':pygame.mixer.Sound(rp('sounds//lawnmower.ogg')),'lose':pygame.mixer.Sound(rp('sounds//lose.mp3')),'pear_hit':pygame.mixer.Sound(rp('sounds/something_hit2.ogg')),'sus':pygame.mixer.Sound(rp('sounds/impreveal.mp3')),
          'sussy':pygame.mixer.Sound(rp('sounds//reportingbody.mp3')),'scissors':pygame.mixer.Sound(rp('sounds//grafting.ogg')),'fire':pygame.mixer.Sound(rp('sounds//firepea.ogg')),'explode':pygame.mixer.Sound(rp('sounds//generic_explosion.ogg')),
          'nut_crack':pygame.mixer.Sound(rp('sounds//nut_crack.ogg')),'revolution':pygame.mixer.Sound(rp('sounds//revolution.ogg')),
          'win':pygame.mixer.Sound(rp('sounds//pvz-victory.mp3')),'coin':pygame.mixer.Sound(rp('sounds//coin.ogg')),
          'zombie_coming':pygame.mixer.Sound(rp('sounds//zombie_coming.mp3')),
          'disco':pygame.mixer.Sound(rp('sounds//disco.mp3')),
          'report':pygame.mixer.Sound(rp('sounds//report.mp3')),
          'chomp':pygame.mixer.Sound(rp('sounds//BigChomp.ogg')),
          'magical':pygame.mixer.Sound(rp('sounds//magic.wav')),
          'plantern':pygame.mixer.Sound(rp('sounds//plantern.mp3')),
          'plantern_die':pygame.mixer.Sound(rp('sounds//plantern_die.wav')),
          'ghost_die':pygame.mixer.Sound(rp('sounds//ghost_death.mp3')),
          'ghost_appear':pygame.mixer.Sound(rp('sounds//ghost_appear.mp3')),
          'bow_load':pygame.mixer.Sound(rp('sounds//bow_load.mp3')),
          'bow_release':pygame.mixer.Sound(rp('sounds//bow_release.mp3')),
          'ghost_beam':pygame.mixer.Sound(rp('sounds//ghost_beam.mp3')),
          'power_beam':pygame.mixer.Sound(rp('sounds//power_beam.mp3')),
          'powerflower_magic':pygame.mixer.Sound(rp('sounds//powerflower_magic.mp3')),
          'void_portal':pygame.mixer.Sound(rp('sounds//void_portal.mp3')),
          'purchase':pygame.mixer.Sound(rp('sounds/purchase.mp3')),
          'wrong':pygame.mixer.Sound(rp('sounds//wrong.mp3'))
          }
for a in range(0, 8):
    sounds['groan_' +
           str(a)+'.ogg'] = pygame.mixer.Sound(rp('sounds//groan_'+str(a)+'.ogg'))
for a in range(0, 4):
    sounds['chomp_' +
           str(a)+'.ogg'] = pygame.mixer.Sound(rp('sounds//chomp_'+str(a)+'.ogg'))

pygame.mixer.set_num_channels(69)
def play(soundname, volume):
    if not get_value('state')=='loading' and not get_value('mute'):
        sounds[soundname].set_volume(volume)
        pygame.mixer.find_channel(True).play(sounds[soundname])
def update(events):
    for event in events:
        if not get_value('mute'):
            if event.type==NEXT:
                pygame.mixer.music.play()

def new_theme(theme):
    # start first track
    if not get_value('mute'):
        set_value('current_theme',theme)
        pygame.mixer.music.load(rp(theme))
        pygame.mixer.music.play()

        # send event NEXT every time tracks ends
        pygame.mixer.music.set_endevent(NEXT)
