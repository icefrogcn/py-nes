# -*- coding: UTF-8 -*-
#This is where all 6502 instructions are kept.

#自定义类
#from cpu6502commands import *
from cpu6502 import cpu6502

from deco import *

@deco
def Read6502(cpu, Address):
        if Address >=0x0 and Address <=0x1FFF:
            return cpu.bank0[Address & 0x7FF]
        elif Address >=0x8000 and Address <=0x9FFF:
            return cpu.bank8[Address - 0x8000]
        elif Address >=0xA000 and Address <=0xBFFF:
            return cpu.bankA[Address - 0xA000]
        elif Address >=0xC000 and Address <=0xDFFF:
            return cpu.bankC[Address - 0xC000]
        elif Address >=0xE000 and Address <=0xFFFF:
            return cpu.bankE[Address - 0xE000]
        elif Address == 0x2002:
            return

        





def reset6502(cpu = cpu6502()):
  cpu.a = 0; cpu.X = 0; cpu.Y = 0; cpu.p = 0x22
  cpu.S = 0xFF
  
  PC = Read6502(cpu,0xFFFC) + (Read6502(cpu,0xFFFD) * 0x100)
  print "Reset to $" , hex(PC) , "[" ,cpu.PC , "]"



if __name__ == '__main__':
    cpu = cpu6502()
    zpx6502(cpu)
    #print help(cpu)
    #print cpu.PC

        










        
