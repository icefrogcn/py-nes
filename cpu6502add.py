# -*- coding: UTF-8 -*-
#CPU Memory Map
'''
' M6502 CPU Implementation for basicNES 2000.
' By Don Jarrett and Tobias Str鰉stedt, 1997-2000
' If you use this file commercially please drop me a mail
' at r.jarrett@worldnet.att.net or d.jarrett@worldnet.att.net.
' basicNES Copyright (C) 1996-2000 Don Jarrett.
'''
#自定义类
from cpu6502commands import *
from neshardware import *

from deco import *

         

         

'===================================='
'       MapperWrite(Address,value)   '
' Selects/Switches Chr-ROM and Prg-  '
' ROM depending on the mapper. Based '
' on DarcNES.                        '
'===================================='
def MapperWrite(Address, value):
    if Mapper == 1:
        pass
        #MMC1_Write Address, value
    elif Mapper == 2:
        reg8 = (value * 2)
        regA = reg8 + 1
        #SetupBanks
    elif Mapper == 3:
        pass
        #Select8KVROM (value And AndIt)


CurrentLine =0 #Long 'Integer
AddressMask =0 #Long 'Integer

'Registers and tempregisters'
'DF: Be careful. Anything, anywhere that uses a variable of the same name without declaring it will be using these:'
a =0 #Byte                '累加器
X =0 #Byte                '寄存器索引
Y =0 #Byte                '寄存器2
S =0 #Byte                '堆栈寄存器
P =0 #Byte                '标志寄存器

'32bit instructions are faster in protected mode than 16bit'
PC = 0 # As Long                   '16 bit 寄存器 其值为指令地址
savepc = 0 # As Long
value = 0 # As Long 'Integer
value2 = 0 # As Long 'Integer
_sum = 0 # As Long 'Integer
saveflags = 0 # As Long 'Integer
_help = 0 # As Long

opcode = 0 # As Byte
clockticks6502 = 0 # As Long

' arrays'
TICKS = [0] * 0x100 # As Byte
addrmode = [0] * 0x100 # As Byte
instruction = [0] * 0x100 # As Byte
gameImage = [] #As Byte

CPUPaused = False #As Boolean

addrmodeBase = 0 #As Long

maxCycles1 = 0 # As Long 'max cycles per scanline from scanlines 0-239
maxCycles = 0 # As Long 'max cycles until next scanline
SmartExec = False # As Boolean
realframes = 0 # As Long 'actual # of frames rendered


if __name__ == '__main__':
    print TICKS, instruction, addrmode
    TICKS, instruction, addrmode = init6502()
    print TICKS, instruction, addrmode
                #break

        










        
