# -*- coding: UTF-8 -*-
#This is where all 6502 instructions are kept.

from numba import jit
#自定义类
#from cpu6502 import cpu6502


#@jit
def ABS(cpu,):
    cpu.savepc = self.Read6502_2(cpu.PC) #+ (self.Read6502(self.PC + 1) << 8 )
    cpu.PC += 2

            
if __name__ == '__main__':
    pass


    #print help(cpu)
    #print cpu.PC

        










        
