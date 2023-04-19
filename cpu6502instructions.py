# -*- coding: UTF-8 -*-
#This is where all 6502 instructions are kept.

from numba import jit
#自定义类
#from cpu6502 import cpu6502

from deco import *


@jit(forceobj=True)
def ADC(cpu, source):
        
        #cpu.adrmode(cpu.opcode)
        #temp_value = source#cpu.Read6502(cpu.savepc)
     
        cpu.saveflags = cpu.p & 0x1
        #print "adc6502"
        
        _sum = (cpu.a + source) & 0xFF
        _sum = (_sum + cpu.saveflags) & 0xFF
        cpu.p = (cpu.p | 0x40) if (_sum > 0x7F) or (_sum < -0x80) else (cpu.p & 0xBF)
      
        _sum = cpu.a + (source + cpu.saveflags)
        cpu.p = (cpu.p | 0x1) if (_sum > 0xFF)  else (cpu.p & 0xFE)

      
        cpu.a = _sum & 0xFF
        if (cpu.p & 0x8) :
            cpu.p = (cpu.p & 0xFE)
            if ((cpu.a & 0xF) > 0x9) :
                cpu.a = (cpu.a + 0x6) & 0xFF

            if ((cpu.a & 0xF0) > 0x90) :
                cpu.a = (cpu.a + 0x60) & 0xFF
                cpu.p = cpu.p | 0x1

        else:
            cpu.clockticks6502 += 1

    
        cpu.p = (cpu.p & 0xFD) if (cpu.a) else (cpu.p | 0x2)
        cpu.p = (cpu.p | 0x80) if (cpu.a & 0x80) else (cpu.p & 0x7F)

if __name__ == '__main__':
    cpu = cpu6502()
    zpx6502(cpu)
    #print help(cpu)
    #print cpu.PC

        










        
