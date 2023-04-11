# -*- coding: UTF-8 -*-
import sys
sys.path.append("..")



#MAPPER
from mapper import MAPPER
from nes import NES


class MAPPER(MAPPER,NES):

    #def __init__(self,debug = False):
    #     print 'init MAPPER 0',PRGRAM.shape

    def reset(self):
        print "RESET MAPPER ", NES.Mapper
        self.SetVROM_8K_Bank(0)
        if self.PROM_16K_SIZE == 1: # 16K only
            self.SetPROM_16K_Bank( 4, 0 )
            self.SetPROM_16K_Bank( 6, 0 )
            
        elif self.PROM_16K_SIZE == 2:	#// 32K
            self.SetPROM_32K_Bank( 0,1,2,3 )
            
        #return super(MAPPER,self).reset()






if __name__ == '__main__':
    mapper = MAPPER()











        
