# -*- coding: UTF-8 -*-
import re

import time
import datetime
import threading

import codecs
#import turtle
try:
    import Tkinter as tkinter
except:
    import tkinter

from PIL import Image
from PIL import ImageTk
#import cv2


import matplotlib.pyplot as plt#约定俗成的写法plt
import numpy as np

#自定义类
#from neshardware import * 
from deco import *
from wrfilemod import *

nesROMdata =[]
i16K_ROM_NUMBER = 0
i8K_VROM_NUMBER = 0
ROM = []
VROM = []
def rom_ok(data):
    if ''.join([chr(i) for i in data[:0x4]]) == 'NES\x1a':
        print 'ROM OK!'
        return True
    else:
        return False
#@deco
def get_16k_rom_num(data):
    return ord(data[0x4])
#@deco
def get_8k_vrom_num(data):
    return ord(data[0x5])

def get_block(block_start,block_num,block_len):
    block=[]
    for i in range(block_num):
        
        block_t = nesROMdata[block_start:(block_start + block_len)]
        
        block.append(block_t)

        block_start += block_len
        
        
    return block,block_start

#@deco
def Tile_(data):
    Tile = []
    for item in data:
        Tile.append('{:0^8}'.format((bin(ord(item)))[2:]))
    return Tile

#@deco
def Tile_mix(data1,data2):
    Tile_mix = []
    for i,row in enumerate(data2):
        Tile_row = ''
        for j,bit in enumerate(list(row)):
            pass
            Tile_row += str(int(bit)*2 + int(data1[i][j:j+1]))
        #print i,row,data1[i],Tile_row
        Tile_mix.append(Tile_row)
    return Tile_mix

#@deco
def get_Tile(block_num,offset):
    return Tile_mix(Tile_(VROM[block_num][offset:(offset+0x8)]),Tile_(VROM[block_num][(offset+0x8):(offset+0x10)]))

def HEX_RGB(value):
    digit = int(filter(lambda x:x in '0123456789ABCDEF',value),16)
    a1 = digit // 0xFFFF
    a2 = (digit - a1) // 0xFF
    a3 = digit % 0xFF
    return (a1, a2, a3)
#print HEX_RGB('#80')


def pal_arr(cpal):
    pal_arr = []
    for i in cpal:
        pal_arr.append(HEX_RGB(i))
    return pal_arr

def draw_str(Tiles,i):
        Tile_color = ['white','yellow','red','green']
        global image
        #print Tiles
        #print i/2,
        digit = list(map(str, range(10))) + list("ABCDEF")
        pos_x = (i * 8) % s_w * ratio
        pos_y = (i // (s_w / 8)) * 8 * ratio
        #print pos_x,pos_y
        for y,Tile in enumerate(Tiles):
            point_y = pos_y + y * ratio
            for x,c in enumerate(Tile):
                point_x = pos_x + x*ratio
                image[point_y, point_x] = pal_array[int(c)]
                #image[point_y, point_x, 0] = digit.index(CPal[int(c)][1]) * 16 + digit.index(CPal[int(c)][2])
                #image[point_y, point_x, 1] = digit.index(CPal[int(c)][3]) * 16 + digit.index(CPal[int(c)][4])
                #image[point_y, point_x, 2] = digit.index(CPal[int(c)][5]) * 16 + digit.index(CPal[int(c)][6])
                
'''
canvas.create_rectangle(pos_x + x*ratio ,
                                        pos_y + y * ratio + 1 ,
                                        pos_x + (x+1)*ratio,
                                        pos_y + (y + 1) * ratio + 1,
                                        outline = CPal[int(c)],
                                        fill = CPal[int(c)])
'''
        
def Tiles_arr(Tiles):
    Tiles_arr = []
    for y,Tile in enumerate(Tiles):
        Tile_arr = []
        for x,c in enumerate(Tile):
            Tile_arr.append(pal_array[int(c)])
        Tiles_arr.append(Tile_arr)
    return Tiles_arr



#camera = cv2.VideoCapture(0)
firstframe=None 
tk = tkinter.Tk()                      # 创建窗口对象的背景色
#创建一个宽为400，高为400，背景为蓝色色的画布
ratio = 1
s_w,s_h = 256,240
canvas = tkinter.Canvas(tk,width=s_w*ratio,height=s_h*ratio,bg="black")
canvas.pack()
#tk.mainloop()
#pal_array = pal_arr(CPal)

#video_loop()

#cv2.namedWindow("Image")
'''
while True:  
    ret,frame = camera.read()  
    if not ret:  
        break  
    gray=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)  
    gray=cv2.GaussianBlur(gray,(21,21),0)  
    if firstframe is None:  
        firstframe=gray  
        continue  
      
    frameDelta = cv2.absdiff(firstframe,gray)  
    thresh = cv2.threshold(frameDelta, 25, 255, cv2.THRESH_BINARY)[1]  
    thresh = cv2.dilate(thresh, None, iterations=2)  
    # cnts= cv2.findContours(thresh.copy(),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)  
      
    x,y,w,h=cv2.boundingRect(thresh)  
    frame=cv2.rectangle(frame,(x,y),(x+w,y+h),(0,0,255),2)  
    cv2.imshow("frame", frame)  
    cv2.imshow("Thresh", thresh)  
    cv2.imshow("frame2", frameDelta)  
    key = cv2.waitKey(1)&0xFF  
      
    if key == ord("q"):  
        break
'''
if __name__ == '__main__':
    nesROMdata = read_file_to_array('mario.nes')
    nes_head = nesROMdata[:0x20]
    print (nes_head)
    #print hex(len(nesROMdata))
    #fig,axes=plt.subplots(nrows=2,ncols=2)#定一个2*2的plot
    plt.figure(figsize=(8,4))
    plt.show()
    
    if rom_ok(nes_head):
        i16K_ROM_NUMBER = get_16k_rom_num(nes_head)
        ROM,ROM_address_offset_end = get_block(0x10,i16K_ROM_NUMBER,0X4000)
        #print len(ROM[1]),hex(ROM_address_offset_end)

        
        i8K_VROM_NUMBER = get_8k_vrom_num(nes_head)
        VROM,VROM_address_offset_end = get_block(ROM_address_offset_end,i8K_VROM_NUMBER,0x2000)
        #print len(nesROMdata),hex(VROM_address_offset_end)
        
        print hex(len(VROM[0]))

        #font = cv2.FONT_HERSHEY_SIMPLEX

        fps = 0
        fps_t = ''
        s_t = 0
        
        while 1:
            fps += 1
            image=np.zeros([s_h * ratio,s_w * ratio,3],np.uint8)
            for i in xrange(0,len(VROM[0]),0x10):
                pass
                #print Tiles_arr(get_Tile(0,i))
                draw_str(get_Tile(0,i),i/16)
                #break

                if i>= 0x10*16:
                    pass
                    #break
            if time.time() - s_t >= 2:
                fps_t = 'fps:' + str(fps/(time.time() - s_t))
                fps = 0
                s_t = time.time()
            #else:
                #s_t = time.time()

            #if key == ord("q"):  
            #    break    
        tk.mainloop()
        
    #image = cv2.imread('8x8.png')
    
    #cv2.waitKey(0)
    #cv2.destroyAllWindows()
    #print(image.shape) # (h,w,c)
    #print(image.size)
    #print(image.dtype) 
    #print(image)

    
    # convert the images to PIL format...
    #image = Image.fromarray(image)
    # ...and then to ImageTk format
    #image = ImageTk.PhotoImage(image)




        
