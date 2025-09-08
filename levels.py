
import pygame
from system import *
from missles import *
from plants import *
from time import *
from resources import *
from config import *
from particles import *
from zombies import *
from filter import *
import sounds
import random
import sys
import os,json,copy,getpass
import inspect
import zombies,particles
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)
#constants#constant
FILTERS_=['hit','milk','freeze','black','transparent']
FILTERS__=[tuple()]
LEVEL_START=pygame.USEREVENT+114514
BACK_TO_MAIN=pygame.USEREVENT+71
for a in range(1,len(FILTERS_)+1):
    res = 0
    # x,n表示在x个数字中选出n个数字的组合, nums表示原始的数字列表, index表示当前递归的位置, count表示记录当前已经选了多少个数字了, rec列表记录中间递归过程中的结果
    def combination(x: int, n: int, rec: List[int], nums: List[int], index: int, count: int):
        global FILTERS__
        FILTERS__.append(tuple(rec))
        if count == n:
            global res
            res += 1
            return
        # for循环中限定了下标的范围所以不会存在越界的问题
        for i in range(index, x):
            rec.append(nums[i])
            combination(x, n, rec, nums, i + 1, count + 1)
            # 回溯, 尝试下一个数字
            rec.pop()
    combination(len(FILTERS_),a,[],FILTERS_,0,0)
FILTERS=[]
for filtr in FILTERS__:
    if not filtr in FILTERS:
        FILTERS.append(filtr)
RENDERS=dict()
for filtr in FILTERS:
    RENDERS[filtr]=list()


HARD_MODE_EXCLUSIVE=[6]
FLAG_ZOMBIES={1:['heal_','turbo_','aggro_'],2:['heal_','turbo_','aggro_','taunt_','summon_'],3:['heal_','turbo_','aggro_','taunt_','summon_','crowd_','grave_','revive_','deadly_'],4:['heal_','turbo_','aggro_','taunt_','summon_','crowd_','grave_','revive_','deadly_'],5:['heal_','turbo_','aggro_','taunt_','summon_','crowd_','grave_','revive_','deadly_']}

#function
def load_game():
    random_level()
    #fonts
    font = Font(resource_path(f'fonts/{get_value("language")}.ttf'), 15)
    sounds.new_theme('bgms//main_menu.wav')

    scene=None
    # start load
    set_value('on_scene',('title_screen',0))
    title=TitleScreen()
    title.update(1,1)
    #load or create save file
    newpath = rf'C:\Users\{getpass.getuser()}\AppData\Local\pvzidk'
    new=False
    if not os.path.exists(newpath):
        os.makedirs(newpath)
    with open(rf'{newpath}\beta_data.idk','a+') as f:
        pass
    with open(rf'{newpath}\beta_data.idk','r') as f:
        try:
            data=json.load(f)
            try:                    #checking if the save file contains money
                print(data['money'])
            except:
                data['money']=0
            try:                    #checking if the save file contains chroma credits
                print(data['chromas'])
            except:
                data['chromas']=0
            try:                    #checking if the save file contains 'unlocked features'
                #1: daily challenges 2:shops
                print(data['unlocked_features'])
            except:
                data['unlocked_features']=[]
            try:                    #checking if the save file contains 'unlocked stages'
                print(data['unlocked_stages'])
            except:
                data['unlocked_stages']=[1]
            try:                    #checking if the save file contains daily related data
                print(data['last_daily_seed'])
            except:
                data['last_daily_seed']=0
            try:
                print(data['completed_daily'])
            except:
                data['completed_daily']=False
            try:
                print(data['time'])
            except:
                data['time']='day'
            try:
                print(data['seed_limit'])
            except:
                data['seed_limit']=6
            try:
                print(data['seen_dialogues'])
            except:
                data['seen_dialogues']=[]
            
        except:
            new=True
    if new:
        with open(rf'{newpath}\beta_data.idk','w') as f:
            data={'unlocked_levels':['1-1'],
                  'unlocked_plants':[1],
                  'unlocked_powerups':[0],'money':0,
                  'language':'chinese','chromas':0,'unlocked_features':[],'unlocked_stages':[1],
                  'last_daily_seed':0,'completed_daily':0,'time':'day','seed_limit':6,'seen_dialogues':[]}
            json.dump(data,f)
        set_value('new',True)
    set_value('data',data)
    
    #update daily status
    seed=datetime.now().year*366+datetime.now().month*31+datetime.now().day
    if get_value('data')['last_daily_seed']!=seed:
        data['last_daily_seed']=seed
        data['completed_daily']=False
    save(data)
        
    set_value('money',data['money'])
    set_value('language',data['language'])
    get_value('screen').blit(title.image,(0,0))
    set_value('completed_daily',data['completed_daily'])
    set_value('max_seeds',data['seed_limit'])
    if get_value('language')=='chinese':
        text='努力加载中……'
    else:
        text='loading like crazy...'
    font.render_to(get_value('screen'), (700, 620), text, (255, 255, 255))
    pygame.display.update()
    set_value('state', 'loading')
    with open(resource_path(f'lore//{get_value("language")}//pause.txt'),encoding="utf8") as t:
        set_value('pause_texts',t.readlines())
    #load & render images
    images=os.listdir(resource_path('images//'))
    images_=dict()
    for image in images:
        if '.png' in image:
            images_[image]=dict()
            for filter_ in FILTERS:
                images_[image][filter_] = cv2_2_pygame(
                        pillow_pvz_filter(resource_path('images//'+image), filter_))            
    set_value('images',images_)
    #switch_scene(('level','alpha 0.1.2 is patched!'))
    switch_scene(('level_select','frontyard'))
def get_power_map(lane_map):
    power_map=[0]*len(lane_map)
    for lane in range(len(lane_map)):
        for key in ZOMBIE_POWER_LEVELS:
            for zombie in lane_map[lane]:
                if zombie in ZOMBIE_POWER_LEVELS[key]:
                    power_map[lane]=power_map[lane]+key
    return power_map
def adjust_power_distribution(lanes,power_map,zombie_num,last_power,last_last_power=[],lane=[1,2,3,4,5]):
    cnt=0
    for a in power_map:
        for b in power_map:
            cnt+=abs(a-b)
    cnt=cnt/zombie_num/2
    if zombie_num>=4:
        if not power_map==last_last_power:
            shifted_zombie=random.choice(lanes[power_map.index(max(power_map))])
            if power_map.index(min(power_map))+1 in lane:
                lanes[power_map.index(min(power_map))
                    ] = lanes[power_map.index(min(power_map))]+[shifted_zombie]
                lanes[power_map.index(
                    max(power_map))].remove(shifted_zombie)
                return adjust_power_distribution(lanes,get_power_map(lanes),zombie_num,power_map,last_power)
            else:
                return lanes
        else:
            return lanes
    else:
        return lanes

def random_lanes(zombies=['basics'], lane=[1,2,3,4,5]):
    lanes=[[]]*10
    
    zombie_num=len(zombies)
    for zombie in zombies:
        rnd_lane=random.choice(lane)-1
        lanes[rnd_lane]=lanes[rnd_lane]+[zombie]
    try:
        lanes=adjust_power_distribution(lanes,get_power_map(lanes),zombie_num,10000,lane)
    except:
        lanes=[[]]*10
        
        zombie_num=len(zombies)
        for zombie in zombies:
            rnd_lane=random.choice(lane)-1
            lanes[rnd_lane]=lanes[rnd_lane]+[zombie]
            lanes=adjust_power_distribution(lanes,get_power_map(lanes),zombie_num,10000,lane)
    return lanes
def spawn_zombies(lane_map):
    for lane in range(len(lane_map)):
        for zombie in lane_map[lane]:
            if lane+1 not in get_value('level').available_lanes:
                lane=random.choice(get_value('level').available_lanes)-1
            get_value('zombies').add(ZOMBIE_CLASSES[zombie](
                (random.randint(950, 1150), 90+(lane)*90)))


def spawn_zombie(zombies, lanes):
    spawn_zombies(random_lanes(zombies,lanes))

def start_dialogue(name):
    if not int(name) in get_value('data')['seen_dialogues']:
        with open(resource_path(f'lore//{get_value("language")}//dialogues//{name}.txt'),encoding='utf-8') as f:
            queue = json.load(f)    
            new=queue[0]
            queue.remove(new)
            print(new,len(new))
            if len(new)>=8:
                choice=new[7:]
            else:
                choice=None
            get_value('uber_uis').add(Dialogue(new[0],new[1],new[2],new[3],side=new[4],move=new[5],other_sprite=new[6],queue=queue,choices=choice))
        if not int(name) in REPEATED_DIALOGUES:
            d=get_value('data')['seen_dialogues']
            d.append(int(name))
            change_and_save('seen_dialogues',d)
    else:
        set_value('in_dialogue',False)
def get_level_setup(level='alpha 0.1.2 is patched!'):
    with open(resource_path('levels//levels//'+level+'.txt'),encoding='utf-8') as f:
        setup = json.load(f)
    return setup
#classes
class Level():
    def __init__(self,level_name,level=None):
        self.flag_zombie=copy.deepcopy(FLAG_ZOMBIES)
        print(level_name)
        if level_name:
            level_setup=get_level_setup(level_name)
        else:
            level_setup=level
        self.level_setup=level_setup
        self.name=level_name
        self.available_lanes=level_setup['lanes']
        self.lane_num=len(self.available_lanes)
        self.selection=None
        self.scene=level_setup['scene']
        self.sun_fall=level_setup['sun_fall']
        self.shroom_sleep=level_setup['shroom_sleep']
        self.opening_grave=level_setup['opening_grave']
        self.grave_danger = level_setup['grave_danger']
        self.max_grave = level_setup['max_grave']
        self.wave_duration=level_setup['wave_duration']
        self.gimmicks=level_setup['gimicks']
        self.end_dialogue=level_setup.get('end_dialogue')
        self.start_dialogue=level_setup.get('start_dialogue')
        self.win_dialogue=level_setup.get('win_dialogue')
        if 'locked and loaded' in self.gimmicks:
            self.locked_plants=level_setup['locked_plants']
            print('hihihi')
        if get_value('language')=='chinese':
            self.level=level_setup['level'][1]
        else:
            self.level=level_setup['level'][0]
        self.grave_area=level_setup['grave_area']
        self.zombies_=level_setup['zombie_spawn']
        self.sun_fall_duration=level_setup['sun_fall_duration']
        self.big_wave=level_setup['big_wave']
        self.unlocks=level_setup['unlocks']
        self.seeds=None
        set_value('sun',level_setup['start_sun'])
        self.wave = 0
        self.fps=0
        self.idk=0
        self.veils={'darkness':None}
        self.won=False
        self.wave_fps=0
        self.level_start=False
        set_value('pos_shift',(300,0))
        self.level_move_state=1 #1:from 300 to -200 #2:stay still at -200(seed selection) #3: from -200 to 0 #4:stay still at 0
        #level set up
        self.missles = pygame.sprite.Group()
        #fonts
        self.font = Font(resource_path(f'fonts/{get_value("language")}.ttf'), 15)
        self.plants = pygame.sprite.Group()
        self.resources = pygame.sprite.Group()
        self.particles_0 = pygame.sprite.Group()
        self.particles_1 = pygame.sprite.Group()
        self.particles_n1 = pygame.sprite.Group()
        self.particles_n2=pygame.sprite.Group()
        self.obstacles = pygame.sprite.Group()
        self.zombies = StupidOrderedGroup()
        self.afterlife=pygame.sprite.Group()
        self.yanyuans=pygame.sprite.Group()
        self.uber_uis=pygame.sprite.Group()
        self.tile_modifiers=[] #[effect,pos,duration,delta duration]
        self.lawnmowers=[LawnMower(a) for a in self.available_lanes]
        self.lanes=[{'obstacles':[],'plants':[],'zombies':[]} for a in range(999)]
        self.uis = pygame.sprite.Group()
        self.uis.add(ProgressBar())
        self.out=Return((800,550))
        self.uis.add(self.out)
        self.icon_list=[]
        self.progressing=False
        self.level_can_start=False
        set_value('level',self)
        set_value('plants', self.plants)
        set_value('missles', self.missles)
        set_value('resources', self.resources)
        set_value('particles_0', self.particles_0)
        set_value('particles_1', self.particles_1)
        set_value('particles_-1', self.particles_n1)
        set_value('particles_-2', self.particles_n2)
        set_value('grave_num',0)
        set_value('lanes', self.lanes)
        set_value('uis', self.uis)
        set_value('zombies', self.zombies)
        set_value('difficulty',1)
        set_value('seed_selection',None)
        set_value('afterlife',self.afterlife)
        set_value('uber_uis',self.uber_uis)
        set_value('pos_shift',(0,0))
        set_value('specials',[])
        set_value('tile_modifiers',[])
        self.gimmick_setup_early()
        if get_value('hard_mode'):
            set_value('difficulty',3)
        if self.sun_fall:
            self.sun_fall_cnt=self.sun_fall_duration[0]
        set_value('state', 'leveling')
        self.lanes = [{'obstacles': [], 'plants':[], 'zombies':[]}
                      for a in range(10)]
        grave_spots = []
        for x in range(self.grave_area[0], self.grave_area[1]):
            for y in self.available_lanes:
                grave_spots.append((x, y))
        set_value('lanes',self.lanes)
        set_value('grave_spots', grave_spots)
        for a in range(self.opening_grave):
            spawn_random_graves(1)
        if self.scene == 'lawn_night':
            sounds.new_theme('bgms//lawn_night_bg.wav')
            self.background_image = loady(
                resource_path('bgs//lawn_night.png'))
            set_value('map_veil',[16, 41, 100,65])
        if self.scene=='void':
            sounds.new_theme('bgms//void_theme.mp3')
            self.background_image=loady(resource_path('bgs//void.png'))
            set_value('map_veil',[16,41,100,65])
        if self.scene == 'lawn_day':
            sounds.new_theme('bgms//lawn_day_bg.wav')
            self.background_image = loady(
                resource_path('bgs//lawn_day.png'))
            set_value('map_veil',[0,0,0,0])
        if self.scene == 'lawn_day_1':
            sounds.new_theme('bgms//lawn_day_bg.wav')
            self.background_image = loady(
                resource_path('bgs//lawn_day_1.png'))
            set_value('map_veil',[0,0,0,0])
        if self.scene == 'lawn_night_1':
            sounds.new_theme('bgms//lawn_night_bg.wav')
            self.background_image = loady(
                resource_path('bgs//lawn_night_1.png'))
            set_value('map_veil',[16, 41, 100,65])
        self.uis.add(SunBank())
        self.zombie_preview()
    def update(self, events, screen):
        if get_value('in_dialogue'):
            self.level_start=False
        elif self.level_can_start:
            self.level_start=True
        self.idk+=get_value('equivalent_frame')
        set_value('events',events)
        screen.fill((10,100,10))
        blity(self.background_image,(-300,0))
        #movement of the screen
        if not get_value('paused'):
            self.move()
            set_value('plants',self.plants)
            set_value('resources',self.resources)
            set_value('particles_0',self.particles_0)
            set_value('particles_1', self.particles_1)
            set_value('particles_-1',self.particles_n1)
            set_value('particles_-2', self.particles_n2)
            set_value('seed_packets', self.seeds)
            set_value('obstacles',self.obstacles)
            set_value('zombies',self.zombies)
            set_value('missles',self.missles)
            set_value('yanyuans',self.yanyuans)
            set_value('uis',self.uis)
            set_value('lanes',self.lanes)
            set_value('fps',self.fps)
            set_value('uber_uis',self.uber_uis)
            set_value('wave_fps',self.wave_fps)
            set_value('tile_modifiers',self.tile_modifiers)

            if get_value('state')!='dead':
                self.particles_1.update(screen)
                self.plants.update(screen)
                self.obstacles.update(screen)
                self.zombies.draw(screen)
                self.missles.update(screen)
                if self.sun_fall and self.level_start:
                    self.sun_fall_cnt-=get_value('equivalent_frame')
                    if int(self.sun_fall_cnt)==0:
                        self.sun_fall_cnt=self.sun_fall_duration[1]
                        x=random.randint(100,700)
                        self.resources.add(Sun((x,-100),(x,random.randint(300,600))))
                for mower in self.lawnmowers:
                    mower.update('bruh')
        #print(self.lanes)
        #tile modifiers
        out_modifiers=[]
        for a in range(len(self.tile_modifiers)):
            #print(self.tile_modifiers[a])
            self.tile_modifiers[a][2]-=self.tile_modifiers[a][3]
            #update the tiles
            if self.tile_modifiers[a][0]=='lava':
                sound_play=False
                for zombie in get_value('zombies'):
                    if [zombie.column,zombie.lane]==self.tile_modifiers[a][1] and int(self.idk)%20==0:
                        zombie.damage(5,'fire','homing')
                        sound_play=True
                for obstacle in get_value('obstacles'):
                    if [obstacle.column,obstacle.lane]==self.tile_modifiers[a][1] and int(self.idk)%20==0:
                        obstacle.hp-=20
                        obstacle.hit_timer=1
                        sound_play=True
                get_value('particles_1').add(LavaTile([self.tile_modifiers[a][1][0]*90-30,self.tile_modifiers[a][1][1]*90+40]))
                if sound_play:
                    sounds.play('fire',1)
            if self.tile_modifiers[a][2]<=0:
                out_modifiers.append(self.tile_modifiers[a])
        for tile in out_modifiers:
            self.tile_modifiers.remove(tile)
        #draw special effects
        for special in get_value('specials'):
            #print(special)
            #print([icon.name for icon in self.icon_list])
            if special in SPECIAL_ICON_LIST and not special in [icon.name for icon in self.icon_list]:
                icon=SpecialIcon(special,(800,540-len(self.icon_list)*70),len(self.icon_list))
                self.icon_list.append(icon)
                self.uis.add(icon)
        for icon in self.icon_list:
            if not icon.name in get_value('specials'):
                cnt=icon.cnt
                for icon_ in self.icon_list:
                    if icon_.cnt>cnt:
                        icon_.cnt-=get_value('equivalent_frame')
                self.icon_list.remove(icon)
                icon.kill()
        for lane in self.lanes:
            for group in ['plants','obstacles','zombies']:
                if group=='plants':
                    lol=reversed(lane[group])
                else:
                    lol=lane[group]
                for sprite in lol:
                    if sprite:
                        seed=False
                        try:
                            seed=sprite.seed
                        except:
                            pass
                        if not seed:
                            try:
                                if not seed and sprite.rect.left[0]<=900 and sprite.rect.bottom[1]>=0 and sprite.rect.right[0]>=0 and sprite.rect.top[1]<=640:
                                    sprite.display()
                            except:
                                sprite.display()
        
        veil=get_value('map_veil')
        s=pygame.Surface((900,640))
        s.set_alpha(veil[3])
        s.fill(veil[0:3])
        blity(s,(0,0),True)
        #darkness
        if 'blind' in get_value('specials'):
            if int(self.fps)%20==0:
                s=pygame.Surface((900,640),flags=pygame.SRCALPHA)
                s.set_alpha(255)
                s.fill((0,0,0))
                for tile in self.tile_modifiers:
                    if tile[0]=='light':
                        pygame.draw.polygon(s,(0,0,0,20),
                                            [[tile[1][0]*90-30,tile[1][1]*90+30],[tile[1][0]*90+90-30,tile[1][1]*90+30],
                                             [tile[1][0]*90+90-30,tile[1][1]*90+90+30],[tile[1][0]*90-30,tile[1][1]*90+90+30]])
                        for a in range(36):
                            #gradient up
                            if find_layer('light',[tile[1][0],tile[1][1]-1])==0:
                                pygame.draw.line(s,(0,0,0,20+a*5),[tile[1][0]*90+25-30-a,tile[1][1]*90+30+25-a],[tile[1][0]*90+65-30+a,tile[1][1]*90+25+30-a])

                            #gradient left
                            if find_layer('light',[tile[1][0]-1,tile[1][1]])==0:
                                pygame.draw.line(s,(0,0,0,20+a*5),[tile[1][0]*90+25-30-a,tile[1][1]*90+25+30-a],[tile[1][0]*90+25-30-a,tile[1][1]*90+65+30+a])

                            #gradient right
                            if find_layer('light',[tile[1][0]+1,tile[1][1]])==0:
                                pygame.draw.line(s,(0,0,0,20+a*5),[tile[1][0]*90+65-30+a,tile[1][1]*90+30+25-a],[tile[1][0]*90+65-30+a,tile[1][1]*90+65+30+a])

                            #gradient down
                            if find_layer('light',[tile[1][0],tile[1][1]+1])==0:
                                pygame.draw.line(s,(0,0,0,20+a*5),[tile[1][0]*90+25-30-a,tile[1][1]*90+65+25+a],[tile[1][0]*90+65-30+a,tile[1][1]*90+25+65+a])
                self.veils['darkness']=s
            if self.veils['darkness']:
                blity(self.veils['darkness'],(0,0),True)
        self.uis.update(screen,events)
        self.yanyuans.update(screen)
        self.yanyuans.draw(screen)
        if not get_value('paused'):
            if self.selection!=None:
                self.selection.update(screen,events)
            if get_value('state')!='dead':
                self.particles_0.update(screen)
                self.particles_n1.update(screen)
                if self.seeds:
                    self.seeds.update(screen,events)
                self.resources.update(screen, events)
                self.particles_n2.update(screen)
        if get_value('hard_mode'):
            self.font.render_to(screen, (760, 620), 'HARD MODE ON', (255, 0, 100))
        self.font.render_to(screen,(30,620),self.level,(255,255,100))
        if not get_value('paused'):
            if self.level_start:
                self.fps+=get_value('equivalent_frame')
                self.wave_fps+=get_value('equivalent_frame')
            if self.wave>=len(self.zombies_)+1:
                if len(self.zombies.sprites())==0 and not self.won and not get_value('in_dialogue'):
                    self.won=True
                    print(self.unlocks,len(self.unlocks),'hihihihihi')
                    if self.unlocks[1]!='False' and not self.unlocks[1] in get_value('data')['unlocked_plants']:
                        see_=SEEDS_WITH_ID[self.unlocks[1]]((10000,100000))
                        self.uis.add(LevelEnd((random.randint(100,600),random.randint(100,500)),see_.image1,self))
                    if self.unlocks[2]!='False' and not self.unlocks[2] in get_value('data')['unlocked_powerups']:
                        see_=POWERUPS_WITH_ID[self.unlocks[2]]()
                        self.uis.add(LevelEnd((random.randint(100,600),random.randint(100,500)),see_.image1,self))
                    if len(self.unlocks)>=5:
                        print(self.unlocks[4])
                        if self.unlocks[4]:
                            self.uis.add(LevelEnd((random.randint(100,600),random.randint(100,500)),get_value('images')['chroma_credit.png'][tuple()],self))
                   
                    L=LevelEnd((random.randint(100,600),random.randint(100,500)),get_value('images')['money_bag.png'][tuple()],self)
                    L.coin=random.randint(6,16)
                    self.uis.add(L)
            else:
                if (self.wave==0 and int(self.wave_fps)>self.wave_duration[0]+140) or (self.wave>0 and (self.wave_fps>=self.wave_duration[1] or (len(get_value('zombies').sprites())==0 and self.wave_fps>=self.wave_duration[2]))):
                    try:
                        if self.wave!=0 and self.wave%self.big_wave==self.big_wave-1:
                            if self.wave+1==len(self.zombies_):
                                self.particles_n2.add(FinalWave())
                            else:
                                self.particles_n2.add(HugeWave())
                            flag=random.choice(self.flag_zombie[get_value('difficulty')])
                            if get_value('difficulty')<5:
                                if flag in self.flag_zombie[get_value('difficulty')+1]:
                                    self.flag_zombie[get_value('difficulty')+1].remove(flag)
                            else:
                                if flag in self.flag_zombie[get_value('difficulty')+1]:
                                    self.flag_zombie[get_value('difficulty')].remove(flag)
                            get_value('zombies').add(FlagZombie((990, random.choice([lane*90 for lane in self.available_lanes])),flag))
                        if 'flag_crowd' in get_value('specials'):
                            self.zombies_[self.wave]*=2
                        spawn_zombie(self.zombies_[self.wave],self.available_lanes)
                        if not self.progressing:
                            sounds.play('zombie_coming',1)
                            self.progressing=True
                        self.wave+=1
                        self.wave_fps=0
                        
                        if self.wave%2==0:
                            spawn_random_graves(self.grave_danger)
                    except IndexError:
                        if len(self.zombies.sprites())==0 and not self.won:
                            if not get_value('in_dialogue'):
                                if self.win_dialogue:
                                    start_dialogue(self.win_dialogue)
                                    self.win_dialogue=False
                                if not get_value('in_dialogue'):
                                    self.won=True
                                    print(self.unlocks,len(self.unlocks),'hihihihihi')
                                    if self.unlocks[1]!='False' and not self.unlocks[1] in get_value('data')['unlocked_plants']:
                                        see_=SEEDS_WITH_ID[self.unlocks[1]]((10000,100000))
                                        self.uis.add(LevelEnd((random.randint(100,600),random.randint(100,500)),see_.image1,self))
                                    if self.unlocks[2]!='False' and not self.unlocks[2] in get_value('data')['unlocked_powerups']:
                                        see_=POWERUPS_WITH_ID[self.unlocks[2]]()
                                        self.uis.add(LevelEnd((random.randint(100,600),random.randint(100,500)),see_.image1,self))
                                    if len(self.unlocks)>=5:
                                        print(self.unlocks[4])
                                        if self.unlocks[4]:
                                            self.uis.add(LevelEnd((random.randint(100,600),random.randint(100,500)),get_value('images')['chroma_credit.png'][tuple()],self))
                                   
                                    L=LevelEnd((random.randint(100,600),random.randint(100,500)),get_value('images')['money_bag.png'][tuple()],self)
                                    L.coin=random.randint(6,16)
                                    self.uis.add(L)
            if (not self.wave == 1 and not self.wave==2) and self.wave % 10 == 0 and self.wave_fps == 0 and self.level_start:
                if get_value('difficulty')<5:
                    set_value('difficulty',get_value('difficulty')+1)
            if (not self.wave == 0) and self.wave % self.big_wave == 0 and abs(self.wave_fps-100) <=get_value('equivalent_frame')*0.5 and self.level_start:
                for grave in self.obstacles:
                    get_value('particles_0').add(SpawnGraveZombie(grave.location,random.randint(1,2),lane=grave.lane))
            if self.wave%5==0 and self.wave_fps==0 and self.level_start and self.grave_danger>=1:
                self.grave_danger+=1
            if self.wave%7==0 and self.wave_fps==0 and self.level_start:
                self.max_grave+=1
                    
            #*dies*
            if get_value('state')!='dead':
                for zombie in self.zombies:
                    if zombie.x<=-50:
                        self.die()
            else:
                self.return_timer-=get_value('equivalent_frame')
                set_value('specials',[])
                if int(self.return_timer)<=0:
                    switch_scene(get_value('last_scene'))
                blity(loady(resource_path('bgs//zombies_ate_ur_brainz.png')),(-300,0))
                self.afterlife.update(get_value('screen'),events)
        self.uber_uis.update(get_value('screen'),events)
    def seed_selection(self):
        #create seed window and stuff
        
        if self.idk>=50:
            if self.selection==None:
                seed=SelectingSeeds(list(range(1,len(PLANTS_WITH_ID.keys())+1)),10)
                self.selection=seed
                if 'last_stand' in self.gimmicks:
                    for seed_ in self.selection:
                        if seed_.plant_id in SUN_PRODUCING_PLANTS:
                            seed_.disabled=True
                set_value('seed_selection',seed)
            if self.selection.done_seeds:
                if self.selection.menu.gadgets:
                    self.selection.menu.gadgets.down()
                    self.out.kill()
                    return self.selection.done_seeds,self.selection.menu.gadgets.value
                return self.selection.done_seeds,None
            
            
            
        return None
    def die(self):
        set_value('state','dead')
        self.level_move_state=7
        sounds.new_theme('sounds//lose.mp3')
        self.afterlife.add(SussyImposter((371,271)))
        self.return_timer=125
    def gimmick_setup(self):
        #gimmick set up
        if 'last_stand' in self.gimmicks:
            self.uis.add(LetsRock((700,90),self))
            self.level_start=False
            self.level_can_start=False
            set_value('state','pre-planting')
        if 'bruh' in self.gimmicks:
            self.level_move_state=5
            self.eradicate_preview_zombies()
        if 'plant parade' in self.gimmicks:
            for x in range(1,7):
                for y in range(1,6):
                    plant(x,y,self.plants,PLANTS_WITH_ID[(x-1)*5+y],self.missles,self.particles_0,0)
        if 'graft tutorial' in self.gimmicks:
            for x in range(1,10):
                for y in range(1,6):
                    if not (x==5 and y==3):
                        self.particles_0.add(SpawnGrave((x*90-20,y*90+10)))
            plant(5,3,self.plants,Sunflower,self.resources,self.particles_0,50)
        if 'save our seeds' in self.gimmicks:
            plants=self.level_setup['planted_plants']
            for plant_ in plants:
                p=plant(plant_[1],plant_[2],self.plants,PLANTS_WITH_ID[plant_[0]],self.resources,self.particles_0,0)
                if plant_[3]==1:
                    p.protect=True
    def gimmick_setup_early(self):
        for gimmick in self.gimmicks:
            set_value('specials', get_value('specials')+[gimmick])
    def ui_setup(self):
        
        #UIs
        self.uis.add(CoinCount())
        self.uis.add(TurboButton())
        if not 'graft tutorial' in self.gimmicks:
            self.uis.add(ShovelButton())
        self.uis.add(PauseButton())
        #ready set go!!!!
        self.particles_n2.add(Ready())
    def zombie_preview(self):
        zombie_list=[]
        for wave in self.zombies_:
            for zombie in wave:
                if not zombie in zombie_list:
                    
                    zombie_list.append(zombie)
        a=0
        random.shuffle(zombie_list)
        for zombie in zombie_list:
            z=ZOMBIE_CLASSES[zombie]((random.randint(900,1000),int(500/len(zombie_list)*a+random.randint(10,20))))
            z.preview=True
            self.zombies.add(z)
            a+=1
    def eradicate_preview_zombies(self):
        for zombie in self.zombies:
            zombie.kill()
            zombie.on_death(get_value('screen'))
        if 'graft tutorial' in self.gimmicks:
            for x in range(1,10):
                z=BasicZombie((500+20*x,270))
                z.stop_timer=9999999999999999
                self.zombies.add(z)
        if 'zombie parade' in self.gimmicks:
            for x in range(1,20):
                z=ZOMBIE_CLASSES[x]((100+35*x,270))
                z.stop_timer=9999999999999999
                self.zombies.add(z)
    def win(self):
        data=get_value('data')
        data['money']=get_value('money')
        print(self.unlocks)
        unlock=['coins',None]
        if not self.unlocks[0]=='False':
            if not self.unlocks[0] in data['unlocked_levels']:
                data['unlocked_levels'].append(self.unlocks[0])
        if not self.unlocks[1]=='False':
            if not self.unlocks[1] in data['unlocked_plants']:
                data['unlocked_plants'].append(self.unlocks[1])
                unlock=['plant',self.unlocks[1]]
        if not self.unlocks[2]=='False':
            if not self.unlocks[2] in data['unlocked_powerups']:
                data['unlocked_powerups'].append(self.unlocks[2])
                unlock=['powerup',self.unlocks[2]]
        if len(self.unlocks)>=4:
            if not self.unlocks[3] in data['unlocked_features'] and not self.unlocks[3]=='False':
                data['unlocked_features'].append(self.unlocks[3])
                unlock=['feature',self.unlocks[3]]
        if len(self.unlocks)>=5:
            unlock=['chromas',self.unlocks[4]]
            data['chromas']+=self.unlocks[4]
            data['completed_daily']=True
            set_value('completed_daily',True)
        save(data)
        set_value('main_dialogue',self.end_dialogue)
        switch_scene(('new_unlock',unlock))
    def move(self):
        if self.level_move_state==1:
            set_value('pos_shift', (get_value('pos_shift')
                      [0]-10, get_value('pos_shift')[1]))
            if get_value('pos_shift')[0]==-200:
                self.level_move_state=2
                set_value('state','seed_selection')
                #create seed window
        if self.level_move_state==2:
            if 'locked and loaded' in self.gimmicks:
                seeds=self.locked_plants
            else:
                seeds=self.seed_selection()
            if seeds:
                if self.start_dialogue:
                    self.level_start=False
                    start_dialogue(self.start_dialogue)
                else:
                    self.level_start=True
                self.level_can_start=True
                self.level_move_state=3
                print(seeds[0])
                self.seeds = SeedPackets([SEEDS_WITH_ID[seed] for seed in seeds[0]],get_value('data')['seed_limit'])
                #self.seeds=SeedPackets([SEEDS_WITH_ID[seed] for seed in SEEDS_WITH_ID],24)
                if not seeds[1]==None:
                    self.seeds.add(POWERUPS_WITH_ID[seeds[1]]())
                self.gimmick_setup()
                self.ui_setup()
        if self.level_move_state == 3:
            set_value('pos_shift', (get_value('pos_shift')
                      [0]+10, get_value('pos_shift')[1]))
            if get_value('pos_shift')[0] == 0:
                self.level_move_state = 4
                if not 'last_stand' in self.gimmicks:
                    set_value('state', 'leveling')
                self.eradicate_preview_zombies()
        if self.level_move_state == 5:
            set_value('pos_shift', (get_value('pos_shift')
                      [0]+5, get_value('pos_shift')[1]))
            if get_value('pos_shift')[0] == 300:
                self.level_move_state = 6
        if self.level_move_state == 6:
            set_value('pos_shift', (get_value('pos_shift')
                      [0]-5, get_value('pos_shift')[1]))
            if get_value('pos_shift')[0] == -200:
                self.level_move_state = 5
        if self.level_move_state==7:
            set_value('pos_shift', (get_value('pos_shift')
                      [0]+10, get_value('pos_shift')[1]))
            if get_value('pos_shift')[0] >= 300:
                self.level_move_state = 4
def find_layer(effect,tile):
    #find the number of a specific effect on a certain tile
    cnt=0
    for tile_ in get_value('tile_modifiers'):
        if tile_[1]==tile and tile_[0]==effect:
            cnt+=1
    return cnt
#save file
def save(new_data):
    #load or create save file
    newpath = rf'C:\Users\{getpass.getuser()}\AppData\Local\pvzidk'
    if not os.path.exists(newpath):
        os.makedirs(newpath)
    with open(rf'{newpath}\beta_data.idk','a+') as f:
        pass
    with open(rf'{newpath}\beta_data.idk','w') as f:
        json.dump(new_data,f)
    set_value('data',new_data)
def change_and_save(change_key,change_value):
    data=get_value('data')
    data[change_key]=change_value
    save(data)
#generate a random level for daily challenge
def random_level():
    #select one zombie from each power level
    level=dict()
    zombies=[random.choice(ZOMBIE_POWER_LEVELS[power]) for power in range(1,6)]
    #add one zombie from a random power level
    zombies.append(random.choice(ZOMBIE_POWER_LEVELS[random.randint(1,5)]))
    level['start_sun']=50*random.randint(1,5)
    level['lane_num']=5
    level['scene']=random.choice(['lawn_night','lawn_day','void'])
    level['sun_fall']=random.randint(0,1)
    if level['start_sun']<=50:
        level['sun_fall']=1
    if level['scene']=='lawn_night':
        level['sun_fall']=0
    level['wave_duration']=[random.randint(7,15)*100,
                            random.randint(4,8)*100,300]
    level['gimicks']=[]
    level['level']=['Daily challenge!','每日挑战！']
    if level['scene']=='lawn_night' or level['scene']=='void':
        level['shroom_sleep']=0
    else:
        level['shroom_sleep']=1
    level['opening_grave']=random.randint(0,5)
    level['grave_danger']=random.randint(0,1)
    level['max_grave']=random.randint(5,20)
    level['grave_area']=[random.randint(4,7),10]
    level['sun_fall_duration']=[300,random.randint(8,18)*50]
    level['big_wave']=random.randint(1,2)*5
    level['unlocks']=['False','False','False','False',1]
    level['zombie_spawn']=generate_level(zombies)
    print('level')
    return(level)
def generate_level(zombies):
    # Choose total number of waves randomly
    total_waves = random.choice([10, 15, 20, 25])
    
    waves = []
    
    for wave_idx in range(total_waves):
        # Calculate progression through the level (0 to 1)
        progression = wave_idx / (total_waves - 1) if total_waves > 1 else 0.0
        
        # Determine number of zombies in this wave
        base_zombies = int(progression * 6+(progression*10)**1.5/8)  # Ranges from 1 to 11
        min_z = max(1, base_zombies - random.randint(1,4))
        max_z = base_zombies+1
        num_zombies = random.randint(min_z, max_z)
        
        wave = []
        for _ in range(num_zombies):
            # 3% chance to spawn cameo (last element)
            if random.random() < 0.05:
                wave.append(zombies[-1])
            else:
                # Calculate weights for regular zombies (first 5 elements)
                weights = [
                    (5 - k) * (1 - progression) + (k + 1) * progression
                    for k in range(5)
                ]
                total_weight = sum(weights)
                rand_val = random.uniform(0, total_weight)
                
                # Select zombie type based on weights
                cumulative = 0
                for k in range(5):
                    cumulative += weights[k]
                    if rand_val <= cumulative:
                        wave.append(zombies[k])
                        break
        
        waves.append(wave)
    
    return waves
  
#scene stuff
def switch_scene(scene):
    print('pos',get_value('pos_shift'))
    set_value('in_dialogue',False)
    scene_=list(get_value('on_scene'))
    if scene_[0]=='level_select':
        if len(scene_)<3:
            scene_.append(get_value('pos_shift'))
        else:
            scene_[2]=get_value('pos_shift')
        set_value('last_main',scene_)
        print('last_main',scene_)
    if not scene_[0]=='level':
        set_value('last_scene',scene_)
        print('last scene',scene_)
    set_value('on_scene',scene)
    set_value('turbo',False)
    set_value('pos_shift',[0,0])
    if scene[0]=='title_screen':
        set_value('scene',TitleScreen)
    elif scene[0]=='level':
        if type(scene[1])==type([1]):
            set_value('scene',Level(scene[1][0],scene[1][1]))
        else:
            set_value('scene',Level(scene[1]))
    elif scene[0]=='level_select':
        set_value('scene',LevelSelect(scene[1]))
        if len(scene)>=3:
            set_value('pos_shift',scene[-1])
    elif scene[0]=='new_unlock':
        set_value('scene',NewUnlock(scene[1][0],scene[1][1]))
    elif scene[0]=='daily':
        set_value('scene',DailyScreen(get_value('last_main')))
    elif scene[0]=='shop':
        set_value('scene',Shop(get_value('last_main')))
class TitleScreen():
    def __init__(self):
        self.font=Font(resource_path(f'fonts/{get_value("language")}.ttf'), 25)
        self.image=loady(resource_path(random.choice(['bgs//title_screen.png','bgs//title_screen_0.1.2.png','bgs//title_screen_0.1.9.png'])))
    def update(self,events,screen):   
        get_value('screen').blit(self.image,(0,0))
        self.font.render_to(get_value('screen'), (700, 620), 'loading like crazy...', (20, 20, 25))
        pygame.display.update()
        set_value('state', 'loading')
class LevelSelect():
    def __init__(self,scene_name):
        if not get_value('current_theme')=='bgms//world1_bg.mp3':
            sounds.new_theme('bgms//world1_bg.mp3')
        self.name=scene_name
        set_value('map_veil',[0,0,0,0])
        self.time=get_value('data')['time']
        self.image=loady(resource_path('bgs//'+self.name+'_'+get_value('data')['time']+'.png'))
        self.scroll_speed=0
        self.uis=pygame.sprite.Group()
        self.uis.add(CoinCount())
        if 1 in get_value('data')['unlocked_features']:
            self.uis.add(Unicorn())
        if 3 in get_value('data')['unlocked_features']:
            self.uis.add(ShopButton())
        if '2-1' in get_value('data')['unlocked_levels']:
            self.uis.add(JHPCS())
            if not 28 in get_value('data')['unlocked_plants'] and random.randint(1,8)==1:
                self.uis.add(Sprout())
        self.uber_uis=pygame.sprite.Group()
        set_value('uis',self.uis)
        set_value('uber_uis',self.uber_uis)
        with open(resource_path('levels//level_selections//'+self.name+'.txt')) as f:
            buttons = json.load(f)
        for button in buttons:
            self.uis.add(LevelSelectButton(button[0],button[1]))
        self.uis.add(Language())
        if get_value('main_dialogue'):
            dialogue=get_value('main_dialogue')
            set_value('main_dialogue',None)
            start_dialogue(dialogue)
        #self.uis.add(Unicorn())
    def update(self,events,screen):
        if not get_value('data')['time']==self.time:
            self.image=loady(resource_path('bgs//'+self.name+'_'+get_value('data')['time']+'.png'))
        blity(self.image,(0,0))
        self.uis.update(screen,events)
        self.uber_uis.update(screen,events)
        set_value('state','level_select')
        keys=pygame.key.get_pressed()
        if abs(self.scroll_speed)<16:
            if keys[pygame.K_LEFT]:
                self.scroll_speed+=4
            if keys[pygame.K_RIGHT]:
                self.scroll_speed-=4
        if self.scroll_speed>0:
            self.scroll_speed-=1
        elif self.scroll_speed<0:
            self.scroll_speed+=1
        new_shift=get_value('pos_shift')[0]+self.scroll_speed
        if new_shift>0:
            self.scroll_speed=0
            new_shift=0
        elif new_shift<900-self.image.get_width():
            self.scroll_speed=0
            new_shift=900-self.image.get_width()
        set_value('pos_shift', (new_shift, get_value('pos_shift')[1]))
        set_value('uis',self.uis)
        set_value('uber_uis',self.uber_uis)
        veil=get_value('map_veil')
        s=pygame.Surface((900,640))
        s.set_alpha(veil[3])
        s.fill(veil[0:3])
        blity(s,(0,0),True)
class NewUnlock():
    def __init__(self,unlock_type,unlock_id):
        sounds.new_theme('bgms//garden_bg.wav')
        self.image=loady(resource_path('bgs//unlock_screen.png'))
            
        self.uis=pygame.sprite.Group()
        self.uber_uis=pygame.sprite.Group()
        if unlock_type=='coins':
            self.display_image=pygame.transform.smoothscale_by(get_value('images')['money_bag.png'][tuple()],1.5)
            self.uis.add(CoinCount())
            if get_value('language')=='chinese':
                self.title='一小袋金币'
                self.desc='食之无味，弃之可惜'
            else:
                self.title='A bag of coins'
                self.desc='Better than nothing ig'
        elif unlock_type=='feature':
            self.display_image=get_value('images')[FEATURE_IMAGE[unlock_id]][tuple()]
  
            if get_value('language')=='chinese':
                with open(resource_path(rf'lore//chinese//features//{unlock_id}.txt'),encoding="utf8") as f:
                    self.title = f.readline().strip('\n')
                    self.desc=''
                    for line in f.readlines():
                        self.desc+=line.strip()+' '
            else:
                with open(resource_path(rf'lore//english//features//{unlock_id}.txt'),encoding="utf8") as f:
                    self.title = f.readline().strip('\n')
                    self.desc=''
                    for line in f.readlines():
                        self.desc+=line.strip()+' '
        elif unlock_type=='chromas':
            self.uis.add(ChromaCount())
            self.display_image=pygame.transform.smoothscale_by(get_value('images')['chroma_credit.png'][tuple()],4)
            if get_value('language')=='chinese':
                self.title='星虹代币！'
                self.desc='神秘的金属制（？）扁片上泛着彩虹般的光芒。'+'现有'+str(get_value('data')['chromas'])+'块。明天再次挑战，以获取更多！'
                change_and_save('money',get_value('money')+200)
                set_value('money',get_value('money')+200)
            else:
                self.title='A chroma credit'
                self.desc='A rainbow-like glow shines on the mysterious metallic chip. '+' Currently has '+str(get_value('data')['chromas'])+'. Come back tomorrow for more !!!'
                change_and_save('money',get_value('money')+200)
                set_value('money',get_value('money')+200)
        elif unlock_type=='plant':
            self.display_image=pygame.transform.smoothscale_by(SEEDS_WITH_ID[unlock_id]((10000,100000)).image1,2)
  
            if get_value('language')=='chinese':
                with open(resource_path(rf'lore//chinese//plants//short//{unlock_id}.txt'),encoding="utf8") as f:
                    self.title = f.readline().strip('\n')
                    self.desc=''
                    for line in f.readlines():
                        self.desc+=line.strip()+' '
            else:
                with open(resource_path(rf'lore//english//plants//short//{unlock_id}.txt'),encoding="utf8") as f:
                    self.title = f.readline().strip('\n')
                    self.desc=''
                    for line in f.readlines():
                        self.desc+=line.strip()+' '
        elif unlock_type=='powerup':
            self.display_image=pygame.transform.smoothscale_by(POWERUPS_WITH_ID[unlock_id]().image1,2)
  
            if get_value('language')=='chinese':
                with open(resource_path(rf'lore//chinese//gadgets//short//{unlock_id}.txt'),encoding="utf8") as f:
                    self.title = f.readline().strip('\n')
                    self.desc=''
                    for line in f.readlines():
                        self.desc+=line.strip()+' '
            else:
                with open(resource_path(rf'lore//english//gadgets//short//{unlock_id}.txt'),encoding="utf8") as f:
                    self.title = f.readline().strip('\n')
                    self.desc=''
                    for line in f.readlines():
                        self.desc+=line.strip()+' '
        self.uis.add(BackMainMenu((325,530),get_value('last_main')))
        self.uis.add(SmartText(self.title,(310,25),32,100,0,(56,28,0)))
        if get_value('language')=='chinese':
            self.uis.add(SmartText(self.desc,(275,350),20,18,30,(56,28,0)))
        else:
            self.uis.add(SmartText(self.desc,(275,350),13,40,20,(56,28,0)))
        set_value('uis',self.uis)
        set_value('uber_uis',self.uber_uis)
        print(self.title)
        print(self.desc)
    def update(self,events,screen):
        blity(self.image,(0,0))
        blity(self.display_image,(370,140))
        self.uis.update(screen,events)
        self.uber_uis.update(screen,events)
        set_value('state','unlock_screen')
        set_value('uis',self.uis)
        set_value('uber_uis',self.uber_uis)
        
class DailyScreen():
    def __init__(self,scene=get_value('last_main')):
        sounds.new_theme('bgms//Bubblegum Halo.mp3')
        self.image=loady(resource_path('bgs//bg_daily.png'))
            
        self.uis=pygame.sprite.Group()
        self.uber_uis=pygame.sprite.Group()
        self.scene=scene
        self.uis.add(Return((660,65),scene))
        self.uis.add(ChromaCount())
        self.uis.add(DailyChallenge())
        self.uis.add(ShopUnicorn())
        #self.uis.add(SmartText(self.title,(310,25),32,100,0,(56,28,0)))
        import datetime
        formatted_date = datetime.datetime.now().strftime("%d/%m/%Y")
        if get_value('language')=='chinese':
            self.uis.add(SmartText(formatted_date,(90,185),25,18,30,(56,28,0)))
            if datetime.datetime.now().weekday()>=5: 
                self.uis.add(SmartText('周末双倍！',(125,220),25,18,30,(0, 8, 197)))
            if get_value('completed_daily'):
                self.uis.add(SmartText('已完成~',(130,350),25,18,30,(0,160,30)))
            else:
                self.uis.add(SmartText('快来~',(140,350),25,18,30,(160,0,0)))
        else:
            self.uis.add(SmartText(formatted_date,(90,185),25,40,20,(56,28,0)))
            if datetime.datetime.now().weekday()>=5: 
                self.uis.add(SmartText('Weekend reward x2!!!',(50,225),20,18,30,(0, 8, 197)))
            if get_value('completed_daily'):
                self.uis.add(SmartText('Completed~',(100,350),25,18,30,(0,160,30)))
            else:
                self.uis.add(SmartText('Come~',(130,350),25,18,30,(160,0,0)))
        cnt=0
        row=0
        for plant in CHROMA_SHOP_LIST.keys():
            if not plant in get_value('data')['unlocked_plants']:
                self.uis.add(ShopSeed((320+cnt*90,340+row*90),plant))
                self.uis.add(PurchaseButton((320+cnt*90,400+row*90),CHROMA_SHOP_LIST[plant],['plant',plant],'chromas'))

                cnt+=1
                if cnt>4:
                    row+=1
                    cnt=0
        set_value('uis',self.uis)
        set_value('uber_uis',self.uber_uis)
        start_dialogue("40")
    def refresh(self):
            
        self.uis=pygame.sprite.Group()
        self.uber_uis=pygame.sprite.Group()
        scene=self.scene
        self.uis.add(Return((660,65),scene))
        self.uis.add(ChromaCount())
        self.uis.add(DailyChallenge())
        self.uis.add(ShopUnicorn())
        #self.uis.add(SmartText(self.title,(310,25),32,100,0,(56,28,0)))
        import datetime
        formatted_date = datetime.datetime.now().strftime("%d/%m/%Y")
        if get_value('language')=='chinese':
            self.uis.add(SmartText(formatted_date,(90,185),25,18,30,(56,28,0)))
            if datetime.datetime.now().weekday()>=5: 
                self.uis.add(SmartText('周末双倍！',(125,220),25,18,30,(0, 8, 197)))
            if get_value('completed_daily'):
                self.uis.add(SmartText('已完成~',(130,350),25,18,30,(0,160,30)))
            else:
                self.uis.add(SmartText('快来~',(140,350),25,18,30,(160,0,0)))
        else:
            self.uis.add(SmartText(formatted_date,(90,185),25,40,20,(56,28,0)))
            if datetime.datetime.now().weekday()>=5: 
                self.uis.add(SmartText('Weekend reward x2!!!',(50,225),20,18,30,(0, 8, 197)))
            if get_value('completed_daily'):
                self.uis.add(SmartText('Completed~',(100,350),25,18,30,(0,160,30)))
            else:
                self.uis.add(SmartText('Come~',(130,350),25,18,30,(160,0,0)))
        cnt=0
        row=0
        for plant in CHROMA_SHOP_LIST.keys():
            if not plant in get_value('data')['unlocked_plants']:
                self.uis.add(ShopSeed((320+cnt*90,340+row*90),plant))
                self.uis.add(PurchaseButton((320+cnt*90,400+row*90),CHROMA_SHOP_LIST[plant],['plant',plant],'chromas'))

                cnt+=1
                if cnt>4:
                    row+=1
                    cnt=0
        set_value('uis',self.uis)
        set_value('uber_uis',self.uber_uis)
        
    def update(self,events,screen):
        blity(self.image,(0,0))
        self.uis.update(screen,events)
        self.uber_uis.update(screen,events)
        set_value('state','daily_screen')
        set_value('uis',self.uis)
        set_value('uber_uis',self.uber_uis)

class Shop():
    def __init__(self,scene=get_value('last_main')):
        if not get_value('current_theme')=='bgms//main_menu.wav':
            sounds.new_theme('bgms//main_menu.wav')
        self.image=loady(resource_path('bgs//shop.png'))
            
        self.uis=pygame.sprite.Group()
        self.uber_uis=pygame.sprite.Group()
        self.scene=scene
        self.uis.add(Return((775,15),scene))
        self.uis.add(CoinCount())
        set_value('uis',self.uis)
        set_value('uber_uis',self.uber_uis)
        cnt=0
        row=0
        if get_value('data')['seed_limit']<15:
            self.uis.add(ShopPacket((80,80)))
            self.uis.add(PurchaseButton((80,160),500*2**(get_value('data')['seed_limit']-6),['feature','more_packets'],'money'))
                
            
        for plant in SHOP_LIST['plants'].keys():
            if not plant in get_value('data')['unlocked_plants']:
                self.uis.add(ShopSeed((425+cnt*90,100+row*90),plant))
                self.uis.add(PurchaseButton((425+cnt*90,160+row*90),SHOP_LIST['plants'][plant],['plant',plant],'money'))
                cnt+=1
                if cnt>4:
                    row+=1
                    cnt=0
        cnt=0
        row=0
        for plant in SHOP_LIST['gadgets'].keys():
            if not plant in get_value('data')['unlocked_powerups']:
                self.uis.add(ShopPower((425+cnt*120,350+row*90),plant))
                self.uis.add(PurchaseButton((435+cnt*120,410+row*90),SHOP_LIST['gadgets'][plant],['powerup',plant],'money'))
       
                cnt+=1
                if cnt>3:
                    row+=1
                    cnt=0
        start_dialogue("37")
    def refresh(self):
            
        self.uis=pygame.sprite.Group()
        self.uber_uis=pygame.sprite.Group()
        self.uis.add(Return((775,15),self.scene))
        self.uis.add(CoinCount())
        set_value('uis',self.uis)
        set_value('uber_uis',self.uber_uis)
        cnt=0
        row=0
        if get_value('data')['seed_limit']<15:
            self.uis.add(ShopPacket((80,80)))
            self.uis.add(PurchaseButton((80,160),500*2**(get_value('data')['seed_limit']-6),['feature','more_packets'],'money'))
                
           
        for plant in SHOP_LIST['plants'].keys():
            if not plant in get_value('data')['unlocked_plants']:
                self.uis.add(ShopSeed((425+cnt*90,100+row*90),plant))
                self.uis.add(PurchaseButton((425+cnt*90,160+row*90),SHOP_LIST['plants'][plant],['plant',plant],'money'))
                cnt+=1
                if cnt>4:
                    row+=1
                    cnt=0
        cnt=0
        row=0
        for plant in SHOP_LIST['gadgets'].keys():
            if not plant in get_value('data')['unlocked_powerups']:
                self.uis.add(ShopPower((425+cnt*120,350+row*90),plant))
                self.uis.add(PurchaseButton((435+cnt*120,410+row*90),SHOP_LIST['gadgets'][plant],['powerup',plant],'money'))
       
                cnt+=1
                if cnt>3:
                    row+=1
                    cnt=0
    def update(self,events,screen):
        blity(self.image,(0,0))
        self.uis.update(screen,events)
        self.uber_uis.update(screen,events)
        set_value('state','daily_screen')
        set_value('uis',self.uis)
        set_value('uber_uis',self.uber_uis)
        
SUN_PRODUCING_PLANTS=[2,6,30]
SPECIAL_ICON_LIST=['flag_crowd','flag_deadly','flag_turbo','flag_shield','thunderstorm',
                   'blind','grave','sleep','locked and loaded',
                   'random graves','double power','save our seeds']
FEATURE_IMAGE={1:'npc_unicorn_1.png',2:'nut_cracker_powerup.png',3:'shop_icon.png'}
NIGHT_SCENES=['lawn_night','lawn_night_1']
SHOP_LIST={'plants':{9:500,12:750,18:750,
                     20:750,23:500,3:350,
                     15:350,17:400,19:350,
                     21:350},'gadgets':{2:650,3:650,4:650}}
CHROMA_SHOP_LIST={8:4,22:6,26:12,27:12}
