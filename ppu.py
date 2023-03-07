# -*- coding: UTF-8 -*-

import time
import math
import traceback

import cv2
import numpy as np


from nes import NES
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

        self.tilebased = True
        
        self.EmphVal = 0   #???????Color
        
        self.VRAM = [0] * 0x4000 #3FFF #As Byte, VROM() As Byte  ' Video RAM
        self.SpriteRAM = [0] * 0x100 #FF# As Byte      '活动块存储器，单独的一块，不占内存


        self.width,self.height = 263,241

        'DF: array to draw each frame to'
        #self.vBuffer = [16]* (256 * 241 - 1) 
        '256*241 to allow for some overflow     可以允许一些溢出'
        self.vBuffer = np.random.randint(0,1,size = (self.height,self.width,3),dtype=np.uint8)

        self.vBuffer16 = [0]*(256 * 240 - 1) #As Integer
        self.vBuffer32 = [0]*(256 * 240 - 1) #As Long

        #self.tLook = NES.fillTLook()#[0]*(65536 * 8 - 1) #As Byte

        self.PatternTable = 0

        self.Pal = [[item >> 16, item >> 8 & 0xFF ,item & 0xFF] for item in NES.CPal]

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
            #print "Write PPU_AddressIsHi"
            #print "PPUAddress:$" & Hex$(PPUAddress), "Value:$" & Hex$(value)
            self.Address = self.Address & 0x3FFF
            if NES.Mapper == 9 or NES.Mapper == 10 :
                if PPUAddress <= 0x1FFF :
                    if PPUAddress > 0xFFF :
                        pass
                        #MMC2_latch VRAM(PPUAddress), True
                    else:
                        pass
                        #MMC2_latch VRAM(PPUAddress), False
            if self.Address >= 0x3F00 and self.Address <= 0x3FFF:
                self.VRAM[self.Address & 0x3F1F] = value
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
        #self.vBuffer[Scanline] = np.array(Tiles_arr,np.uint8)[0]
        #self.vBuffer[Scanline] = np.random.randint(0,256,size = (1,self.width,3),dtype=np.uint8)[0]
        #return

        if self.tilebased:
            h = 16 if self.Control1 & 0x20 else 8
            if self.Status & 0x40 == 0:
                if Scanline > self.SpriteRAM[0] + h :
                    self.Status = self.Status | 64
            if Scanline == 1:
                self.vBuffer[Scanline] = np.random.randint(15,16,size = (1,self.width,3),dtype=np.uint8)[0]
                #DrawSprites True
            if  Scanline == 239:
                pass
                #DrawSprites False
        else:
            sc = Scanline * 0x100
            #self.vBuffer[sc:sc + 255] = ([16] * 256)
            self.vBuffer[Scanline] = np.random.randint(15,16,size = (1,self.width,3),dtype=np.uint8)[0]
            #'draw background sprites
            self.RenderSprites(Scanline, True)

        sc = Scanline + self.vScroll
        
        #draw background
        TileRow = (sc // 8) % 30
        TileYOffset = sc & 7
        
        if Scanline < 240 - self.vScroll :
            self.NameTable = 0x2000 + (0x400 * (self.Control1 & 0b11))
        else:
            self.NameTable = 0x2000 + (0x400 * (self.Control1 & 0b11)) ^ 0x800

        atrtab = self.NameTable + 0x3C0
        PatternTable = (self.Control1 & 0x10) * 0x100

        for TileCounter in range(self.HScroll // 8 , 31):
            TileIndex = self.VRAM[self.NameTable + TileCounter + TileRow * 32]
            '''If Mapper = 9 Or Mapper = 10 Then
                If PatternTable = &H0 Then
                    MMC2_latch TileIndex, False
                ElseIf PatternTable = &H1000& Then
                    MMC2_latch TileIndex, True
                End If
            End If'''
            Byte1 = self.VRAM[PatternTable + TileIndex * 16 + TileYOffset]
            Byte2 = self.VRAM[PatternTable + TileIndex * 16 + 8 + TileYOffset]
            X = TileCounter * 8 - self.HScroll + 7
            m = X if X < 7 else 7
            X = X + Scanline * 256
            LookUp = self.VRAM[atrtab + TileCounter // 4 + (TileRow // 4) * 0x8]
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
            for pixel in range(m+1): # = m To 0 Step -1
                #print m,addToCol
                try:
                    Color = NES.tLook[a + pixel]
                except:
                    print a,m,pixel,a + pixel
                if Color :
                    #print pixel
                    #print Color | addToCol
                    #print self.Pal[Color | addToCol]
                    #print self.vBuffer[Scanline]
                    #self.vBuffer[X - pixel] = Color | addToCol
                    self.vBuffer[Scanline][8 - pixel + TileCounter * 8] = np.array(self.Pal[Color | addToCol],np.uint8)
                    

        if not self.tilebased :#'draw foreground sprites
            self.RenderSprites(Scanline, False)

    def RenderSprites(self,Scanline,topLayer):
        if self.Control2 & 16 == 0 :return
        TileRow = Scanline // 8
        TileYOffset = Scanline & 7
        h = 16 if self.Control1 & 0x20 else 8
        self.PatternTable = 0x1000 if self.Control1 & 0x8 and h == 8 else 0

        minX = 0 if self.Control2 & 0x20 else 8

        i = Scanline * 0x100
        

    def blitScreen(self):
        cv2.imshow("Main", self.vBuffer)
        cv2.waitKey(1)

    def blitPal(self):
        #print np.array([[self.Pal[self.VRAM[i + 0x3F00]] for i in range(31)]],np.uint8)
        cv2.imshow("Pal", np.array([[self.Pal[self.VRAM[i + 0x3F00]] for i in range(0x20)]],np.uint8))
        cv2.waitKey(1)
                            
if __name__ == '__main__':
    ppu = PPU()
    print ppu.Read(0x2000)











        
