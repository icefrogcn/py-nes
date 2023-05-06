# -*- coding: UTF-8 -*-

import time
import math
import traceback


import numpy as np
import numba as nb
from numba import jit,njit
from numba import jitclass
from numba import uint8,uint16

from nes import NES
from memory import Memory
from ppu_reg import PPUREG, PPU_reg_type, PPUBIT, PPU_bit_type
from ppu_memory import PPU_Memory
from ppu_memory import PPU_memory_type
from rom import ROM,ROM_class_type

from pal import BGRpal

#PPU

        

print('loading PPU CLASS')      
@jitclass([('CurrentLine',uint16),('HScroll',uint16),('vScroll',uint16), ('scX',uint16), ('scY',uint16), \
           ('reg',PPU_reg_type),
           ('memory',PPU_memory_type),
           ('ROM',ROM_class_type),
           ('Pal',uint8[:,:]), \
           ('FrameArray',uint8[:,:]),
           ('Running',uint8),
           ('render',uint8),
           ('tilebased',uint8),
           ('debug',uint8),
           ('ScanlineSPHit',uint8[:])
    ])
class PPU(object):

    def __init__(self, memory = Memory(), ROM = ROM(), pal = BGRpal(), debug = 0):
        self.CurrentLine = 0 
        self.HScroll = 0
        self.vScroll = 0        
        self.scX = 0
        self.scY = 0

        self.ROM = ROM
        self.memory = PPU_Memory(memory)
        self.reg = PPUREG(self.memory, self.ROM)

        self.Pal        = pal

        self.FrameArray = np.zeros((720, 768),np.uint8)
        
        #self.BGPAL = [0] * 0x10
        #self.SPRPAL = [0] * 0x10
        
        self.debug = debug
        
        self.Running = 1
        
        self.render = 1

        self.ScanlineSPHit = np.zeros(257, np.uint8)

        self.tilebased = 0

        
    @property
    def bit(self):
        return 0
    @property
    def VRAM(self):
        return self.memory.VRAM
    @property
    def SpriteRAM(self):
        return self.memory.SpriteRAM
    @property
    def Palettes(self):
        return self.memory.Palettes
    @property
    def PRGRAM(self):
        return self.memory.PRGRAM



        
    @property
    def Mirroring(self):
        return self.ROM.Mirroring
    @property
    def MirrorXor(self):
        return self.ROM.MirrorXor
    
    def pPPUinit(self,Running = 1,render = 1,debug = 0):
        self.Running = Running
        self.render = render
        self.debug = debug
        

        #self.ScrollToggle = 0 #$2005-$2006 Toggle PPU56Toggle

        #self.loopy_v = 0
        #self.loopy_t = 0
        #self.loopy_x = 0
        #self.loopy_y = 0
        #self.loopy_shift = 0

        #self.loopy_v0 = 0
        #self.loopy_t0 = 0
        #self.loopy_x0 = 0
        #self.loopy_y0 = 0
        #self.loopy_shift0 = 0


        #self.MirrorXor = 0
        
        

        #self.width,self.height = 257,241

        #
        
        #self.blankPixel = 0 #np.array([16,16,16] ,dtype=np.uint8)
        
        #self.blankLine = np.array([self.blankPixel] * self.width ,dtype=np.uint8)
        #self.blankLine = [[0,0,16]] * self.height 
        
        #'DF: array to draw each frame to'
        #self.vBuffer = [16]* (256 * 241 - 1) 
        #'256*241 to allow for some overflow     可以允许一些溢出'
        #self.vBuffer = np.random.randint(0,1,size = (self.height,self.width,3),dtype=np.uint8)
        
        #self.vBuffer = np.array([self.blankLine] * self.height ,dtype=np.uint8)
        
        
        
        #self.PatternTable = np.uint8(0)

        #self.Pal = np.array([[item >> 16, item >> 8 & 0xFF ,item & 0xFF] for item in NES.CPal])
    @property
    def sp16(self):
        return 1 if self.reg.PPUCTRL & self.reg.bit.PPU_SP16_BIT else 0

    
    def Read(self,addr):
        return self.reg.read(addr)

        
    def Write(self,address,value):
        self.reg.write(address,value)

    def CurrentLine_ZERO(self):
        self.CurrentLine = 0
                
    def CurrentLine_increment_1(self):
        self.CurrentLine += 1
                
    def RenderScanline(self):
        '''if self.CurrentLine == 0:
            self.FrameStart()
            self.ScanlineNext()
            #mapper->HSync( scanline )
            self.ScanlineStart()

            self.loopy_v0 = self.loopy_v
            self.loopy_t0 = self.loopy_t
            self.loopy_x0 = self.loopy_x
            self.loopy_y0 = self.loopy_y
            self.loopy_shift0 = self.loopy_shift
            
            self.NTnum = self.Control1 & PPU_NAMETBL_BIT
        
        elif self.CurrentLine < 240:
            self.ScanlineNext()
            #mapper->HSync( scanline )
            self.ScanlineStart()
'''
        if self.CurrentLine > 239:return

        #if self.CurrentLine < 8 :
            #self.Status = self.Status & 0x3F

        if self.CurrentLine == 239 :
            #self.Status = self.Status | 0x80#PPU_VBLANK_FLAG
            self.reg.PPUSTATUS_W(self.reg.PPUSTATUS | 0x80) #PPU_VBLANK_FLAG
	    
        if self.Running == 0:
            if self.reg.PPUMASK & self.reg.bit.PPU_SPDISP_BIT == 0 :return
            if self.reg.PPUSTATUS & 0x40 :return #PPU_SPHIT_FLAG
            if self.CurrentLine > self.SpriteRAM[0] + 8:
                self.reg.PPUSTATUS_W(self.reg.PPUSTATUS | 0x40)#PPU_SPHIT_FLAG
            return

        self.ScanlineSPHit[self.CurrentLine] =  1 if self.reg.PPUSTATUS & self.reg.bit.PPU_SPHIT_FLAG else 0

        '''self.sp_h = 16 if self.Control1 & PPU_SP16_BIT else 8

'''

    def ScanlineStart(self):
        if( self.reg.PPUMASK & (PPU_BGDISP_BIT|PPU_SPDISP_BIT) ):
            self.loopy_v = (self.loopy_v & 0xFBE0)|(self.loopy_t & 0x041F)
            self.loopy_shift = self.loopy_x
            self.loopy_y = (self.loopy_v&0x7000)>>12
            #nes->mapper->PPU_Latch( 0x2000 + (loopy_v & 0x0FFF) );
                
    def ScanlineNext(self):
        if( self.reg.PPUMASK & (PPU_BGDISP_BIT|PPU_SPDISP_BIT) ):
            if( (self.loopy_v & 0x7000) == 0x7000 ):
                self.loopy_v &= 0x8FFF
                if( (self.loopy_v & 0x03E0) == 0x03A0 ):
                    self.loopy_v ^= 0x0800
                    self.loopy_v &= 0xFC1F
                else:
                    if( (self.loopy_v & 0x03E0) == 0x03E0 ):
                        self.loopy_v &= 0xFC1F
                    else:
                        self.loopy_v += 0x0020
            else :
                self.loopy_v += 0x1000

            self.loopy_y = (self.loopy_v&0x7000)>>12
                
    def FrameStart(self):
        if self.reg.PPUMASK & (PPU_SPDISP_BIT|PPU_BGDISP_BIT):
            self.loopy_v = self.loopy_t
            self.loopy_shift = self.loopy_x
            self.loopy_y = (self.loopy_v & 0x7000)>>12

                    
    

    @property
    def PatternTables(self):
        #if self.Control2 & (PPU_SPDISP_BIT|PPU_BGDISP_BIT) == 0 :return

        #PatternTablesAddress,PatternTablesSize = (0x1000,0x1000) if self.reg.PPUCTRL & self.reg.bit.PPU_SPTBL_BIT else (0,0x1000)
        PatternTablesAddress,PatternTablesSize = (0x1000,0x1000) if self.reg.PPU_SPTBL_BIT else (0,0x1000)
        
        return self.PatternTableArr(self.VRAM[PatternTablesAddress:PatternTablesAddress + 0x1000])

        '''img = np.zeros((8,256,3),np.uint8)
        for y in range(8):
            for index in range(32):
                for x in range(8):
                    img[y][index * 8 + x] = self.Pal[PatternTable[index][y][x]]
                #print img_line[y]

        #print img[0]
        return img#np.array(img,np.uint8)'''
    #@property
    def NameTables_data(self,offset):
        NameTablesAddress = 0x2000 + offset * 0x400
        NameTablesSize = 0x3C0
        
        return self.VRAM[NameTablesAddress: NameTablesAddress + NameTablesSize]
    
        
    def RenderFrame(self):
        #return
        if self.reg.PPUMASK & (self.reg.bit.PPU_SPDISP_BIT|self.reg.bit.PPU_BGDISP_BIT) == 0 :return
        
        

        #NTnum = (self.loopy_v0 & 0x0FFF) >>10
        #NTnum = self.reg.PPUCTRL & self.reg.bit.PPU_NAMETBL_BIT
        NTnum = self.reg.PPU_NAMETBL_BIT

        #fineYscroll = self.loopy_v >>12
        #coarseYscroll  = (self.loopy_v & 0x03FF) >> 5
        #coarseXscroll = self.loopy_v & 0x1F

        if self.reg.Mirroring:
            #self.scY = (coarseYscroll << 3) + fineYscroll + ((NTnum>>1) * 240) 
            #self.scX = (coarseXscroll << 3)+ self.loopy_x0 #self.HScroll
            self.scY = self.reg.vScroll + ((NTnum>>1) * 240)
            self.scX = self.reg.HScroll + ((NTnum & 1) * 256)
            
        if self.reg.Mirroring == 0:
            #self.scY = (coarseYscroll << 3) + fineYscroll + ((NTnum>>1) * 240) #if self.loopy_v&0x0FFF else self.scY
            self.scY = self.reg.vScroll + ((NTnum>>1) * 240) 
            #if self.loopy_v&0x0FFF else self.scY
        
        self.RenderBG()

        self.RenderSprites()
        
        #self.FrameBuffer = paintBuffer(self.FrameArray,self.Pal,self.Palettes)

        

            
    def RenderSprites(self):
        #PatternTablesAddress = 0x1000 if self.Control1 & PPU_SPTBL_BIT and self.sp16 else 0
        PatternTablesAddress,PatternTablesSize = (0x1000,0x1000) if self.reg.PPUCTRL & self.reg.bit.PPU_SPTBL_BIT and self.sp16 else (0 ,0x1000)
        
        PatternTable_Array = self.PatternTableArr(self.VRAM[PatternTablesAddress : PatternTablesAddress + PatternTablesSize])

        
        self.RenderSpriteArray(self.FrameArray, self.SpriteRAM, PatternTable_Array)
         

    def RenderAttributeTables(self,offset):
        AttributeTablesAddress = 0x2000 + (offset * 0x400 + 0x3C0)
        AttributeTablesSize = 0x40
        
        return self.VRAM[AttributeTablesAddress: AttributeTablesAddress + AttributeTablesSize]
    

    #@njit
    def PatternTableArr(self, Pattern_Tables):
        PatternTable = np.zeros((len(Pattern_Tables)>>4,8,8),np.uint8)
        bitarr = range(0x7,-1,-1)
        for TileIndex in range(len(Pattern_Tables)>>4):
            for TileY in range(8):
                PatternTable[TileIndex,TileY] = np.array([1 if (Pattern_Tables[(TileIndex << 4) + TileY]) & (2**bit) else 0 for bit in bitarr], np.uint8) + \
                                                np.array([2 if (Pattern_Tables[(TileIndex << 4) + TileY + 8]) & (2**bit) else 0 for bit in bitarr], np.uint8)

        return PatternTable

    def RenderBG(self):
        
        PatternTablesAddress = self.reg.PPU_BGTBL_BIT << 8 #PPU_BGTBL_BIT = 0x10
        
        PatternTable_Array = self.PatternTableArr(self.VRAM[PatternTablesAddress : PatternTablesAddress + 0x1000])

        if self.ROM.Mirroring == 1:
            self.RenderNameTableH(PatternTable_Array, 0,1)

        elif self.ROM.Mirroring == 0 :
            
            self.RenderNameTableV(PatternTable_Array, 0,2)
            
        elif self.ROM.Mirroring == 2:
            self.RenderNameTables(PatternTable_Array, 0,1,2,3)
        else:
            self.RenderNameTables(PatternTable_Array, 0,1,2,3)

            
    #@jit
    def RenderNameTableH(self, PatternTables,nt0,nt1):
        tempBuffer0 = self.NameTableArr(self.NameTables_data(nt0),PatternTables)
        self.RenderNameTable(self.AttributeTables_data(nt0), tempBuffer0)
        
        tempBuffer1 = self.NameTableArr(self.NameTables_data(nt1),PatternTables)
        self.RenderNameTable(self.AttributeTables_data(nt1), tempBuffer1)
        
        self.FrameArray[0:480,0:768] = np.row_stack((np.column_stack((tempBuffer0,tempBuffer1,tempBuffer0)),np.column_stack((tempBuffer0,tempBuffer1,tempBuffer0))))

    #@njit
    def RenderNameTableV(self, PatternTables, nt0, nt2):
        tempBuffer0 = self.NameTableArr(self.NameTables_data(nt0),PatternTables)
        self.RenderNameTable(self.AttributeTables_data(nt0), tempBuffer0)
        
        tempBuffer2 = self.NameTableArr(self.NameTables_data(nt2),PatternTables)
        self.RenderNameTable(self.AttributeTables_data(nt2), tempBuffer2)
        
        self.FrameArray[0:720,0:512] =  np.column_stack((np.row_stack((tempBuffer0,tempBuffer2,tempBuffer0)),np.row_stack((tempBuffer0,tempBuffer2,tempBuffer0))))

    def RenderNameTables(self, PatternTables,nt0,nt1,nt2,nt3):
            
        #tempBuffer0 = self.AttributeTableArr(AttributeTables_data(VRAM,nt0), NameTableArr(NameTables_data(VRAM,nt0),PatternTables))
        
        tempBuffer0 = self.NameTableArr(self.NameTables_data(nt0),PatternTables)
        self.RenderNameTable(self.AttributeTables_data(nt0), tempBuffer0)
        #tempBuffer1 = self.AttributeTableArr(AttributeTables_data(VRAM,nt1), NameTableArr(NameTables_data(VRAM,nt1),PatternTables))
        tempBuffer1 = self.NameTableArr(self.NameTables_data(nt1),PatternTables)
        self.RenderNameTable(self.AttributeTables_data(nt1), tempBuffer1)
        #tempBuffer2 = self.AttributeTableArr(AttributeTables_data(VRAM,nt2), NameTableArr(NameTables_data(VRAM,nt2),PatternTables))
        tempBuffer2 = self.NameTableArr(self.NameTables_data(nt2),PatternTables)
        self.RenderNameTable(self.AttributeTables_data(nt2), tempBuffer2)
        #tempBuffer3 = self.AttributeTableArr(AttributeTables_data(VRAM,nt3), NameTableArr(NameTables_data(VRAM,nt3),PatternTables))
        tempBuffer3 = self.NameTableArr(self.NameTables_data(nt3),PatternTables)
        self.RenderNameTable(self.AttributeTables_data(nt3), tempBuffer3)

        self.FrameArray[0:480,0:512] =  np.row_stack((np.column_stack((tempBuffer3,tempBuffer2)),np.column_stack((tempBuffer1,tempBuffer0))))
    
    #@property
    def AttributeTables_data(self,offset):
        AttributeTablesAddress = 0x2000 + (offset * 0x400 + 0x3C0)
        AttributeTablesSize = 0x40
        return self.VRAM[AttributeTablesAddress: AttributeTablesAddress + AttributeTablesSize]

    def RenderSpriteArray(self, BGbuffer, SPRAM, PatternTableArray):
        SpriteArr = np.zeros((16, 8),np.uint8) if self.sp16 else np.zeros((8, 8),np.uint8)
        
        for spriteIndex in range(63,-1,-1):
            spriteOffset =  spriteIndex * 4
            if SPRAM[spriteOffset] >= 240: continue
            
            spriteY = SPRAM[spriteOffset] + self.scY
            spriteX = SPRAM[spriteOffset + 3] + self.scX
            

            
            chr_index = SPRAM[spriteOffset + 1]
            if self.sp16:
                chr_index = chr_index ^ (chr_index & 1)
            chr_l = PatternTableArray[chr_index]
            chr_h = PatternTableArray[(chr_index + 1) & 0xFF]
     
                
            if SPRAM[spriteOffset + 2] & 0x40:
                chr_l = chr_l[:,::-1]    
                if self.sp16:
                    chr_h = chr_h[:,::-1]
                    

            if SPRAM[spriteOffset + 2] & 0x80:
                chr_l = chr_l[::-1] 
                if self.sp16:
                    chr_h = chr_h[::-1]
                    chr_l,chr_h = chr_h,chr_l
            
            SpriteArr = np.row_stack((chr_l,chr_h)) if self.sp16 else chr_l

            #SpriteArr = np.add(SpriteArr, ((SPRAM[spriteOffset + 2] & 0x03) << 2) + 0x10)
            hiColor = ((SPRAM[spriteOffset + 2] & 0x03) << 2) + 0x10
            [rows, cols] = SpriteArr.shape
            for i in range(rows):
                for j in range(cols):
                    SpriteArr[i,j] += hiColor
                    
            spriteW = 8 
            spriteH = SpriteArr.shape[0] 
            
            if BGbuffer.shape[0] - spriteY > spriteH and BGbuffer.shape[1] - spriteX > spriteW :
                BGPriority = SPRAM[spriteOffset + 2] & 0x20 #SP_PRIORITY_BIT

                for i in range(spriteW):
                     for j in range(spriteH):
                        if BGPriority:
                            if BGbuffer[spriteY + j, spriteX + i] & 3 == 0:
                                BGbuffer[spriteY + j, spriteX + i] = SpriteArr[j,i]
                        else:
                            if SpriteArr[j,i] & 3 > 0:
                                BGbuffer[spriteY + j, spriteX + i] = SpriteArr[j,i]
                                
                #if BGPriority:
                    #continue

                    
                    #BG_alpha = BGbuffer[spriteY:spriteY + spriteH, spriteX:spriteX + spriteW] & 3
                    #BGbuffer[spriteY:spriteY + spriteH, spriteX:spriteX + spriteW][BG_alpha == 0] = SpriteArr[BG_alpha == 0]
                #else:
                    #continue
                    #if self.ScanlineSPHit[spriteY - self.scY]:
                    #    BGbuffer[spriteY:spriteY + spriteH, spriteX:spriteX + spriteW][SpriteArr & 3 > 0] = SpriteArr[SpriteArr & 3 > 0]#<<1#[0:spriteH,0:spriteW]
                    #else:

                    
                    #BGbuffer[spriteY:spriteY + spriteH, spriteX:spriteX + spriteW][SpriteArr & 3 > 0] = SpriteArr[SpriteArr & 3 > 0]
                #BG[spriteY:spriteY + spriteH, spriteX:spriteX + spriteW] = SpriteArr
                    
        #return BG

    def NameTableArr(self, NameTables, PatternTables):
        width = 8 * 32 if len(NameTables) > 0x1f else len(NameTables)  #256
        height = ((len(NameTables) - 1) / 32 + 1) * 8 #240
        ntbuffer = np.zeros((height + 1,width + 1), np.uint8)
        for row in range(width / 8):
            for col in range(height / 8):
                if NameTables[col * 32 + row] == 0:
                    continue
                ntbuffer[col << 3 :(col << 3) + 8 ,row  << 3: (row  << 3) + 8] = PatternTables[NameTables[col * 32 + row]]
        
        return ntbuffer[0:height,0:width]

    def RenderNameTable(self,AttributeTables, FrameBuffer):
        tempFrame = np.zeros((257, 257),np.uint8)
        for i in range(len(AttributeTables)):
            col = i >> 3; row = i & 7
            if AttributeTables[i] == 0:
                continue
            tempFrame[(col << 5)        :(col << 5) + 16 ,  (row << 5)      : (row  << 5) + 16] = (AttributeTables[i] & 0b11) << 2
            tempFrame[(col << 5) + 16   :(col << 5) + 32 ,  (row << 5)      : (row  << 5) + 16] = (AttributeTables[i] & 0b110000) >> 2
            tempFrame[(col << 5)        :(col << 5) + 16 ,  (row << 5) + 16 : (row  << 5) + 32] = (AttributeTables[i] & 0b1100)
            tempFrame[(col << 5) + 16   :(col << 5) + 32 ,  (row << 5) + 16 : (row  << 5) + 32] = (AttributeTables[i] & 0b11000000) >> 4

        
        FrameBuffer |= tempFrame[0:240,0:256]

        [rows, cols] = FrameBuffer.shape
        for i in range(rows):
            for j in range(cols):
                if FrameBuffer[i,j] & 3 == 0: 
                    FrameBuffer[i,j] == 0
                
    def PatternTableArr(self, Pattern_Tables):
        PatternTable = np.zeros((len(Pattern_Tables)>>4,8,8),np.uint8)
        bitarr = range(0x7,-1,-1)
        for TileIndex in range(len(Pattern_Tables)>>4):
            for TileY in range(8):
                PatternTable[TileIndex,TileY] = np.array([1 if (Pattern_Tables[(TileIndex << 4) + TileY]) & (2**bit) else 0 for bit in bitarr], np.uint8) + \
                                                np.array([2 if (Pattern_Tables[(TileIndex << 4) + TileY + 8]) & (2**bit) else 0 for bit in bitarr], np.uint8)

        return PatternTable

PPU_type = nb.deferred_type()
PPU_type.define(PPU.class_type.instance_type)

'''                        
#@jit
def RenderNameTableH(FrameArray, VRAM, PatternTables,nt0,nt1):
        tempBuffer0 = NameTableArr(NameTables_data(VRAM, nt0),PatternTables)
        RenderNameTable(AttributeTables_data(VRAM, nt0), tempBuffer0)
        tempBuffer1 = NameTableArr(NameTables_data(VRAM, nt1),PatternTables)
        RenderNameTable(AttributeTables_data(VRAM, nt1), tempBuffer1)
        FrameArray[0:480,0:768] = np.row_stack((np.column_stack((tempBuffer0,tempBuffer1,tempBuffer0)),np.column_stack((tempBuffer0,tempBuffer1,tempBuffer0))))

#@njit
def RenderNameTableV(FrameArray, VRAM, PatternTables, nt0, nt2):
        tempBuffer0 = NameTableArr(self.NameTables_data(nt0),PatternTables)
        RenderNameTable(AttributeTables_data(VRAM, nt0), tempBuffer0)
        tempBuffer2 = NameTableArr(NameTables_data(VRAM, nt2),PatternTables)
        RenderNameTable(AttributeTables_data(VRAM, nt2), tempBuffer2)
        FrameArray[0:720,0:512] =  np.column_stack((np.row_stack((tempBuffer0,tempBuffer2,tempBuffer0)),np.row_stack((tempBuffer0,tempBuffer2,tempBuffer0))))

        
@njit    
def RenderNameTables(VRAM,PatternTables,nt0,nt1,nt2,nt3):
        
        tempBuffer0 = AttributeTableArr(AttributeTables_data(VRAM,nt0), NameTableArr(NameTables_data(VRAM,nt0),PatternTables))
        tempBuffer1 = AttributeTableArr(AttributeTables_data(VRAM,nt1), NameTableArr(NameTables_data(VRAM,nt1),PatternTables))
        tempBuffer2 = AttributeTableArr(AttributeTables_data(VRAM,nt2), NameTableArr(NameTables_data(VRAM,nt2),PatternTables))
        tempBuffer3 = AttributeTableArr(AttributeTables_data(VRAM,nt3), NameTableArr(NameTables_data(VRAM,nt3),PatternTables))

        return np.row_stack((np.column_stack((tempBuffer3,tempBuffer2)),np.column_stack((tempBuffer1,tempBuffer0))))


@njit
def AttributeTables_data(VRAM,offset):
        AttributeTablesAddress = 0x2000 + (offset * 0x400 + 0x3C0)
        AttributeTablesSize = 0x40
        return VRAM[AttributeTablesAddress: AttributeTablesAddress + AttributeTablesSize]
    
@njit
def NameTables_data(VRAM,offset):
        NameTablesAddress = 0x2000 + offset * 0x400
        NameTablesSize = 0x3C0
        return VRAM[NameTablesAddress: NameTablesAddress + NameTablesSize]

@njit
def RenderScanlineArray(VRAM, NameTable, PatternTable, Scanline):
    offset = (Scanline - 1)  / 8 * 32
    NameTableArray = VRAM[NameTable + offset: NameTable + offset + 32]
    PTArr = PatternTableArr(VRAM[PatternTable: PatternTable + 0x1000])
    NoAttriArray = NameTableArr(NameTableArray, PTArr)
    return NoAttriArray

@njit
def paintBuffer(FrameBuffer,Pal,Palettes):
    [rows, cols] = FrameBuffer.shape
    img = np.zeros((rows, cols,3),np.uint8)
    for i in range(rows):
        for j in range(cols):
            img[i, j] = Pal[Palettes[FrameBuffer[i, j]]]
    return img

#@jit



@njit
def RenderNameTable(AttributeTables, FrameBuffer):
    tempFrame = np.zeros((257, 257),np.uint8)
    for i in range(len(AttributeTables)):
        col = i >> 3; row = i & 7
        if AttributeTables[i] == 0:
            continue
        tempFrame[(col << 5)        :(col << 5) + 16 ,  (row << 5)      : (row  << 5) + 16] = (AttributeTables[i] & 0b11) << 2
        tempFrame[(col << 5) + 16   :(col << 5) + 32 ,  (row << 5)      : (row  << 5) + 16] = (AttributeTables[i] & 0b110000) >> 2
        tempFrame[(col << 5)        :(col << 5) + 16 ,  (row << 5) + 16 : (row  << 5) + 32] = (AttributeTables[i] & 0b1100)
        tempFrame[(col << 5) + 16   :(col << 5) + 32 ,  (row << 5) + 16 : (row  << 5) + 32] = (AttributeTables[i] & 0b11000000) >> 4

    
    FrameBuffer |= tempFrame[0:240,0:256]

    [rows, cols] = FrameBuffer.shape
    for i in range(rows):
        for j in range(cols):
            if FrameBuffer[i,j] & 3 == 0: 
                FrameBuffer[i,j] == 0



@njit
def NameTableArr(NameTables, PatternTables):
    width = 8 * 32 if len(NameTables) > 0x1f else len(NameTables)  #256
    height = ((len(NameTables) - 1) / 32 + 1) * 8 #240
    ntbuffer = np.zeros((height + 1,width + 1), np.uint8)
    for row in range(width / 8):
        for col in range(height / 8):
            if NameTables[col * 32 + row] == 0:
                continue
            ntbuffer[col << 3 :(col << 3) + 8 ,row  << 3: (row  << 3) + 8] = PatternTables[NameTables[col * 32 + row]]
    
    return ntbuffer[0:height,0:width]
    

@njit
def PatternTableArr(Pattern_Tables):
    PatternTable = np.zeros((len(Pattern_Tables)>>4,8,8),np.uint8)
    bitarr = range(0x7,-1,-1)
    for TileIndex in range(len(Pattern_Tables)>>4):
        for TileY in range(8):
            PatternTable[TileIndex,TileY] = np.array([1 if (Pattern_Tables[(TileIndex << 4) + TileY]) & (2**bit) else 0 for bit in bitarr], np.uint8) + \
                                            np.array([2 if (Pattern_Tables[(TileIndex << 4) + TileY + 8]) & (2**bit) else 0 for bit in bitarr], np.uint8)

    return PatternTable
'''
@jit
def byte2bit1(byte):
    return np.array([1 if (byte) & (2**bit) else 0 for bit in range(0x7,-1,-1)], np.uint8)
@jit
def byte2bit2(byte):
    return  np.array([2 if (byte) & (2**bit) else 0 for bit in range(0x7,-1,-1)], np.uint8)
            

'''        elif addr == 5:
            if( not self.ScrollToggle):
                #First write
                #tile X t:0000000000011111=d:11111000
                self.loopy_t = (self.loopy_t & 0xFFE0)|(value>>3)
		#scroll offset X x=d:00000111
                self.loopy_x = value & 0x07
            else:
                #Second write
		#tile Y t:0000001111100000=d:11111000
                self.loopy_t = (self.loopy_t & 0xFC1F)|((value & 0xF8)<<2)
		#scroll offset Y t:0111000000000000=d:00000111
                self.loopy_t = (self.loopy_t & 0x8FFF)|((value & 0x07)<<12)


            
        elif addr == 6:
            if( not self.ScrollToggle):
                #First write
		#t:0011111100000000=d:00111111
                # t:1100000000000000=0
                self.loopy_t = (self.loopy_t & 0x00FF)|((value & 0x3F)<<8)

            else:
                #Second write
		#// t:0000000011111111=d:11111111
                self.loopy_t = (self.loopy_t & 0xFF00)|value
		#v=t
                self.loopy_v = self.loopy_t

'''



@jit        
def adc1(reg):
    reg.a += 1


def adc2(reg):
    reg.a += 2
                    
if __name__ == '__main__':
    ppu = PPU()
    #print ppu.Pal
    #ppu.pPPUinit()
    #print ppu.blankLine
    #print len(ppu.vBuffer)
    #print len(ppu.vBuffer[0])
    #print ppu.vBuffer[2:4]
    #print ppu.vBuffer[3]
    #print ppu.vBuffer[2][1]
    #cv2.imshow("Main", np.array(ppu.vBuffer,dtype=np.uint8))
    #print ppu.Read(0x2000)
    #print byte2bit1(0x0) + byte2bit2(0x28)
    #aa = PatternTableArr(np.array([0x10,0,0x44,0,0xfe,0,0x82,00,00,0x28,0x44,0x82,00,0x82,0x82,00],dtype=np.uint8))

    
    
    
    








        
