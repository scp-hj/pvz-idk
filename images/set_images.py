import numpy
import cv2 as cv
import os
from PIL import Image
images = os.listdir(r'C:\Users\lccs2015087\Desktop\pvz idk\images')
def blacken(name):
    if not ('black_' in name or 'hit_' in name or 'milk_' in name or 'freeze_' in name):
        image = Image.open(name).convert('RGBA')
        pixels = image.getdata()
        x, y = 0, 0
        for pixel in pixels:
            new_pixel = []
            new_pixel.append(int(pixel[0]*0.3))
            new_pixel.append(int(pixel[1]*0.3))
            new_pixel.append(int(pixel[2]*0.3))
            new_pixel.append(pixel[3])
            new_pixel = tuple(new_pixel)
            image.putpixel((x, y), new_pixel)
            x += 1
            if x == image.size[0]:
                y += 1
                x = 0
        image.save('black_'+name)


def hit(name):
    if not ('hit_' in name or 'black_' in name or 'milk_' in name or 'freeze_' in name):
        img = cv.imread(name, cv.IMREAD_UNCHANGED)
        cv.imwrite('hit_'+name, cv.add(img, (img*0.5).astype(numpy.uint8)))


def milk(name):
    if not ('hit_' in name or 'black_' in name or 'milk_' in name or 'freeze_' in name):
        image=Image.open(name).convert('RGBA')
        pixels=image.getdata()
        x,y=0,0
        for pixel in pixels:
            new_pixel=[]
            if pixel[0]+30>=255:
                new_pixel.append(255)
            else:
                new_pixel.append(pixel[0]+30)
            if pixel[1]+30 >= 255:
                new_pixel.append(255)
            else:
                new_pixel.append(pixel[1]+30)
            if pixel[2]-10 <= 0:
                new_pixel.append(0)
            else:
                new_pixel.append(pixel[2]-10)
            new_pixel.append(pixel[3])
            new_pixel=tuple(new_pixel)
            image.putpixel((x, y), new_pixel)
            x+=1
            if x==image.size[0]:
                y+=1
                x=0
        image.save('milk_'+name)

def freeze(name):
    if not ('hit_' in name or 'black_' in name or 'freeze_' in name):
        image = Image.open(name).convert('RGBA')
        pixels = image.getdata()
        x, y = 0, 0
        for pixel in pixels:
            new_pixel = []
            if pixel[0]-20 <= 0:
                new_pixel.append(0)
            else:
                new_pixel.append(pixel[0]-20)
            if pixel[1]-20 <= 0:
                new_pixel.append(0)
            else:
                new_pixel.append(pixel[0]-20)
            if pixel[2]+60 >= 255:
                new_pixel.append(255)
            else:
                new_pixel.append(pixel[2]+60)
            new_pixel.append(pixel[3])
            new_pixel = tuple(new_pixel)
            image.putpixel((x, y), new_pixel)
            x += 1
            if x == image.size[0]:
                y += 1
                x = 0
        image.save('freeze_'+name)


for image in images:
    if '.png' in image:
        blacken(image)
        hit(image)
        milk(image)
        freeze(image)
