# -*- coding: UTF-8 -*-

import time
from numba import jit,jitclass
from numba import int8,uint8,int16,uint16
import numpy as np
import numba as nb

import traceback

import keyboard

#CPU Memory Map
'''
' M6502 CPU Implementation for basicNES 2000.
' By Don Jarrett & Tobias Str鰉stedt, 1997-2000
' If you use this file commercially please drop me a mail
' at r.jarrett@worldnet.att.net | d.jarrett@worldnet.att.net.
' basicNES Copyright (C) 1996-2000 Don Jarrett.
'''
#自定义类
from cpu6502commands import *

from cpu6502instructions import *

import cpu6502addressmode as addressmode

         
import memory


from mmc import MMC

from apu import APU
from ppu import PPU
from joypad import JOYPAD



C_FLAG = 0x01	#	// 1: Carry
Z_FLAG = 0x02	#	// 1: Zero
I_FLAG = 0x04	#	// 1: Irq disabled
D_FLAG = 0x08	#	// 1: Decimal mode flag (NES unused)
B_FLAG = 0x10	#	// 1: Break
R_FLAG = 0x20	#	// 1: Reserved (Always 1)
V_FLAG = 0x40	#	// 1: Overflow
N_FLAG = 0x80	#	// 1: Negative



#uint8_vector = nb.types.Array(dtype=uint8[:], ndim=1, layout="A")
#uint16_vector = nb.types.Array(dtype=uint16[:], ndim=1, layout="C")

@jitclass([('RAM',uint8[:,:]), \
           ('PRGRAM',uint8[:,:])])
class Memory(object):
    def __init__(self, memory = memory.Memory()):
        self.RAM = memory.RAM
        self.PRGRAM = self.RAM
        #self.bank0 = self.PRGRAM[0]#[0]*2048 #As Byte ' RAM 
        #self.bank6 = self.PRGRAM[3]#[0]*8192 #As Byte ' SaveRAM 
        #self.bank8 = self.PRGRAM[4]#[0]*8192 #As Byte '8-E are PRG-ROM
        #self.bankA = self.PRGRAM[5]#[0]*8192 #As Byte
        #self.bankC = self.PRGRAM[6]#[0]*8192 #As Byte
        #self.bankE = self.PRGRAM[7]#[0] * 8192 #As Byte

    def Read(self,address):
        bank = address >> 13
        value = 0
        if bank == 0x00:                        # Address >=0x0 and Address <=0x1FFF:
            return self.PRGRAM[0, address & 0x7FF]
        elif bank > 0x03:
            return self.PRGRAM[bank, address & 0x1FFF]

    def write(self,address):
        pass
        

class cpu6502(MMC):
    
    AddressMask =0 #Long 'Integer

    'Registers & tempregisters'
    'DF: Be careful. Anything, anywhere that uses a variable of the same name without declaring it will be using these:'
    
    '32bit instructions are faster in protected mode than 16bit'

    #value = 0 # As Long 'Integer
    #_sum = 0 # As Long 'Integer
    #_help = 0 # As Long

    ' arrays'
    #gameImage = [] #As Byte

    
    
    addrmodeBase = np.uint16(0) #As Long

    maxCycles1 = np.uint8(114) # As Long 'max cycles per scanline from scanlines 0-239
    maxCycles = np.uint8(0) # As Long 'max cycles until next scanline
    SmartExec = False # As Boolean
    realframes = np.uint8(0) # As Long 'actual # of frames rendered


    CPU_MEM_BANK = 8
    
    totalFrame = 0
    
    Frames = 0



    tilebased = True
    

    def __init__(self, _consloe):
        self.PC = np.uint16(0) #             16 bit 寄存器 其值为指令地址
        self.a = np.uint8(0) #                '累加器
        self.X = np.uint8(0) #                '寄存器索引
        self.Y = np.uint8(0) #                '寄存器2
        self.S = np.uint8(0) #                '堆栈寄存器
        self.p = np.uint8(0) #                '标志寄存器
        self.savepc = np.uint16(0) # As Long
        self.saveflags = np.uint16(0) # As Long 'Integer
        self.clockticks6502 = np.uint16(0) # As Long
        self.opcode = np.uint8(0) # As Byte

        self.reg = reg()
        self.RAM = Memory(_consloe.memory)
        self.PRGRAM = self.RAM.PRGRAM
        self.bank0 = self.PRGRAM[0]
        self.bank6 = self.PRGRAM[3]
        self.bank8 = self.PRGRAM[4]
        self.bankA = self.PRGRAM[5]
        self.bankC = self.PRGRAM[6]
        self.bankE = self.PRGRAM[7]
        
        
        
        self.debug = False
        self.MapperWriteFlag = 0
        self.MapperWriteData = {'Address':0,'value':0}

        self.FrameFlag = 0

        self.consloe = _consloe
        self.PPU = _consloe.PPU
        self.PPU_reg = self.PPU.reg
        self.APU = _consloe.APU
        self.JOYPAD1 = _consloe.JOYPAD1
        self.JOYPAD2 = _consloe.JOYPAD2
        
        self.CPURunning = 1
        
        self.addrmode = addrmode
        self.instructions = instruction
        self.Ticks = Ticks

        self.instruction_dic ={
             INS_BNE: self.bne6502,
             INS_CMP: self.cmp6502,
             INS_LDA: self.lda6502,
             INS_STA: self.sta6502,
             INS_BIT: self.bit6502,
             INS_BVC: self.bvc6502,
             INS_BEQ: self.beq6502,
             INS_INY: self.iny6502,
             INS_BPL: self.bpl6502,
             INS_DEX: self.dex6502,
             INS_INC: self.inc6502,
             INS_JMP: self.jmp6502,
             INS_DEC: self.dec6502,
             INS_JSR: self.jsr6502,
             INS_AND: self.and6502,
             INS_NOP: self.nop6502,
             INS_BRK: self.brk6502,
             INS_ADC: self.adc6502,
             INS_EOR: self.eor6502,
             INS_ASL: self.asl6502,
             INS_ASLA: self.asla6502,
             INS_BCC: self.bcc6502,
             INS_BCS: self.bcs6502,
             INS_BMI: self.bmi6502,
             INS_BVS: self.bvs6502,
             INS_CLC: self.clc6502,
             INS_CLD: self.cld6502,
             INS_CLI: self.cli6502,
             INS_CLV: self.clv6502,
             INS_CPX: self.cpx6502,
             INS_CPY: self.cpy6502,
             INS_DEA: self.dea6502,
             INS_DEY: self.dey6502,
             INS_INA: self.ina6502,
             INS_INX: self.inx6502,
             INS_LDX: self.ldx6502,
             INS_LDY: self.ldy6502,
             INS_LSR: self.lsr6502,
             INS_LSRA: self.lsra6502,
             INS_ORA: self.ora6502,
             INS_PHA: self.pha6502,
             INS_PHX: self.phx6502,
             INS_PHP: self.php6502,
             INS_PHY: self.phy6502,
             INS_PLA: self.pla6502,
             INS_PLP: self.plp6502,
             INS_PLX: self.plx6502,
             INS_PLY: self.ply6502,
             INS_ROL: self.rol6502,
             INS_ROLA: self.rola6502,
             INS_ROR: self.ror6502,
             INS_RORA: self.rora6502,
             INS_RTI: self.rti6502,
             INS_RTS: self.rts6502,
             INS_SBC: self.sbc6502,
             INS_SEC: self.sec6502,
             INS_SED: self.sed6502,
             INS_SEI: self.sei6502,
             INS_STX: self.stx6502,
             INS_STY: self.sty6502,
             INS_TAX: self.tax6502,
             INS_TAY: self.tay6502,
             INS_TXA: self.txa6502,
             INS_TYA: self.tya6502,
             INS_TXS: self.txs6502,
             INS_TSX: self.tsx6502,
             INS_BRA: self.bra6502
        }


        self.adrmode_dic ={
            ADR_ABS: self.abs6502,
            ADR_ABSX: self.absx6502,
            ADR_ABSY: self.absy6502,
            ADR_IMP: ' nothing really necessary cause implied6502 = ""',
            ADR_IMM: self.imm6502,
            ADR_INDABSX: self.indabsx6502,
            ADR_IND: self.indirect6502,
            ADR_INDX: self.indx6502,
            ADR_INDY: self.indy6502,
            ADR_INDZP: self.indzp6502,
            ADR_REL: self.rel6502,
            ADR_ZP: self.zp6502,
            ADR_ZPX: self.zpx6502,
            ADR_ZPY: self.zpy6502
            }

        self.new_instruction ={
             #INS_BNE: self.bne6502,
             #INS_CMP: self.cmp6502,
             #INS_LDA: self.lda6502,
             #INS_STA: self.sta6502,
             #INS_BIT: self.bit6502,
             #INS_BVC: self.bvc6502,
             #INS_BEQ: self.beq6502,
             #INS_INY: self.iny6502,
             #INS_BPL: self.bpl6502,
             #INS_DEX: self.dex6502,
             #INS_INC: self.inc6502,
             #INS_JMP: self.jmp6502,
             #INS_DEC: self.dec6502,
             #INS_JSR: self.jsr6502,
             #INS_AND: self.and6502,
             #INS_NOP: self.nop6502,
             #INS_BRK: self.brk6502,
             INS_ADC: ADC(self, None),
             #INS_EOR: self.eor6502,
             #INS_ASL: self.asl6502,
             #INS_ASLA: self.asla6502,
             #INS_BCC: self.bcc6502,
             #INS_BCS: self.bcs6502,
             #INS_BMI: self.bmi6502,
             #INS_BVS: self.bvs6502,
             #INS_CLC: self.clc6502,
             #INS_CLD: self.cld6502,
             #INS_CLI: self.cli6502,
             #INS_CLV: self.clv6502,
             #INS_CPY: self.cpy6502,
             #INS_DEA: self.dea6502,
             #INS_DEY: self.dey6502,
             #INS_INA: self.ina6502,
             #INS_INX: self.inx6502,
             #INS_LDX: self.ldx6502,
             #INS_LDY: self.ldy6502,
             #INS_LSR: self.lsr6502,
             #INS_LSRA: self.lsra6502,
             #INS_ORA: self.ora6502,
             #INS_PHA: self.pha6502,
             #INS_PHX: self.phx6502,
             #INS_PHP: self.php6502,
             #INS_PHY: self.phy6502,
             #INS_PLA: self.pla6502,
             #INS_PLP: self.plp6502,
             #INS_PLX: self.plx6502,
             #INS_PLY: self.ply6502,
             #INS_ROL: self.rol6502,
             #INS_ROLA: self.rola6502,
             #INS_ROR: self.ror6502,
             #INS_RORA: self.rora6502,
             #INS_RTI: self.rti6502,
             #INS_RTS: self.rts6502,
             #INS_SBC: self.sbc6502,
             #INS_SEC: self.sec6502,
             #INS_SED: self.sed6502,
             #INS_SEI: self.sei6502,
             #INS_STX: self.stx6502,
             #INS_STY: self.sty6502,
             #INS_TAX: self.tax6502,
             #INS_TAY: self.tay6502,
             #INS_TXA: self.txa6502,
             #INS_TYA: self.tya6502,
             #INS_TXS: self.txs6502,
             #INS_TSX: self.tsx6502,
             #INS_BRA: self.bra6502
        }

        self.new_adrmode ={
            ADR_ABS: self.abs6502,
            #ADR_ABSX: self.absx6502,
            #ADR_ABSY: self.absy6502,
            #ADR_IMP: ' nothing really necessary cause implied6502 = ""',
            #ADR_IMM: self.imm6502,
            #ADR_INDABSX: self.indabsx6502,
            #ADR_IND: self.indirect6502,
            #ADR_INDX: self.indx6502,
            #ADR_INDY: self.indy6502,
            #ADR_INDZP: self.indzp6502,
            #ADR_REL: self.rel6502,
            #ADR_ZP: self.zp6502,
            #ADR_ZPX: self.zpx6502,
            #ADR_ZPY: self.zpy6502
            }



    def sync_cpu2reg(self,reg):
        reg.PC = self.PC
        reg.a = self.a
        reg.X = self.X
        reg.Y = self.Y
        reg.S = self.S
        reg.p = self.p
        reg.savepc = self.savepc
        reg.saveflags = self.saveflags
        reg.clockticks6502 = self.clockticks6502
        

    def sync_reg2cpu(self,reg):
        self.PC = reg.PC
        self.a = reg.a
        self.X = reg.X
        self.Y = reg.Y
        self.S = reg.S
        self.p = reg.p
        self.savepc = reg.savepc
        self.saveflags = reg.saveflags
        self.clockticks6502 = reg.clockticks6502

        
    def implied6502(self):
        return

    def reset6502(self):
        self.a = 0; self.X = 0; self.Y = 0; self.p = 0x22
        self.S = 0xFF
        self.PC = self.Read6502_2(0xFFFC)
        print "6502 reset:",self.status()

    def status(self):
        return self.Frames,self.PC,self.clockticks6502,self.PPU_reg.PPUSTATUS,self.PPU.CurrentLine,"a:%d X:%d Y:%d S:%d p:%d" %(self.a,self.X,self.Y,self.S,self.p),self.opcode

    def log(self,*args):
        #print self.debug
        if self.debug:
            print args
    
    def exec6502(self,fun_type = 'normal'):

        #exec6502new(self)
        
        while self.consloe.Running:

            if self.FrameFlag or self.MapperWriteFlag:
                    
                    return
                
            self.opcode = self.Read6502(self.PC)  #Fetch Next Operation
            self.PC += 1
            self.clockticks6502 += self.Ticks[self.opcode]

            instruction = self.instructions[self.opcode]

            self.instruction_dic.get(instruction)()

            if self.clockticks6502 > self.maxCycles1:
                self.Scanline()



    def Scanline(self):

                #if self.MAPPER.Clock(self.clockticks6502):self.irq6502()
                #self.log("Scanline:",self.status()) ############################

                
                if self.PPU.CurrentLine < 240:
                    self.PPU.RenderScanline()

                    
                if self.MAPPER.Mapper == 4:
                    if MMC.MMC3_HBlank(self, self.PPU.CurrentLine, self.PPU.Control1):
                        print 'MMC3_HBlank'
                        #self.irq6502()
                        
                if self.PPU.CurrentLine >= 240:
                    #self.log("CurrentLine:",self.status()) ############################
                    if self.PPU.CurrentLine == 240 :
                        if self.PPU_reg.PPUCTRL & 0x80:
                            self.nmi6502()
                           #realframes = realframes + 1
                    
                    self.PPU.reg.PPUSTATUS_W(0x80)

                        
                if self.PPU.CurrentLine == 262:
                    #self.log("FRAME:",self.status()) ###########################
                    self.APU.updateSounds()
                    
                    
                    self.PPU.CurrentLine = 0

                    if self.PPU.Running and self.PPU.render:self.PPU.blitFrame()
        
                    
                    #self.PPU.Frames += 1
                    #print NES.Frames
                    #self.PPU.Status = 0x0
                    self.PPU.reg.PPUSTATUS_W(0)
                    self.consloe.ShowFPS()
                else:
                    self.PPU.CurrentLine +=  1
                

                self.clockticks6502 -= self.maxCycles1

                

        #"DF: reordered the the case's. Made address long (was variant)."
    
    def exec_opcode(self,instruction_opcode):
            try:
                self.instruction_dic[instruction_opcode]()
            except:
                print "Invalid opcode - %s" %hex(instruction_opcode)
                print (traceback.print_exc())
            

    ' This is where all 6502 instructions are kept.'
    #@jit
    def adc6502(self):
        
        self.adrmode(self.opcode)
        temp_value = self.Read6502(self.savepc)
     
        self.saveflags = self.p & 0x1
        #print "adc6502"
        _sum = self.a
        _sum = (_sum + temp_value) & 0xFF
        _sum = (_sum + self.saveflags) & 0xFF
        self.p = (self.p | 0x40) if (_sum > 0x7F) or (_sum < -0x80) else (self.p & 0xBF)
      
        _sum = self.a + (temp_value + self.saveflags)
        self.p = (self.p | 0x1) if (_sum > 0xFF)  else (self.p & 0xFE)

      
        self.a = _sum & 0xFF
        if (self.p & 0x8) :
            self.p = (self.p & 0xFE)
            if ((self.a & 0xF) > 0x9) :
                self.a = (self.a + 0x6) & 0xFF

            if ((self.a & 0xF0) > 0x90) :
                self.a = (self.a + 0x60) & 0xFF
                self.p = self.p | 0x1

        else:
            self.clockticks6502 += 1

    
        self.p = (self.p & 0xFD) if (self.a) else (self.p | 0x2)
        self.p = (self.p | 0x80) if (self.a & 0x80) else (self.p & 0x7F)

    def adrmode(self, opcode):    #--------------------------   adrmode   -------------------
        #self.adrmode_opcode()
        #if self.addrmode[opcode] = ADR_REL
        self.adrmode_dic[self.addrmode[opcode]]()


    
    def indabsx6502(self):
      #temp_value = self.Read6502_2(self.PC) + self.X
      
      self.savepc = self.Read6502_2(self.Read6502_2(self.PC) + self.X)


    def indx6502(self):
      #'TS: Changed PC++ & removed ' (?)
      temp_value = self.Read6502(self.PC) & 0xFF
      temp_value = (temp_value + self.X) & 0xFF
      self.PC += 1
      self.savepc = self.Read6502_2(temp_value)


    def indy6502(self):
        #'TS: Changed PC++ & == to != (If then else)
        #print 'indy6502'
        #temp_value = self.Read6502(self.PC)
      
        self.savepc = self.Read6502_2(self.Read6502(self.PC))
        self.PC += 1
  
        if (Ticks[self.opcode] == 5) and (self.savepc >>8 != (self.savepc + self.Y) >> 8):
            
            self.clockticks6502 += 1
                    
            #self.clockticks6502 += 0 if self.savepc >>8 == (self.savepc + self.Y) >> 8 else 1

        self.savepc += self.Y
  
    def indzp6502(self):
        'Added pc=pc+1, & (value+1) (Why Don?)'
        '''temp_value = self.Read6502(self.PC)
        self.PC += 1
        self.savepc = self.Read6502_2(temp_value)'''
        print 'indzp6502'
        self.savepc = self.Read6502_2(self.Read6502(self.PC))
        self.PC += 1
        
    def zpx6502(self):
        #'TS: Rewrote everything!
        #'Overflow stupid check
        self.savepc = self.Read6502(self.PC)
        self.savepc = self.savepc + self.X
        self.PC += 1
        #savepc = savepc & 0xFF
    def zpy6502(self):
        'TS: Added PC=PC+1'
        self.savepc = self.Read6502(self.PC)
        self.savepc = self.savepc + self.Y
        self.PC += 1
        'savepc = savepc & 0xFF'
    def zp6502(self):
        self.savepc = self.Read6502(self.PC)
        self.PC += 1



    def immediate6502(self):
        self.savepc = self.PC
        self.PC += 1
    
    def indirect6502(self):
        #self._help = self.Read6502_2(self.PC)
        self.savepc = self.Read6502_2(self.Read6502_2(self.PC))
        self.PC += 2


    def absx6502(self):
        'TS: Changed to if then else instead of if then (!= instead of ==)'
        #self.savepc = self.Read6502(self.PC)
        #self.savepc = savepc + (self.Read6502(self.PC + 1) * 0x100)
        #self.PC += 2
        self.abs6502()
        self.abs_ct(self.X)
        self.savepc += self.X
    def absy6502(self):
        'TS: Changed to != instead of == (Look at absx for more details)'
        #savepc = Read6502(PC) + (Read6502(PC + 1) * 0x100&)
        #PC = PC + 2
        self.abs6502()
        self.abs_ct(self.Y)
        self.savepc += self.Y
    def abs6502(self):
        self.savepc = self.Read6502_2(self.PC) #+ (self.Read6502(self.PC + 1) << 8 )
        self.PC += 2
            
      
    def abs_ct(self,var):
        if Ticks[self.opcode] == 4:
            self.clockticks6502 += 0 if (self.savepc >> 8) == ((self.savepc + var) >> 8) else 1
            #self.clockticks6502 += 0 if (self.savepc >> 8) == ((self.savepc + var) >> 8) else 1


    def imm6502(self):
        self.savepc = self.PC
        self.PC += 1
    def rel6502(self):
        self.savepc = self.Read6502(self.PC)
        self.PC += 1
        if (self.savepc & 0x80):
            self.savepc -=  0x100

    
    def and6502(self):
        self.adrmode(self.opcode)
        temp_value = self.Read6502(self.savepc)
        self.a &= temp_value
        self.common_set_p(self.a)



    def asl6502(self):
        self.adrmode(self.opcode)
        temp_value = self.Read6502(self.savepc)
  
        self.p = (self.p & 0xFE) | ((temp_value >> 7) & 0x1)
        temp_value = temp_value << 1 & 0xFF #(temp_value * 2) & 0xFF
  
        self.Write6502(self.savepc, (temp_value & 0xFF))
        self.common_set_p(temp_value)


    def asla6502(self):
        self.p = (self.p & 0xFE) | ((self.a >> 7) & 0x1)
        self.a = self.a << 1 & 0xFF #(self.a * 2) & 0xFF
        self.common_set_p(self.a)



    def bcc6502(self):
      if (self.p & 0x1) :
        self.PC += 1
      else:
        self.adrmode(self.opcode)
        self.PC += self.savepc
        self.clockticks6502 += 1



    def bcs6502(self):
      if (self.p & 0x1) :
        self.adrmode(self.opcode)
        self.PC +=  self.savepc
        self.clockticks6502 += 1
      else:
        self.PC += 1

    def beq6502(self):
      if (self.p & 0x2) :
        self.adrmode(self.opcode)
        self.PC += self.savepc
        self.clockticks6502 += 1
      else:
        self.PC += 1



    def bit6502(self):
        self.adrmode(self.opcode)
        temp_value = self.Read6502(self.savepc)

        self.p = (self.p & 0xFD) if (temp_value & self.a)  else (self.p | 0x2)
        self.p = ((self.p & 0x3F) | (temp_value & 0xC0))


    def bmi6502(self):
      if (self.p & 0x80) :
        self.adrmode(self.opcode)
        self.PC +=  self.savepc
        self.clockticks6502 +=  1
      else:
        self.PC += 1



    def bne6502(self):
      if ((self.p & 0x2) == 0) :
        self.adrmode(self.opcode)
        self.PC += self.savepc
      else:
        self.PC += 1

    def bpl6502(self):
      if ((self.p & 0x80) == 0) :
        self.adrmode(self.opcode)
        self.PC += self.savepc
      else:
        self.PC += 1


    def brk6502(self):
      #print "brk code"
      self.PC += 1
      self.Write6502(0x100 + self.S, (self.PC >> 8) & 0xFF)
      self.S = (self.S - 1) & 0xFF
      self.Write6502(0x100 + self.S, (self.PC & 0xFF))
      self.S = (self.S - 1) & 0xFF
      self.Write6502(0x100 + self.S, self.p)
      self.S = (self.S - 1) & 0xFF
      self.p = self.p | 0x14
      self.PC = self.Read6502_2(0xFFFE)# + (self.Read6502(0xFFFF) * 0x100)


    def bvc6502(self):
      if ((self.p & 0x40) == 0) :
        self.adrmode(self.opcode)
        self.PC += self.savepc
        self.clockticks6502 +=  1
      else:
        self.PC += 1

    def bvs6502(self):
      if (self.p & 0x40) :
        self.adrmode(self.opcode)
        self.PC += self.savepc
        self.clockticks6502 += 1
      else:
        self.PC += 1


    def clc6502(self):
        self.p &= 0xFE
    def cld6502(self):
        self.p &= 0xF7
    def cli6502(self):
        self.p &= 0xFB
    def clv6502(self):
        self.p &= 0xBF

    def cmp6502(self):
      self.compare_var(self.a)

    def cpx6502(self):
      self.compare_var(self.X)

    def cpy6502(self):
        self.compare_var(self.Y)

    #@jit(nopython=True)
    
    def compare_var(self,var):
      self.adrmode(self.opcode)
      temp_value = self.Read6502(self.savepc)

      self.p = (self.p | 0x1) if (var + 0x100 - temp_value > 0xFF) else (self.p & 0xFE)
      
      temp_value = (var + 0x100 - temp_value) & 0xFF

      self.common_set_p(temp_value)


    def common_set_p(self, var):
        self.p = (self.p & 0xFD) if var else (self.p | 0x2)
        #print (var & 0x80)
        self.p = (self.p | 0x80) if (var & 0x80) else (self.p & 0x7F)

    def dec6502(self):
        self.adrmode(self.opcode)
        self.Write6502((self.savepc), (self.Read6502(self.savepc) - 1) & 0xFF)
          
        #temp_value = self.Read6502(self.savepc)
        self.common_set_p(self.Read6502(self.savepc))

    def dex6502(self):
        self.X = (self.X - 1) & 0xFF
        self.common_set_p(self.X)

    def dey6502(self):
        self.Y = (self.Y - 1) & 0xFF
        self.common_set_p(self.Y)

    def dea6502(self):
        self.a = (self.a - 1) & 0xFF
        self.common_set_p(self.a)

    def eor6502(self):
        self.adrmode(self.opcode)
        self.a = self.a ^ self.Read6502(self.savepc)
        self.common_set_p(self.a)

    def inc6502(self):
        self.adrmode(self.opcode)
        self.Write6502(self.savepc, (self.Read6502(self.savepc) + 1) & 0xFF)
  
        temp_value = self.Read6502(self.savepc)
        self.common_set_p(temp_value)
        
    def inx6502(self):
        self.X = (self.X + 1) & 0xFF
        self.common_set_p(self.X)

    def iny6502(self):
        self.Y = (self.Y + 1) & 0xFF
        self.common_set_p(self.Y)

    def ina6502(self):
        self.a = (self.a + 1) & 0xFF
        self.common_set_p(self.a)

    def jmp6502(self):
        self.adrmode(self.opcode)
        self.PC = self.savepc

    def jsr6502(self):
      self.PC += 1
      self.Write6502(self.S + 0x100, (self.PC >> 8))
      self.S = (self.S - 1) & 0xFF
      self.Write6502(self.S + 0x100, (self.PC & 0xFF))
      self.S = (self.S - 1) & 0xFF
      self.PC = self.PC - 1
      self.adrmode(self.opcode)
      self.PC = self.savepc

    def lda6502(self):
        self.adrmode(self.opcode)
        self.a = self.Read6502(self.savepc)
        
        self.common_set_p(self.a)

        
    def ldx6502(self):
        self.adrmode(self.opcode)
        self.X = self.Read6502(self.savepc)
  
        self.common_set_p(self.X)

    def ldy6502(self):
        self.adrmode(self.opcode)
        self.Y = self.Read6502(self.savepc)
  
        self.common_set_p(self.Y)

    def lsr6502(self):
        self.adrmode(self.opcode)
        temp_value = self.Read6502(self.savepc)
         
        self.p = (self.p & 0xFE) | (temp_value & 0x1)
  
        temp_value = (temp_value // 2) & 0xFF
        self.Write6502(self.savepc, (temp_value & 0xFF))
  
        self.common80_set_p(temp_value)

    def common80_set_p(self, var):
        self.p = (self.p & 0xFD) if (var) else (self.p | 0x2)
        self.p = (self.p | 0x80) if (var & 0x80) == 0x80 else (self.p & 0x7F)
        
    def lsra6502(self):
        self.p = (self.p & 0xFE) | (self.a & 0x1)
        self.a = (self.a // 2) & 0xFF
        
        self.common_set_p(self.a)
       
    def nop6502(self):
        'TS: Implemented complex code structure ;)'
        pass

    def ora6502(self):
        self.adrmode(self.opcode)
        self.a = self.a | self.Read6502(self.savepc)
        self.common_set_p(self.a)

    def pha6502(self):
        self.Write6502(0x100 + self.S, self.a)
        self.S = (self.S - 1) & 0xFF

    def php6502(self):
        self.Write6502(0x100 + self.S, self.p)
        self.S = (self.S - 1) & 0xFF

    def phx6502(self):
        self.Write6502(0x100 + self.S, self.X)
        self.S = (self.S - 1) & 0xFF

    def phy6502(self):
        self.Write6502(0x100 + self.S, self.Y)
        self.S = (self.S - 1) & 0xFF

    def pla6502(self):
        self.S = (self.S + 1) & 0xFF
        self.a = self.Read6502(self.S + 0x100)
        self.common_set_p(self.a)

    def plx6502(self):
        self.S = (self.S + 1) & 0xFF
        self.X = self.Read6502(self.S + 0x100)
        self.common_set_p(self.X)

    def ply6502(self):
        self.S = (self.S + 1) & 0xFF
        self.Y = self.Read6502(self.S + 0x100)
        self.common_set_p(self.Y)

    def plp6502(self):
        self.S = (self.S + 1) & 0xFF
        self.p = self.Read6502(self.S + 0x100) | 0x20

    def rol6502(self):
        self.saveflags = (self.p & 0x1)
        self.adrmode(self.opcode)
        temp_value = self.Read6502(self.savepc)
      
        self.p = (self.p & 0xFE) | ((temp_value >> 7) & 0x1)
  
        temp_value = (temp_value * 2) & 0xFF
        temp_value = temp_value | self.saveflags
  
        self.Write6502(self.savepc, (temp_value & 0xFF))
        self.common_set_p(temp_value)
        
    def rola6502(self):
        self.saveflags = (self.p & 0x1)
        self.p = (self.p & 0xFE) | ((self.a  >> 7) & 0x1)
        self.a = (self.a * 2) & 0xFF
        self.a = self.a | self.saveflags
        self.common_set_p(self.a)

    def ror6502(self):
        self.saveflags = (self.p & 0x1)
        self.adrmode(self.opcode)
        temp_value = self.Read6502(self.savepc)
      
        self.p = (self.p & 0xFE) | (temp_value & 0x1)
        temp_value = (temp_value // 2) & 0xFF

        
        if (self.saveflags) :
            temp_value = temp_value | 0x80

        self.Write6502(self.savepc, (temp_value & 0xFF))
        self.common_set_p(temp_value)

    def rora6502(self):
        self.saveflags = (self.p & 0x1)

        self.p = (self.p & 0xFE) | (self.a & 0x1)
        self.a = (self.a // 2) & 0xFF
  
        if (self.saveflags) :
            self.a = self.a | 0x80

        self.common_set_p(self.a)

    def rti6502(self):
      self.S = (self.S + 1) & 0xFF
      self.p = self.Read6502(self.S + 0x100) | 0x20
      self.S = (self.S + 1) & 0xFF
      self.PC = self.Read6502(self.S + 0x100)
      self.S = (self.S + 1) & 0xFF
      self.PC = self.PC + (self.Read6502(self.S + 0x100) * 0x100)

    def rts6502(self):
      self.S = (self.S + 1) & 0xFF
      self.PC = self.Read6502(self.S + 0x100)
      self.S = (self.S + 1) & 0xFF
      self.PC = self.PC + (self.Read6502(self.S + 0x100) * 0x100)
      self.PC += 1

    def sbc6502(self):
      self.adrmode(self.opcode)
      temp_value = self.Read6502(self.savepc) ^ 0xFF
  
      self.saveflags = (self.p & 0x1)
  
      _sum = self.a
      _sum = (_sum + temp_value) & 0xFF
      _sum = (_sum + (self.saveflags * 16)) & 0xFF
      
      
      self.p = self.p | 0x40 if ((_sum > 0x7F) | (_sum <= -0x80)) else self.p & 0xBF

      
      _sum = self.a + (temp_value + self.saveflags)
      
      self.p = (self.p | 0x1) if (_sum > 0xFF) else (self.p & 0xFE)

      
      self.a = _sum & 0xFF
      if (self.p & 0x8) :
        self.a = (self.a - 0x66) & 0xFF
        self.p = self.p & 0xFE
        if ((self.a & 0xF) > 0x9) :
          self.a = (self.a + 0x6) & 0xFF
        
        if ((self.a & 0xF0) > 0x90) :
          self.a = (self.a + 0x60) & 0xFF
          self.p = self.p | 0x1
        
      else:
        self.clockticks6502 = self.clockticks6502 + 1
      
      #print "sbc6502"
      self.common_set_p(self.a)

      
    def sec6502(self):
        self.p = self.p | 0x1
    def sed6502(self):
        self.p = self.p | 0x8
    def sei6502(self):
        self.p = self.p | 0x4

    def sta6502(self):
      self.adrmode(self.opcode)
      self.Write6502((self.savepc), self.a)
    def stx6502(self):
      self.adrmode(self.opcode)
      self.Write6502((self.savepc), self.X)
    def sty6502(self):
      self.adrmode(self.opcode)
      self.Write6502((self.savepc), self.Y)

    def tax6502(self):
      self.X = self.a
      self.common_set_p(self.X)
    def tay6502(self):
      self.Y = self.a
      self.common_set_p(self.Y)
    def tsx6502(self):
      self.X = self.S
      self.common_set_p(self.X)
    def txa6502(self):
      self.a = self.X
      self.common_set_p(self.a)
    def txs6502(self):
      self.S = self.X
    def tya6502(self):
      self.a = self.Y
      self.common_set_p(self.a)
      
    def bra6502(self):
        self.adrmode(self.opcode)
        self.PC = self.PC + self.savepc
        self.clockticks6502 = self.clockticks6502 + 1

    
    def nmi6502(self):
        'TS: Changed PC>>8 to / not *'
        self.Write6502( (self.S + 0x100), (self.PC >> 8))
        self.S = (self.S - 1) & 0xFF
        self.Write6502( (self.S + 0x100), (self.PC & 0xFF))
        self.S = (self.S - 1) & 0xFF
        self.Write6502( (self.S + 0x100), self.p)
        self.p = self.p | 0x4
        self.S = (self.S - 1) & 0xFF
        self.PC = self.Read6502(0xFFFA) + (self.Read6502(0xFFFB) << 8)
        #print "nmi=" , self.PC , "[$" , hex(self.PC) , "]"
        self.clockticks6502 = self.clockticks6502 + 7

    def irq6502(self):
        #' Maskable interrupt
        if (self.p & 0x4) == 0 :
            self.Write6502(0x100 + self.S, self.PC // 256)
            self.S = (self.S - 1) & 0xFF
            self.Write6502(0x100 + self.S, (self.PC & 0xFF))
            self.S = (self.S - 1) & 0xFF
            self.Write6502(0x100 + self.S, self.p)
            self.S = (self.S - 1) & 0xFF
            self.p = self.p | 0x4
            self.PC = self.Read6502(0xFFFE) + (self.Read6502(0xFFFF) * 0x100)
            self.clockticks6502 = self.clockticks6502 + 7




    def Read6502_2(self,Address):
        return self.Read6502(Address) + (self.Read6502(Address + 1) << 8)

    #@jit
    def Read6502(self, address):
        bank = address >> 13
        value = 0
        if bank in (0x00,0x04,0x05,0x06,0x07):                        # Address >=0x0 and Address <=0x1FFF:
            return self.RAM.Read(address)
        
        elif bank == 0x01: #Address == 0x2002 or Address == 0x2004 or Address == 0x2007:
            if self.PPU.Running:
                value = self.PPU.Read(address)
            else:
                return self.PRGRAM[1, address & 0x0007]

        elif (address >=0x4000 and address <=0x4013) or address == 0x4015:
            return self.APU.Sound[address - 0x4000]
        
        elif address == 0x4016: #"Read JOY1"
            value = self.JOYPAD1.Read()

        elif address == 0x4017: #"Read JOY2 "
            value = self.JOYPAD2.Read()
            
        elif bank == 0x03: #Address == 0x6000 -0x7FFF:
            return self.MAPPER.ReadLow(address)
            
        return value  

#'=========================================='
#'           Write6502(Address,value)       '
#"   Used to write values to the 6502's mem "
#' and Mappers.                             '
#'=========================================='
    def Write6502(self,address,value):
        addr = address >> 13
        addr2 = address >> 15
        if addr == 0x00:
            'Address >=0x0 and Address <=0x1FFF:'
            self.bank0[address & 0x7FF] = value
            #self.PRGRAM[0][address & 0x7FF] = value
            #RamWrite(address,value,self.PRGRAM)
            
        elif addr == 0x01 or address == 0x4014:
            '$2000-$3FFF'
            #print "PPU Write" ,Address
            if self.PPU.Running:
                self.PPU.Write(address,value)
            else:
                PPUWrite(address,value,self.PRGRAM)
            
        elif addr == 0x02:
            '$4000-$5FFF'
            if address < 0x4100:self.WriteReg(address,value)
        
        elif addr == 0x03:#Address >= 0x6000 and Address <= 0x7FFF:
            #print 'WriteLow'
            return self.MAPPER.WriteLow(address, value)
            if NES.SpecialWrite6000 == True :
                #print 'SpecialWrite6000'
                self.MapperWrite(address, value)

            elif NES.UsesSRAM:
                if Mapper != 69:
                    self.PRGRAM[3, address & 0x1FFF] = value

        elif addr >= 0x04: #Address >=0x8000 and Address <=0xFFFF:
            self.MapperWrite(address, value)
            

                    
        else:
            print hex(Address)
            print "Write HARD bRK"

            
    def WriteReg(self,Address,value):
        addr = Address & 0xFF
        if  addr <= 0x13 or addr == 0x15:
            self.APU.Write(addr,value)
        elif addr == 0x14:
            #print 'DF: changed gameImage to bank0. This should work'
            pass
            self.PPU.SpriteRAM = self.PRGRAM[0][value * 0x100:value * 0x100 + 0x100]#self.bank0[value * 0x100:value * 0x100 + 0x100]
            print self.PPU.SpriteRAM
        elif addr == 0x16:
            pass
            self.JOYPAD1.Joypad_Count = 0x0
        elif addr == 0x17:
            pass
            self.JOYPAD2.Joypad_Count = 0x0
        else:
            print addr
    
    def MapperWrite(self,Address, value):
        #print "MapperWrite"
        if NES.newmapper_debug:
            exsound_enable =  self.MAPPER.Write(Address, value)
                
            if exsound_enable:
                self.APU.ExWrite(Address, value)
                    
        else:
            #self.consloe.MapperWrite(self.MapperWriteData)
            self.MapperWriteFlag = True
            self.MapperWriteData['Address'] = Address
            self.MapperWriteData['value'] = value
    


#@jit(forceobj=True)
def exec6502new(cpu):
        while cpu.CPURunning:

            if cpu.FrameFlag or cpu.MapperWriteFlag:
                    
                    return
                
            cpu.opcode = cpu.Read6502(cpu.PC)  #Fetch Next Operation
            cpu.PC += 1
            cpu.clockticks6502 += cpu.Ticks[cpu.opcode]

            instruction = cpu.instructions[cpu.opcode]
            '''if instruction == INS_ADC:
                #print self.opcode
                cpu.adrmode(cpu.opcode)
                ADC(cpu, None)
            else:'''
            cpu.instruction_dic.get(instruction)()

            if cpu.clockticks6502 > cpu.maxCycles1:
                cpu.Scanline()


#@jit(forceobj=True)
def Read6502(cpu, address):
        bank = address >> 13
        value = 0
        if bank == 0x00:                        # Address >=0x0 and Address <=0x1FFF:

            return cpu.bank0[address & 0x7FF]
        
        elif bank > 0x03:
            return cpu.PRGRAM[bank, address & 0x1FFF]
       
        elif bank == 0x01: #Address == 0x2002 or Address == 0x2004 or Address == 0x2007:
            if cpu.PPU.Running:
                value = cpu.PPU.Read(address)
            else:
                return cpu.PRGRAM[1, address & 0x0007]

        elif (address >=0x4000 and address <=0x4013) or address == 0x4015:
            return cpu.APU.Sound[address - 0x4000]
        
        elif address == 0x4016:
            #print "Read JOY1"
            #return 0x40
            value = cpu.JOYPAD1.Read()

        elif address == 0x4017:
            #print "Read JOY2 "
            #pass
            value = cpu.JOYPAD2.Read()
        elif bank == 0x03: #Address == 0x6000 -0x7FFF:
            return cpu.MAPPER.ReadLow(address)
            
        return value  




@jit
def PPUWrite(address,value,PRGRAM):
    addr = address & 0x0007
    PRGRAM[1,addr] = value

@jit
def PPURead(address,PRGRAM):
    #improve speed
    addr = address & 0x0007
    return PRGRAM[1,addr]

    
@jit
def a(value):
    for i in range(2):
        #value = True
        value = value & 0xFF
@jit
def a1(value):
    for i in range(2):
        #value = 1
        value = value & 0b11111111
        #value &= 0xFF

def b(value):
    for i in range(2):
        value = 1
        value = value & 0xFF

def b1(value):
    for i in range(2):
        value = 333 #& 0xFF
        value &= 0xFF

if __name__ == '__main__':
    cpu_ram = Memory()
    cpu = cpu6502()
    #cpu.testspeed()
    
    #print help(cpu)
    #print ADR_IMM
    #print cpu.adrmode_opcode(3)
    Address = 15
    #cpu.aa = 200
    list1 = [0x00,0x01,0x02,0x03,0x04,0x05,0x06,0x07,0x08,0x09,0x0A,0x0B,0x0C,0x0D,0x0E,0x0F,0x10,0x11,0x12,0x13,0x15]

    start = time.clock()
    a(Address)
    print time.clock() - start

    start = time.clock()
    a1(Address)
    print time.clock() - start

    
    start = time.clock()
    b(Address)
    print time.clock() - start

    start = time.clock()
    b1(Address)
    print time.clock() - start

    
    aa = 10
    aa <<= 1
    print bin(aa)

    aa &= 0x7
    print bin(aa)
                #break
    
        










        
