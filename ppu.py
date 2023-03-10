# -*- coding: UTF-8 -*-

import time
import math
import traceback

import cv2
import numpy as np
from numba import jit

from nes import NES
from pal import BGRpal
#PPU

class PPU(NES):

# PPU Control Register #1	PPU #0
    PPU_VBLANK_BIT	=	0x80
    PPU_SPHIT_BIT	=	0x40		#
    PPU_SP16_BIT	=	0x20
    PPU_BGTBL_BIT	=	0x10
    PPU_SPTBL_BIT	=	0x08
    PPU_INC32_BIT	=	0x04
    PPU_NAMETBL_BIT	=	0x03


    NameTable = 0

        
    def __init__(self,debug = False):
        #6502中没有寄存器，故使用工作内存地址作为寄存器
        self.PPU_Write = {
            0x2000:self.PPU_Control1_W,
            #0x2001:self.PPU_Control2_W,
            #0x2003:self.SPR_RAM_Address_W,
            #0x2004:self.SPR_RAM_W,
            #0x2005:self.PPU_Scroll_W,
            #0x2006:self.PPU_Control1_W,
                }

        self.PPU_Read = {
            0x2000:self.PPU7_Temp,
            0x2001:self.PPU7_Temp,
            0x2003:self.PPU7_Temp,
            0x2005:self.PPU7_Temp,
            0x2006:self.PPU7_Temp,
            
            0x2002:self.PPU_Control1_R,
            0x2004:self.SPR_RAM_R,
            0x2007:self.VRAM_R,
                }

    def pPPUinit(self):
        self.Control1 = 0 # $2000
        self.Control2 = 0 # $2001
        self.Status = 0 # $2002
        self.SpriteAddress = 0 #As Long ' $2003
        self.AddressHi = 0 # $2006, 1st write
        self.Address = 0 # $2006
        self.AddressIsHi = 1
        self.PPU7_Temp = 0xFF
        self.ScrollToggle = 0
        self.HScroll = 0
        self.vScroll = 0
        #self.MirrorXor = 0

        self.render = True

        self.tilebased = False
        
        self.EmphVal = 0   #???????Color
        
        self.VRAM = [0] * 0x4000 #3FFF #As Byte, VROM() As Byte  ' Video RAM
        #self.VRAM = np.array([0] * 0x4000, np.uint8) #3FFF #As Byte, VROM() As Byte  ' Video RAM
        self.SpriteRAM = [0] * 0x100 #FF# As Byte      '活动块存储器，单独的一块，不占内存


        self.width,self.height = 263,241

        self.blankPixel = np.array([16,0,0] ,dtype=np.uint8)
        
        self.blankLine = np.array([[16,0,0]] * self.width ,dtype=np.uint8)
        #self.blankLine = [[0,0,16]] * self.height 
        
        'DF: array to draw each frame to'
        #self.vBuffer = [16]* (256 * 241 - 1) 
        '256*241 to allow for some overflow     可以允许一些溢出'
        #self.vBuffer = np.random.randint(0,1,size = (self.height,self.width,3),dtype=np.uint8)
        
        self.vBuffer = np.array([self.blankLine] * self.height ,dtype=np.uint8)
        
        
        #print self.blankLine

        self.vBuffer16 = [0]*(256 * 240 - 1) #As Integer
        self.vBuffer32 = [0]*(256 * 240 - 1) #As Long

        #self.tLook = NES.fillTLook()#[0]*(65536 * 8 - 1) #As Byte

        self.PatternTable = 0

        #self.Pal = np.array([[item >> 16, item >> 8 & 0xFF ,item & 0xFF] for item in NES.CPal])
        self.Pal = BGRpal

        self.Palettes = [0] * 0x20
        self.BGPAL = [0] * 0x10
        self.SPRPAL = [0] * 0x10
        
        
        if self.render:
            cv2.namedWindow('Main', cv2.WINDOW_NORMAL)
        cv2.namedWindow('Pal', cv2.WINDOW_NORMAL)
        
    def PPU7_Temp(self):
        return 0xFF
        
    def PPU_Control1_R(self):
        ret = self.Status
        self.AddressIsHi = True
        self.ScrollToggle = 0
        self.Status = self.Status & 0x3F
        return ret #PPU_Status = 0

    def SPR_RAM_R(self):
        print "Read SpiritRAM "
        ret = self.SpriteRAM(self.SpriteAddress)
        self.SpriteAddress = (self.SpriteAddress + 1) #& 0xFF
        return ret

    def VRAM_R(self):
        #print "Read PPU MMC",hex(self.Address)
        #if self.Mapper == 9 or self.Mapper == 10:
            #print "Mapper 9 - 10"

        mmc_info = self.VRAM[self.Address & 0x3F1F - 1] if (self.Address >= 0x3F20 and self.Address <= 0x3FFF) else self.VRAM[self.Address - 1]

        self.Address +=  32 if (self.Control1 & 0x4) else 1
        
        #print "Read PPU addr",mmc_info,self.Address
        return mmc_info
        
    def Read(self,addr):
        try:
            return self.PPU_Read.get(addr)()
        except:
            print "Invalid PPU Read - %s" %hex(addr)
            print (traceback.print_exc())
            return 0
            
    def PPU_Control1_W(self,value):
        #print value
        self.Control1 = value

        
    def Write(self,addr,value):
        '''try:
            self.PPU_Write_dic.get(addr)(value)
        except:
            print "Invalid PPU Write - %s : %s" %hex(addr),hex(value)
'''
        if addr == 0x2000:
            #self.Control1 = value
            self.PPU_Control1_W(value)
       
        elif addr == 0x2001:
            self.Control2 = value
            #print "Write PPU crl2"
            self.EmphVal = (value & 0xE0) * 2
        elif addr == 0x2003:
            #print "Write SpriteAddress"
            self.SpriteAddress = value
        elif addr == 0x2004:
            #print "Write SpriteRAM"
            self.SpriteRAM[self.SpriteAddress] = value
            self.SpriteAddress = (self.SpriteAddress + 1) #And 0xFF
        elif addr == 0x2005:
            #print "Write PPU Scroll Register(W2)"
            if self.AddressIsHi :
                self.HScroll = value
                self.AddressIsHi = 0
            else:
                self.vScroll = value
                self.AddressIsHi = 1
        elif addr == 0x2006:
            if self.AddressIsHi :
                self.AddressHi = value * 0x100
                self.AddressIsHi = 0
            else:
                self.Address = self.AddressHi + value
                self.AddressIsHi = 1
        elif addr == 0x2007:
            self.Address = self.Address & 0x3FFF
            '''if NES.Mapper == 9 or NES.Mapper == 10 :
                if PPUAddress <= 0x1FFF :
                    if PPUAddress > 0xFFF :
                        pass
                        #MMC2_latch VRAM(PPUAddress), True
                    else:
                        pass
                        #MMC2_latch VRAM(PPUAddress), False'''
            if  0x3F00 <= self.Address:# <= 0x3FFF:
                self.VRAM[self.Address & 0x3F1F] = value
                self.Palettes[self.Address & 0x1F] = value
                
                if self.Address & 0x000F == 0x0000:
                    self.BGPAL[0] = self.SPRPAL[0] = value
                elif self.Address & 0x0010 == 0x0000:
                    self.BGPAL[self.Address & 0x000F] = value
                else:
                    self.SPRPAL[self.Address & 0x000F] = value
                    
               #'VRAM((PPUAddress And 0x3F1F) Or 0x10) = value  'DF: All those ref's lied. The palettes don't mirror
            else:
                if (self.Address & 0x3000) == 0x2000:
                    self.VRAM[self.Address ^ self.MirrorXor] = value
                self.VRAM[self.Address] = value
                
            if (self.Control1 & 0x4) :
                self.Address = self.Address + 32
            else:
                self.Address = self.Address + 1
                
    def RenderScanline(self,Scanline):

        self.Scanline = Scanline
        
        if Scanline > 239:return
        
        if Scanline < 8 :
            self.Status = self.Status & 0x3F

        if Scanline == 239 :
            self.Status = self.Status | 0x80

        if not self.render:
            if self.Control2 & 16 == 0 :return
            if self.Status & 64 == 0 :return
            if Scanline > self.SpriteRAM[0] + 8:
                self.Status = self.Status | 64
            return

        if self.tilebased:
            h = 16 if self.Control1 & 0x20 else 8
            if self.Status & 0x40 == 0:
                if Scanline > self.SpriteRAM[0] + h :
                    self.Status = self.Status | 64
            if Scanline == 1:
                self.vBuffer[Scanline] = self.blankLine
                self.DrawSprites(True)
                
            if  Scanline == 239:
                pass
                self.DrawSprites(False)
        else:
            #sc = Scanline * 0x100
            self.vBuffer[Scanline] = self.blankLine
            #'draw background sprites
            self.RenderSprites(Scanline, True)

        
        #draw background

        if Scanline < 240 - self.vScroll :
            pass
            #self.NameTable = 0x2000 + (0x400 * (self.Control1 & 0b11))
            self.RenderScanlinePixel(0)
            #self.NameTable = 0x2000 + (0x400 * (self.Control1 & 0b11)) ^ 0x400
            self.RenderScanlinePixel(0x400)
        else:
            pass
            self.RenderScanlinePixel(0x800)
            self.RenderScanlinePixel(0xC00)

        if not self.tilebased :#'draw foreground sprites
            pass
            self.RenderSprites(Scanline, False)


    def DrawSprites(self,ontop):
        if self.Control2 & 16 == 0 :return
        SpritePattern = (self.Control1 & 0x8) * 0x200
        h = 16 if self.Control1 & 0x20 else 8
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
                            '''for y1 in range(h-1,0,-1):#= h - 1 To 0 Step -1
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
                                if i >= 256 * 240:break'''
                        else:
                            i += 7
                            Xflag = -X
                            i = self.DrawSpritesPixel(i,h,sa,Xflag,Y,palette)
                            '''for y1 in range(h-1,0,-1):#= h - 1 To 0 Step -1
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
                                if i >= 256 * 240:break'''
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
                                    self.vBuffer[Y][X1 + Xflag] = self.Pal[Color | palette]
                            i += 256
                            if i >= 256 * 240:break
                        return i

                

    def RenderScanlinePixel(self, NameTableAddress):
        sc = self.Scanline + self.vScroll
        
        TileRow = (sc // 8) % 30
        TileYOffset = sc & 7

        NameTable = 0x2000 + (0x400 * (self.Control1 & 0b11)) ^ NameTableAddress
        self.PatternTable = (self.Control1 & 0x10) << 8 #* 0x100
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
            Byte1 = self.VRAM[self.PatternTable + TileIndex * 16 + TileYOffset]
            Byte2 = self.VRAM[self.PatternTable + TileIndex * 16 + 8 + TileYOffset]
            
            c1 = ((Byte1>>1)&0x55)|(Byte2&0xAA)
            c2 = (Byte1&0x55)|((Byte2<<1)&0xAA)
            '''if True:#c1 or c2:
                #print hex(c1),hex(c2)
                self.vBuffer[self.Scanline][0 + TileCounter * 8] = self.Pal[(c1>>6)]
                self.vBuffer[self.Scanline][4 + TileCounter * 8] = self.Pal[(c1>>2)&3]
                self.vBuffer[self.Scanline][1 + TileCounter * 8] = self.Pal[(c2>>6)]
                self.vBuffer[self.Scanline][5 + TileCounter * 8] = self.Pal[(c2>>2)&3]
                self.vBuffer[self.Scanline][2 + TileCounter * 8] = self.Pal[(c1>>4)&3]
                self.vBuffer[self.Scanline][6 + TileCounter * 8] = self.Pal[c1&3]
                self.vBuffer[self.Scanline][3 + TileCounter * 8] = self.Pal[(c2>>4)&3]
                self.vBuffer[self.Scanline][7 + TileCounter * 8] = self.Pal[c2&3]'''
            
            
            X = TileCounter * 8 - self.HScroll + 7
            m = X if X < 7 else 7
            X = X + self.Scanline * 256
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
                if Color :
                    pass
                    #self.vBuffer[Scanline][8 - pixel + TileCounter * 8] = self.Pal[Color | addToCol]
                    self.vBuffer[self.Scanline][8 - pixel + TileCounter * 8] = self.Pal[self.BGPAL[Color | addToCol]]



                    
    def RenderSprites(self,Scanline,topLayer):
        
        if self.Control2 & 0b00010000 == 0 :return
        
        TileRow = Scanline / 8
        TileYOffset = Scanline & 0b111
        h = 16 if self.Control1 & 0x20 else 8
        self.PatternTable = 0x1000 if self.Control1 & 0x8 and h == 8 else 0

        minX = 0 if self.Control2 & 0x20 else 8

        i = Scanline << 16 #* 0x100

        for spr in range(63,-1,-1):
            SpriteAddr = spr << 2
            y1 = self.SpriteRAM[SpriteAddr] + 1
            
            if Scanline - h < y1 <= Scanline  :
                attr = self.SpriteRAM[SpriteAddr + 2]
                if (attr & 32) == 0 ^ topLayer:
                    X1 = self.SpriteRAM[SpriteAddr + 3]
                    if X1 >= minX:
                        if self.render and (X1 < 248):
                            addToCol = 0x10 + (attr & 3) * 4
                    
                            TileIndex = self.SpriteRAM[SpriteAddr + 1]

                            #Mapper = 9 Or Mapper = 10
                            
                            if h == 16 :
                                if TileIndex & 1 :
                                    self.PatternTable = 0x1000
                                    TileIndex = TileIndex ^ 1
                                else:
                                    self.PatternTable = 0
                            if attr & 128 :# 'vertical flip
                                v = y1 - Scanline - 1
                            else:
                                v = Scanline - y1

                            v = v & h - 1 #****************** maybe debug
                            if v >= 8:v = v + 8
                            Byte1 = self.VRAM[self.PatternTable + (TileIndex * 16) + v]
                            Byte2 = self.VRAM[self.PatternTable + (TileIndex * 16) + 8 + v]
                            #c1 = ((Byte1>>1)&0x55)|(Byte2&0xAA)
                            #c2 = (Byte1&0x55)|((Byte2<<1)&0xAA)
            
                            #real sprite 0 detection
                            if spr == 0 and (self.Status & 64) == 0:
                                if attr & 64 : # 'horizontal flip
                                    '''self.vBuffer[self.Scanline][0 + X1] = self.Pal[(c1>>6)]
                                    self.vBuffer[self.Scanline][4 + X1] = self.Pal[(c1>>2)&3]
                                    self.vBuffer[self.Scanline][1 + X1] = self.Pal[(c2>>6)]
                                    self.vBuffer[self.Scanline][5 + X1] = self.Pal[(c2>>2)&3]
                                    self.vBuffer[self.Scanline][2 + X1] = self.Pal[(c1>>4)&3]
                                    self.vBuffer[self.Scanline][6 + X1] = self.Pal[c1&3]
                                    self.vBuffer[self.Scanline][3 + X1] = self.Pal[(c2>>4)&3]
                                    self.vBuffer[self.Scanline][7 + X1] = self.Pal[c2&3]'''
                                    #a = i + X1
                                    for X in range(8):#= 0 To 7 #'draw yellow block for now.
                                        Color = 1 if Byte1 & NES.pow2[X] else 0
                                        if Byte2 & NES.pow2[X] : Color = Color + 2
                                        if Color:
                                            if (self.vBuffer[Scanline][X1 + X] == self.blankPixel).all():
                                                pass
                                            else:
                                                self.Status = self.Status | 64
                                            #if self.vBuffer[Scanline][a + X] <> 16: self.Status = self.Status | 64
                                            self.vBuffer[Scanline][X1 + X] =  self.Pal[self.Palettes[Color | addToCol]]
                                else:
                                    '''self.vBuffer[self.Scanline][0 - X1] = self.Pal[(c1>>6)]
                                    self.vBuffer[self.Scanline][4 - X1] = self.Pal[(c1>>2)&3]
                                    self.vBuffer[self.Scanline][1 - X1] = self.Pal[(c2>>6)]
                                    self.vBuffer[self.Scanline][5 - X1] = self.Pal[(c2>>2)&3]
                                    self.vBuffer[self.Scanline][2 - X1] = self.Pal[(c1>>4)&3]
                                    self.vBuffer[self.Scanline][6 - X1] = self.Pal[c1&3]
                                    self.vBuffer[self.Scanline][3 - X1] = self.Pal[(c2>>4)&3]
                                    self.vBuffer[self.Scanline][7 - X1] = self.Pal[c2&3]'''
                                    a = i + X1 + 7
                                    for X  in range(8):#= 0 To 7 #'draw yellow block for now.
                                        Color = 1 if Byte1 & NES.pow2[X] else 0
                                        if Byte2 & NES.pow2[X] : Color = Color + 2
                                        if Color:
                                            #print self.vBuffer[Scanline][X1 - X]
                                            if not (self.vBuffer[Scanline][X1 - X] == self.blankPixel).all():
                                                self.Status = self.Status | 64
                                            #if self.vBuffer[Scanline][a + X] <> 16: self.Status = self.Status | 64
                                            self.vBuffer[Scanline][X1 - X] =  self.Pal[self.Palettes[Color | addToCol]]
                            else:
                                if attr & 64 : # 'horizontal flip
                                    '''self.vBuffer[self.Scanline][0 + X1] = self.Pal[(c1>>6)]
                                    self.vBuffer[self.Scanline][4 + X1] = self.Pal[(c1>>2)&3]
                                    self.vBuffer[self.Scanline][1 + X1] = self.Pal[(c2>>6)]
                                    self.vBuffer[self.Scanline][5 + X1] = self.Pal[(c2>>2)&3]
                                    self.vBuffer[self.Scanline][2 + X1] = self.Pal[(c1>>4)&3]
                                    self.vBuffer[self.Scanline][6 + X1] = self.Pal[c1&3]
                                    self.vBuffer[self.Scanline][3 + X1] = self.Pal[(c2>>4)&3]
                                    self.vBuffer[self.Scanline][7 + X1] = self.Pal[c2&3]'''
                                    a = i + X1
                                    for X in range(8):#= 0 To 7 #'draw yellow block for now.
                                        Color = 1 if Byte1 & NES.pow2[X] else 0
                                        if Byte2 & NES.pow2[X] : Color = Color + 2
                                        if Color:
                                            self.vBuffer[Scanline][X1 + X] =  self.Pal[self.Palettes[Color | addToCol]]
                                else:
                                    
                                    a = i + X1 + 7
                                    for X  in range(8):#= 0 To 7 #'draw yellow block for now.
                                        Color = 1 if Byte1 & NES.pow2[X] else 0
                                        if Byte2 & NES.pow2[X] : Color = Color + 2
                                        if Color:
                                            self.vBuffer[Scanline][X1 - X] =  self.Pal[self.Palettes[Color | addToCol]]                             
                                    
                        
                        if spr == 0 :
                            if Scanline == y1 + h - 1 :
                                self.Status = self.Status ^ 0x40 #'claim we hit sprite #0




                    

    def blitScreen(self):
        
        cv2.imshow("Main", self.vBuffer)
        cv2.waitKey(1)

    def blitPal(self):
        #print np.array([[self.Pal[self.VRAM[i + 0x3F00]] for i in range(31)]],np.uint8)
        #cv2.imshow("Pal", np.array([[self.Pal[self.VRAM[i + 0x3F00]] for i in range(0x20)]]))
        cv2.imshow("Pal", np.array([[self.Pal[i] for i in (self.BGPAL + self.SPRPAL)]]))
        cv2.waitKey(1)

#@jit
def RenderPixelJit( Scanline, vScroll, HScroll, PPU_Control1, NameTableAddress,VRAM,tLook, Pal):
        sc = Scanline + vScroll
        
        TileRow = (sc // 8) % 30
        TileYOffset = sc & 7

        NameTable = 0x2000 + (0x400 * (PPU_Control1 & 0b11)) ^ NameTableAddress
        PatternTable = (PPU_Control1 & 0x10) * 0x100
        AttributeTable = NameTable + 0x3C0

        vBuffer = [[0,0,16]] * 263
        for TileCounter in range(HScroll // 8 , 31):
            TileIndex = VRAM[NameTable + TileCounter + TileRow * 32]
            '''If Mapper = 9 Or Mapper = 10 Then
                If PatternTable = &H0 Then
                    MMC2_latch TileIndex, False
                ElseIf PatternTable = &H1000& Then
                    MMC2_latch TileIndex, True
                End If
            End If'''
            Byte1 = VRAM[PatternTable + TileIndex * 16 + TileYOffset]
            Byte2 = VRAM[PatternTable + TileIndex * 16 + 8 + TileYOffset]
            X = TileCounter * 8 - HScroll + 7
            m = X if X < 7 else 7
            X = X + Scanline * 256
            LookUp = VRAM[AttributeTable + TileCounter // 4 + (TileRow // 4) * 0x8]
            Tiletemp = (TileCounter & 2) | (TileRow & 2) * 2
            if Tiletemp == 0:
                    addToCol = LookUp * 4 & 12
            elif Tiletemp == 2:
                    addToCol = LookUp & 12
            elif Tiletemp == 4:
                    addToCol = LookUp // 4 & 12
            elif Tiletemp == 6:
                    addToCol = LookUp // 16 & 12
            
            a = (Byte1 * 2048) + (Byte2 * 8)
                
            #for pixel in range(m,0,-1): # = m To 0 Step -1
            for pixel in range(m + 1): # = m To 0 Step -1

                Color = tLook[a + pixel]

                if Color :
                    vBuffer[8 - pixel + TileCounter * 8] = Pal[Color | addToCol]
        return np.array(vBuffer,dtype=np.uint8)

                    
if __name__ == '__main__':
    ppu = PPU()
    ppu.pPPUinit()
    #print ppu.blankLine
    print len(ppu.vBuffer)
    print len(ppu.vBuffer[0])
    #print ppu.vBuffer[2:4]
    #print ppu.vBuffer[3]
    #print ppu.vBuffer[2][1]
    #cv2.imshow("Main", np.array(ppu.vBuffer,dtype=np.uint8))
    print ppu.Read(0x2000)











        
