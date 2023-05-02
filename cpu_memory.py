# -*- coding: UTF-8 -*-
import numpy as np
from numba import jitclass
from numba import uint8,uint16



@jitclass([('VRAM',uint8[:]), \
           ('SpriteRAM',uint8[:]), \
           ('RAM',uint8[:,:]) \
           ])
class Memory(object):
    def __init__(self):
        self.VRAM = np.zeros(0x4000,np.uint8)
        self.SpriteRAM = np.zeros(0x100,np.uint8)
        self.RAM = np.zeros((8,0x2000), np.uint8)
        

        

        

                    
if __name__ == '__main__':

    ram = Memory()

    

    
    
    
    








        
