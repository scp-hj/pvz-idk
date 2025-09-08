import pygame

class global_var:
    '''需要定义全局变量的放在这里，最好定义一个初始值'''
    data={'sun':0,'turbo':False,'planting':False,'planting_plant':None,'plants':pygame.sprite.Group(),
          'missles':pygame.sprite.Group(),'resources':pygame.sprite.Group(),
          'particles_0':pygame.sprite.Group(),'particles_1':pygame.sprite.Group(),
    'events':[],'seed_packets':None,'grave_ratio':[1,1,1,1,1,2,2,2,2,2,3,3,3,3,3,4,4,5]
    ,'plant_largest_id':0,'state':'leveling','difficulty':1,'specials':[],'hard_mode':False,
          'grave_num': 0, 'lanes': [{'obstacles': [], 'plants':[], 'zombies':[]} for a in range(100)],'pos_shift':(0,0),
          'images':dict(),'on_scene':('title_screen',0),'dev_pass':'crisbethicc','for_real?':'no',
          'key_press':'','DT':0.005,'dt':0.003,'scene':None,'sun_data':['','yellow'],'seed_selection':None,
          'money':0,'paused':False,'language':'chinese','new':False,'newest_plant':None,'factors':[1,1],
          'window size':[900,640],'full screen':False,'window pos shift':[0,0],
          'shake':0,'veil':[0,0,0,0,0],'map_veil':[0,0,0,0],'gravity':0.4,'mute':False,
          'last_daily_seed':0,'completed_daily':False,'last_scene':['title_screen'],'current_theme':'',
          'last_main':['title_screen'],'dt':0.025,'equivalent_frame':1,'max_seeds':6,'in_dialogue':False,
          'main_dialogue':None}
#screens: (title_scr:een), (main_menu),(level,'(level_name)') (level_select,0-9 (10 with meme world,114514 is void placeholder)) , (cutscreen, 0-idk) 
# 对于每个全局变量，都需要定义get_value和set_value接口


def set_value(key,value):
    global_var.data[key] = value


def get_value(key):
    return global_var.data[key]

def _circlepoints(r):
    points = set()
    x, y, d = r, 0, 1 - r
    while x >= y:
        points.update({
            ( x,  y), (-x,  y), ( x, -y), (-x, -y),
            ( y,  x), (-y,  x), ( y, -x), (-y, -x)
        })
        y += 1
        if d < 0:
            d += 2 * y + 1
        else:
            x -= 1
            d += 2 * (y - x) + 1
    return list(points)

def render(text, font, gfcolor=pygame.Color('dodgerblue'), ocolor=(255, 255, 255), opx=2):

    # Detect freetype vs classic font
    is_freetype = hasattr(font, "get_sized_height") or getattr(font, "__module__", "").startswith("pygame.freetype")

    # Normalize font.render to always yield a Surface
    def _render_surf(fnt, txt, color):
        if is_freetype:
            out = fnt.render(txt, color)  # freetype: (Surface, Rect) or Surface
            if isinstance(out, tuple):
                out = out[0]
        else:
            out = fnt.render(txt, True, color)  # classic: Surface
        return out.convert_alpha()

    textsurface = _render_surf(font, text, gfcolor)
    w = textsurface.get_width() + 2 * opx

    # Height consistent with original behavior; fall back if needed
    if is_freetype:
        try:
            h = font.get_sized_height()
        except Exception:
            h = textsurface.get_height()
    else:
        h = font.get_height()

    osurf = pygame.Surface((w, h + 2 * opx), pygame.SRCALPHA).convert_alpha()
    osurf.fill((0, 0, 0, 0))

    surf = osurf.copy()

    osurf.blit(_render_surf(font, text, ocolor), (0, 0))

    for dx, dy in _circlepoints(opx):
        surf.blit(osurf, (dx + opx, dy + opx))

    surf.blit(textsurface, (opx, opx))
    return surf
