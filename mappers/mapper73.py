# -*- coding: UTF-8 -*-
import sys
sys.path.append("..")



#MAPPER
from mapper import MAPPER

from nes import NES


class MAPPER(MAPPER,NES):


    def reset(self):
        self.SetPROM_32K_Bank(0, 1, NES.PROM_8K_SIZE-2, NES.PROM_8K_SIZE-1)

	patch = 0
            
        return 1

    
    def Write(self,addr,data):#$8000-$FFFF Memory write
        if addr == 0xF000:
            self.SetPROM_16K_Bank(4, data )


if __name__ == '__main__':
    mapper = MAPPER()











        
