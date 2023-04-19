# -*- coding: UTF-8 -*-
import os,re
import traceback

import time
import datetime
import threading


import keyboard
import cv2

#from numba import jit

#自定义类
from deco import *
from wrfilemod import read_file_to_array


import rom
from rom import nesROM as ROM
from rom import get_Mapper_by_fn


from cpu6502commands import init6502

import cpu6502
from cpu6502 import *

from ppu import PPU
from apu import APU

from vbfun import MemCopy

from nes import NES

from mmc import MMC


class neshardware(MMC, NES):       
    #EmphVal =0

    romName =''




    'DF: powers of 2'
    pow2 = [0]*(31) #As Long

    tilebased = False

        # NES Hardware defines

    

    ROM = ROM()
    reg8 = 0 # As Byte
    regA = 0 # As Byte
    regC = 0 # As Byte
    regE = 0 # As Byte

    NESPal = [0]*0xF #As Byte

        #Public CPal() As Long


    FrameSkip = 0 #'Integer


    PatternTable =0 #Long
    NameTable =0 #Long

    bank_regs = [0]*16 #Byte

   
    
    
    def __init__(self,debug = False):
        NESLoop = 0
        CPURunning = True
        FirstRead = True

        SpriteAddress = 0
        self.debug = debug
        
        self.PPU = PPU()
        
        self.APU = APU()
        self.JOYPAD1 = JOYPAD()
        self.JOYPAD2 = JOYPAD()

        self.PRGRAM = np.zeros((8,0x2000), dtype=np.uint8)

        self.cpu6502 = cpu6502(self.PRGRAM,self.PPU, self.APU, self.JOYPAD1, self.JOYPAD2)
        self.cpu6502.debug = debug
        
        #self.CPURunning = cpu6502.CPURunning

    def LoadROM(self,filename):
        self.ROM.LoadROM(filename)
        
            
    def PowerON(self):
        NES.CPURunning = True

    def PowerOFF(self):
        self.PPU.ShutDown()
        self.APU.ShutDown()

        
    def StartingUp(self):
        init6502()
        self.PPU.pPPUinit()
        self.APU.pAPUinit()

        
        try:
            PRGRAM = 'self.PRGRAM'
            VRAM = 'self.PPU.VRAM'
            mapper = __import__('mapper',fromlist = ['mapper%d' %self.Mapper])
            self.cpu6502.MAPPER = eval('mapper.mapper%d.MAPPER(%s,%s)' %(self.Mapper,PRGRAM,VRAM))
            self.MAPPER = eval('mapper.mapper%d.MAPPER(%s,%s)' %(self.Mapper,PRGRAM,VRAM))
            self.MAPPER.reset()
            print self.cpu6502.PRGRAM
            #self.cpu6502.PRGRAM = self.MAPPER.reset()
            print  type(self.cpu6502.PRGRAM)
            print "NEW MAPPER process"
            NES.newmapper_debug = 1
            LoadNES = 1
        except:
            print (traceback.print_exc())
            NES.newmapper_debug = 0
            mapper = __import__('mapper')
            self.cpu6502.MAPPER = mapper.MAPPER(self.cpu6502.PRGRAM,self.cpu6502.PPU.VRAM)
            LoadNES = self.MapperChoose(NES.Mapper)
            if( NES.VROM_8K_SIZE ):
                self.Select8KVROM(0)
            else:
                pass
        

        
        if LoadNES == 0 :
            return False

 
        print "Successfully loaded %s" %self.ROM.filename
        self.cpu6502.reset6502()
        #self.cpu6502.PPU.MirrorXor = self.ROM.MirrorXor # As Long 'Integer

        start = time.time()
        starttk = time.time()
        totalFrame = 0

        self.PPU.ScrollToggle = 1
        self.PowerON()
        self.PPU.ScreenShow()
        
        while NES.CPURunning:

            self.cpu6502.exec6502()
            if self.cpu6502.MapperWriteFlag:
                self.MapperWrite(self.cpu6502.MapperWriteData)

            if time.time() - start > 4:
                FPS =  'FPS: %d'%(totalFrame >> 2) # 
                if self.cpu6502.PPU.debug == False:
                    
                    cv2.setWindowTitle('Main',"%s %d %d %d"%(FPS,self.cpu6502.PPU.CurrentLine,self.cpu6502.PPU.vScroll,self.cpu6502.PPU.HScroll))
                else:
                    print FPS,self.cpu6502.PPU.render,self.cpu6502.PPU.tilebased
                start = time.time()
                totalFrame = 0

            
            totalFrame += 1 if self.cpu6502.FrameFlag else 0
            #print self.cpu6502.PPU.VRAM
            self.cpu6502.FrameFlag = False

        self.PowerOFF()
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
                
                self.reg8 = 0; self.regA = 1; self.regC = 2; self.regE = 3
                
            elif self.ROM.PrgCount == 1:
                self.reg8 = 0; self.regA = 1; self.regC = 0; self.regE = 1
            else:
                self.reg8 = 0; self.regA = 0; self.regC = 0; self.regE = 0
            self.SetupBanks()
            
        elif MapperType == 1:
            self.Select8KVROM(0)
            self.reg8 = 0; self.regA = 1; self.regC = 0xFE; self.regE = 0xFF
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
            self.Select8KVROM(0)
            self.reg8 = 0
            self.regA = 1
            self.regC = 0xFE
            self.regE = 0xFF
            self.SetupBanks()
            
        elif MapperType == 4:
            MMC.swap = 0
            self.reg8 = 0
            self.regA = 1
            self.regC = 0xFE
            self.regE = 0xFF
            self.MMC3_Sync()
            MMC.MMC3_IrqVal = 0
            MMC.irq_enable = False
            MMC.MMC3_TmpVal = 0
            if NES.VROM_8K_SIZE :
                self.Select8KVROM(0)

            
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
        self.cpu6502.MapperWriteFlag = False
        if NES.Mapper == 0:
            pass
        elif NES.Mapper == 2:
            self.reg8 = MapperWriteData['value'] * 2
            self.regA = self.reg8 + 1
            self.SetupBanks()
            
        elif NES.Mapper == 3:
            self.Select8KVROM(MapperWriteData['value'] & self.ROM.AndIt)
            
        elif NES.Mapper == 4:
            self.MMC3Write(MapperWriteData['value'], MapperWriteData['Address']) #' this function is too big to store here..
            
        else:
            print "Unsupport MapperWrite", NES.Mapper
        
    #@deco
    def MaskVROM(self, page, mask):
        return page & (mask - 1)


    def Select8KVROM(self, val1):
        #val1 = self.MaskVROM(val1, NES.VROM_8K_SIZE)
        #self.cpu6502.PPU.VRAM[0:0x2000] = MMC.Select8KVROM(self, val1, self.ROM.VROM)
        self.cpu6502.PPU.VRAM[0:0x2000] = NES.VROM[val1 * 0x2000 : val1 * 0x2000 + 0x2000]
        #MemCopy(self.cpu6502.PPU.VRAM, 0, self.ROM.VROM, val1 * 0x2000, 0x2000)

    def Select1KVROM(self, val1, bank):
        val1 = self.MaskVROM(val1, self.ROM.ChrCount * 8)
        if NES.Mapper == 4:
            MemCopy(self.PPU.VRAM, (MMC.MMC3_ChrAddr ^ (bank * 0x400)), NES.VROM, (val1 * 0x400), 0x400)
            
        elif NES.Mapper == 23:
            pass
            #MemCopy VRAM(bank * &H400&), VROM(val1 * &H400&), &H400&
        else:
            pass
            #MemCopy VRAM(bank * &H400&), VROM(val1 * &H400&), &H400&


    #'only switches banks when needed
    #'******只有需要时才切换******
    def SetupBanks(self):

        self.reg8 = MaskBankAddress(self.reg8,self.ROM.PrgCount)
        self.regA = MaskBankAddress(self.regA,self.ROM.PrgCount)
        self.regC = MaskBankAddress(self.regC,self.ROM.PrgCount)
        self.regE = MaskBankAddress(self.regE,self.ROM.PrgCount)
        
        '''
        self.cpu6502.bank8 = np.array(self.PRGROM[self.reg8 * 0x2000: self.reg8 * 0x2000 + 0x2000], np.uint8)
        self.cpu6502.bankA = np.array(self.PRGROM[self.regA * 0x2000: self.regA * 0x2000 + 0x2000], np.uint8)
        self.cpu6502.bankC = np.array(self.PRGROM[self.regC * 0x2000: self.regC * 0x2000 + 0x2000], np.uint8)
        self.cpu6502.bankE = np.array(self.PRGROM[self.regE * 0x2000: self.regE * 0x2000 + 0x2000], np.uint8)
        '''

        MemCopy(self.PRGRAM[4], 0, self.ROM.PROM, self.reg8 * 0x2000, 0x2000)
        MemCopy(self.PRGRAM[5], 0, self.ROM.PROM, self.regA * 0x2000, 0x2000)
        MemCopy(self.PRGRAM[6], 0, self.ROM.PROM, self.regC * 0x2000, 0x2000)
        MemCopy(self.PRGRAM[7], 0, self.ROM.PROM, self.regE * 0x2000, 0x2000)
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


    def MMC3_Sync(self):
        if MMC.swap:
            self.reg8 = 0xFE
            self.regA = MMC.PrgSwitch2
            self.regC = MMC.PrgSwitch1
            self.regE = 0xFF
        else:
            self.reg8 = MMC.PrgSwitch1
            self.regA = MMC.PrgSwitch2
            self.regC = 0xFE
            self.regE = 0xFF
        
        self.SetupBanks()

    def MMC3Write(self,value, Address):
        if Address == 0x8000:
                MMC.MMC3_Command = value & 0x7
                MMC.MMC3_ChrAddr == 0x1000 if value & 0x80 else  0
                MMC.swap = 1 if value & 0x40 else 0
                
        elif Address == 0x8001:
            if MMC.MMC3_Command == 0:
                self.Select1KVROM( value, 0)
                self.Select1KVROM( value + 1, 1)
            elif MMC.MMC3_Command == 1:
                self.Select1KVROM( value, 2)
                self.Select1KVROM( value + 1, 3)
            elif MMC.MMC3_Command == 2:
                self.Select1KVROM( value, 4)
            elif MMC.MMC3_Command == 3:
                self.Select1KVROM( value, 5)
            elif MMC.MMC3_Command == 4:
                self.Select1KVROM( value, 6)
            elif MMC.MMC3_Command == 5:
                self.Select1KVROM( value, 7)
            elif MMC.MMC3_Command == 6:
                MMC.PrgSwitch1 = value
                self.MMC3_Sync()
            elif MMC.MMC3_Command == 7:
                MMC.PrgSwitch2 = value
                self.MMC3_Sync()
                
        elif Address == 0xA000:
            NES.Mirroring = 0 if value & 1 else 1
            NES.MirrorXor = ((NES.Mirroring + 1) % 3) * 0x400

        elif Address == 0xA001:
            NES.UsesSRAM = True if value else False
        elif Address == 0xC000:
            MMC.MMC3_IrqVal = value
        elif Address == 0xC001:
            MMC.MMC3_TmpVal = value
        elif Address == 0xE000:
            MMC.irq_enable = False
            MMC.MMC3_IrqVal = MMC.MMC3_TmpVal
        elif Address == 0xE001:
            MMC.irq_enable = True

@jit
def MaskBankAddress(bank, PrgCount):
        if bank >= PrgCount * 2 :
            i = 0xFF
            while (bank & i) >= PrgCount * 2:
                i = i // 2
            
            MaskBankAddress = (bank & i)
        else:
            MaskBankAddress = bank
        return MaskBankAddress

    
def show_rom_info(ROM):
    print "[ " , ROM.PrgCount , " ] 16kB ROM Bank(s)"
    print "[ " , ROM.ChrCount , " ] 8kB CHR Bank(s)"
    print "[ " , ROM.ROMCtrl , " ] ROM Control Byte #1"
    print "[ " , ROM.ROMCtrl2 , " ] ROM Control Byte #2"
    print "[ " , ROM.Mapper , " ] Mapper"
    print "Mirroring=" , ROM.Mirroring , " Trainer=" , ROM.Trainer , " FourScreen=" , ROM.FourScreen , " SRAM=" , ROM.UsesSRAM
    

ROMS_DIR = os.getcwd()+ '\\roms\\'
#ROMS_DIR = 'F:\\individual_\\Amuse\\EMU\FCSpec\\'

def roms_list():
    return [item for item in os.listdir(ROMS_DIR) if ".nes" in item.lower()]

def get_roms_mapper(roms_list):
    roms_info = []
    for i,item in enumerate(roms_list):
        mapper = get_Mapper_by_fn(ROMS_DIR + item)
        #if mapper in [0,2]:
            
        roms_info.append([i,item,get_Mapper_by_fn(ROMS_DIR + item)])
    return roms_info
        
def show_choose(ROMS_INFO):
    for item in ROMS_INFO:
        print item[0],item[1],item[2]
    print "---------------"
    print 'choose a number as a selection.'

def run(debug = True):
    ROMS = roms_list()
    ROMS_INFO = get_roms_mapper(ROMS)
    while True:
        show_choose(ROMS_INFO)
        gn = input("choose a number: ")
        print gn
        if gn == 'c':
            break
        if not gn <= len(ROMS):
            continue
        fc = neshardware(debug)
        #fc.debug = True
        fc.LoadROM(ROMS_DIR + ROMS[gn])
        fc.PPU.Running = 1
        fc.PPU.render = 1
        fc.PPU.debug = debug
        fc.StartingUp()
        
if __name__ == '__main__':
    run(True)

        










        
