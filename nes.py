# -*- coding: UTF-8 -*-
import os,re

import time
import datetime
import threading

import keyboard

#from numba import jit

#自定义类
from deco import *
from wrfilemod import read_file_to_array

#import mmc

from pal import pal

from vbfun import MemCopy



pow2 = [2**i for i in range(31)]#*(31) #As Long

pow2 +=  [-2147483648]


def fillTLook():
    tLook = [0] * 0x80000
    for b1 in range(0x100):             #= 0 To 255
        for b2 in range(0x100):              #= 0 To 255
            for X in range(0x8):                #= 0 To 7
                c = 1 if b1 & pow2[X] else  0
                c += 2 if b2 & pow2[X]  else 0
                tLook[b1 * 2048 + b2 * 8 + X] = c
    return tLook

class NES(object):       
    #EmphVal =0

    romName =''




    'DF: powers of 2'
    #pow2 = [0]*(31) #As Long

    #tilebased = False

        # NES Hardware defines

    CPU_RAM = [0]* 0x10000



        
    
    #VROM = []  


    #reg8 = 0 # As Byte
    #regA = 0 # As Byte
    #regC = 0 # As Byte
    #regE = 0 # As Byte

    NESPal = [0]*0xF #As Byte

        #Public CPal() As Long


    #FrameSkip = 0 #'Integer


        #tLook = [0]*0x80000 #颜色查询表
    CPal = [0x686868, 0x804000, 0x800000, 0x800040, 0x800080, 0x400080, 0x80, 0x55, 
    0x4040, 0x5033, 0x5000, 0x5000, 0x404000, 0x0, 0x0, 0x0, 
    0x989898, 0xC08000, 0xC04040, 0xC00080, 0xC000C0, 0x8000C0, 0x2020C0, 0x40C0, 
    0x8080, 0x8055, 0x8000, 0x338033, 0x808000, 0x0, 0x0, 0x0, 
    0xD0D0D0, 0xFFC040, 0xFF8080, 0xFF40C0, 0xFF00FF, 0xC040FF, 0x5050FF, 0x4080FF, 
    0xC0C0, 0xC080, 0xC000, 0x55C055, 0xC0C000, 0x333333, 0x0, 0x0,
    0xFFFFFF, 0xFFFF80, 0xFFC0C0, 0xFF80FF, 0xFF40FF, 0xFF80FF, 0x8080FF, 0x80C0FF, 
    0x40FFFF, 0x40FFC0, 0x40FF40, 0xAAFFAA, 0xFFFF40, 0x999999, 0x0, 0x0] #颜色板

    '''CPal = ["#686868", "#804000", "#800000", "#800040", "#800080", "#400080", "#80", "#55", 
    "#4040", "#5033", "#5000", "#5000", "#404000", "#0", "#0", "#0", 
    "#989898", "#C08000", "#C04040", "#C00080", "#C000C0", "#8000C0", "#2020C0", "#40C0", 
    "#8080", "#8055", "#8000", "#338033", "#808000", "#0", "#0", "#0", 
    "#D0D0D0", "#FFC040", "#FF8080", "#FF40C0", "#FF00FF", "#C040FF", "#5050FF", "#4080FF", 
    "#C0C0", "#C080", "#C000", "#55C055", "#C0C000", "#333333", "#0", "#0",
    "#FFFFFF", "#FFFF80", "#FFC0C0", "#FF80FF", "#FF40FF", "#FF80FF", "#8080FF", "#80C0FF", 
    "#40FFFF", "#40FFC0", "#40FF40", "#AAFFAA", "#FFFF40", "#999999", "#0", "#0"] #颜色板'''


    PatternTable =0 #Long
    NameTable =0 #Long

    'DF: powers of 2'


    
    bank_regs = [0]*16 #Byte

    maxCycles1 = 114
    Mapper = 0

    PROM_8K_SIZE  = 0
    PROM_16K_SIZE = 0
    PROM_32K_SIZE = 0

    VROM_1K_SIZE = 0
    VROM_2K_SIZE = 0
    VROM_4K_SIZE = 0
    VROM_8K_SIZE = 0

    
    Mapper, Mirroring, Trainer, FourScreen = 0,0,0,0
    MirrorXor = 0 # As Long 'Integer
    UsesSRAM = False #As Boolean
    
    SpecialWrite6000 = False
    
    CPUPaused = False #As Boolean

    CPURunning = False

    APURunning = True
    
    Frames = 0

    tLook = fillTLook()

    pow2 = [2**i for i in range(31)]#*(31) #As Long

    pow2 +=  [-2147483648]
    
    def __init__(self,debug = False):
        NESLoop = 0

        FirstRead = True

        self.debug = False









if __name__ == '__main__':
    pass

    
    print fillTLook()[0:100]
        










        
