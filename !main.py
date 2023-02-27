# -*- coding: UTF-8 -*-
import os

#import neshardware
from neshardware import neshardware
from rom import nesROM,get_Mapper_by_fn

ROMS_DIR = os.getcwd()+ '\\roms\\'
#ROMS_DIR = 'F:\\individual_\\Amuse\\EMU\FCSpec\\'

def roms_list():
    return [item for item in os.listdir(ROMS_DIR) if ".nes" in item.lower()]

def show_choose():
    for i,item in enumerate(roms_list()):
        print i,get_Mapper_by_fn(ROMS_DIR + item),item
    print "---------------"
    print 'choose a number as a selection.'
    
if __name__ == '__main__':
    pass
    show_choose()
    gn = input("choose a number: ")
    
    fc = neshardware()
    #fc.debug = True
    fc.ROM.LoadNES(ROMS_DIR + roms_list()[gn])
    fc.StartingUp()
    










        
