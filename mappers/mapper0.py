# -*- coding: UTF-8 -*-

from numba import jit,jitclass
from mapper import MAPPER_class_type

@jitclass([('cartridge',MAPPER_class_type)])
class MAPPER(object):

    def __init__(self,cartridge):
         self.cartridge = cartridge

    def Mapper(self):
        return self.cartridge.ROM.Mapper
    def reset(self):
        self.cartridge.SetVROM_8K_Bank(0)

        if self.cartridge.ROM.PROM_16K_SIZE == 1: # 16K only
            self.cartridge.SetPROM_16K_Bank( 4, 0 )
            self.cartridge.SetPROM_16K_Bank( 6, 0 )
            
        elif self.cartridge.ROM.PROM_16K_SIZE == 2:	#// 32K
            self.cartridge.SetPROM_32K_Bank( 0,1,2,3 )
        #print "RESET SUCCESS MAPPER ", self.Mapper







if __name__ == '__main__':
    mapper = MAPPER()











        
