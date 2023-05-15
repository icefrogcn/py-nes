# -*- coding: UTF-8 -*-
import os,shutil,re
import traceback

import time

import datetime
import threading
import multiprocessing

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


from cpu6502_opcodes import init6502

#import cpu6502
#from cpu6502 import cpu6502


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

        print print_now(),'init APU'
        self.APU = APU(self.memory)
        #self.APU.pAPUinit()
        self.JOYPAD1 = JOYPAD()
        self.JOYPAD2 = JOYPAD()

        #self.FrameBuffer = np.zeros((720, 768, 3),np.uint8)
               
        #self.CPURunning = cpu6502.CPURunning
        
    @property
    def status(self):
        return "PC:%d,clockticks:%d PPUSTATUS:%d,CurrLine:%d a:%d X:%d Y:%d S:%d p:%d opcode:%d " %self.CPU.status()
    
    def LoadROM(self,filename):
        self.ROM = self.nesROM.LoadROM(filename)
        
            
    def PowerON(self):
        NES.CPURunning = True

    def PowerOFF(self):
        self.ShutDown()
        #self.APU.ShutDown()

    def initMIDI(self):
        pass

    def Load_MAPPER_New(self):
        cartridge = __import__('mappers.main',fromlist = ['MAPPER'])#['MAIN',MAIN_class_type])
        MAPPER = cartridge.MAPPER(self.ROM, self.memory)

        shutil.copyfile('mappers/mapper%d.py' %MAPPER.Mapper,'mappers/mapper.py' )  #set new MAPPER class
            
        new_MAPPER = __import__('mappers.mapper',fromlist = ['MAPPER'])
            
        return new_MAPPER.MAPPER(MAPPER)

    def Load_MAPPER_Old(self):
        shutil.copyfile('mappers/main.py','mappers/mapper.py' )  #set OLD MAPPER class

        cartridge = __import__('mappers.mapper',fromlist = ['MAPPER'])#['MAIN',MAIN_class_type])
        return cartridge.MAPPER(self.ROM, self.memory)

    def import_CPU_class(self):
        print print_now(),'init CPU'
        fresh_pyc("cpu6502.pyc")
        CPU = __import__('cpu6502',fromlist=['cpu6502'])
        return CPU.cpu6502(self.memory, self.PPU, self.MAPPER, self.APU.ChannelWrite)#, #self.APU,)
         

    
    def StartingUp(self):
        init6502()
        #PPU = __import__('ppu',fromlist = ['PPU'])
        print print_now(),'init PPU'
        self.PPU = PPU(self.memory, self.ROM)
        self.PPU.pPPUinit(self.PPU_Running,self.PPU_render,self.PPU_debug)
        #self.FrameBuffer = self.PPU.FrameBuffer
        
        print print_now(),'init MAPPER'

        try:
            
            self.MAPPER = self.Load_MAPPER_New()
            self.CPU = self.import_CPU_class()
            self.CPU.SET_NEW_MAPPER_TRUE()
            
            self.MAPPER.reset()
            
            LoadNES = 1
            print print_now(),"NEW MAPPER process"


        except:
            print (traceback.print_exc())
            
       
            self.MAPPER = self.Load_MAPPER_Old()
            self.CPU = self.import_CPU_class()
            self.CPU.SET_NEW_MAPPER_FALSE()
                
            if( NES.VROM_8K_SIZE ):
                self.Select8KVROM(0)
                
            LoadNES = self.MapperChoose(NES.Mapper)
            print print_now(),'OLD MapperWrite'


        print self.CPU.PRGRAM
        print type(self.CPU.PRGRAM)

        
        if LoadNES == 0 :
            return False

 
        print print_now(),"Successfully loaded %s" %self.nesROM.filename
        
        self.start = time.time()
        self.totalFrame = 0

        #self.PPU.ScrollToggle = 1
        self.PowerON()
        self.ScreenShow()



        
        print print_now(),"The number of CPU is:",str(multiprocessing.cpu_count())
        print print_now(),'Parent process %s.' % os.getpid()
        self.pool = multiprocessing.Pool(multiprocessing.cpu_count())

            
        self.Running = 1

        self.CPU.reset6502()
        print '6502 reset:', self.status 
        
        Waiting_thread = threading.Thread(target = self.Waiting_compiling)
        Waiting_thread.setDaemon(True)
        Waiting_thread.start()
        fps_thread = threading.Thread(target = self.ShowFPS)
        fps_thread.setDaemon(True)
        fps_thread.start()
        #if self.PPU_Running and self.PPU_render:

        #    blit_thread.start()

        blit_delay = 0
        self.Frames = 0
        wish_fps = 60
        start = time.time()
        while self.Running:
            #t = threading.Thread(target = self.CPU.exec6502)
            #t.start()
            FrameFlag = self.CPU.exec6502()
            #self.CPU.exec6502()
            #blit_delay = time.time()

            if FrameFlag & self.CPU.FrameSound:
                self.APU.updateSounds(self.CPU.Frames)

            
            if FrameFlag & self.CPU.FrameRender:
                #Frames = self.CPU.Frames
                if self.CPU.Frames % wish_fps == 0 or blit_delay/((self.CPU.Frames % wish_fps) + 1) <= (1.000/wish_fps):
                    self.blitFrame()
                    #blit_thread = threading.Thread(target = self.blitFrame)
                    #blit_thread.setDaemon(True)
                    ##blit_thread.start()
                    #blit_thread.join()
                    self.Frames += 1
                    #blit_delay = (time.time() - start)
                #else:
                    #blit_delay -= 0.02#1 - (self.CPU.Frame % wish_fps) / wish_fps

                blit_delay += (time.time() - start)
                

                #while time.time() - start < 0.02:
                #    continue
                if self.CPU.Frames % wish_fps == wish_fps - 1:
                    blit_delay = 0
                start = time.time()
                #if blit_delay > 0.02:

                

                
                #if self.CPU.Frames % 60 == 0 or (blit_delay > 0.02 and blit_delay < 0.04):
                    #R_S = time.time()
                    #self.blitFrame()
                    #blit_thread.start()
                #    self.Frames += 1
                #    blit_delay = time.time() - start
                #   start = time.time()
                    #print time.time() - R_S
                #else:
                    #while time.time() - start < 0.016:
                    #    continue
                #    blit_delay += 0.02
                #self.playSounds()

                #self.ShowFPS(self.CPU.Frames)
                
                #self.CPU.FrameFlag_ZERO()

                self.Running = JOYPAD_CHK(self.CPU)



                
            
            if self.CPU.MapperWriteFlag:
                self.MapperWrite(self.CPU.MapperWriteAddress, self.CPU.MapperWriteData)
           
            
            

        self.PowerOFF()
    
    def cpu_run(self):
        self.CPU.exec6502()
    
    def Waiting_compiling(self):
        print print_now(),'First runing jitclass, compiling is a very time-consuming process...'
        print print_now(),'take about 300 seconds (i3-6100U)...ooh...waiting...'
        start = time.time()
        while self.CPU.Frames == 0:
            print print_now(),'jitclass is compiling...',((time.time()- start) / 3.00) , '%'
            #print '6502:',self.status 
            time.sleep(5)
            if ((time.time()- start) / 3.00) > 150:break
        print print_now(),'jitclass compiled...'
        
        #while self.CPU.FrameFlag & self.CPU.FrameRender:
        #    self.blitFrame()
        #    print time.time()-start
        #    start = time.time()
        #print print_now(),'Waiting_compiling  compiled...'
        
    
    
    
            
    def blitFrame(self):
        if self.PPU_Running:
            if self.CPU.Frames:
                if self.PPU_render:
                    self.PPU.RenderFrame()
                    
                    if self.debug:
                        pass
                        self.blitPatternTable()
                        self.blitPal()
                    else:
                        self.blitScreen()
                        self.blitPal()

    def blitFrame_thread(self):

            print 'blitFrame: ',self.CPU.Frames
            if self.CPU.Frames:
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
        if self.APU.available_ports:
            self.APU.midiout.close_port()
        del self.CPU
        del self.APU
        del self.PPU
        del self.MAPPER
            
    def blitScreen(self):
        self.FrameBuffer = paintBuffer(self.PPU.FrameArray[self.PPU.scY:self.PPU.scY + 240,self.PPU.scX:self.PPU.scX+256],self.PPU.Pal,self.PPU.Palettes)
        cv2.imshow("Main", self.FrameBuffer)
        cv2.waitKey(1)

    def blitPal(self):
        cv2.imshow("Pal", np.array([[self.PPU.Pal[i] for i in self.PPU.Palettes]]))
        cv2.waitKey(1)

    def blitPatternTable(self):
        self.FrameBuffer = paintBuffer(self.PPU.FrameArray,self.PPU.Pal,self.PPU.Palettes)
        cv2.line(self.FrameBuffer,(0,240),(768,240),(0,255,0),1) 
        cv2.line(self.FrameBuffer,(0,480),(768,480),(0,255,0),1) 
        cv2.line(self.FrameBuffer,(256,0),(256,720),(0,255,0),1) 
        cv2.line(self.FrameBuffer,(512,0),(512,720),(0,255,0),1) 
        cv2.rectangle(self.FrameBuffer, (self.PPU.scX,self.PPU.scY),(self.PPU.scX+255,self.PPU.scY + 240),(0,0,255),1)
        cv2.imshow("PatternTable0", self.FrameBuffer)
        cv2.waitKey(1)
        
    def ShowFPS(self):
        while self.CPU.Frames == 0:
            pass
            
        start = time.time()
        totalFrame = 0
        while self.Running:
            time.sleep(2)
            nowFrames = self.CPU.Frames
            duration = time.time() - start
            #if duration > 4:
            start = time.time()
            FPS =  'FPS: %d / %d' %(int((nowFrames - totalFrame) / duration), int(self.Frames/duration))  # 
            #cv2.setWindowTitle('Main',"%s %d %d %d"%(FPS,self.CPU.PPU.CurrentLine,self.CPU.PPU.vScroll,self.CPU.PPU.HScroll))
            self.Frames = 0
            print FPS, nowFrames, self.CPU.FrameFlag,self.APU.ChannelWrite #,self.CPU.PPU.render,self.CPU.PPU.tilebased
                
            
            totalFrame = nowFrames
        
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
            self.sequence = 0
            self.accumulator = 0
            self.data = [0] * 4
            self.data[0] = 0x1F
            self.data[3] = 0
        
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
        self.CPU.MapperWriteFlag = 0
        #print 'OLD MapperWrite'
        if NES.Mapper == 0:
            pass
        elif NES.Mapper == 1:
            self.map1_write(MapperWriteData, MapperWriteAddress)
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
        #BankSwitch 0, val1 * 8, 8

    def Select4KVROM(self, val1, bank):
        val1 = self.MaskVROM(val1, self.nesROM.ChrCount * 2)
        self.PPU.VRAM[bank * 4 * 0x400: (bank + 1) * 4 * 0x400] = self.nesROM.VROM[val1 * 4 * 0x400 : val1 * 4 * 0x400 + 4 * 0x400]
        #BankSwitch bank * 4, val1 * 4, 4

    def Select2KVROM(self, val1, bank):
        val1 = self.MaskVROM(val1, self.nesROM.ChrCount * 4)
        self.PPU.VRAM[bank * 2 * 0x400: (bank + 1) * 2 * 0x400] = self.nesROM.VROM[val1 * 2 * 0x400 : val1 * 2 * 0x400 + 2 * 0x400]
        #BankSwitch bank * 2, val1 * 2, 2


    def Select1KVROM(self, val1, bank):
        val1 = self.MaskVROM(val1, self.nesROM.ChrCount * 8)
        if NES.Mapper == 4:
            MemCopy(self.PPU.VRAM, (MMC.MMC3_ChrAddr ^ (bank * 0x400)), self.nesROM.VROM, (val1 * 0x400), 0x400)
            
        elif NES.Mapper == 23:
            pass
            #MemCopy VRAM(bank * &H400&), VROM(val1 * &H400&), &H400&
        else:
            pass
            self.PPU.VRAM[bank * 0x400: (bank + 1) * 0x400] = self.nesROM.VROM[val1 * 0x400 : val1 * 0x400 + 0x400]


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


    def map1_write(self, Address  , value ):

        bank_select = 0 #int16

        if (value & 0x80) :
            self.data[0] = self.data[0] | 0xC
            self.accumulator = self.data[(Address // 0x2000) & 3]
            self.sequence = 5
        else:
            if value & 1 : self.accumulator = self.accumulator | (2 ** sequence)
            self.sequence = self.sequence + 1
        

        if (self.sequence == 5) :
            self.data[(Address // 0x2000) & 3] = self.accumulator
            self.sequence = 0
            self.accumulator = 0

            #'MirrorXor = pow2((data(0) And &H3) + 10)
            
            if (self.nesROM.PrgCount == 0x20) :# '/* 512k cart */'
                bank_select = (self.data[1] & 0x10) * 2
            else:# '/* other carts */'
                bank_select = 0
           
            
            if self.data[0] & 2 :# 'enable panning
                NES.Mirroring = (self.data[0] & 1) ^ 1
            else:# 'disable panning
                NES.Mirroring = 2
            
            #DoMirror
            #Select Case Mirroring
            #Case 0
            #    MirrorXor = &H400
            #Case 1
            #    MirrorXor = &H800
            #Case 2
            #    MirrorXor = 0
            #End Select
            
            if (self.data[0] & 8) == 0 :# 'base boot select $8000?
                self.reg8 = 4 * (self.data[3]& 15) + bank_select
                self.regA = 4 * (self.data[3]& 15) + bank_select + 1
                self.regC = 4 * (self.data[3]& 15) + bank_select + 2
                self.regE = 4 * (self.data[3]& 15) + bank_select + 3
                self.SetupBanks()
            elif (self.data[0]& 4) :# '16k banks
                self.reg8 = ((self.data[3]& 15) * 2) + bank_select
                self.regA = ((self.data[3]& 15) * 2) + bank_select + 1
                self.regC = 0xFE
                self.regE = 0xFF
                self.SetupBanks()
            else: #'32k banks
                self.reg8 = 0
                self.regA = 1
                self.regC = ((self.data[3] & 15) * 2) + bank_select
                self.regE = ((self.data[3] & 15) * 2) + bank_select + 1
                self.SetupBanks()
            
            
            if (self.data[0]& 0x10) :# '4k
                self.Select4KVROM(self.data[1], 0)
                self.Select4KVROM(self.data[2], 1)
            else:# '8k
                self.Select8KVROM(self.data[1] // 2)
            




def JOYPAD_CHK(CPU):
    
    CPU.JOYPAD1.A_press(keyboard.is_pressed('k'))
    CPU.JOYPAD1.B_press(keyboard.is_pressed('j'))
    CPU.JOYPAD1.SELECT_press(keyboard.is_pressed('v'))
    CPU.JOYPAD1.START_press(keyboard.is_pressed('b'))
    CPU.JOYPAD1.UP_press(keyboard.is_pressed('w'))
    CPU.JOYPAD1.DOWN_press(keyboard.is_pressed('s'))
    CPU.JOYPAD1.LEFT_press(keyboard.is_pressed('a'))
    CPU.JOYPAD1.RIGTH_press(keyboard.is_pressed('d'))
    if keyboard.is_pressed('0'):
        print "turnoff"
        return 0
    else:
        return 1
    

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

def fresh_pyc(pyc):
    if '.pyc' in pyc:
        if os.path.exists(pyc):os.remove(pyc)

def run(debug = False):
    ROMS = roms_list()
    ROMS_INFO = get_roms_mapper(ROMS)
    while True:
        fc = CONSLOE(debug)
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
        del fc
    del fc
if __name__ == '__main__':
    #run(True)
    run(False)

        










        
