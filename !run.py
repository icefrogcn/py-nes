# -*- coding: UTF-8 -*-
import os
import cProfile

#import neshardware
from hardware import neshardware
from rom import nesROM,get_Mapper_by_fn

ROMS_DIR = os.getcwd()+ '\\roms\\'
#ROMS_DIR = 'F:\\individual_\\Amuse\\EMU\FCSpec\\'

def roms_list():
    return [item for item in os.listdir(ROMS_DIR) if ".nes" in item.lower()]

def get_roms_mapper(roms_list):
    roms_info = []
    for i,item in enumerate(roms_list):
        mapper = get_Mapper_by_fn(ROMS_DIR + item)
        #if mapper in [0,2]:
            
        roms_info.append([i,item,get_Mapper_by_fn(ROMS_DIR + item)])
    return roms_info
        
def show_choose(ROMS_INFO):
    for item in ROMS_INFO:
        print item
    print "---------------"
    print 'choose a number as a selection.'
    
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
    










        
