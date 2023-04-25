# -*- coding: UTF-8 -*-

import time
import math
import traceback

import cv2
import numpy as np
import numba as nb
from numba import jit,njit
from numba import jitclass
from numba import uint8,uint16

from nes import NES
from pal import BGRpal
#PPU

# PPU Control Register #1	PPU #0 $2000
PPU_VBLANK_BIT	=	0x80
PPU_SPHIT_BIT	=	0x40		#
PPU_SP16_BIT	=	0x20
PPU_BGTBL_BIT	=	0x10
PPU_SPTBL_BIT	=	0x08
PPU_INC32_BIT	=	0x04
PPU_NAMETBL_BIT	=	0x03

# PPU Control Register #2	PPU #1 $2001
PPU_BGCOLOR_BIT	=	0xE0
PPU_SPDISP_BIT	=	0x10
PPU_BGDISP_BIT	=	0x08
PPU_SPCLIP_BIT	=	0x04
PPU_BGCLIP_BIT	=	0x02
PPU_COLORMODE_BIT =	0x01

# PPU Status Register		PPU #2 $2002
PPU_VBLANK_FLAG	=	0x80
PPU_SPHIT_FLAG	=	0x40
PPU_SPMAX_FLAG	=	0x20
PPU_WENABLE_FLAG=	0x10

# SPRITE Attribute
SP_VMIRROR_BIT	=	0x80
SP_HMIRROR_BIT	=	0x40
SP_PRIORITY_BIT	=	0x20
SP_COLOR_BIT	=	0x03


@jitclass([('VRAM',uint8[:]), \
           ('SpriteRAM',uint8[:]), \
           ('Palettes',uint8[:]), \
           ('Pal',uint8[:,:]), \
           ('FrameArray',uint8[:,:]), \
           ('PPUREG',uint8[:]) \
           ])
class Memory(object):
    def __init__(self,Pal):
        self.VRAM = np.zeros(0x4000,np.uint8)
        self.SpriteRAM = np.zeros(0x100,np.uint8)
        self.Palettes = np.zeros(0x20, np.uint8) 
        self.Pal = Pal
        self.FrameArray = np.zeros((720, 768),np.uint8)

        self.PPUREG = np.zeros(0x8, np.uint8) 
    
    
    def read(self,address):
        addr = address & 0x3FFF
        data = 0
        if 0x2000<= addr <0x3F00:
            t_address = addr - 0x2000
            t_address %= 0x1000
            return self.VRAM[t_address + 0x2000]
        elif(addr >= 0x3000):
            if addr >= 0x3F00:
                data &= 0x3F
                data = self.Palettes[addr & 0x1F]
            addr &= 0xEFFF
        else:
            return self.VRAM[addr]
        return data
        
@jitclass([('reg',uint8[:]), \
           ('VRAM',uint8[:]), \
           ('SpriteRAM',uint8[:]), \
           ('Palettes',uint8[:]), \
           ('Pal',uint8[:,:]) \
           ])
class PPUREG(object):
    def __init__(self,RAM):
        self.reg = np.zeros(0x10, np.uint8) 
        self.VRAM = RAM.VRAM #3FFF #As Byte, VROM() As Byte  ' Video RAM
        self.SpriteRAM = RAM.SpriteRAM
        self.Palettes = RAM.Palettes
        self.Pal = RAM.Pal
        
    @property
    def PPUCTRL(self):
        return self.reg[0]
    def PPUCTRL_W(self,value): 
        self.reg[0] = value
        
        
    @property
    def PPUMASK(self):
        return self.reg[1]
    def PPUMASK_W(self,value):
        self.reg[1] = value
        
    @property
    def PPUSTATUS(self):
        return self.reg[2]
    def PPUSTATUS_W(self,value):
        self.reg[2] = value
        
        
    @property
    def OAMADDR(self):
        return self.reg[3]
    def OAMADDR_W(self,value):
        self.reg[3] = value
        
    @property
    def OAMDATA(self):
        return self.reg[4]
    def OAMDATA_W(self,value):
        self.SpriteRAM[self.OAMADDR] = value
        self.reg[3] = (self.reg[3] + 1) & 0xFF
        
    @property
    def PPUSCROLL(self):
        return self.reg[5]
    def PPUSCROLL_W(self,value):
        self.reg[5] = value
        
    @property
    def PPUADDR(self):
        return self.reg[6]
    def PPUADDR_W(self,value):
        self.reg[6] = value
        
    @property
    def PPUDATA(self):
        return self.reg[7]
    def PPUDATA_W(self,value):
        self.reg[8] = value
        self.reg[6] &= 0x3FFF
        if self.reg[6] >= 0x3F00:
            self.Palettes[self.reg[6] & 0x1F] = value
            if self.reg[6] & 3 == 0 and value:
                self.Palettes[(self.reg[6] & 0x1F) ^ 0x10] = value
        else:
            self.VRAM[self.reg[6]] = value
            if (self.reg[6] & 0x3000) == 0x2000:
                self.VRAM[self.reg[6] ^ self.cartridge.MirrorXor] = value
        
        self.reg[6] += 32 if self.reg[0] & 0x04 else 1
        
    @property
    def PPU7_Temp(self):
        return self.reg[8]
    def PPU7_Temp_W(self,value):
        self.reg[8] = value
        
    @property
    def OAMDMA(self):
        return self.reg[9]
        
        
        

class PPU(object):

    CurrentLine = np.uint16(0) #Long 'Integer

    NameTable = np.uint8(0)


    
    PPU7_Temp = np.uint8(0xFF)
    
    def __init__(self,debug = False):
        self.RAM = Memory(BGRpal())
        #self.reg = PPUREG(self.RAM)
        self.VRAM = self.RAM.VRAM #3FFF #As Byte, VROM() As Byte  ' Video RAM
        self.SpriteRAM = self.RAM.SpriteRAM
        self.Palettes = self.RAM.Palettes
        self.Pal = self.RAM.Pal
        #self.BGPAL = [0] * 0x10
        #self.SPRPAL = [0] * 0x10

        self.FrameArray = np.zeros((720, 768),np.uint8)

        self.debug = debug
        
        self.PPU_Read = {
            0x2000:self.PPU7_T,
            0x2001:self.PPU7_T,
            0x2003:self.PPU7_T,
            0x2005:self.PPU7_T,
            0x2006:self.PPU7_T,
            
            0x2002:self.PPU_Status_R,
            0x2004:self.SPRRAM_2004_R,
            0x2007:self.VRAM_2007_R,
                }

        self.Running = 1
        
        self.render = False

        self.tilebased = False

    def pPPUinit(self):
        
        self.Control1 = np.uint8(0) # $2000
        self.Control2 = np.uint8(0) # $2001
        self.Status = np.uint8(0) # $2002
        self.SpriteAddress = 0 #As Long ' $2003
        self.AddressHi = np.uint8(0) # $2006, 1st write
        self.Address = 0 # $2006
        self.AddressIsHi = 1

        self.ScrollToggle = 0 #$2005-$2006 Toggle PPU56Toggle
        self.HScroll = 0
        self.vScroll = 0

        self.loopy_v = 0
        self.loopy_t = 0
        self.loopy_x = 0
        self.loopy_y = 0
        self.loopy_shift = 0

        self.loopy_v0 = 0
        self.loopy_t0 = 0
        self.loopy_x0 = 0
        self.loopy_y0 = 0
        self.loopy_shift0 = 0

        self.scX = 0
        self.scY = 0
        #self.MirrorXor = 0
        self.sp_h = 0
        
        
        self.EmphVal = 0   #???????Color
        
        

        self.width,self.height = 257,241

        self.ScanlineSPHit = np.zeros(257, np.uint8)
        
        self.blankPixel = 0 #np.array([16,16,16] ,dtype=np.uint8)
        
        self.blankLine = np.array([self.blankPixel] * self.width ,dtype=np.uint8)
        #self.blankLine = [[0,0,16]] * self.height 
        
        'DF: array to draw each frame to'
        #self.vBuffer = [16]* (256 * 241 - 1) 
        '256*241 to allow for some overflow     可以允许一些溢出'
        #self.vBuffer = np.random.randint(0,1,size = (self.height,self.width,3),dtype=np.uint8)
        
        self.vBuffer = np.array([self.blankLine] * self.height ,dtype=np.uint8)
        
        
        
        self.PatternTable = np.uint8(0)

        #self.Pal = np.array([[item >> 16, item >> 8 & 0xFF ,item & 0xFF] for item in NES.CPal])

        
        


    def ScreenShow(self):
        if self.Running == 0:
            self.render = False
            return
        if self.Running and self.render and self.debug == False:
            cv2.namedWindow('Main', cv2.WINDOW_NORMAL)
            cv2.namedWindow('Pal', cv2.WINDOW_NORMAL)
            
        else:
            cv2.namedWindow('Pal', cv2.WINDOW_NORMAL)
            cv2.namedWindow('PatternTable0', cv2.WINDOW_NORMAL)
            cv2.namedWindow('SC_TEST', cv2.WINDOW_NORMAL)
        #cv2.namedWindow('PatternTable2', cv2.WINDOW_NORMAL)
        #cv2.namedWindow('PatternTable3', cv2.WINDOW_NORMAL)
    
    def ShutDown(self):
        if self.render:
            cv2.destroyAllWindows()
            
    def PPU7_T(self):
        print 'PPU7_Temp'
        return self.PPU7_Temp
        
    def PPU_Status_R(self):
        ret = (self.PPU7_Temp & 0x1F) | self.Status
        self.AddressIsHi = True
        self.ScrollToggle = 0
        if ret & 0x80:
            
            self.Status = self.Status & 0x60 #
            
        return ret #PPU_Status = 0

    def SPRRAM_2004_R(self):
        print "Read SpiritRAM "
        tmp = self.PPU7_Temp
        self.PPU7_Temp = self.SpriteRAM(self.SpriteAddress)
        self.SpriteAddress = (self.SpriteAddress + 1) & 0xFF
        return tmp

    def VRAM_2007_R(self):
        #print "Read PPU MMC",hex(self.Address)
        #if self.Mapper == 9 or self.Mapper == 10:
            #print "Mapper 9 - 10"
        
        addr = self.Address & 0x3FFF
        data = self.PPU7_Temp
        

        if(addr >= 0x3000):
            if addr >= 0x3F00:
                data &= 0x3F
                return self.Palettes[addr & 0x1F]
            addr &= 0xEFFF
        else:
            self.PPU7_Temp = self.VRAM[addr & 0x3FFF]
            

        self.PPU7_Temp = 0xFF #self.VRAM[addr>>10][addr&0x03FF]
        self.Address +=  32 if (self.Control1 & PPU_INC32_BIT) else 1

        return data
        
    def Read(self,addr):
        try:
            return self.PPU_Read.get(addr)()
            return self.reg.read(addr)()
        except:
            print "Invalid PPU Read - %s" %hex(addr)
            print (traceback.print_exc())
            return self.PPU_Read.get(addr)()
            #return 0
            
        
    def Write(self,address,value):
        '''try:
            self.PPU_Write_dic.get(addr)(value)
        except:
            print "Invalid PPU Write - %s : %s" %hex(addr),hex(value)
'''
        self.PPU7_Temp = value
        self.reg.PPU7_Temp_W(value)
        addr = address & 0x000F
        if addr == 0:
            self.Control1 = value
            self.reg.PPUCTRL_W(value)
       
        elif addr == 1:
            self.Control2 = value
            self.reg.PPUMASK_W(value)
            
            self.EmphVal = (value & 0xE0) * 2
            
        elif addr == 2:
            self.PPU7_Temp = value
            self.reg.PPU7_Temp_W(value)
            
        elif addr == 3:
            #print "Write SpriteAddress:",value
            self.SpriteAddress = value
            self.reg.OAMADDR_W(value)
            
        elif addr == 4:
            #print "Write SpriteRAM:",value
            self.SpriteRAM[self.SpriteAddress] = value
            self.SpriteAddress = (self.SpriteAddress + 1) & 0xFF
            
            self.reg.OAMADDR_W(value)
            
            
        elif addr == 5:
            #print "Write PPU Scroll Register(W2)"
            if self.AddressIsHi :
                self.HScroll = value
                self.AddressIsHi = 0
            else:
                self.vScroll = value
                self.AddressIsHi = 1

            '''if( not self.ScrollToggle):
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
                self.loopy_t = (self.loopy_t & 0x8FFF)|((value & 0x07)<<12)'''
            
            self.ScrollToggle = not self.ScrollToggle
                
        elif addr == 6:
            if self.AddressIsHi :
                self.AddressHi = value * 0x100
                self.AddressIsHi = 0
            else:
                self.Address = self.AddressHi + value
                self.reg.PPUADDR_W(self.AddressHi + value)
                self.AddressIsHi = 1

            '''if( not self.ScrollToggle):
                #First write
		#t:0011111100000000=d:00111111
                # t:1100000000000000=0
                self.loopy_t = (self.loopy_t & 0x00FF)|((value & 0x3F)<<8)

            else:
                #Second write
		#// t:0000000011111111=d:11111111
                self.loopy_t = (self.loopy_t & 0xFF00)|value
		#v=t
                self.loopy_v = self.loopy_t'''

            self.ScrollToggle = not self.ScrollToggle
                
        elif addr == 7:
            
            self.PPU7_Temp = value
            self.Address = self.Address & 0x3FFF

            if self.Address >= 0x3F00:# <= 0x3FFF:
                PalOffset = self.Address & 0x1F
                #self.VRAM[self.Address & 0x3F1F] = value
                if PalOffset & 0x3 == 0 and value:
                    self.Palettes[PalOffset ^ 0x10] = value
                    self.Palettes[PalOffset] = value
                else:
                    self.Palettes[PalOffset] = value
                    
                    
               #'VRAM((PPUAddress And 0x3F1F) Or 0x10) = value  'DF: All those ref's lied. The palettes don't mirror
            else:
                if (self.Address & 0x3000) == 0x2000:
                    self.VRAM[self.Address ^ self.cartridge.MirrorXor] = value
                self.VRAM[self.Address] = value
                
            if (self.Control1 & PPU_INC32_BIT) :
                self.Address = self.Address + 32
            else:
                self.Address = self.Address + 1

            self.reg.PPUDATA_W(value)

                
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
            self.Status = self.Status | 0x80#PPU_VBLANK_FLAG
        
	    
        if self.Running == 0:
            if self.Control2 & PPU_SPDISP_BIT == 0 :return
            if self.Status & 0x40 :return #PPU_SPHIT_FLAG
            if self.CurrentLine > self.SpriteRAM[0] + 8:
                self.Status = self.Status | 0x40#PPU_SPHIT_FLAG
            return

        self.ScanlineSPHit[self.CurrentLine] =  1 if self.Status & PPU_SPHIT_FLAG else 0

        '''self.sp_h = 16 if self.Control1 & PPU_SP16_BIT else 8

'''

    def ScanlineStart(self):
        if( self.Control2 & (PPU_BGDISP_BIT|PPU_SPDISP_BIT) ):
            self.loopy_v = (self.loopy_v & 0xFBE0)|(self.loopy_t & 0x041F)
            self.loopy_shift = self.loopy_x
            self.loopy_y = (self.loopy_v&0x7000)>>12
            #nes->mapper->PPU_Latch( 0x2000 + (loopy_v & 0x0FFF) );
                
    def ScanlineNext(self):
        if( self.Control2 & (PPU_BGDISP_BIT|PPU_SPDISP_BIT) ):
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
        if self.Control2 & (PPU_SPDISP_BIT|PPU_BGDISP_BIT):
            self.loopy_v = self.loopy_t
            self.loopy_shift = self.loopy_x
            self.loopy_y = (self.loopy_v & 0x7000)>>12

                    
    


    def PatternTables(self):
        #if self.Control2 & (PPU_SPDISP_BIT|PPU_BGDISP_BIT) == 0 :return

        PatternTablesAddress,PatternTablesSize = (0x1000,0x1000) if self.Control1 & PPU_SPTBL_BIT else (0,0x1000)
        
        return PatternTableArr(self.VRAM[PatternTablesAddress:PatternTablesAddress + 0x1000])

        '''img = np.zeros((8,256,3),np.uint8)
        for y in range(8):
            for index in range(32):
                for x in range(8):
                    img[y][index * 8 + x] = self.Pal[PatternTable[index][y][x]]
                #print img_line[y]

        #print img[0]
        return img#np.array(img,np.uint8)'''

    def NameTables_data(self,offset):
        NameTablesAddress = 0x2000 + offset * 0x400
        NameTablesSize = 0x3C0
        
        return self.VRAM[NameTablesAddress: NameTablesAddress + NameTablesSize]
    
           
        
    def NewRenderScanlinePixel(self, NameTableAddress):
        if self.Control2 & PPU_BGDISP_BIT == 0 :return
        if self.CurrentLine >240:return
        sc = self.CurrentLine + self.vScroll
        #sc = 1  + self.vScroll

        #NameTableAddress = 0x400 if 1 < 240 - self.vScroll else 0x800
        
        #TileRow = (sc // 8) % 30
        #TileYOffset = sc & 7

        NameTable = 0x2000 + (0x400 * (self.Control1 & PPU_NAMETBL_BIT)) ^ NameTableAddress
        
        PatternTable = (self.Control1 & PPU_BGTBL_BIT) << 8 #* 0x100
        
        AttributeTable = NameTable + 0x3C0

        lineArry = RenderScanlineArray(self.VRAM, NameTable, PatternTable, sc)
        #print lineArry.shape
        #print lineArry[TileYOffset]
        self.vBuffer[self.CurrentLine:self.CurrentLine+8] = lineArry[0:8]
        #self.lineBuffer = lineArry
        
    def blitFrame(self):
        #return
        if self.Control2 & (PPU_SPDISP_BIT|PPU_BGDISP_BIT) == 0 :return
        
        self.sp16 = 1 if self.Control1 & PPU_SP16_BIT else 0

        #NTnum = (self.loopy_v0 & 0x0FFF) >>10
        NTnum = self.Control1 & PPU_NAMETBL_BIT

        #fineYscroll = self.loopy_v >>12
        #coarseYscroll  = (self.loopy_v & 0x03FF) >> 5
        #coarseXscroll = self.loopy_v & 0x1F

        if self.cartridge.Mirroring:
            #self.scY = (coarseYscroll << 3) + fineYscroll + ((NTnum>>1) * 240) 
            #self.scX = (coarseXscroll << 3)+ self.loopy_x0 #self.HScroll
            self.scY = self.vScroll + ((NTnum>>1) * 240)
            self.scX = self.HScroll + ((NTnum & 1) * 256)
            
        if self.cartridge.Mirroring == 0:
            #self.scY = (coarseYscroll << 3) + fineYscroll + ((NTnum>>1) * 240) #if self.loopy_v&0x0FFF else self.scY
            self.scY = self.vScroll + ((NTnum>>1) * 240) 
            #if self.loopy_v&0x0FFF else self.scY
        
        RenderBG(self.FrameArray, self.VRAM, self.Control1, self.cartridge.Mirroring)

        self.RenderSprites()
        
        self.FrameBuffer = paintBuffer(self.FrameArray,self.Pal,self.Palettes)

        
        if self.debug == False and self.render:
            pass
            self.blitScreen()
            self.blitPal()
        else:
            #if self.debug:
            #    print self.vScroll, hex(NTnum), self.scY, self.scX, self.HScroll #,hex(coarseYscroll), hex(coarseXscroll), 
            self.blitPatternTable()
            self.blitPal()
            
    def RenderSprites(self):
        #PatternTablesAddress = 0x1000 if self.Control1 & PPU_SPTBL_BIT and self.sp16 else 0
        PatternTablesAddress,PatternTablesSize = (0x1000,0x1000) if self.Control1 & PPU_SPTBL_BIT and self.sp16 else (0 ,0x1000)
        
        PatternTable_Array = PatternTableArr(self.VRAM[PatternTablesAddress : PatternTablesAddress + PatternTablesSize])

        
        RenderSpriteArray(self.FrameArray, self.SpriteRAM, PatternTable_Array, self.scY, self.scX, self.sp16, self.ScanlineSPHit)
         

    def RenderAttributeTables(self,offset):
        AttributeTablesAddress = 0x2000 + (offset * 0x400 + 0x3C0)
        AttributeTablesSize = 0x40
        
        return self.VRAM[AttributeTablesAddress: AttributeTablesAddress + AttributeTablesSize]
    
    def blitScreen(self):
        
        cv2.imshow("Main", self.FrameBuffer[self.scY:self.scY + 240,self.scX:self.scX+256])
        cv2.waitKey(1)

    def blitPal(self):
        cv2.imshow("Pal", np.array([[self.Pal[i] for i in self.Palettes ]]))
        cv2.waitKey(1)

    def blitPatternTable(self):
        cv2.line(self.FrameBuffer,(0,240),(768,240),(0,255,0),1) 
        cv2.line(self.FrameBuffer,(0,480),(768,480),(0,255,0),1) 
        cv2.line(self.FrameBuffer,(256,0),(256,720),(0,255,0),1) 
        cv2.line(self.FrameBuffer,(512,0),(512,720),(0,255,0),1) 
        cv2.rectangle(self.FrameBuffer, (self.scX,self.scY),(self.scX+255,self.scY + 240),(0,0,255),1)
        cv2.imshow("PatternTable0", self.FrameBuffer)
        cv2.waitKey(1)

#@jit
def RenderBG(FrameArray, VRAM, PPU_Control1, Mirroring):
        
        PatternTablesAddress = (PPU_Control1 & 0x10 ) << 8 #PPU_BGTBL_BIT = 0x10
        
        PatternTable_Array = PatternTableArr(VRAM[PatternTablesAddress : PatternTablesAddress + 0x1000])

        if Mirroring == 1:
            RenderNameTableH(FrameArray, VRAM, PatternTable_Array, 0,1)

        elif Mirroring == 0 :
            
            RenderNameTableV(FrameArray,VRAM,PatternTable_Array, 0,2)
            
        elif Mirroring == 2:
            return  RenderNameTables(VRAM,PatternTable_Array, 0,1,2,3)
        else:
            return RenderNameTables(VRAM,PatternTable_Array, 0,1,2,3)

            
#@jit
def RenderNameTableH(FrameArray, VRAM, PatternTables,nt0,nt1):
    tempBuffer0 = NameTableArr(NameTables_data(VRAM, nt0),PatternTables)
    RenderNameTable(AttributeTables_data(VRAM, nt0), tempBuffer0)
    tempBuffer1 = NameTableArr(NameTables_data(VRAM, nt1),PatternTables)
    RenderNameTable(AttributeTables_data(VRAM, nt1), tempBuffer1)
    FrameArray[0:480,0:768] = np.row_stack((np.column_stack((tempBuffer0,tempBuffer1,tempBuffer0)),np.column_stack((tempBuffer0,tempBuffer1,tempBuffer0))))

#@njit
def RenderNameTableV(FrameArray, VRAM, PatternTables, nt0, nt2):
    tempBuffer0 = NameTableArr(NameTables_data(VRAM, nt0),PatternTables)
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
def RenderSpriteArray(BGbuffer, SPRAM, PatternTableArray,  vScroll, HScroll, SP16, SPHIT):
    #SpriteArr = np.zeros((8, 16),np.uint8) if SP16 else np.zeros((8, 8),np.uint8)
    
    for spriteIndex in range(63,-1,-1):
        spriteOffset =  spriteIndex * 4
        if SPRAM[spriteOffset] >= 240: continue
        
        spriteY = SPRAM[spriteOffset] + vScroll
        spriteX = SPRAM[spriteOffset + 3] + HScroll
        

        
        chr_index = SPRAM[spriteOffset + 1]
        if SP16:
            chr_index = chr_index ^ (chr_index & 1)
        chr_l = PatternTableArray[chr_index]
        chr_h = PatternTableArray[(chr_index + 1) & 0xFF]
 
            
        if SPRAM[spriteOffset + 2] & 0x40:
            chr_l = chr_l[:,::-1]    
            if SP16:
                chr_h = chr_h[:,::-1]
                

        if SPRAM[spriteOffset + 2] & 0x80:
            chr_l = chr_l[::-1] 
            if SP16:
                chr_h = chr_h[::-1]
                chr_l,chr_h = chr_h,chr_l
        
        SpriteArr = np.row_stack((chr_l,chr_h)) if SP16 else chr_l

        SpriteArr = np.add(SpriteArr, ((SPRAM[spriteOffset + 2] & 0x03) << 2) + 0x10)

        spriteW = 8 
        spriteH = SpriteArr.shape[0] 
        
        if BGbuffer.shape[0] - spriteY > spriteH and BGbuffer.shape[1] - spriteX > spriteW :
            BGPriority = SPRAM[spriteOffset + 2] & SP_PRIORITY_BIT
            if BGPriority:
                #continue
                BG_alpha = BGbuffer[spriteY:spriteY + spriteH, spriteX:spriteX + spriteW] & 3
                BGbuffer[spriteY:spriteY + spriteH, spriteX:spriteX + spriteW][BG_alpha == 0] = SpriteArr[BG_alpha == 0]
            else:
                #continue
                if SPHIT[spriteY - vScroll]:
                    BGbuffer[spriteY:spriteY + spriteH, spriteX:spriteX + spriteW][SpriteArr & 3 > 0] = SpriteArr[SpriteArr & 3 > 0]#<<1#[0:spriteH,0:spriteW]
                else:
                    BGbuffer[spriteY:spriteY + spriteH, spriteX:spriteX + spriteW][SpriteArr & 3 > 0] = SpriteArr[SpriteArr & 3 > 0]
            #BG[spriteY:spriteY + spriteH, spriteX:spriteX + spriteW] = SpriteArr
                
    #return BG


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

@jit
def byte2bit1(byte):
    return np.array([1 if (byte) & (2**bit) else 0 for bit in range(0x7,-1,-1)], np.uint8)
@jit
def byte2bit2(byte):
    return  np.array([2 if (byte) & (2**bit) else 0 for bit in range(0x7,-1,-1)], np.uint8)
            


@jitclass([('a',uint8),('p',uint8),('reg',uint8[:])])
class regt(object):
    def __init__(self,register):
        self.a = register[0]
        self.p = register[1]
        self.reg = register

    def __call__(self):
        print 'self.a,self.p',self.a,self.p
        
    def r_a(self):
        return a

    def w_a(self,value):
        self.a = value
    
#@jitclass([('reg',uint8[:])])
class regt2(object):
    def __init__(self,regt):
        self.reg = regt
        self.a = regt.a

    def __call__(self):
        print 'self.a,self.p',self.a,self.p
        
    def r_a(self):
        return a

    def w_a(self):
        self.reg.reg[0] += 10
        self.reg.a += 100

@jit        
def adc1(reg):
    reg.a += 1


def adc2(reg):
    reg.a += 2
                    
if __name__ == '__main__':
    #ppu = PPU()
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

    reg = PPUREG(Memory(BGRpal()))
    reg.PPUCTRL_W(1)
    print reg.PPUCTRL
    
    bb = np.zeros(2, np.uint8)
    test = regt(bb)
    print type(test)#test.a
    adc1(test)
    print test.a
    adc2(test)
    print test.a
    test2 = regt2(test)
    test3 = regt2(test)
    print test.a
    print test.reg
    print test2.reg.a
    print test2.reg.reg
    print '---'
    test2.a = 5
    print test.a
    print test.reg
    print test2.reg.a
    print test2.a
    print test2.reg.reg
    print test3.reg.a
    print test.a
    print test3.reg.reg
    
    
    
    








        
