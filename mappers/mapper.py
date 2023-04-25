# -*- coding: UTF-8 -*-

import sys
sys.path.append("..")

from numba import jit,jitclass
from numba import int8,uint8,int16,uint16
import numpy as np
import numba as nb

from nes import NES

__all__ = ['MAPPER']
#MAPPER

@jitclass([('ROM_info',uint16[:]), \
           ('PROM_SIZE_array',uint8[:]), \
           ('VROM_SIZE_array',uint8[:]), \
           ('PRGRAM',uint8[:,:]), \
           ('VRAM',uint8[:]), \
           ('PROM',uint8[:]), \
           ('VROM',uint8[:]) \
           ])
class MAPPER(object):
    
    def __init__(self,ROM,CPU_PRGRAM,PPU_VRAM):

        self.ROM_info = ROM.info

        self.PROM_SIZE_array = ROM.PROM_SIZE_array
        self.VROM_SIZE_array = ROM.VROM_SIZE_array
      
        self.PRGRAM = CPU_PRGRAM
        self.VRAM = PPU_VRAM
        self.PROM = ROM.PROM
        self.VROM = ROM.VROM

    @property
    def Mapper(self):
        return self.ROM_info[0]
    @property
    def Trainer(self):
        return self.ROM_info[1]
    @property
    def Mirroring(self):
        return self.ROM_info[2]
    @property
    def FourScreen(self):
        return self.ROM_info[3]
    @property
    def UsesSRAM(self):
        return self.ROM_info[4]
    @property
    def MirrorXor(self):
        return self.ROM_info[5]
    @property
    def PROM_8K_SIZE(self):
        return self.PROM_SIZE_array[8]
    @property
    def PROM_16K_SIZE(self):
        return self.PROM_SIZE_array[16]
    @property
    def PROM_32K_SIZE(self):
        return self.PROM_SIZE_array[32]
    @property
    def VROM_1K_SIZE(self):
        return self.VROM_SIZE_array[1]
    @property
    def VROM_2K_SIZE(self):
        return self.VROM_SIZE_array[2]
    @property
    def VROM_4K_SIZE(self):
        return self.VROM_SIZE_array[4]
    @property
    def VROM_8K_SIZE(self):
        return self.VROM_SIZE_array[8]

    
    def MirrorXor_W(self,value):
        self.ROM_info[5] = value    
    def Mirroring_W(self,value):
        self.ROM_info[2] = value
        
    def reset(self):
        return self.PRGRAM

    def Write(self,address,data):#$8000-$FFFF Memory write
        print 'init Write'

    def Read(self,address):#$8000-$FFFF Memory read(Dummy)
        return self.PRGRAM[addr>>13,address & 0x1FFF]

    def ReadLow(self,address):#$4100-$7FFF Lower Memory read
        if( address >= 0x6000 ):
            return self.PRGRAM[3, address & 0x1FFF]
        return address>>8

    def WriteLow(self,address,data): #$4100-$7FFF Lower Memory write
        #$6000-$7FFF WRAM
        if( address >= 0x6000 ) :
            self.PRGRAM[3, address & 0x1FFF] = data
    
    def ExRead(self,address): #$4018-$40FF Extention register read/write
        return 0
    
    def ExWrite(self, address, data ):
        pass
    def Clock(self, cycle ):
        pass
    

    def SetPROM_8K_Bank(self, page, bank):

        bank %= self.PROM_8K_SIZE
        self.PRGRAM[page] = self.PROM[0x2000 * bank : 0x2000 * bank + 0x2000]

        
            
    def SetPROM_16K_Bank(self,page, bank):
        self.SetPROM_8K_Bank( page+0, bank*2+0 )
        self.SetPROM_8K_Bank( page+1, bank*2+1 )
        
    def SetPROM_32K_Bank0(self,bank):
        self.SetPROM_8K_Bank( 4, bank*4 + 0 )
        self.SetPROM_8K_Bank( 5, bank*4 + 1 )
        self.SetPROM_8K_Bank( 6, bank*4 + 2 )
        self.SetPROM_8K_Bank( 7, bank*4 + 3 )

    def SetPROM_32K_Bank(self,bank0,bank1,bank2,bank3):
        self.SetPROM_8K_Bank( 4, bank0 )
        self.SetPROM_8K_Bank( 5, bank1 )
        self.SetPROM_8K_Bank( 6, bank2 )
        self.SetPROM_8K_Bank( 7, bank3 )
	


    def SetCRAM_1K_Bank(self, page, bank):
        print "Set CRAM"
        bank &= 0x1F
        CRAM = 32768 + 0x0400 * bank
        self.VRAM[page*0x400:page*0x400 + 0x400] = self.VRAM[CRAM:CRAM + 0x400]

    def SetVRAM_1K_Bank(self, page, bank):
        #print "Set VRAM"
        bank &= 0x3
        VRAM = 0x0400 * bank + 4096
        self.VRAM[page*0x400:page*0x400 + 0x400] = self.VRAM[VRAM:VRAM + 0x400]

    def SetVROM_8K_Bank(self,bank):
        for i in range(8):
            self.SetVROM_1K_Bank( i, bank * 8 + i )

    def SetVROM_1K_Bank(self, page, bank):
        #print 'DEBUG: NES.VROM_1K_SIZE',NES.VROM_1K_SIZE,hex(len(self.VROM)),hex(len(self.VRAM))
        bank %= self.VROM_1K_SIZE
        self.VRAM[page*0x400:page*0x400 + 0x400] = self.VROM[0x0400*bank:0x0400*bank + 0x400]
        #print NES.VRAM[0:100]


if __name__ == '__main__':
    pass










        
