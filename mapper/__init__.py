# -*- coding: UTF-8 -*-

import sys
sys.path.append("..")

#MAPPER
from nes import NES


class MAPPER(NES):
    
    def __init__(self,PRGRAM):
        print 'init MAPPER',PRGRAM.shape
        self.PRGRAM = PRGRAM

    def reset(self):
        return self.PRGRAM

    def Write(self):#$8000-$FFFF Memory write
        print 'init Write'

    def Read(self,address):#$8000-$FFFF Memory read(Dummy)
        return NES.Read(self,address)
        '''
        addr = address >> 13
        if addr == 0x04:                      #Address >=0x8000 and Address <=0x9FFF:
            return NES.bank8[address & 0x1FFF]
        elif addr == 0x05:                      #Address >=0xA000 and Address <=0xBFFF:
            return NES.bankA[address & 0x1FFF]
        elif addr == 0x06:                      #Address >=0xC000 and Address <=0xDFFF:
            return NES.bankC[address & 0x1FFF]
        elif addr == 0x07:                      #Address >=0xE000 and Address <=0xFFFF:
            return NES.bankE[address & 0x1FFF]
'''
    def ReadLow(self,address):#$4100-$7FFF Lower Memory read
        if( address >= 0x6000 ):
	    return  NES.bank6[address & 0x1FFF]
        return addr>>8

    def WriteLow(self,addr,data): #$4100-$7FFF Lower Memory write
        #$6000-$7FFF WRAM
	if( addr >= 0x6000 ) :
	    NES.bank6[addr & 0x1FFF] = data
    
    def ExRead(self,addr): #$4018-$40FF Extention register read/write
        return 0
    
    def ExWrite(self, addr, data ):
        pass
    def Clock(self, cycle ):
        pass
    

    def SetPROM_8K_Bank(self, page, bank):

	bank %= NES.PROM_8K_SIZE
        #print 'DEBUG: NES.PROM_8K_SIZE',NES.PROM_8K_SIZE
	self.PRGRAM[page] = self.PROM[0x2000*bank:0x2000*bank+0x2000]
        '''if page == 4:
            NES.bank8 = self.PROM[0x2000*bank:0x2000*bank+0x2000]
        elif page == 5:
            NES.bankA = self.PROM[0x2000*bank:0x2000*bank+0x2000]
        elif page == 6:
            NES.bankC = self.PROM[0x2000*bank:0x2000*bank+0x2000]
        elif page == 7:
            NES.bankE = self.PROM[0x2000*bank:0x2000*bank+0x2000]'''
        
            
    def SetPROM_16K_Bank(self,page, bank):
        self.SetPROM_8K_Bank( page+0, bank*2+0 )
        self.SetPROM_8K_Bank( page+1, bank*2+1 )
        
    def SetPROM_32K_Bank0(self,bank):
        self.SetPROM_8K_Bank( 4, bank*4 + 0 )
	self.SetPROM_8K_Bank( 5, bank*4 + 1 )
	self.SetPROM_8K_Bank( 6, bank*4 + 2 )
	self.SetPROM_8K_Bank( 7, bank*4 + 3 )

    def SetPROM_32K_Bank(self,bank0,bank1,bank2,bank3):
        self.SetPROM_8K_Bank( 4, bank0 )
	self.SetPROM_8K_Bank( 5, bank1 )
	self.SetPROM_8K_Bank( 6, bank2 )
	self.SetPROM_8K_Bank( 7, bank3 )
	
    def SetVROM_8K_Bank(self,bank):
        #val1 = MaskVROM(val1, NES.VROM_8K_SIZE)
        #self.VRAM[0:0x2000] = self.VROM[bank * 0x2000 : bank * 0x2000 + 0x2000]
        for i in range(8):
	    self.SetVROM_1K_Bank( i, bank * 8 + i )

    def SetVROM_1K_Bank(self, page, bank):
        #print 'DEBUG: NES.VROM_1K_SIZE',NES.VROM_1K_SIZE,hex(len(self.VROM)),hex(len(self.VRAM))
        bank %= NES.VROM_1K_SIZE
        NES.VRAM[page*0x400:page*0x400 + 0x400] = NES.VROM[0x0400*bank:0x0400*bank + 0x400]
        #print NES.VRAM[0:100]

    def SetCRAM_1K_Bank(self, page, bank):
        print "Set CRAM"
        bank &= 0x1F
        CRAM = 32768 + 0x0400 * bank
        NES.VRAM[page*0x400:page*0x400 + 0x400] = NES.VROM[CRAM:CRAM + 0x400]

    def SetVRAM_1K_Bank(self, page, bank):
        print "Set VRAM"
        bank &= 0x3
        VRAM = 4096 + 0x0400 * bank
        NES.VRAM[page*0x400:page*0x400 + 0x400] = NES.VROM[VRAM:VRAM + 0x400]


if __name__ == '__main__':
    mapper = mapper()











        
