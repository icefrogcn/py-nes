# -*- coding: UTF-8 -*-
#This is where all 6502 instructions are kept.

from numba import jit
#自定义类
#from cpu6502 import cpu6502

from deco import *


@jit
def ADC(cpu, source):
        #cpu.adrmode(cpu.opcode)
        temp_value = source
     
        cpu.saveflags = cpu.p & 0x1
        #print "adc6502"
        
        _sum = (cpu.a + temp_value) & 0xFF
        _sum = (_sum + cpu.saveflags) & 0xFF
        cpu.p = (cpu.p | 0x40) if (_sum > 0x7F) or (_sum < -0x80) else (cpu.p & 0xBF)
      
        _sum = cpu.a + (temp_value + cpu.saveflags)
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


def REL(cpu, source):
        cpu.savepc = self.Read6502(self.PC)
        cpu.PC += 1
        if (cpu.savepc & 0x80):
            cpu.savepc = cpu.savepc - 0x100

'''    
def exec6502(self,fun_type = 'normal'):

        PC = np.uint16(0) #             16 bit 寄存器 其值为指令地址
        a = np.uint8(0) #                '累加器
        X = np.uint8(0) #                '寄存器索引
        Y = np.uint8(0) #                '寄存器2
        S = np.uint8(0) #                '堆栈寄存器
        p = np.uint8(0) #                '标志寄存器
        savepc = np.uint16(0) # As Long
        saveflags = np.uint16(0) # As Long 'Integer
        clockticks6502 = np.uint16(0) # As Long

        
        def ADC(cpu, source):
            #cpu.adrmode(cpu.opcode)
            #temp_value = source#cpu.Read6502(cpu.savepc)
         
            saveflags = p & 0x1
            
            _sum = (a + source) & 0xFF
            _sum = (_sum + saveflags) & 0xFF
            p = (p | 0x40) if (_sum > 0x7F) or (_sum < -0x80) else (p & 0xBF)
          
            _sum = a + (source + saveflags)
            p = (p | 0x1) if (_sum > 0xFF)  else (p & 0xFE)

          
            a = _sum & 0xFF
            if (p & 0x8) :
                p = (p & 0xFE)
                if ((a & 0xF) > 0x9) :
                    a = (a + 0x6) & 0xFF

                if ((a & 0xF0) > 0x90) :
                    a = (a + 0x60) & 0xFF
                    p = p | 0x1

            else:
                clockticks6502 += 1

        
            p = (p & 0xFD) if (a) else (p | 0x2)
            p = (p | 0x80) if (a & 0x80) else (p & 0x7F)


'''

            
if __name__ == '__main__':
    cpu = cpu6502()
    zpx6502(cpu)
    #print help(cpu)
    #print cpu.PC

        










        
