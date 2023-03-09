# -*- coding: UTF-8 -*-
import os,re

import time
import datetime
import threading

import cv2

import keyboard

#from numba import jit

#自定义类
from deco import *
from wrfilemod import read_file_to_array

#import mmc

import rom
from rom import nesROM

#import cpu6502commands
from cpu6502commands import *

import cpu6502
from cpu6502 import *

from ppu import PPU
from apu import APU

from vbfun import MemCopy

from nes import NES


class neshardware(NES):       
    #EmphVal =0

    romName =''




    'DF: powers of 2'
    pow2 = [0]*(31) #As Long

    tilebased = False

        # NES Hardware defines

    CPU_RAM = [0]* 0x10000



        
    
    VROM = []  


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


    i16K_ROM_NUMBER = 0
    i8K_VROM_NUMBER = 0
    nesROMdata = []
    
    ROM = nesROM()
    
    
    maxCycles1 = 114
    
    def __init__(self,debug = False):
        NESLoop = 0
        CPURunning = True
        FirstRead = True

        SpriteAddress = 0
        self.debug = False
        self.cpu6502 = cpu6502()
        self.cpu6502.debug = debug

        self.cpu6502.PPU = PPU()
        self.cpu6502.APU = APU()
        self.cpu6502.JOYPAD1 = JOYPAD()
        self.cpu6502.JOYPAD2 = JOYPAD()
        
        #self.CPURunning = cpu6502.CPURunning

    def LoadROM(self,filename):
        self.ROM.LoadROM(filename)
        
            
    def PowerON(self):
        NES.CPURunning = True


    def StartingUp(self):
        init6502()
        self.cpu6502.PPU.pPPUinit()
        self.cpu6502.APU.pAPUinit()
    
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
            self.AndIt = self.ROM.ChrCount - 1
    
        LoadNES = self.MapperChoose(NES.Mapper)
        if LoadNES == 0 :
            return False

        #super().Mapper = self.ROM.Mapper
        #self.cpu6502.Mapper = self.ROM.Mapper
        #self.cpu6502.Mirroring = self.ROM.Mirroring
        #self.cpu6502.Trainer = self.ROM.Trainer
        #self.cpu6502.FourScreen = self.ROM.FourScreen
        #self.cpu6502.UsesSRAM = self.ROM.UsesSRAM #As Boolean
    
        print "Successfully loaded %s" %self.ROM.filename
        self.cpu6502.reset6502()
        self.cpu6502.PPU.MirrorXor = self.ROM.MirrorXor # As Long 'Integer

        start = time.time()
        starttk = time.time()
        totalFrame = 0

        self.PowerON()
        
        while NES.CPURunning:

            self.cpu6502.exec6502()
            if self.cpu6502.MapperWriteFlag:
                self.MapperWrite(self.cpu6502.MapperWriteData)

            if time.time() - start > 4:
                FPS =  'FPS: %d'%(totalFrame >> 2) # 
                if self.cpu6502.PPU.render:
                    cv2.setWindowTitle('Main',FPS)
                else:
                    print FPS,self.cpu6502.PPU.render,self.cpu6502.PPU.tilebased
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
            self.Select8KVROM(0)

            if self.ROM.PrgCount >= 2:
                
                self.reg8 = 0;self.regA = 1;self.regC = 2;self.regE = 3
                
            elif self.ROM.PrgCount == 1:
                self.reg8 = 0;self.regA = 1;self.regC = 0;self.regE = 1
            else:
                self.reg8 = 0;self.regA = 0;self.regC = 0;self.regE = 0
            self.SetupBanks()
            
        elif MapperType == 1:
            self.Select8KVROM(0)
            self.reg8 = 0;self.regA = 1;self.regC = 0xFE;self.regE = 0xFF
            self.SetupBanks()
            sequence = 0;accumulator = 0
            #Erase data
            #data(0) = &H1F: data(3) = 0
        
        elif MapperType == 2:
            self.reg8 = 0
            self.regA = 1
            self.regC = 0xFE
            self.regE = 0xFF
            self.SetupBanks()
        elif MapperType == 3:
            self.Select8KVROM( 0)
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
        if NES.Mapper == 0:
            return
        elif NES.Mapper == 2:
            self.reg8 = MapperWriteData['value'] * 2
            self.regA = self.reg8 + 1
            self.SetupBanks()
            self.cpu6502.MapperWriteFlag = False
        elif NES.Mapper == 3:
            self.Select8KVROM(MapperWriteData['value'] & self.AndIt)
        else:
            print "Unsupport MapperWrite", NES.Mapper
    #@deco
    def MaskVROM(self, page, mask):
        return page & (mask - 1)


    def Select8KVROM(self, val1):
        val1 = self.MaskVROM(val1, NES.VROM_8K_SIZE)
        MemCopy(self.cpu6502.PPU.VRAM, 0, self.VROM, val1 * 0x2000, 0x2000)

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

    #@deco
    def MaskBankAddress(self,bank):
        if bank >= self.ROM.PrgCount * 2 :
            i = 0xFF
            while (bank & i) >= self.ROM.PrgCount * 2:
                i = i // 2
            
            MaskBankAddress = (bank & i)
        else:
            MaskBankAddress = bank
        return MaskBankAddress

    def SetPROM_8K_Bank(self, page, bank ):
        pass
	#'''bank %= NES.PROM_8K_SIZE;
	#CPU_MEM_BANK[page] = PROM+0x2000*bank;
	#CPU_MEM_TYPE[page] = BANKTYPE_ROM;
	#CPU_MEM_PAGE[page] = bank;'''








if __name__ == '__main__':
    pass
    fc = neshardware(debug)
    print fc.Mapper
    #fc.debug = True
    fc.LoadROM(os.getcwd() + '\\roms\\Twinbee (J).nes')
    print fc.Mapper
    #print [[hex(i),hex(fc.MaskBankAddress(i)),hex(i & 0xF)] for i in range(255)]
    #print fc.MaskBankAddress(1)
    #print fc.MaskBankAddress(0xEE)
    #print fc.MaskBankAddress(0xFF)
    fc.StartingUp()
        










        
