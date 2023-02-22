# -*- coding: UTF-8 -*-

import time
from numba import jit

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


from deco import *
from vbfun import MemCopy
         

         
from apu import APU






class cpu6502:
    CurrentLine =0 #Long 'Integer
    AddressMask =0 #Long 'Integer

    'Registers & tempregisters'
    'DF: Be careful. Anything, anywhere that uses a variable of the same name without declaring it will be using these:'

    a =0 #Byte                '累加器
    X =0 #Byte                '寄存器索引
    Y =0 #Byte                '寄存器2
    S =0 #Byte                '堆栈寄存器
    p =0 #Byte                '标志寄存器


    C_FLAG = 0x01	#	// 1: Carry
    Z_FLAG = 0x02	#	// 1: Zero
    I_FLAG = 0x04	#	// 1: Irq disabled
    D_FLAG = 0x08	#	// 1: Decimal mode flag (NES unused)
    B_FLAG = 0x10	#	// 1: Break
    R_FLAG = 0x20	#	// 1: Reserved (Always 1)
    V_FLAG = 0x40	#	// 1: Overflow
    N_FLAG = 0x80	#	// 1: Negative

    
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
    #TICKS = [0] * 0x100 # As Byte
    #addrmode = [0] * 0x100 #As Byte
    #instruction = [0] * 0x100 # As Byte
    #Ticks, instruction, addrmode = init6502()
    #gameImage = [] #As Byte

    #print TICKS, instruction, addrmode
    
    CPUPaused = False #As Boolean

    CPURunning = True
    
    addrmodeBase = 0 #As Long

    maxCycles1 = 114 # As Long 'max cycles per scanline from scanlines 0-239
    maxCycles = 0 # As Long 'max cycles until next scanline
    SmartExec = False # As Boolean
    realframes = 0 # As Long 'actual # of frames rendered
    
    bank0 = [0]*2048 #As Byte ' RAM            主工作内存
    bank6 = [0]*8192 #As Byte ' SaveRAM        记忆内存
    bank8 = [0]*8192 #As Byte '8-E are PRG-ROM.主程序
    bankA = [0]*8192 #As Byte
    bankC = [0]*8192 #As Byte
    bankE = [0] * 8192 #As Byte

        #6502中没有寄存器，故使用工作内存地址作为寄存器
    PPU_Status = 0
    PPU_Control1 = 0 # $2000
    PPU_Control2 = 0 # $2001
    PPU_Status = 0 # $2002
    SpriteAddress = 0 #As Long ' $2003
    PPUAddressHi = 0 # $2006, 1st write
    PPUAddress = 0 # $2006
    PPU_AddressIsHi = False

    VRAM = [0] * 0x4000 #3FFF #As Byte, VROM() As Byte  ' Video RAM
    SpriteRAM = [0] * 0x100 #FF# As Byte      '活动块存储器，单独的一块，不占内存

    totalFrame = 0
    
    Frames = 0



    tilebased = True


    Joypad1 = [0x40] * 8
    Joypad1_Count = 0

    apu = APU()
    
    bgBuffer = [0] * 4096 # As Long
    def __init__(self):
        self.debug = False
        self.MapperWrite = False
        self.MapperWriteData = {'Address':0,'value':0}

        self.FrameFlag = False

        
        
    def implied6502(self):
        return

    def reset6502(self):
        self.a = 0; self.X = 0; self.Y = 0; self.p = 0x22
        self.S = 0xFF
        self.PC = self.Read6502_2(0xFFFC)
        print "6502 reset:",self.status()

    def status(self):
        return self.PC,self.clockticks6502,self.PPU_Status,self.CurrentLine,"a:%d X:%d Y:%d S:%d p:%d" %(self.a,self.X,self.Y,self.S,self.p),self.opcode

    def log(self,*args):
        #print self.debug
        if self.debug:
            print args
    
    def exec6502(self):

        while self.CPURunning:
            #self.debug()
            if self.MapperWrite or self.FrameFlag:
                return
            
            self.opcode = self.Read6502(self.PC)  #Fetch Next Operation
            self.PC += 1
            self.clockticks6502 += Ticks[self.opcode]
            starttk = time.clock()
            self.exec_opcode(instruction[self.opcode])
            #print time.clock() - starttk
            #print self.clockticks6502
                
            
            if self.clockticks6502 > self.maxCycles1:
                #print "Normal: ",self.debug() ###########################
                
                self.CurrentLine = self.CurrentLine + 1
                if self.CurrentLine < 8 :
                    self.PPU_Status = self.PPU_Status & 0x3F
                if self.CurrentLine == 239 :
                    self.PPU_Status = self.PPU_Status | 0x80
                    
                if (self.PPU_Control2 & 16) != 0 and (self.PPU_Status & 64==0) and self.CurrentLine > self.SpriteRAM[0] + 8:
                    self.PPU_Status = self.PPU_Status | 64

                '''if self.tilebased:
                    h = 16 if (self.PPU_Control1 & 0x20)  else  8
                    if (self.PPU_Status & 64) == 0 :
                        if self.CurrentLine > self.SpriteRAM[0] + h :
                            self.PPU_Status = self.PPU_Status | 64'''
                        
                if self.CurrentLine >= 240:

                    if self.CurrentLine == 240 :
                        #if render :
                            #pass
                            #blitScreen()
                            #realframes = realframes + 1
                        self.Frames = self.Frames + 1
                       
                            
                        pass
                        'ensure most recent keyboard input'

            
                    self.PPU_Status = 0x80

                    #JoyPadINPUT()
                    
                    if self.CurrentLine == 240 and (self.PPU_Control1 & 0x80):
                        self.nmi6502()
                if self.CurrentLine == 262:
                    self.log("FRAME:",self.status()) ###########################
                    self.apu.updateSounds(self.Frames)
                    
                    
                    self.CurrentLine = 0
                    
                    self.PPU_Status = 0x0
                    self.FrameFlag = True
                    

                self.clockticks6502 -= self.maxCycles1




        #"DF: reordered the the case's. Made address long (was variant)."
    
    def exec_opcode(self,instruction_opcode):
        instruction_dic ={
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
        '''method = instruction_dic.get(instruction_opcode)
        if method:
            #print method
            method()
        else:'''
            
        try:
            instruction_dic.get(instruction_opcode)()
        except:
            print "Invalid opcode - %d" %instruction_opcode

    ' This is where all 6502 instructions are kept.'
    def adc6502(self):
        
        self.adrmode(self.opcode)
        self.value = self.Read6502(self.savepc)
     
        self.saveflags = self.p & 0x1
        #print "adc6502"
        self._sum = self.a
        self._sum = (self._sum + self.value) & 0xFF
        self._sum = (self._sum + self.saveflags) & 0xFF
        self.p = (self.p | 0x40) if (self._sum > 0x7F) or (self._sum < -0x80) else (self.p & 0xBF)
      
        self._sum = self.a + (self.value + self.saveflags)
        self.p = (self.p | 0x1) if (self._sum > 0xFF)  else (self.p & 0xFE)

      
        self.a = self._sum & 0xFF
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

    def adrmode(self, opcode):
        self.adrmode_opcode(addrmode[opcode])

    def adrmode_opcode(self,addrmode_opcode):
        #print ADR_ABS
        adrmode_dic ={
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
        try:
            adrmode_dic.get(addrmode_opcode)()
        except:
            print "Invalid addrmode - %d" %addrmode_opcode

    
    def indabsx6502(self):
      self.value = self.Read6502_2(self.PC) + self.X
      
      self.savepc = self.Read6502_2(self.value)


    def indx6502(self):
      #'TS: Changed PC++ & removed ' (?)
      self.value = self.Read6502(self.PC) & 0xFF
      self.value = (self.value + self.X) & 0xFF
      self.PC += 1
      self.savepc = self.Read6502_2(self.value)


    def indy6502(self):
        #'TS: Changed PC++ & == to != (If then else)
        self.value = self.Read6502(self.PC)
        self.PC += 1
      
        self.savepc = self.Read6502_2(self.value)
  
        if (Ticks[self.opcode] == 5) and (self.savepc >>8 != (self.savepc + self.Y) >> 8):
            
            self.clockticks6502 += 1
                    
            #self.clockticks6502 += 0 if self.savepc >>8 == (self.savepc + self.Y) >> 8 else 1

        self.savepc += self.Y
  
    def indzp6502(self):
        'Added pc=pc+1, & (value+1) (Why Don?)'
        self.value = self.Read6502(self.PC)
        self.PC += 1
        self.savepc = self.Read6502_2(self.value)

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
        self._help = self.Read6502_2(self.PC)
        self.savepc = self.Read6502_2(self._help)
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


    def imm6502(self):
        self.savepc = self.PC
        self.PC += 1
    def rel6502(self):
        self.savepc = self.Read6502(self.PC)
        self.PC += 1
        if (self.savepc & 0x80):
            self.savepc = self.savepc - 0x100

    
    def and6502(self):
        self.adrmode(self.opcode)
        self.value = self.Read6502(self.savepc)
        self.a &= self.value
        self.common_set_p(self.a)



    def asl6502(self):
        self.adrmode(self.opcode)
        self.value = self.Read6502(self.savepc)
  
        self.p = (self.p & 0xFE) | ((self.value >> 7) & 0x1)
        self.value = self.value << 1 & 0xFF #(self.value * 2) & 0xFF
  
        self.Write6502(self.savepc, (self.value & 0xFF))
        self.common_set_p(self.value)


    def asla6502(self):
        self.p = (self.p & 0xFE) | ((self.a >> 7) & 0x1)
        self.a = self.a << 1 & 0xFF #(self.a * 2) & 0xFF
        self.common_set_p(self.a)



    def bcc6502(self):
      if (self.p & 0x1) :
        self.PC += 1
      else:
        self.adrmode(self.opcode)
        self.PC = self.PC + self.savepc
        self.clockticks6502 += 1



    def bcs6502(self):
      if (self.p & 0x1) :
        self.adrmode(self.opcode)
        self.PC = self.PC + self.savepc
        self.clockticks6502 += 1
      else:
        self.PC += 1

    def beq6502(self):
      if (self.p & 0x2) :
        self.adrmode(self.opcode)
        self.PC = self.PC + self.savepc
        self.clockticks6502 += 1
      else:
        self.PC += 1



    def bit6502(self):
        self.adrmode(self.opcode)
        self.value = self.Read6502(self.savepc)

        self.p = (self.p & 0xFD) if (self.value & self.a)  else (self.p | 0x2)
        self.p = ((self.p & 0x3F) | (self.value & 0xC0))


    def bmi6502(self):
      if (self.p & 0x80) :
        self.adrmode(self.opcode)
        self.PC = self.PC + self.savepc
        self.clockticks6502 = self.clockticks6502 + 1
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
      self.value = self.Read6502(self.savepc)

      self.p = (self.p | 0x1) if (var + 0x100 - self.value > 0xFF) else (self.p & 0xFE)
      
      self.value = (var + 0x100 - self.value) & 0xFF

      self.common_set_p(self.value)


    def common_set_p(self, var):
        self.p = (self.p & 0xFD) if var else (self.p | 0x2)
        #print (var & 0x80)
        self.p = (self.p | 0x80) if (var & 0x80) else (self.p & 0x7F)

    def dec6502(self):
        self.adrmode(self.opcode)
        self.Write6502((self.savepc), (self.Read6502(self.savepc) - 1) & 0xFF)
          
        self.value = self.Read6502(self.savepc)
        self.common_set_p(self.value)

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
  
        self.value = self.Read6502(self.savepc)
        self.common_set_p(self.value)
        
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
        self.value = self.Read6502(self.savepc)
         
        self.p = (self.p & 0xFE) | (self.value & 0x1)
  
        self.value = (self.value // 2) & 0xFF
        self.Write6502(self.savepc, (self.value & 0xFF))
  
        self.common80_set_p(self.value)

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
        self.value = self.Read6502(self.savepc)
      
        self.p = (self.p & 0xFE) | ((self.value >> 7) & 0x1)
  
        self.value = (self.value * 2) & 0xFF
        self.value = self.value | self.saveflags
  
        self.Write6502(self.savepc, (self.value & 0xFF))
        self.common_set_p(self.value)
        
    def rola6502(self):
        self.saveflags = (self.p & 0x1)
        self.p = (self.p & 0xFE) | ((self.a  >> 7) & 0x1)
        self.a = (self.a * 2) & 0xFF
        self.a = self.a | self.saveflags
        self.common_set_p(self.a)

    def ror6502(self):
        self.saveflags = (self.p & 0x1)
        self.adrmode(self.opcode)
        self.value = self.Read6502(self.savepc)
      
        self.p = (self.p & 0xFE) | (self.value & 0x1)
        self.value = (self.value // 2) & 0xFF

        
        if (self.saveflags) :
            self.value = self.value | 0x80

        self.Write6502(self.savepc, (self.value & 0xFF))
        self.common_set_p(self.value)

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
      self.value = self.Read6502(self.savepc) ^ 0xFF
  
      self.saveflags = (self.p & 0x1)
  
      self._sum = self.a
      self._sum = (self._sum + self.value) & 0xFF
      self._sum = (self._sum + (self.saveflags * 16)) & 0xFF
      
      
      self.p = self.p | 0x40 if ((self._sum > 0x7F) | (self._sum <= -0x80)) else self.p & 0xBF

      
      self._sum = self.a + (self.value + self.saveflags)
      
      self.p = (self.p | 0x1) if (self._sum > 0xFF) else (self.p & 0xFE)

      
      self.a = self._sum & 0xFF
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





    def Read6502_2(self,Address):
        return self.Read6502(Address) + (self.Read6502(Address + 1) << 8)

    #@deco
    def Read6502(self, Address):
        if Address >=0x0 and Address <=0x1FFF:
            return self.bank0[Address & 0x7FF]
        elif Address >=0x8000 and Address <=0x9FFF:
            return self.bank8[Address - 0x8000]
        elif Address >=0xA000 and Address <=0xBFFF:
            return self.bankA[Address - 0xA000]
        elif Address >=0xC000 and Address <=0xDFFF:
            return self.bankC[Address - 0xC000]
        elif Address >=0xE000 and Address <=0xFFFF:
            return self.bankE[Address - 0xE000]
        elif Address == 0x2002:
            #print "Read PPU "
            ret = self.PPU_Status
            self.PPU_AddressIsHi = True
            self.ScrollToggle = 0
            self.PPU_Status = self.PPU_Status & 0x3F
            return ret #PPU_Status = 0
        elif Address == 0x2004:
            print "Read SpiritRAM "
        elif Address == 0x2007:
            #print "Read PPU MMC",hex(self.PPUAddress)
            if self.Mapper == 9 or self.Mapper == 10:
                print "Mapper 9 - 10"

            mmc_info = self.VRAM[self.PPUAddress & 0x3F1F - 1] if self.PPUAddress >= 0x3F20 and self.PPUAddress <= 0x3FFF else self.VRAM[self.PPUAddress - 1]

            self.PPUAddress = (self.PPUAddress + 32) if (self.PPU_Control1 & 0x4) else self.PPUAddress + 1
                
            return mmc_info
            
        elif (Address >=0x4000 and Address <=0x4013) or Address == 0x4015:
            print "Read SOUND "
            return self.apu.Sound[Address - 0x4000]
        elif Address == 0x4016:
            #print "Read JOY "
            joypad1_info = self.Joypad1[self.Joypad1_Count]
            self.Joypad1_Count = (self.Joypad1_Count + 1) & 7
            return joypad1_info
        elif Address == 0x4017:
            #print "Read Unknow "
            return 0
        elif Address == 0x6000 -0x7FFF:
            print "Read SRAM "
        else:
            print hex(Address)
            print "Read HARD bRK",self.debug() ###########################

#'=========================================='
#'           Write6502(Address,value)       '
#"   Used to write values to the 6502's mem "
#' and Mappers.                             '
#'=========================================='
    def Write6502(self,Address,value):
        
        if Address >=0x0 and Address <=0x1FFF:
            self.bank0[Address & 0x7FF] = value
        elif Address >=0x8000 and Address <=0xFFFF:
            #print Address
            self.MapperWrite = True
            self.MapperWriteData['Address'] = Address
            self.MapperWriteData['value'] = value
        elif Address == 0x2000:
            self.PPU_Control1 = value
            #print "Write PPU crl1",value
            #print self.PC,self.clockticks6502,instruction[self.opcode],"a:%d X:%d Y:%d S:%d p:%d" %(self.a,self.X,self.Y,self.S,self.p),self.opcode
        elif Address == 0x2001:
            self.PPU_Control2 = value
            #print "Write PPU crl2"
            self.EmphVal = (value & 0xE0) * 2
        elif Address == 0x2003:
            #print "Write SpriteAddress"
            self.SpriteAddress = value
        elif Address == 0x2004:
            #print "Write SpriteRAM"
            self.SpriteRAM[self.SpriteAddress] = value
            self.SpriteAddress = (self.SpriteAddress + 1) #And 0xFF
        elif Address == 0x2005:
            #print "Write PPU_AddressIsHi"
            if self.PPU_AddressIsHi :
                self.HScroll = value
                self.PPU_AddressIsHi = False
            else:
                self.vScroll = value
                self.PPU_AddressIsHi = True
        elif Address == 0x2006:
            if self.PPU_AddressIsHi :
                self.PPUAddressHi = value * 0x100
                self.PPU_AddressIsHi = False
            else:
                self.PPUAddress = self.PPUAddressHi + value
                self.PPU_AddressIsHi = True
        elif Address == 0x2007:
            #print "Write PPU_AddressIsHi"
            #'Debug.Print "PPUAddress:$" & Hex$(PPUAddress), "Value:$" & Hex$(value)
            self.PPUAddress = self.PPUAddress & 0x3FFF
            '''if Mapper == 9 or Mapper == 10 :
                if PPUAddress <= 0x1FFF :
                    if PPUAddress > 0xFFF :
                        pass
                        #MMC2_latch VRAM(PPUAddress), True
                    else:
                        pass
                        #MMC2_latch VRAM(PPUAddress), False'''
            if self.PPUAddress >= 0x3F00 and self.PPUAddress <= 0x3FFF:
                self.VRAM[self.PPUAddress & 0x3F1F] = value
               #'VRAM((PPUAddress And 0x3F1F) Or 0x10) = value  'DF: All those ref's lied. The palettes don't mirror
            else:
                if (self.PPUAddress & 0x3000) == 0x2000:
                    self.VRAM[self.PPUAddress ^ self.MirrorXor] = value
                self.VRAM[self.PPUAddress] = value
            if (self.PPU_Control1 & 0x4) :
                self.PPUAddress = self.PPUAddress + 32
            else:
                self.PPUAddress = self.PPUAddress + 1
        elif Address >= 0x4000 and Address <= 0x4013:
            #print "Sound Write"
            self.apu.Sound[Address - 0x4000] = value
            n = (Address - 0x4000) >> 2
            if n < 4 :
                self.apu.ChannelWrite[n] = True
        elif Address == 0x4014:
            #print 'DF: changed gameImage to bank0. This should work'
            MemCopy(self.SpriteRAM, 0, self.bank0, (value * 0x100), 0x100)
        elif Address == 0x4015:
            self.apu.SoundCtrl = value #'Sound(Address - 0x4000&) = value'
        elif Address == 0x4016:
            Joypad1_Count = 0x0
        elif Address == 0x4017:
            pass
        elif Address >= 0x6000 and Address <= 0x7FFF:
            if SpecialWrite6000 == True :
                pass
                #MapperWrite Address, value
            elif UsesSRAM:
                if Mapper != 69:
                    pass
                    #bank6(Address & 0x1FFF) = value
                    
        else:
            pass

    
from cpu6502instructions import *



if __name__ == '__main__':
    #cpu = cpu6502()
    
    #print help(cpu)
    #print ADR_IMM
    #print cpu.adrmode_opcode(3)
    start = time.clock()
    Address = 1345
    for i in range(1000000):
        if Address >=0x0 and Address <=0x1FFF:
            #print Address
            pass
        
        
    print time.clock() - start
    #print Address & 0x1FFF
    #print bin(Address & 0x1FFF)
    #print bin(Address)
    
    start = time.clock()
    
    for i in range(1000000):
 
        if  Address & 0x1FFF == Address:
            pass
            #print Address
        
    print time.clock() - start
    aa = 10
    aa <<= 1
    print bin(aa)

    aa &= 0x7
    print bin(aa)
                #break
    
        










        
