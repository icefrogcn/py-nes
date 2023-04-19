# -*- coding: UTF-8 -*-

import time
import math
import traceback

import cv2
import numpy as np
import numba as nb
from numba import jit
from numba import jitclass

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



class PPU(NES):

    CurrentLine = np.uint16(0) #Long 'Integer

    NameTable = np.uint8(0)


    VRAM = np.zeros(0x4000, np.uint8) #3FFF #As Byte, VROM() As Byte  ' Video RAM

    PPU7_Temp = np.uint8(0xFF)
    
    def __init__(self,debug = False):

        self.debug = debug
        
        #6502中没有寄存器，故使用工作内存地址作为寄存器
        self.PPU_Write = {
            #0x2000:self.PPU_Control1_W,
            #0x2001:self.PPU_Control2_W,
            #0x2003:self.SPR_RAM_Address_W,
            #0x2004:self.SPR_RAM_W,
            #0x2005:self.PPU_Scroll_W,
            #0x2006:self.PPU_Control1_W,
                }

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
        self.PPU7_Temp 
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
        
        #self.VRAM = [0] * 0x4000 #3FFF 
        #self.VRAM = np.zeros(0x4000, np.uint8) #3FFF #As Byte, VROM() As Byte  ' Video RAM
        #self.SpriteRAM = [0] * 0x100 #FF# As Byte     
        self.SpriteRAM = np.zeros(0x100, np.uint8) #'活动块存储器，单独的一块，不占内存
        

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
        self.Pal = BGRpal

        self.Palettes = np.zeros(0x20, np.uint8)#[0] * 0x20
        self.BGPAL = [0] * 0x10
        self.SPRPAL = [0] * 0x10
        
        


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
        


        mmc_info = 0
        if 0x2000<= addr <=0x2FFF:
            pass
            #self.PPU7_Temp = nt(mirror((addr & 0xC00) / 0x400), addr & 0x3FF)
        elif(addr >= 0x3000):
            if addr >= 0x3F00:
                data &= 0x3F
                self.PPU7_Temp = self.Palettes[addr & 0x1F]
            addr &= 0xEFFF
        else:
            self.PPU7_Temp = self.VRAM[addr & 0x3FFF]
            

        self.PPU7_Temp = 0xFF #self.VRAM[addr>>10][addr&0x03FF]
        self.Address +=  32 if (self.Control1 & PPU_INC32_BIT) else 1

        return data
        
    def Read(self,addr):
        try:
            return self.PPU_Read.get(addr)()
        except:
            print "Invalid PPU Read - %s" %hex(addr)
            print (traceback.print_exc())
            return 0
            
        
    def Write(self,address,value):
        '''try:
            self.PPU_Write_dic.get(addr)(value)
        except:
            print "Invalid PPU Write - %s : %s" %hex(addr),hex(value)
'''
        self.PPU7_Temp = value
        addr = address & 0x000F
        if addr == 0:
            self.Control1 = value
           
       
        elif addr == 1:
            self.Control2 = value
            #print "Write PPU crl2"
            self.EmphVal = (value & 0xE0) * 2
            
        elif addr == 2:
            self.PPU7_Temp = value
            
        elif addr == 3:
            #print "Write SpriteAddress:",value
            self.SpriteAddress = value
            
        elif addr == 4:
            #print "Write SpriteRAM:",value
            self.SpriteRAM[self.SpriteAddress] = value
            self.SpriteAddress = (self.SpriteAddress + 1) & 0xFF
            
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

            if  0x3F00 <= self.Address:# <= 0x3FFF:
                self.VRAM[self.Address & 0x3F1F] = value
                self.Palettes[self.Address & 0x1F] = value
                
                    
               #'VRAM((PPUAddress And 0x3F1F) Or 0x10) = value  'DF: All those ref's lied. The palettes don't mirror
            else:
                if (self.Address & 0x3000) == 0x2000:
                    self.VRAM[self.Address ^ NES.MirrorXor] = value
                self.VRAM[self.Address] = value
                
            if (self.Control1 & PPU_INC32_BIT) :
                self.Address = self.Address + 32
            else:
                self.Address = self.Address + 1
                
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

        if self.CurrentLine < 8 :
            self.Status = self.Status & 0x3F

        if self.CurrentLine == 239 :
            self.Status = self.Status | PPU_VBLANK_FLAG
        
        self.ScanlineSPHit[self.CurrentLine] =  1 if self.Status & PPU_SPHIT_FLAG else 0
	    
        if self.Running == 0:
            if self.Control2 & PPU_SPDISP_BIT == 0 :return
            if self.Status & PPU_SPHIT_FLAG == 0 :return
            if self.CurrentLine > self.SpriteRAM[0] + 8:
                self.Status = self.Status | PPU_SPHIT_FLAG
            return

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

    
    def RenderScanlinePixel(self, NameTableAddress):
        if self.Control2 & PPU_BGDISP_BIT == 0 :return
            
        sc = self.CurrentLine + self.vScroll
        
        TileRow = (sc // 8) % 30
        TileYOffset = sc & 7

        
        NameTable = 0x2000 + (0x400 * (self.Control1 & PPU_NAMETBL_BIT)) ^ NameTableAddress
        
        self.PatternTable = (self.Control1 & PPU_BGTBL_BIT) << 8 #* 0x100
        
        AttributeTable = NameTable + 0x3C0


        for TileCounter in range(self.HScroll / 8, 32):
            TileIndex = self.VRAM[NameTable + TileCounter + TileRow * 32]
            '''If Mapper = 9 Or Mapper = 10 Then
                If PatternTable = &H0 Then
                    MMC2_latch TileIndex, False
                ElseIf PatternTable = &H1000& Then
                    MMC2_latch TileIndex, True
                End If
            End If'''
            Byte1 = self.VRAM[self.PatternTable + TileIndex * 16 + TileYOffset]  #-1
            Byte2 = self.VRAM[self.PatternTable + TileIndex * 16 + 8 + TileYOffset] #-1
            
            c1 = ((Byte1>>1)&0x55)|(Byte2&0xAA)
            c2 = (Byte1&0x55)|((Byte2<<1)&0xAA)
            '''if True:#c1 or c2:
                #print hex(c1),hex(c2)
                self.vBuffer[self.CurrentLine][0 + TileCounter * 8] = self.Pal[self.BGPAL[(c1>>6)]]
                self.vBuffer[self.CurrentLine][4 + TileCounter * 8] = self.Pal[self.BGPAL[(c1>>2)&3]]
                self.vBuffer[self.CurrentLine][1 + TileCounter * 8] = self.Pal[self.BGPAL[(c2>>6)]]
                self.vBuffer[self.CurrentLine][5 + TileCounter * 8] = self.Pal[self.BGPAL[(c2>>2)&3]]
                self.vBuffer[self.CurrentLine][2 + TileCounter * 8] = self.Pal[self.BGPAL[(c1>>4)&3]]
                self.vBuffer[self.CurrentLine][6 + TileCounter * 8] = self.Pal[self.BGPAL[c1&3]]
                self.vBuffer[self.CurrentLine][3 + TileCounter * 8] = self.Pal[self.BGPAL[(c2>>4)&3]]
                self.vBuffer[self.CurrentLine][7 + TileCounter * 8] = self.Pal[self.BGPAL[c2&3]]'''
            
            
            X = TileCounter * 8 - self.HScroll + 7
            m = X if X < 7 else 7
            X = X + self.CurrentLine * 256
            LookUp = self.VRAM[AttributeTable + TileCounter / 4 + (TileRow / 4) * 0x8]
            
            Tiletemp = (TileCounter & 2) | (TileRow & 2) * 2
            if Tiletemp == 0:
                    addToCol = LookUp * 4 & 12
            elif Tiletemp == 2:
                    addToCol = LookUp & 12
            elif Tiletemp == 4:
                    addToCol = LookUp / 4 & 12
            elif Tiletemp == 6:
                    addToCol = LookUp / 16 & 12
            
            a = (Byte1 * 2048) + (Byte2 * 8)
                
            #for pixel in range(m,0,-1): # = m To 0 Step -1
            for pixel in range(m + 1): # = m To 0 Step -1
                try:
                    Color = NES.tLook[a + pixel]
                except:
                    print a,m,pixel,a + pixel
                if Color:# addToCol :
                    pass
                    #self.vBuffer[Scanline][8 - pixel + TileCounter * 8] = self.Pal[Color | addToCol]
                    self.vBuffer[self.CurrentLine][8 - pixel + TileCounter * 8] = Color | addToCol


        

                    
    


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
        if self.Control2 & (PPU_SPDISP_BIT|PPU_BGDISP_BIT) == 0 :return
        
        self.sp16 = 1 if self.Control1 & PPU_SP16_BIT else 0

        #NTnum = (self.loopy_v0 & 0x0FFF) >>10
        NTnum = self.Control1 & PPU_NAMETBL_BIT

        #fineYscroll = self.loopy_v >>12
        #coarseYscroll  = (self.loopy_v & 0x03FF) >> 5
        #coarseXscroll = self.loopy_v & 0x1F

        if NES.Mirroring:
            #self.scY = (coarseYscroll << 3) + fineYscroll + ((NTnum>>1) * 240) 
            #self.scX = (coarseXscroll << 3)+ self.loopy_x0 #self.HScroll
            self.scY = self.vScroll + ((NTnum>>1) * 240)
            self.scX = self.HScroll + ((NTnum & 1) * 256)
            
        if NES.Mirroring == 0:
            #self.scY = (coarseYscroll << 3) + fineYscroll + ((NTnum>>1) * 240) #if self.loopy_v&0x0FFF else self.scY
            self.scY = self.vScroll + ((NTnum>>1) * 240) 
            #if self.loopy_v&0x0FFF else self.scY
        
        self.RenderBG()

        self.RenderSprites()
        
        self.FrameBuffer = paintBuffer(self.FrameBuffer,self.Pal,self.Palettes)

        
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

        
        self.FrameBuffer = RenderSpriteArray(self.SpriteRAM, PatternTable_Array, self.FrameBuffer, self.scY, self.scX, self.sp16, self.ScanlineSPHit)
         
    
    def RenderBG(self):
        
        #PatternTablesAddress = 0x1000 if self.Control1 & PPU_SPTBL_BIT and self.sp_h == 8 else 0

        PatternTablesAddress = (self.Control1 & PPU_BGTBL_BIT) << 8 #* 0x100
        
        PatternTable_Array = PatternTableArr(self.VRAM[PatternTablesAddress : PatternTablesAddress + 0x1000])

        if NES.Mirroring == 1:
            self.FrameBuffer = self.RenderNameTableH(PatternTable_Array, 0,1)

        elif NES.Mirroring == 0 :
            
            self.FrameBuffer = self.RenderNameTableV(PatternTable_Array, 0,2)
            
        elif NES.Mirroring == 2:
            self.FrameBuffer = self.RenderNameTables(PatternTable_Array, 0,1,2,3)
        else:
            self.FrameBuffer = self.RenderNameTables(PatternTable_Array, 0,1,2,3)


    
    def RenderNameTableH(self,PatternTables,nt0,nt1):
        tempBuffer0 = AttributeTableArr(self.RenderAttributeTables(nt0), NameTableArr(self.NameTables_data(nt0),PatternTables))
        tempBuffer1 = AttributeTableArr(self.RenderAttributeTables(nt1), NameTableArr(self.NameTables_data(nt1),PatternTables))
        return np.row_stack((np.column_stack((tempBuffer0,tempBuffer1,tempBuffer0)),np.column_stack((tempBuffer0,tempBuffer1,tempBuffer0))))
    
    def RenderNameTableV(self,PatternTables,nt0,nt2):
        tempBuffer0 = AttributeTableArr(self.RenderAttributeTables(nt0), NameTableArr(self.NameTables_data(nt0),PatternTables))
        tempBuffer2 = AttributeTableArr(self.RenderAttributeTables(nt2), NameTableArr(self.NameTables_data(nt2),PatternTables))
        return np.column_stack((np.row_stack((tempBuffer0,tempBuffer2,tempBuffer0)),np.row_stack((tempBuffer0,tempBuffer2,tempBuffer0))))
    
    def RenderNameTables(self,PatternTables,nt0,nt1,nt2,nt3):
        
        tempBuffer0 = AttributeTableArr(self.RenderAttributeTables(nt0), NameTableArr(self.NameTables_data(nt0),PatternTables))
        tempBuffer1 = AttributeTableArr(self.RenderAttributeTables(nt1), NameTableArr(self.NameTables_data(nt1),PatternTables))
        tempBuffer2 = AttributeTableArr(self.RenderAttributeTables(nt2), NameTableArr(self.NameTables_data(nt2),PatternTables))
        tempBuffer3 = AttributeTableArr(self.RenderAttributeTables(nt3), NameTableArr(self.NameTables_data(nt3),PatternTables))

        return np.row_stack((np.column_stack((tempBuffer3,tempBuffer2)),np.column_stack((tempBuffer1,tempBuffer0))))
    
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



@jit
def RenderScanlineArray(VRAM, NameTable, PatternTable, Scanline):
    offset = (Scanline - 1)  / 8 * 32
    NameTableArray = VRAM[NameTable + offset: NameTable + offset + 32]
    PTArr = PatternTableArr(VRAM[PatternTable: PatternTable + 0x1000])
    NoAttriArray = NameTableArr(NameTableArray, PTArr)
    return NoAttriArray

@jit
def paintBuffer(FrameBuffer,Pal,Palettes):
    [rows, cols] = FrameBuffer.shape
    img = np.zeros((rows, cols,3),np.uint8)
    for i in range(rows):
        for j in range(cols):
            img[i, j] = Pal[Palettes[FrameBuffer[i, j]]]
    return img

#@jit
def RenderSpriteArray(SPRAM, PatternTableArray, BG, vScroll, HScroll, SP16, SPHIT):
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

        
        SpriteArr = np.add(SpriteArr, (SPRAM[spriteOffset + 2] & 0x03) << 2)

            
        spriteW = 8 
        spriteH = SpriteArr.shape[0] 
        
        if BG.shape[0] - spriteY > spriteH and BG.shape[1] - spriteX > spriteW :
            BGPriority = SPRAM[spriteOffset + 2] & SP_PRIORITY_BIT
            if BGPriority:
                continue
                BG_alpha = BG[spriteY:spriteY + spriteH, spriteX:spriteX + spriteW] & 3
                BG[spriteY:spriteY + spriteH, spriteX:spriteX + spriteW][BG_alpha == 0] \
                                   = SpriteArr[BG_alpha == 0]
            else:
                BG[spriteY:spriteY + spriteH, spriteX:spriteX + spriteW][SpriteArr & 3 > 0] = SpriteArr[SpriteArr & 3 > 0] + 0x10#<<1#[0:spriteH,0:spriteW]
                
    return BG


@jit
def AttributeTableArr(AttributeTables, FrameBuffer):
    tempFrame = np.zeros((257, 257),np.uint8)
    for i in range(len(AttributeTables)):
        col = i >> 3; row = i & 7
        if AttributeTables[i] == 0:
            continue
        tempFrame[(col << 5)        :(col << 5) + 16 ,  (row << 5)      : (row  << 5) + 16] = (AttributeTables[i] & 0b11) << 2
        tempFrame[(col << 5) + 16   :(col << 5) + 32 ,  (row << 5)      : (row  << 5) + 16] = (AttributeTables[i] & 0b110000) >> 2
        tempFrame[(col << 5)        :(col << 5) + 16 ,  (row << 5) + 16 : (row  << 5) + 32] = (AttributeTables[i] & 0b1100)
        tempFrame[(col << 5) + 16   :(col << 5) + 32 ,  (row << 5) + 16 : (row  << 5) + 32] = (AttributeTables[i] & 0b11000000) >> 4

    
    return FrameBuffer | tempFrame[0:240,0:256]


@jit
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
    

@jit#(nopython = True)
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
            

'''
    def DrawSprites(self,ontop):
        
        if self.Control2 & PPU_SPDISP_BIT == 0 :return
        
        SpritePattern = (self.Control1 & PPU_SPTBL_BIT) * 0x200
        
        h = 16 if self.Control1 & PPU_SP16_BIT else 8
        
        SpriteAddr = 0
        i,sa = 0,0
        for spr in range(63,-1,-1):
            SpriteAddr = 4 * spr
            attrib = self.SpriteRAM[SpriteAddr + 2]
            if (attrib & 32) == 0 ^ ontop:
                X = self.SpriteRAM[SpriteAddr + 3]
                Y = self.SpriteRAM[SpriteAddr]
                if Y < 239 and X < 248 :
                    tileno = self.SpriteRAM[SpriteAddr + 1]
                    if h == 16 :
                        SpritePattern = (tileno & 1) * 0x1000
                        tileno = tileno ^ (tileno & 1)
                    sa = SpritePattern + 16 * tileno
                    i = Y * 256 + X + 256
                    palette = 16 + (attrib & 3) * 4

                    if attrib & 128 :
                        if attrib & 64:
                            Xflag = X
                            i = self.DrawSpritesPixel(i,h,sa,Xflag,Y,palette)
                            for y1 in range(h-1,0,-1):#= h - 1 To 0 Step -1
                                if y1 >= 8 :
                                    Byte1 = VRAM[sa + 8 + y1]
                                    Byte2 = VRAM[sa + 16 + y1]
                                else:
                                    Byte1 = VRAM[sa + y1]
                                    Byte2 = VRAM[sa + y1 + 8]

                                a = Byte1 * 2048 + Byte2 * 8
                                for X1 in range(8):#= 0 To 7
                                    Color = NES.tLook[X1 + a]
                                    if Color:
                                        #vBuffer(i + X1) = Color | pal
                                        self.vBuffer[Y][X1 + X] = self.Pal[Color | pal]
                                i = i + 256
                                if i >= 256 * 240:break
                        else:
                            i += 7
                            Xflag = -X
                            i = self.DrawSpritesPixel(i,h,sa,Xflag,Y,palette)
                            for y1 in range(h-1,0,-1):#= h - 1 To 0 Step -1
                                if y1 >= 8 :
                                    Byte1 = VRAM[sa + 8 + y1]
                                    Byte2 = VRAM[sa + 16 + y1]
                                else:
                                    Byte1 = VRAM[sa + y1]
                                    Byte2 = VRAM[sa + y1 + 8]

                                a = Byte1 * 2048 + Byte2 * 8
                                for X1 in range(8):#= 0 To 7
                                    Color = NES.tLook[X1 + a]
                                    if Color:
                                        #vBuffer(i + X1) = Color | pal
                                        self.vBuffer[Y][X1 - X] = self.Pal[Color | pal]
                                i = i + 256
                                if i >= 256 * 240:break
                    else:
                        if attrib & 64:
                            Xflag = X
                            i = self.DrawSpritesPixel(i,h,sa,Xflag,Y,palette)
                            
                        else:
                            i += 7
                            Xflag = -X
                            i = self.DrawSpritesPixel(i,h,sa,Xflag,Y,palette)
                            

                        

    def DrawSpritesPixel(self,i,h,sa,Xflag,Y,palette):
                        for y1 in range(h-1,0,-1):#= h - 1 To 0 Step -1
                            if y1 >= 8 :
                                Byte1 = self.VRAM[sa + 8 + y1]
                                Byte2 = self.VRAM[sa + 16 + y1]
                            else:
                                Byte1 = self.VRAM[sa + y1]
                                Byte2 = self.VRAM[sa + y1 + 8]

                            a = Byte1 * 2048 + Byte2 * 8
                            for X1 in range(8):#= 0 To 7
                                Color = NES.tLook[X1 + a]
                                if Color:
                                    #vBuffer(i + X1) = Color | pal
                                    self.vBuffer[Y][X1 + Xflag] = self.Pal[self.Palettes[Color | palette]]
                            i += 256
                            if i >= 256 * 240:break
                        return i

                

'''


                    
if __name__ == '__main__':
    ppu = PPU()
    #ppu.pPPUinit()
    #print ppu.blankLine
    #print len(ppu.vBuffer)
    #print len(ppu.vBuffer[0])
    #print ppu.vBuffer[2:4]
    #print ppu.vBuffer[3]
    #print ppu.vBuffer[2][1]
    #cv2.imshow("Main", np.array(ppu.vBuffer,dtype=np.uint8))
    print ppu.Read(0x2000)
    #print byte2bit1(0x0) + byte2bit2(0x28)
    aa = PatternTableArr(np.array([0x10,0,0x44,0,0xfe,0,0x82,00,00,0x28,0x44,0x82,00,0x82,0x82,00],dtype=np.uint8))











        
