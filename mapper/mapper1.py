# -*- coding: UTF-8 -*-
import sys
sys.path.append("..")



#MAPPER
from mapper import MAPPER
from mmc import MMC
from nes import NES


class MAPPER(MAPPER,MMC,NES):

    last_addr = 0
    patch = 0
    wram_patch = 0
    wram_bank = 0
    wram_count = 0

    reg = [0] * 4

    shift = 0
    regbuf = 0

    
    def __init__(self,debug = False):
         pass

    def reset(self):
        reg[0] = 0x0C
        #reg[1] = reg[2] = reg[3] = 0
        #shift = regbuf = 0

        if( NES.PROM_16K_SIZE < 32 ):
            
            self.SetPROM_32K_Bank(0, 1, NES.PROM_8K_SIZE-2, NES.PROM_8K_SIZE-1)
        else:
            self.SetPROM_16K_Bank( 4, 0 )
            self.SetPROM_16K_Bank( 6, 16-1 )

            patch = 1
            
        return 1

    
    def Write(self,addr,data):#$8000-$FFFF Memory write
        self.SetPROM_16K_Bank(4, data )


if __name__ == '__main__':
    mapper = MAPPER()











        
