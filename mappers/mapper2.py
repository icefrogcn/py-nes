# -*- coding: UTF-8 -*-



class MAPPER():

    def __init__(self,MAPPER):
        self.cartridge = MAPPER
        self.Mapper = self.cartridge.Mapper
        print 'init sccess MAPPER ',self.cartridge.ROM_info[0]
        

    def reset(self):
        print 'self.cartridge.PROM_8K_SIZE',self.cartridge.PROM_8K_SIZE
        self.cartridge.SetPROM_32K_Bank(0, 1, self.cartridge.PROM_8K_SIZE - 2, self.cartridge.PROM_8K_SIZE - 1)

	patch = 0
            
        return 1

    
    def Write(self,addr,data):#$8000-$FFFF Memory write
        #print "MAPPER W 2"
        self.cartridge.SetPROM_16K_Bank(4, data )


if __name__ == '__main__':
    mapper = MAPPER()











        
