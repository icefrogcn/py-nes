# -*- coding: UTF-8 -*-
import sys
sys.path.append("..")



#MAPPER
from mapper import MAPPER

from nes import NES


class MAPPER(MAPPER,NES):

    def reset(self):
        self.SetVROM_8K_Bank(0)
        if self.PROM_16K_SIZE == 1: # 16K only
            self.SetPROM_16K_Bank( 4, 0 )
            self.SetPROM_16K_Bank( 6, 0 )
            
        elif self.PROM_16K_SIZE == 2:	#// 32K
            self.SetPROM_32K_Bank( 0,1,2,3 )

        
        return 1

    def Write(self,addr,data):
        print "Mapper Write",hex(Address),value
        self.SetVROM_8K_Bank( data & (data -1) )






if __name__ == '__main__':
    mapper = MAPPER()











        
