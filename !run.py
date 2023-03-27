# -*- coding: UTF-8 -*-
import os
import cProfile

#import neshardware
from hardware import *


    
if __name__ == '__main__':
    pass
    ROMS = roms_list()
    ROMS_INFO = get_roms_mapper(ROMS)
    while True:
        show_choose(ROMS_INFO)
        gn = input("choose a number: ")
        
        if not gn <= len(ROMS):
            continue
        fc = neshardware()
        #fc.debug = True
        fc.LoadROM(ROMS_DIR + ROMS[gn])
        fc.cpu6502.PPU.render = True
        fc.StartingUp()
    










        
