# -*- coding: UTF-8 -*-
from numba import jit,jitclass
from mapper import MAPPER_class_type

@jitclass([('cartridge',MAPPER_class_type)])
class MAPPER(object):

    def __init__(self,cartridge):
        self.cartridge = cartridge

    @property
    def Mapper(self):
        return self.cartridge.ROM.Mapper
    def reset(self):
        self.cartridge.SetPROM_32K_Bank(0, 1, self.cartridge.ROM.PROM_8K_SIZE - 2, self.cartridge.ROM.PROM_8K_SIZE - 1)

	patch = 0
            
        return 1

    
    def Write(self,addr,data):#$8000-$FFFF Memory write
        #print "MAPPER W 2"
        self.cartridge.SetPROM_16K_Bank(4, data )


if __name__ == '__main__':
    mapper = MAPPER()











        
