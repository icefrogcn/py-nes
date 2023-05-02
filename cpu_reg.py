# -*- coding: UTF-8 -*-
import numpy as np
import numba as nb

from numba import jitclass
from numba import uint8,uint16
from numba.typed import Dict
from numba import types

C_FLAG = 0x01	#	// 1: Carry
Z_FLAG = 0x02	#	// 1: Zero
I_FLAG = 0x04	#	// 1: Irq disabled
D_FLAG = 0x08	#	// 1: Decimal mode flag (NES unused)
B_FLAG = 0x10	#	// 1: Break
R_FLAG = 0x20	#	// 1: Reserved (Always 1)
V_FLAG = 0x40	#	// 1: Overflow
N_FLAG = 0x80	#	// 1: Negative
'''
@jitclass([('reg',uint16[:]) \
           ])'''
class CPUREG(object):


    def __init__(self):
        self.reg = np.zeros(0x20, np.uint16) 

        #self.savepc = 0
        #self.saveflags = 0
        #self.clockticks6502  = 0

    @property
    def PC(self):
        return self.reg[0]
    
    @property
    def A(self):
        return self.reg[1]
    
    @property
    def X(self):
        return self.reg[2]
    
    @property
    def Y(self):
        return self.reg[3]
    
    @property
    def S(self):
        return self.reg[4]
    
    @property
    def P(self):
        return self.reg[5]
    
        

        

                    
if __name__ == '__main__':

    reg = CPUREG()

    

    
    
    
    








        
