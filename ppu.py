# -*- coding: UTF-8 -*-

import time
import math

#PPU

class PPU:



    
    def __init__(self,debug = False):
        #6502中没有寄存器，故使用工作内存地址作为寄存器
        pass

    def pPPUinit(self):
        self.Control1 = 0 # $2000
        self.Control2 = 0 # $2001
        self.Status = 0 # $2002
        self.SpriteAddress = 0 #As Long ' $2003
        self.AddressHi = 0 # $2006, 1st write
        self.Address = 0 # $2006
        self.AddressIsHi = True
        self.ScrollToggle = 0
        self.HScroll = 0
        self.vScroll = 0
        self.MirrorXor = 0

        self.render = True

        self.tilebased = True
        
        self.EmphVal = 0   #???????Color
        
        self.VRAM = [0] * 0x4000 #3FFF #As Byte, VROM() As Byte  ' Video RAM
        self.SpriteRAM = [0] * 0x100 #FF# As Byte      '活动块存储器，单独的一块，不占内存

        self.PPU_Write_dic = {
            0x2000:self.PPU_Control1_W,
            #0x2001:self.PPU_Control2_W,
            #0x2003:self.SPR_RAM_Address_W,
            #0x2004:self.SPR_RAM_W,
            #0x2005:self.PPU_Scroll_W,
            #0x2006:self.PPU_Control1_W,
                }

        self.PPU_Read_dic = {
            0x2002:self.PPU_Control1_R,
            0x2004:self.SPR_RAM_R,
            0x2007:self.VRAM_R,
                }
            
    def PPU_Control1_R(self):
        ret = self.Status
        self.AddressIsHi = True
        self.ScrollToggle = 0
        self.Status = self.Status & 0x3F
        return ret #PPU_Status = 0

    def SPR_RAM_R(self):
        print "Read SpiritRAM "
        ret = SpriteRAM(SpriteAddress)
        SpriteAddress = (SpriteAddress + 1) #& 0xFF
        return ret

    def VRAM_R(self):
        #print "Read PPU MMC",hex(self.Address)
        if self.Mapper == 9 or self.Mapper == 10:
            print "Mapper 9 - 10"

        mmc_info = self.VRAM[self.Address & 0x3F1F - 1] if (self.Address >= 0x3F20 and self.Address <= 0x3FFF) else self.VRAM[self.Address - 1]

        self.Address +=  32 if (self.Control1 & 0x4) else 1
                
        return mmc_info
        
    def Read(self,addr):
        try:
            return self.PPU_Read_dic.get(addr)()
        except:
            print "Invalid PPU Read - %s : %s" %hex(addr)
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
            #print "Write PPU_AddressIsHi"
            if self.AddressIsHi :
                self.HScroll = value
                self.AddressIsHi = False
            else:
                self.vScroll = value
                self.AddressIsHi = True
        elif addr == 0x2006:
            if self.AddressIsHi :
                self.AddressHi = value * 0x100
                self.AddressIsHi = False
            else:
                self.Address = self.AddressHi + value
                self.AddressIsHi = True
        elif addr == 0x2007:
            #print "Write PPU_AddressIsHi"
            #'Debug.Print "PPUAddress:$" & Hex$(PPUAddress), "Value:$" & Hex$(value)
            self.Address = self.Address & 0x3FFF
            '''if Mapper == 9 or Mapper == 10 :
                if PPUAddress <= 0x1FFF :
                    if PPUAddress > 0xFFF :
                        pass
                        #MMC2_latch VRAM(PPUAddress), True
                    else:
                        pass
                        #MMC2_latch VRAM(PPUAddress), False'''
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

        if self.tilebased:
            pass
        else:
            pass

        
                    
if __name__ == '__main__':
    ppu = PPU()
    print ppu.PPU_Write()











        
