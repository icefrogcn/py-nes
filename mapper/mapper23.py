# -*- coding: UTF-8 -*-
import sys
sys.path.append("..")



#MAPPER
from mapper import MAPPER

from nes import NES


class MAPPER(MAPPER,NES):
    reg = [0] * 9
    irq_enable = 0
    irq_counter = 0
    irq_latch = 0
    irq_clock = 0
    irq_occur = 0
    
    def __init__(self,debug = False):
         pass

    def reset(self):
        self.addrmask = 0xFFFF

	for i in range(8) :
	    self.reg[i] = i

	self.reg[8] = 0

        self.SetPROM_32K_Bank(0, 1, NES.PROM_8K_SIZE-2, NES.PROM_8K_SIZE-1 )
	self.SetVROM_8K_Bank(0)
	
        return 1


    def Write(self,address,data):#$8000-$FFFF Memory write
        addr = address & self.addrmask
        
        if addr in (0x8000,0x8004,0x8008,0x800C):
            if self.reg[8]:
                self.SetPROM_8K_Bank( 6, data )
            else:
                self.SetPROM_8K_Bank( 4, data )
        elif addr ==0x9000:
            if data != 0xFF:
                data &= 0x03
                if data == 0:NES.Mirroring = 0
                elif data == 1:NES.Mirroring = 1
                elif data == 2:NES.Mirroring = 2 #VRAM_MIRROR4L
                else:NES.Mirroring = 3 #VRAM_MIRROR4H
                NES.MirrorXor = 0x400 if data else 0x800
        elif addr == 0x9008:
            self.reg[8] = data & 0x02

        elif addr in (0xA000,0xA004,0xA008,0xA00C):
            self.SetPROM_8K_Bank( 5, data )

        elif 0xB000 <= addr < 0xF000: 
            if (addr & 0xF) == 0x000:
                index = ((addr >> 12) - 11) * 2
                register = self.reg[index]
                register = (register & 0xF0) | (data & 0x0F)
                self.SetVROM_1K_Bank( index, register )
                
            elif (addr & 0xF) in (0x001,0x004):
                index = ((addr >> 12) - 11) * 2
                register = self.reg[index]
                register = (register & 0x0F) | ((data & 0x0F) << 4)
                self.SetVROM_1K_Bank( index, register)
                            
            elif (addr & 0xF) in (0x002,0x008):
                index = ((addr >> 12) - 11) * 2 + 1
                register = self.reg[index]
                register = (register & 0xF0) | (data & 0x0F)
                self.SetVROM_1K_Bank( index, register )

                            
            elif (addr & 0xF) in (0x003,0x00C):
                index = ((addr >> 12) - 11) * 2 + 1
                register = self.reg[index]
                register = (register & 0x0F) | ((data & 0x0F) << 4);
                self.SetVROM_1K_Bank( index, register )

        elif addr == 0xF008:
            irq_enable = data & 0x03
            if( irq_enable & 0x02 ):
                irq_counter = irq_latch
                irq_clock = 0
            irq_occur = 0

            
			
        elif addr == 0xF00C:
            irq_enable = (irq_enable & 0x01) * 3
            irq_occur = 0
                    

    def Clock(self,cycles):
        if( irq_enable & 0x02 ):
            irq_clock += cycles
            if( irq_clock >= 0x72 ):
                    irq_clock -= 0x72
                    if( irq_counter == 0xFF ):
                        irq_occur = 0xFF
                        irq_counter = irq_latch
                        irq_enable = (irq_enable & 0x01) * 3
                    else:
                        irq_counter += 1
            if( irq_occur ):
                return True

if __name__ == '__main__':
    mapper = MAPPER()











        
