from PIL import Image
import numpy
import cv2 as cv
import sys,os
import pygame
from config import *
from typing import List
from pygame.locals import *



def relative_pos(pos):
    return (pos[0]+get_value('pos_shift')[0]+get_value('pos_shift2')[0],pos[1]+get_value('pos_shift')[1]+get_value('pos_shift2')[1])
def abs_pos(pos):
    return (pos[0]-get_value('pos_shift')[0]-get_value('pos_shift2')[0],pos[1]-get_value('pos_shift')[1]-get_value('pos_shift2')[1])
def loady(pathy):
    try:
        return pygame.image.load(pathy).convert_alpha()
    except:
        return pygame.image.load(pathy)
def blity(surfy,posy,still=False):
    if not still:
        posy=relative_pos(posy)
    get_value('screen').blit(surfy,posy)
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


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


def pillow_pvz_filter(image_path, states):
    img = cv.imread(resource_path(image_path),cv.IMREAD_UNCHANGED)
    img=img.astype('uint8')
    for state in states:
        if state == 'hit':
            img = cv.add(img, (img*0.5).astype(numpy.uint8))
        if state == 'milk':
            a = img.copy()
            a[:, :, 0] = 0
            a[:, :, 1] = 0
            a[:, :, 2] = 0
            img = numpy.clip(img, 10, 225)
            img[:, :, 2] += 30
            img[:, :, 1] += 30
            img[:, :, 0] -= 10
            img[:, :, 3] = 0
            img = img+a
        if state == 'freeze':
            a = img.copy()
            a[:, :, 0] = 0
            a[:, :, 1] = 0
            a[:, :, 2] = 0
            img = numpy.clip(img, 20, 195)
            img[:, :, 2] -= 20
            img[:, :, 1] -= 20
            img[:, :, 0] += 60
            img[:, :, 3] = 0
            img = a+img
        if state == 'toxin':
            a = img.copy()
            a[:, :, 0] = 0
            a[:, :, 1] = 0
            a[:, :, 2] = 0
            img = numpy.clip(img, 20, 195)
            img[:, :, 2] -= 20
            img[:, :, 1] += 60
            img[:, :, 0] -= 20
            img[:, :, 3] = 0
            img = a+img

        if state == 'black':
            a = img.copy()
            a[:, :, 0] = 0
            a[:, :, 1] = 0
            a[:, :, 2] = 0
            img = numpy.clip(img, 175, 255)
            img[:, :, 2] -= 175
            img[:, :, 1] -= 175
            img[:, :, 0] -= 175
            img[:, :, 3] = 0
            img = img+a
        if state == 'hot':
            a = img.copy()
            a[:, :, 0] = 0
            a[:, :, 1] = 0
            a[:, :, 2] = 0
            img = numpy.clip(img, 20, 155)
            img[:, :, 0] += 100
            img[:, :, 1] -= 10
            img[:, :, 2] -= 25
            img[:, :, 3] = 0
            img = img+a
        if state=='transparent':
            img[:,:,3]//=2
            
    img = numpy.clip(img, 0, 255)
    return img

# 检测和修正全屏
# noinspection PyShadowingNames
def check_full(window, full_bool, size):  # -> None
    """接受参数 fullscreen [bool, bool] 
        [窗口现在是否应该处于全屏状态，是否需要修正窗口状态]
        用于修改窗口状态（大小以及是否全屏，会自动修改full_bool的值）"""
    if full_bool[0] and full_bool[1]:  # 现在窗口应该处于全屏状态，并且没有处于全屏状态
        window = pygame.display.set_mode(pygame.display.list_modes()[0], FULLSCREEN)  # 全屏窗口
        full_bool[1] = False
    elif full_bool[1]:  # 不处于全屏状态
        window = pygame.display.set_mode(size, RESIZABLE)  # 自由拖拽窗口
        full_bool[1] = False
    return window

# 是否全屏
full_bool = [False, False]  # [是否全屏，是否需要修正窗口状态]

# 得到鼠标位置
# noinspection PyShadowingNames
def get_pos():
    """接受0个参数hhh"""
    pos = pygame.mouse.get_pos()
    pos = [(pos[0]-get_value('window pos shift')[0])/get_value('factors')[0],
           (pos[1]-get_value('window pos shift')[1])/get_value('factors')[1]]
    return pos

# 设置鼠标位置
# noinspection PyShadowingNames
def set_pos(pos):
    """接受一个参数(鼠标位置)"""
    pos = [(pos[0]-get_value('window pos shift')[0])/get_value('factors')[0],
           (pos[1]-get_value('window pos shift')[1])/get_value('factors')[1]]
    pygame.mouse.set_pos(pos)
