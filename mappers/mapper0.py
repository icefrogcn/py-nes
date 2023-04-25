# -*- coding: UTF-8 -*-


class MAPPER():

    def __init__(self,cartridge):
         self.cartridge = cartridge
         self.Mapper = self.cartridge.Mapper
         print 'init sccess MAPPER ',cartridge.Mapper


    def reset(self):
        self.cartridge.SetVROM_8K_Bank(0)
        print 'PROM_16K_SIZE',self.cartridge.PROM_16K_SIZE
        if self.cartridge.PROM_16K_SIZE == 1: # 16K only
            self.cartridge.SetPROM_16K_Bank( 4, 0 )
            self.cartridge.SetPROM_16K_Bank( 6, 0 )
            
        elif self.cartridge.PROM_16K_SIZE == 2:	#// 32K
            self.cartridge.SetPROM_32K_Bank( 0,1,2,3 )
        #print "RESET SUCCESS MAPPER ", self.Mapper







if __name__ == '__main__':
    mapper = MAPPER()











        
