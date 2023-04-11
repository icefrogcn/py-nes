# -*- coding: UTF-8 -*-
import sys
sys.path.append("..")



#MAPPER
from mapper import MAPPER
from mmc import MMC
from nes import NES


class MAPPER(MAPPER,MMC,NES):

    last_addr = 0
    patch = 0
    wram_patch = 0
    wram_bank = 0
    wram_count = 0

    reg = [0] * 4

    shift = 0
    regbuf = 0

    
    def __init__(self,debug = False):
         pass

    def reset(self):
        self.reg[0] = 0x0C
        #reg[1] = reg[2] = reg[3] = 0
        #shift = regbuf = 0

        if( NES.PROM_16K_SIZE < 32 ):
            
            self.SetPROM_32K_Bank(0, 1, NES.PROM_8K_SIZE-2, NES.PROM_8K_SIZE-1)
        else:
            self.SetPROM_16K_Bank( 4, 0 )
            self.SetPROM_16K_Bank( 6, 16-1 )

            self.patch = 1
            
        return 1

    
    def Write(self,addr,data):#$8000-$FFFF Memory write
        if( self.patch != 1 ):
            if((addr & 0x6000) != (self.last_addr & 0x6000)):
                self.shift = 0
                self.regbuf = 0
            self.last_addr = addr
        
        if( data & 0x80 ):
            self.shift = 0
            self.regbuf = 0
            self.reg[0] |= 0x0C
            
        if( data & 0x01 ):
            self.regbuf |= 1
            self.regbug = self.regbuf << self.shift
            
        self.shift += 1
	if( self.shift < 5 ):
		return 
	addr = (addr & 0x7FFF) >> 13
	self.reg[addr] = self.regbuf
	
        if self.patch != 1: #For Normal Cartridge
            if addr == 0:
                if( self.reg[0] & 0x02 ):
                    NES.Mirroring = 1 if( self.reg[0] & 0x01 ) else 0
                else:
                    NES.Mirroring = 3 if( self.reg[0] & 0x01 ) else 2
            elif addr == 1:
                if NES.VROM_1K_SIZE:
                    if( self.reg[0] & 0x10 ):
                        self.SetVROM_4K_Bank( 0, self.reg[1] )
                    else:
                        self.SetVROM_8K_Bank(self.reg[1] >> 1 )
            elif addr == 2:
                if NES.VROM_1K_SIZE:
                    if( self.reg[0] & 0x10 ):
                        self.SetVROM_4K_Bank(4, self.reg[2] )
                        
            elif addr == 3:
                if not (self.reg[0] & 0x08):
                    self.SetPROM_32K_Bank0( self.reg[3]>>1 )
                else:
                    if( self.reg[0] & 0x04 ):
                        self.SetPROM_16K_Bank( 4, self.reg[3] )
                        self.SetPROM_16K_Bank( 6, NES.PROM_16K_SIZE-1 )
                    else:
                        self.SetPROM_16K_Bank( 6, self.reg[3] )
                        self.SetPROM_16K_Bank( 4, 0)
        else:#For 512K/1M byte Cartridge
            PROM_BASE = 0;
            if( NES.PROM_16K_SIZE >= 32 ) :
		PROM_BASE = self.reg[1] & 0x10
	    if addr == 0:
                if( self.reg[0] & 0x02 ):
                    NES.Mirroring = 1 if( self.reg[0] & 0x01 ) else 0
                else:
                    NES.Mirroring = 3 if( self.reg[0] & 0x01 ) else 2
            if NES.VROM_1K_SIZE:
                    if( self.reg[0] & 0x10 ):
                        self.SetVROM_4K_Bank( 0, self.reg[1] )
                        self.SetVROM_4K_Bank(4, self.reg[2] )
                    else:
                        self.SetVROM_8K_Bank(self.reg[1] >> 1 )
            if(self.reg[0] & 0x08):
                if( self.reg[0] & 0x04 ):
                    self.SetPROM_16K_Bank( 4, PROM_BASE+(self.reg[3]&0x0F) )
		    if( NES.PROM_16K_SIZE >= 32 ):
                        self.SetPROM_16K_Bank( 6, PROM_BASE+16-1 )
                else:
                    self.SetPROM_16K_Bank( 6, PROM_BASE+(self.reg[3]&0x0F) );
		    if( NES.PROM_16K_SIZE >= 32 ):
                        self.SetPROM_16K_Bank( 4, PROM_BASE )
            else:
                self.SetPROM_32K_Bank0( (self.reg[3] & (0xF + PROM_BASE))>>1 )
                        
		
                        
        



if __name__ == '__main__':
    mapper = MAPPER()











        
