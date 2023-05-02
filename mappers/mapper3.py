# -*- coding: UTF-8 -*-




class MAPPER():

    def __init__(self,MAPPER):
        self.cartridge = MAPPER
        self.Mapper = self.cartridge.Mapper
        print 'init sccess MAPPER ',self.Mapper

    def reset(self):
        self.cartridge.SetVROM_8K_Bank(0)
        if self.cartridge.ROM.PROM_16K_SIZE == 1: # 16K only
            self.cartridge.SetPROM_16K_Bank( 4, 0 )
            self.cartridge.SetPROM_16K_Bank( 6, 0 )
            
        elif self.cartridge.ROM.PROM_16K_SIZE == 2:	#// 32K
            self.cartridge.SetPROM_32K_Bank( 0,1,2,3 )

        
        return 1

    def Write(self,addr,data):
        print "Mapper Write",hex(Address),value
        self.cartridge.SetVROM_8K_Bank( data & (data -1) )

    def WriteLow(self,address,data): #$4100-$7FFF Lower Memory write
        self.cartridge.WriteLow(address,data)




if __name__ == '__main__':
    mapper = MAPPER()











        
