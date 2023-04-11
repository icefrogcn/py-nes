# -*- coding: UTF-8 -*-
import sys
sys.path.append("..")



#MAPPER
from mapper import MAPPER

from nes import NES


class MAPPER(MAPPER,NES):
    patch = 0
    exsound_enable = 0
    
    reg = [0] * 3
    exram = [0] * 128
    irq_enable = 0
    irq_counter = 0

    
    def __init__(self,debug = False):
         pass

    def reset(self):
        
        self.SetPROM_32K_Bank(0, 1, NES.PROM_8K_SIZE-2, NES.PROM_8K_SIZE-1 )

	if( NES.VROM_1K_SIZE >= 8 ):
	    self.SetVROM_8K_Bank( NES.VROM_8K_SIZE - 1 );
	self.exsound_enable = 0xFF
        return 1


    def Write(self,address,data):#$8000-$FFFF Memory write
        addr = address & 0xF800
        #print 'irq_occur: ',self.irq_occur
        if addr == 0x8000:
            if ( (data < 0xE0) or (self.reg[0] != 0) ):
                self.SetVROM_1K_Bank( 0, data )
            else:
                self.SetCRAM_1K_Bank( 0, data&0x1F )
        elif addr == 0x8800:
            if ( (data < 0xE0) or (self.reg[0] != 0) ):
                self.SetVROM_1K_Bank( 1, data )
            else:
                self.SetCRAM_1K_Bank( 1, data&0x1F )
        elif addr == 0x9000:
            if ( (data < 0xE0) or (self.reg[0] != 0) ):
                self.SetVROM_1K_Bank( 2, data )
            else:
                self.SetCRAM_1K_Bank( 2, data&0x1F )
        elif addr == 0x9800:
            if ( (data < 0xE0) or (self.reg[0] != 0) ):
                self.SetVROM_1K_Bank( 3, data )
            else:
                self.SetCRAM_1K_Bank( 3, data&0x1F )
                
        elif addr == 0xA000:
            if ( (data < 0xE0) or (self.reg[1] != 0) ):
                self.SetVROM_1K_Bank( 4, data )
            else:
                self.SetCRAM_1K_Bank( 4, data&0x1F )
        elif addr == 0xA800:
            if ( (data < 0xE0) or (self.reg[1] != 0) ):
                self.SetVROM_1K_Bank( 5, data )
            else:
                self.SetCRAM_1K_Bank( 5, 5 )
        elif addr == 0xB000:
            if ( (data < 0xE0) or (self.reg[1] != 0) ):
                self.SetVROM_1K_Bank( 6, data )
            else:
                self.SetCRAM_1K_Bank( 6, data&0x1F )
        elif addr == 0xB800:
            if ( (data < 0xE0) or (self.reg[1] != 0) ):
                self.SetVROM_1K_Bank( 7, data )
            else:
                self.SetCRAM_1K_Bank( 7, data&0x1F )

        elif addr == 0xC000:
            if not self.patch:
                if ( (data <= 0xDF)):
                    self.SetVROM_1K_Bank( 8, data )
                else:
                    self.SetVRAM_1K_Bank( 8, data&0x01 )

        elif addr == 0xC800:
            if not self.patch:
                if ( (data <= 0xDF)):
                    self.SetVROM_1K_Bank( 9, data )
                else:
                    self.SetVRAM_1K_Bank( 9, data&0x01 )

        elif addr == 0xD000:
            if not self.patch:
                if ( (data <= 0xDF)):
                    self.SetVROM_1K_Bank( 10, data )
                else:
                    self.SetVRAM_1K_Bank( 10, data&0x01 )

        elif addr == 0xD800:
            if not self.patch:
                if ( (data <= 0xDF)):
                    self.SetVROM_1K_Bank( 11, data )
                else:
                    self.SetVRAM_1K_Bank( 11, data&0x01 )

        elif addr == 0xE000:
            self.SetPROM_8K_Bank( 4, data & 0x3F )
            #patch
        elif addr == 0xE800:
            self.reg[0] = data & 0x40
            self.reg[1] = data & 0x80
            self.SetPROM_8K_Bank( 5, data & 0x3F )
                
        elif addr == 0xF000:
            self.SetPROM_8K_Bank( 6, data & 0x3F )

        elif addr == 0xF800:
            if self.exsound_enable:
                print "apu_ExWrite"
                return 1
            self.reg[2] = data
            
                    

    def Clock(self,cycles):
        if( self.irq_enable):
            self.irq_counter += cycles
            if(self.irq_counter >= 0x7FFF ):
                self.irq_counter = 0x7FFF
                return True

if __name__ == '__main__':
    mapper = MAPPER()











        
