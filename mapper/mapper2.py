# -*- coding: UTF-8 -*-
import sys
sys.path.append("..")



#MAPPER
from mapper import MAPPER
from mmc import MMC
from nes import NES


class MAPPER(MAPPER,MMC,NES):

    def __init__(self,debug = False):
         pass

    def reset(self):
        self.SetPROM_32K_Bank(0, 1, NES.PROM_8K_SIZE-2, NES.PROM_8K_SIZE-1)

	patch = 0
            
        return 1

    
    def Write(self,addr,data):#$8000-$FFFF Memory write
        self.SetPROM_16K_Bank(4, data )


if __name__ == '__main__':
    mapper = MAPPER()











        
