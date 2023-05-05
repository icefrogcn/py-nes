# -*- coding: UTF-8 -*-
import os,re
import traceback

import time
import datetime
import threading

import rtmidi
import keyboard
import cv2
from numba import njit
import numpy as np


#自定义类
from deco import *
from wrfilemod import read_file_to_array

import memory

import rom
from rom import nesROM
from rom import get_Mapper_by_fn


from cpu6502commands import init6502

import cpu6502
from cpu6502 import cpu6502
#from cpu import *

from ppu import PPU
from apu import APU
from joypad import JOYPAD

from vbfun import MemCopy

from nes import NES

from mmc import MMC


class CONSLOE(MMC, NES):       
    #EmphVal =0

    romName =''

    FrameSkip = 0 #'Integer


    
    def __init__(self,debug = False):
        NESLoop = 0
        CPURunning = 1
        FirstRead = 1

        self.memory = memory.Memory()
        
        self.debug = debug
        self.nesROM = nesROM()
        
        self.JOYPAD1 = JOYPAD()
        self.JOYPAD2 = JOYPAD()

               
        #self.CPURunning = cpu6502.CPURunning

    def LoadROM(self,filename):
        self.NES = self.nesROM.LoadROM(filename)
        
            
    def PowerON(self):
        NES.CPURunning = True

    def PowerOFF(self):
        self.ShutDown()
        #self.APU.ShutDown()

        
    def StartingUp(self):
        init6502()
        print 'init PPU'
        self.PPU = PPU(self.memory, self.nesROM.ROM)
        self.PPU.pPPUinit(self.PPU_Running,self.PPU_render,self.PPU_debug)

        
        #self.ChannelWrite = ChannelWrite
        print 'init APU'
        self.APU = APU(self.memory)
        #self.APU.pAPUinit()

        
        
        print 'init MAPPER'
        MAPPER = __import__('mappers')
        cartridge = MAPPER.mapper.MAPPER(self.nesROM.ROM, self.memory)
        #self.PPU.cartridge = cartridge
        try:

            
            self.MAPPER = eval('MAPPER.mapper%d.MAPPER(cartridge)' %(self.nesROM.Mapper))
            print 'init CPU'
            self.CPU = cpu6502(self.memory, self.PPU, self.MAPPER, self.APU, #self.APU, 
                               self.JOYPAD1, self.JOYPAD2)
        
            self.MAPPER.reset()
            
            #self.CPU.debug = debug

            print "NEW MAPPER process"
            NES.newmapper_debug = 1
            LoadNES = 1
        except:
            print (traceback.print_exc())
            NES.newmapper_debug = 0
            
            self.MAPPER = cartridge
            print 'init CPU'
            self.CPU = cpu6502(self.memory, self.PPU, self.MAPPER, self.APU, #self.APU, 
                               self.JOYPAD1, self.JOYPAD2)
        
            LoadNES = self.MapperChoose(NES.Mapper)
            print 'OLD MapperWrite'
                
            if( NES.VROM_8K_SIZE ):
                self.Select8KVROM(0)
            else:
                pass
        
        print self.CPU.PRGRAM
        print type(self.CPU.PRGRAM)

        
        if LoadNES == 0 :
            return False

 
        print "Successfully loaded %s" %self.nesROM.filename
        self.CPU.reset6502()
        print "6502 reset:",self.CPU.status()
        #self.cpu6502.PPU.MirrorXor = self.ROM.MirrorXor # As Long 'Integer

        self.start = time.time()
        self.totalFrame = 0

        #self.PPU.ScrollToggle = 1
        self.PowerON()
        self.ScreenShow()


        self.midiout = rtmidi.MidiOut()
        self.available_ports = self.midiout.get_ports()
        print self.available_ports
        #self.APU.midiout = self.midiout
        #self.APU.available_ports = self.available_ports
        #print self.midiout.getportcount()
        
        if self.available_ports:
            self.midiout.open_port(0)
        else:
            self.midiout.open_virtual_port("My virtual output")

        self.midiout.send_message([0xC0,80]) #'Square wave'
        self.midiout.send_message([0xC1,80]) #'Square wave'
        self.midiout.send_message([0xC2,87]) #Triangle wave
        self.midiout.send_message([0xC3,127]) #Noise. Used gunshot. Poor but sometimes works.'


        
        
        self.Running = 1
        print 'First runing jitclass need complies about 10-60 seconds...ooh...wait...'
        while self.Running:

            self.CPU.exec6502()
            if self.CPU.FrameFlag:
                #self.APU.updateSounds()
                self.playSounds()
                #print self.CPU.PRGRAM[2][0:0x100]
                #print self.APU.Sound
                #print self.CPU.Sound
                
                if self.PPU_Running and self.PPU_render:
                    self.blitFrame()
                self.ShowFPS()
                self.CPU.FrameFlag = 0

                if keyboard.is_pressed('0'):
                    print "turnoff"
                    self.Running = 0

                
                self.JOYPAD1.Joypad[2] = self.JOYPAD1.BUTTON_PRESS if keyboard.is_pressed('v') else self.JOYPAD1.BUTTON_RELEASE
                self.JOYPAD1.Joypad[3] = self.JOYPAD1.BUTTON_PRESS if keyboard.is_pressed('b') else self.JOYPAD1.BUTTON_RELEASE
                
                self.JOYPAD1.Joypad[1] = self.JOYPAD1.BUTTON_PRESS if keyboard.is_pressed('j') else self.JOYPAD1.BUTTON_RELEASE
                self.JOYPAD1.Joypad[0] = self.JOYPAD1.BUTTON_PRESS if keyboard.is_pressed('k') else self.JOYPAD1.BUTTON_RELEASE
                
                self.JOYPAD1.Joypad[4] = self.JOYPAD1.BUTTON_PRESS if keyboard.is_pressed('w') else self.JOYPAD1.BUTTON_RELEASE
                self.JOYPAD1.Joypad[5] = self.JOYPAD1.BUTTON_PRESS if keyboard.is_pressed('s') else self.JOYPAD1.BUTTON_RELEASE
                self.JOYPAD1.Joypad[6] = self.JOYPAD1.BUTTON_PRESS if keyboard.is_pressed('a') else self.JOYPAD1.BUTTON_RELEASE
                self.JOYPAD1.Joypad[7] = self.JOYPAD1.BUTTON_PRESS if keyboard.is_pressed('d') else self.JOYPAD1.BUTTON_RELEASE


                
            
            if self.CPU.MapperWriteFlag:
                self.MapperWrite(self.CPU.MapperWriteAddress, self.CPU.MapperWriteData)
           
            
            

        self.PowerOFF()

    def playSounds(self):
        #print "Playing"
        #self.APU.Frames += 1
        if self.available_ports and self.APU.doSound :
            for ch in range(4):
                
                if self.APU.chk_SoundCtrl(ch):
                    #self.midiout.send_message([self.APU.SoundChannel[ch],self.APU.tones[ch],self.APU.volume[ch]])
                    if self.APU.SoundChannel[ch] and self.APU.volume[ch] > 0 and self.APU.tones[ch] != 0:
                        
                        self.midiout.send_message([0x90 + ch,self.APU.tones[ch],self.APU.volume[ch]])
                        self.APU.SoundChannel_ZERO(ch)
            
                    else:
                        self.midiout.send_message([0x80 + ch,self.APU.tones[ch],0])
                else:
                    self.midiout.send_message([0x80 + ch,self.APU.tones[ch],0])
                    self.APU.SoundChannel_ONE(ch)
                    
                if self.APU.Frames >= self.APU.lastFrame[ch]:
                    self.midiout.send_message([0x80 + ch,self.APU.tones[ch],0])
                    
            #self.midiout.send_message(self.APU.SoundBuffer[1])
            #self.midiout.send_message(self.APU.SoundBuffer[2])
            #self.midiout.send_message(self.APU.SoundBuffer[3])
            
            
    def blitFrame(self):
        self.FrameBuffer = paintBuffer(self.PPU.FrameArray,self.PPU.Pal,self.PPU.Palettes)
        if self.debug == False and self.PPU_render:
            pass
            self.blitScreen()
            self.blitPal()
        else:
            self.blitPatternTable()
            self.blitPal()
            
    def ScreenShow(self):
        if self.PPU_Running == 0:
            self.PPU_render = False
            return
        if self.PPU_Running and self.PPU_render and self.debug == False:
            cv2.namedWindow('Main', cv2.WINDOW_NORMAL)
            cv2.namedWindow('Pal', cv2.WINDOW_NORMAL)
            
        else:
            cv2.namedWindow('Pal', cv2.WINDOW_NORMAL)
            cv2.namedWindow('PatternTable0', cv2.WINDOW_NORMAL)
            cv2.namedWindow('SC_TEST', cv2.WINDOW_NORMAL)
        #cv2.namedWindow('PatternTable2', cv2.WINDOW_NORMAL)
        #cv2.namedWindow('PatternTable3', cv2.WINDOW_NORMAL)
    def ShutDown(self):
        if self.PPU_render:
            cv2.destroyAllWindows()
        if self.available_ports:
            self.midiout.close_port()
            
    def blitScreen(self):
        
        cv2.imshow("Main", self.FrameBuffer[self.PPU.scY:self.PPU.scY + 240,self.PPU.scX:self.PPU.scX+256])
        cv2.waitKey(1)

    def blitPal(self):
        cv2.imshow("Pal", np.array([[self.PPU.Pal[i] for i in self.PPU.Palettes]]))
        cv2.waitKey(1)

    def blitPatternTable(self):
        cv2.line(self.FrameBuffer,(0,240),(768,240),(0,255,0),1) 
        cv2.line(self.FrameBuffer,(0,480),(768,480),(0,255,0),1) 
        cv2.line(self.FrameBuffer,(256,0),(256,720),(0,255,0),1) 
        cv2.line(self.FrameBuffer,(512,0),(512,720),(0,255,0),1) 
        cv2.rectangle(self.FrameBuffer, (self.PPU.scX,self.PPU.scY),(self.PPU.scX+255,self.PPU.scY + 240),(0,0,255),1)
        cv2.imshow("PatternTable0", self.FrameBuffer)
        cv2.waitKey(1)
        
    def ShowFPS(self):
        if time.time() - self.start > 4:
                FPS =  'FPS: %d'%(self.totalFrame >> 2) # 
                if self.CPU.PPU.debug == False:
                    
                    cv2.setWindowTitle('Main',"%s %d %d %d"%(FPS,self.CPU.PPU.CurrentLine,self.CPU.PPU.vScroll,self.CPU.PPU.HScroll))
                else:
                    print FPS,self.CPU.PPU.render,self.CPU.PPU.tilebased
                self.start = time.time()
                self.totalFrame = 0
        self.totalFrame += 1
        
    def MapperChoose(self,MapperType):
        MapperChoose = 1
        if MapperType == 0:
            self.Select8KVROM(0)

            if self.nesROM.PrgCount >= 2:
                
                self.reg8 = 0; self.regA = 1; self.regC = 2; self.regE = 3
                
            elif self.nesROM.PrgCount == 1:
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

    def MapperWrite(self,MapperWriteAddress, MapperWriteData):
        self.CPU.MapperWriteFlag = False
        if NES.Mapper == 0:
            pass
        elif NES.Mapper == 2:
            self.reg8 = MapperWriteData * 2
            self.regA = self.reg8 + 1
            self.SetupBanks()
            
        elif NES.Mapper == 3:
            self.Select8KVROM(MapperWriteData & self.ROM.AndIt)
            
        elif NES.Mapper == 4:
            self.MMC3Write(MapperWriteData, MapperWriteAddress) #' this function is too big to store here..
            
        else:
            print "Unsupport MapperWrite", NES.Mapper
        
    #@deco
    def MaskVROM(self, page, mask):
        return page & (mask - 1)


    def Select8KVROM(self, val1):
        #val1 = self.MaskVROM(val1, NES.VROM_8K_SIZE)
        #self.cpu6502.PPU.VRAM[0:0x2000] = MMC.Select8KVROM(self, val1, self.ROM.VROM)
        self.PPU.VRAM[0:0x2000] = self.nesROM.VROM[val1 * 0x2000 : val1 * 0x2000 + 0x2000]


    def Select1KVROM(self, val1, bank):
        val1 = self.MaskVROM(val1, self.nesROM.ChrCount * 8)
        if NES.Mapper == 4:
            MemCopy(self.PPU.VRAM, (MMC.MMC3_ChrAddr ^ (bank * 0x400)), self.nesROM.VROM, (val1 * 0x400), 0x400)
            
        elif NES.Mapper == 23:
            pass
            #MemCopy VRAM(bank * &H400&), VROM(val1 * &H400&), &H400&
        else:
            pass
            #MemCopy VRAM(bank * &H400&), VROM(val1 * &H400&), &H400&


    #'only switches banks when needed
    #'******只有需要时才切换******
    def SetupBanks(self):

        self.reg8 = MaskBankAddress(self.reg8,self.nesROM.PrgCount)
        self.regA = MaskBankAddress(self.regA,self.nesROM.PrgCount)
        self.regC = MaskBankAddress(self.regC,self.nesROM.PrgCount)
        self.regE = MaskBankAddress(self.regE,self.nesROM.PrgCount)
        
        '''
        self.cpu6502.bank8 = np.array(self.PRGROM[self.reg8 * 0x2000: self.reg8 * 0x2000 + 0x2000], np.uint8)
        self.cpu6502.bankA = np.array(self.PRGROM[self.regA * 0x2000: self.regA * 0x2000 + 0x2000], np.uint8)
        self.cpu6502.bankC = np.array(self.PRGROM[self.regC * 0x2000: self.regC * 0x2000 + 0x2000], np.uint8)
        self.cpu6502.bankE = np.array(self.PRGROM[self.regE * 0x2000: self.regE * 0x2000 + 0x2000], np.uint8)
        '''

        MemCopy(self.CPU.PRGRAM[4], 0, self.nesROM.PROM, self.reg8 * 0x2000, 0x2000)
        MemCopy(self.CPU.PRGRAM[5], 0, self.nesROM.PROM, self.regA * 0x2000, 0x2000)
        MemCopy(self.CPU.PRGRAM[6], 0, self.nesROM.PROM, self.regC * 0x2000, 0x2000)
        MemCopy(self.CPU.PRGRAM[7], 0, self.nesROM.PROM, self.regE * 0x2000, 0x2000)
        #print len(self.CPU.bankE)

    
    
    #@deco
    def MaskBankAddress(self,bank):
        if bank >= self.nesROM.PrgCount * 2 :
            i = 0xFF
            while (bank & i) >= self.nesROM.PrgCount * 2:
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

@njit
def MaskBankAddress(bank, PrgCount):
        if bank >= PrgCount * 2 :
            i = 0xFF
            while (bank & i) >= PrgCount * 2:
                i = i // 2
            
            MaskBankAddress = (bank & i)
        else:
            MaskBankAddress = bank
        return MaskBankAddress
@njit
def paintBuffer(FrameBuffer,Pal,Palettes):
    [rows, cols] = FrameBuffer.shape
    img = np.zeros((rows, cols,3),np.uint8)
    for i in range(rows):
        for j in range(cols):
            img[i, j] = Pal[Palettes[FrameBuffer[i, j]]]
    return img
    
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

def run(debug = False):
    ROMS = roms_list()
    ROMS_INFO = get_roms_mapper(ROMS)
    fc = CONSLOE(debug)
    while True:
        show_choose(ROMS_INFO)
        gn = input("choose a number: ")
        print gn
        if gn == 999:
            break
        if not gn <= len(ROMS):
            continue
        #fc.debug = True
        fc.LoadROM(ROMS_DIR + ROMS[gn])
        fc.PPU_Running = 1
        fc.PPU_render = 1
        fc.PPU_debug = debug
        fc.StartingUp()
        
if __name__ == '__main__':
    run(True)

        










        
