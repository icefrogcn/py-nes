# -*- coding: UTF-8 -*-
import time


import numpy as np
import numba as nb

from numba import jitclass
from numba import uint8,uint16,uint32
from numba.typed import Dict
from numba import types

from memory import Memory,memory_type
from ppu_memory import PPU_Memory,PPU_memory_type
from rom import ROM,ROM_class_type

#PPU REGISTER


@jitclass([('ver',uint8)])
class PPUBIT(object): 
    def __init__(self):
        self.ver = 0
    # PPU Control Register #1	PPU #0 $2000


    @property
    def PPU_VBLANK_BIT(self):
        return 0x80
    @property
    def PPU_SPHIT_BIT(self):
        return 0x40		
    @property
    def PPU_SP16_BIT(self):
        return 0x20
    @property
    def PPU_BGTBL_BIT(self):
        return 0x10
    @property
    def PPU_SPTBL_BIT(self):
        return 0x08
    @property
    def PPU_INC32_BIT(self):
        return 0x04
    @property
    def PPU_NAMETBL_BIT(self):
        return 0x03

    # PPU Control Register #2	PPU #1 $2001
    @property
    def PPU_BGCOLOR_BIT(self):
        return 0xE0
    @property
    def PPU_SPDISP_BIT(self):
        return 0x10
    @property
    def PPU_BGDISP_BIT(self):
        return 0x08
    @property
    def PPU_SPCLIP_BIT(self):
        return 0x04
    @property
    def PPU_BGCLIP_BIT(self):
        return 0x02
    @property
    def PPU_COLORMODE_BIT(self):
        return 0x01

    # PPU Status Register	PPU #2 $2002
    @property
    def PPU_VBLANK_FLAG(self):
        return 0x80
    @property
    def PPU_SPHIT_FLAG(self):
        return 0x40
    @property
    def PPU_SPMAX_FLAG(self):
        return 0x20
    @property
    def PPU_WENABLE_FLAG(self):
        return 0x10

    # SPRITE Attribute
    @property
    def SP_VMIRROR_BIT(self):
        return 0x80
    @property
    def SP_HMIRROR_BIT(self):
        return 0x40
    @property
    def SP_PRIORITY_BIT(self):
        return 0x20
    @property
    def SP_COLOR_BIT(self):
        return 0x03

PPU_bit_type = nb.deferred_type()
PPU_bit_type.define(PPUBIT.class_type.instance_type)

#data_type = nb.deferred_type()

#data_type.define(nb.typeof(nb.typed.Dict.empty(key_type=nb.int64, value_type=uint8)))

@jitclass([('bit',PPU_bit_type), \
           ('memory',PPU_memory_type), \
           ('reg',uint16[:]), \
           ('ROM',ROM_class_type), \
           ('VRAM',uint8[:]), \
           ('SpriteRAM',uint8[:]), \
           ('Palettes',uint8[:]), \
           ('PRGRAM',uint8[:,:]) 
           ])
class PPUREG(object):
    def __init__(self, memory = PPU_Memory(), ROM = ROM()):
        self.bit = PPUBIT()
        self.memory = memory
        self.reg = np.zeros(0x20, np.uint16) 
        self.VRAM = self.memory.VRAM 
        self.SpriteRAM = self.memory.SpriteRAM
        self.Palettes = self.memory.Palettes
        
        self.ROM = ROM
        self.PRGRAM = self.memory.PRGRAM
        self.reg[9] = 1

    def read(self,address):
        if address == 0x2002:
            return self.PPUSTATUS
        elif address == 0x2004:
            return self.OAMDATA
        elif address == 0x2007:
            return self.PPUDATA
        
    def write(self,address,value):
        self.reg[8] = value
        addr = address & 0xFF
        if addr == 0:
            self.PPUCTRL_W(value)
        elif addr == 0x01:
            self.PPUMASK_W(value)
        elif addr == 0x02:
            self.PPU7_Temp_W(value)
        elif addr == 0x03:
            self.OAMADDR_W(value)
        elif addr == 0x04:
            self.OAMDATA_W(value)
        elif addr == 0x05:
            self.PPUSCROLL_W(value)
        elif addr == 0x06:
            self.PPUADDR_W(value)
        elif addr == 0x07:
            self.PPUDATA_W(value)
        elif addr == 0x14:
            self.OAMDMA_W(value)
        
    @property
    def Mirroring(self):
        return self.ROM.Mirroring
    @property
    def MirrorXor(self):
        return self.ROM.MirrorXor

        
    @property       #2000
    def PPUCTRL(self):
        return self.reg[0]
    def PPUCTRL_W(self,value): 
        self.reg[0] = value

    @property
    def PPU_BGTBL_BIT(self):
        return self.PPUCTRL & self.bit.PPU_BGTBL_BIT
        
    @property
    def PPU_SPTBL_BIT(self):
        return self.PPUCTRL & self.bit.PPU_SPTBL_BIT
        
    @property
    def PPU_NAMETBL_BIT(self):
        return self.PPUCTRL & self.bit.PPU_NAMETBL_BIT
        
    @property       #2001
    def PPUMASK(self):
        return self.reg[1]
    def PPUMASK_W(self,value):
        self.reg[1] = value
        
    @property
    def PPUSTATUS(self):        #2002
        ret = (self.PPU7_Temp & 0x1F) | self.reg[2]
        if ret & 0x80:
            self.reg[2] &= 0x60 #PPU_SPHIT_FLAG + PPU_SPMAX_FLAG
        return ret
        
    def PPUSTATUS_W(self,value):
        self.reg[2] = value
        
        
    @property
    def OAMADDR(self):          #2003
        return self.reg[3]
    def OAMADDR_W(self,value):
        self.reg[3] = value
        
    @property
    def OAMDATA(self):          #2004
        self.reg[3] += 1
        return self.SpriteRAM[self.reg[3]]
    def OAMDATA_W(self,value):
        self.SpriteRAM[self.OAMADDR] = value
        self.reg[3] = (self.reg[3] + 1) & 0xFF
        
    @property
    def ScrollToggle(self): #AddressIsHi #$2005-$2006 Toggle PPU56Toggle
        return self.reg[9]
    def ScrollToggle_W(self): 
        self.reg[9] = 0 if self.reg[9] else 1
    @property
    def HScroll(self): #HScroll
        return self.reg[10]
    @property
    def vScroll(self): #vScroll
        return self.reg[11]
    @property
    def AddressHi(self): #AddressHi
        return self.reg[12]

    def PPUSCROLL_W(self,value):#2005
        if self.reg[9]:
            self.reg[10] = value
        else:
            self.reg[11] = value
        self.ScrollToggle_W()
        #self.reg[5] = value
        
    @property
    def PPUADDR(self):          #2006
        return self.reg[6]
    def PPUADDR_W(self,value):
        if self.reg[9]:
            self.reg[12] = value * 0x100
        else:
            self.reg[6] = self.reg[12] + value
        self.ScrollToggle_W()
        #self.reg[6] = value
        
    @property
    def PPUDATA(self):          #2007
        data = self.reg[8]
        addr = self.reg[6] & 0x3FFF
        self.reg[6] += 32 if self.reg[0] & 0x04 else 1
        if(addr >= 0x3000):
            if addr >= 0x3F00:
                data &= 0x3F
                return self.Palettes[addr & 0x1F]
            addr &= 0xEFFF
        else:
            self.reg[8] = self.VRAM[addr & 0x3FFF]
        self.reg[8] = 0xFF #self.VRAM[addr>>10][addr&0x03FF]
        
        return data
    
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
                self.VRAM[self.reg[6] ^ self.ROM.MirrorXor] = value
            self.VRAM[self.reg[6]] = value
        
        self.reg[6] += 32 if self.reg[0] & 0x04 else 1
                                        #PPU_INC32_BIT

        
    @property
    def PPU7_Temp(self):            #reg[8]
        return self.reg[8]
    def PPU7_Temp_W(self,value):
        self.reg[8] = value

    
    #@property
    def OAMDMA_W(self,value):
        addr = value << 8
        for i in range(0x100):
            temp = self.PRGRAM[0,addr + i]
            self.SpriteRAM[i] = temp#self.PRGRAM[0,value * 0x100:value * 0x100 + 0x100]

PPU_reg_type = nb.deferred_type()
PPU_reg_type.define(PPUREG.class_type.instance_type)

        
@jitclass([('bit',PPU_reg_type),
           ('ROM',ROM_class_type),
           ('memory',PPU_memory_type)

           ])        
class PPU_T(object):
    def __init__(self, memory = Memory(), ROM = ROM(), reg = PPUREG(PPU_Memory(), ROM())):
        self.memory = PPU_Memory(memory)
        self.bit = PPUREG(self.memory, ROM)

        
        def jittest(self):
            temp = 0
            for i in range(10000000):
                temp += i
            return temp

@jitclass([('temp',uint8[:])])
class jit_class_test(object):
    def __init__(self):
        self.temp = np.ones(10000000,np.uint8)
        #self.temp += 1
    
    @property
    def test(self):
        temp = 0
        for i in self.temp:
            temp += i
        return temp


class class_test(object):
    def __init__(self):
        self.temp = np.ones(10000000, np.uint8)
        #self.temp += 1
        
    @property
    def test(self):
        temp = 0
        for i in self.temp:
            temp += i
        return temp
         
if __name__ == '__main__':
    #print PPUBIT()
    #print PPUREG()
    t1 = jit_class_test()
    t2 = class_test()
    start = time.time()
    print t1.test
    print time.time() - start
    start = time.time()
    print t2.test
    print time.time() - start
   #reg.PPUCTRL_W(1)
    #print reg.PPUCTRL,reg.Palettes
    

    
    
    
    








        
