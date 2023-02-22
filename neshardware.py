# -*- coding: UTF-8 -*-
import os,re

import time
import datetime
import threading

#from numba import jit

#自定义类
from deco import *
from wrfilemod import read_file_to_array

#import mmc

import rom
from rom import nesROM

import cpu6502commands
from cpu6502commands import *

import cpu6502
from cpu6502 import *

from apu import APU

from vbfun import MemCopy



class neshardware:       
    EmphVal =0

    romName =''

    'DF: array to draw each frame to'
    vBuffer = [0]* (256 * 241 - 1) 
    '256*241 to allow for some overflow     可以允许一些溢出'

    vBuffer16 = [0]*(256 * 240 - 1) #As Integer
    vBuffer32 = [0]*(256 * 240 - 1) #As Long

    tLook = [0]*(65536 * 8 - 1) #As Byte


    'DF: powers of 2'
    pow2 = [0]*(31) #As Long

    tilebased = False

        # NES Hardware defines

    CPU_RAM = [0]* 0x10000



        
    VRAM = [0]*0x4000 # Video RAM
    VROM = []  
    SpriteRAM = [0]*0xFF     #活动块存储器，单独的一块，不占内存nes_ROM_data =[]

        #Sound(0 To &H15) As Byte
        #SoundCtrl As Byte

    PrgCount = 0 # As Byte
    PrgCount2 = 0 # As Long
    ChrCount = 0 # As Byte,
    ChrCount2 = 0 # As Long


    reg8 = 0 # As Byte
    regA = 0 # As Byte
    regC = 0 # As Byte
    regE = 0 # As Byte

    NESPal = [0]*0xF #As Byte

        #Public CPal() As Long


    FrameSkip = 0 #'Integer


        #tLook = [0]*0x80000 #颜色查询表
    CPal = ["#686868", "#804000", "#800000", "#800040", "#800080", "#400080", "#80", "#55", 
    "#4040", "#5033", "#5000", "#5000", "#404000", "#0", "#0", "#0", 
    "#989898", "#C08000", "#C04040", "#C00080", "#C000C0", "#8000C0", "#2020C0", "#40C0", 
    "#8080", "#8055", "#8000", "#338033", "#808000", "#0", "#0", "#0", 
    "#D0D0D0", "#FFC040", "#FF8080", "#FF40C0", "#FF00FF", "#C040FF", "#5050FF", "#4080FF", 
    "#C0C0", "#C080", "#C000", "#55C055", "#C0C000", "#333333", "#0", "#0",
    "#FFFFFF", "#FFFF80", "#FFC0C0", "#FF80FF", "#FF40FF", "#FF80FF", "#8080FF", "#80C0FF", 
    "#40FFFF", "#40FFC0", "#40FF40", "#AAFFAA", "#FFFF40", "#999999", "#0", "#0"] #颜色板

    PatternTable =0 #Long
    NameTable =0 #Long

    bank_regs = [0]*16 #Byte

    PPU_InVBlank = 0x80
    PPU_Sprite0 = 0x40
    PPU_SpriteCount = 0x20
    PPU_Ignored = 0x10

    i16K_ROM_NUMBER = 0
    i8K_VROM_NUMBER = 0
    nesROMdata = []
    
    ROM = nesROM()
    
    
    maxCycles1 = 114
    
    def __init__(self,debug = False):
        NESLoop = 0
        CPURunning = True
        FirstRead = True
        PPU_AddressIsHi = True
        PPUAddress = 0
        SpriteAddress = 0
        self.debug = False
        self.cpu6502 = cpu6502()
        self.cpu6502.debug = debug

        #self.apu = APU()
        
        self.CPURunning = cpu6502.CPURunning

        



    def StartingUp(self):
    
        '****读取图像数据****'
        self.gameImage = [0] * self.ROM.PrgMark
        #self.gameImage = self.ROM.data[17:self.ROM.PrgMark]# Byte
        MemCopy(self.gameImage,0, self.ROM.data, 17 - 1, self.ROM.PrgMark)
         
        '****读取程序数据****'
        #ReDim VROM(ChrCount2 * &H2000&) As Byte
        self.VROM =[0] * (self.ROM.ChrCount2 * 0x2000) 
        self.ROM.PrgMark = 0x4000 * self.ROM.PrgCount2 + 17
        if self.ROM.ChrCount2:
            
            #self.VROM = self.ROM.data[self.ROM.PrgMark:(self.ROM.ChrCount2 * 0x2000)] # Byte
            MemCopy (self.VROM,0, self.ROM.data, self.ROM.PrgMark, len(self.VROM))
            self.AndIt = self.ChrCount - 1
    
        LoadNES = self.MapperChoose(self.ROM.Mapper)
        if LoadNES == 0 :
            return False

        self.cpu6502.Mapper = self.ROM.Mapper
        self.cpu6502.Mirroring = self.ROM.Mirroring
        self.cpu6502.Trainer = self.ROM.Trainer
        self.cpu6502.FourScreen = self.ROM.FourScreen
        self.cpu6502.MirrorXor = self.ROM.MirrorXor # As Long 'Integer
        self.cpu6502.UsesSRAM = self.ROM.UsesSRAM #As Boolean
    
        print "Successfully loaded %s" %self.ROM.filename
        self.cpu6502.reset6502()

        init6502()
        start = time.time()
        starttk = time.time()
        totalFrame = 0
        while self.CPURunning:
            
            self.cpu6502.exec6502()
            if self.cpu6502.MapperWrite:
                self.MapperWrite(self.cpu6502.MapperWriteData)

            if time.time() - start > 2:
                print 'FPS:',totalFrame >> 1
                start = time.time()
                totalFrame = 0

            totalFrame += 1 if self.cpu6502.FrameFlag else 0

            self.cpu6502.FrameFlag = False
            
        '''If Mirroring = 1 Then MirrorXor = &H800& Else MirrorXor = &H400&
    

    CurrentLine = 0
    For i = 0 To 7
        Joypad1(i) = &H40
    Next i
    Frames = 0
    CPUPaused = False
    ScrollToggle = 1
    LoadNES = 1
'''
    def MapperChoose(self,MapperType):
        MapperChoose = 1
        if MapperType == 0:
            if self.ROM.PrgCount >= 2:
                self.reg8 = 0;self.regA = 1;self.regC = 2;self.regE = 3
            elif self.ROM.PrgCount == 1:
                self.reg8 = 0;self.regA = 1;self.regC = 0;self.regE = 1
            else:
                self.reg8 = 0;self.regA = 0;self.regC = 0;self.regE = 0
            self.Select8KVROM(0)
            self.SetupBanks()

        elif MapperType == 2:
            self.reg8 = 0
            self.regA = 1
            self.regC = 0xFE
            self.regE = 0xFF
            self.SetupBanks()
        else:
            print "Unsupport Mapper",MapperType
            MapperChoose = 0
        return MapperChoose

    '===================================='
    '       MapperWrite(Address,value)   '
    ' Selects/Switches Chr-ROM & Prg-  '
    ' ROM depending on the mapper. Based '
    ' on DarcNES.                        '
    '===================================='

    def MapperWrite(self,MapperWriteData):
        if self.ROM.Mapper == 2:
            self.reg8 = MapperWriteData['value'] * 2
            self.regA = self.reg8 + 1
            self.SetupBanks()
            self.cpu6502.MapperWrite = False
        else:
            print "Unsupport MapperWrite", self.ROM.Mapper
    #@deco
    def MaskVROM(self, page, mask):
        return page & (mask - 1)


    def Select8KVROM(self, val1):
        val1 = self.MaskVROM(val1, self.ROM.ChrCount)
        MemCopy(self.VRAM,0 , self.VROM, val1 * 0x2000, 0x2000)

    #'only switches banks when needed
    #'******只有需要时才切换******
    def SetupBanks(self):

        self.reg8 = self.MaskBankAddress(self.reg8)
        self.regA = self.MaskBankAddress(self.regA)
        self.regC = self.MaskBankAddress(self.regC)
        self.regE = self.MaskBankAddress(self.regE)
        
    
        MemCopy(self.cpu6502.bank8, 0, self.gameImage, self.reg8 * 0x2000, 0x2000)
        MemCopy(self.cpu6502.bankA, 0, self.gameImage, self.regA * 0x2000, 0x2000)
        MemCopy(self.cpu6502.bankC, 0, self.gameImage, self.regC * 0x2000, 0x2000)
        MemCopy(self.cpu6502.bankE, 0, self.gameImage, self.regE * 0x2000, 0x2000)
        #print len(self.CPU.bankE)

    def MaskBankAddress(self,bank):
        if bank >= self.ROM.PrgCount * 2 :
            i = 0xFF
            while (bank & i) >= self.ROM.PrgCount * 2:
                i = i // 2
            
            MaskBankAddress = (bank & i)
        else:
            MaskBankAddress = bank
        return MaskBankAddress



    






if __name__ == '__main__':
    pass
    fc = neshardware(debug)
    #fc.debug = True
    fc.ROM.LoadNES(os.getcwd() + '\\roms\\1944.nes')
    fc.StartingUp()
        










        
