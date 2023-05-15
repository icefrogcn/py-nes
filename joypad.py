# -*- coding: UTF-8 -*-

import time
import numpy as np
import numba as nb
from numba import jit,jitclass
from numba import uint8,uint16,int32,float32
from numba.typed import Dict
from numba import types

#JOYPAD
#from nes import NES

spec = [('Joypad',uint8[:]),
        ('Joypad_Count',uint8)]

@jitclass(spec)
class JOYPAD(object):
    
    def __init__(self,debug = False):
         #self.consloe = consloe
         self.Joypad = np.full(0x8,0x40,np.uint8)
         #self.Joypad = [0x00] * 0x8
         self.Joypad_Count = 0

    @property
    def BUTTON_PRESS(self):
        return 0x41
    @property
    def BUTTON_RELEASE(self):
        return 0x40

    def A_press(self,pressed):
        self.Joypad[0] = self.BUTTON_PRESS if pressed else self.BUTTON_RELEASE
    def B_press(self,pressed):
        self.Joypad[1] = self.BUTTON_PRESS if pressed else self.BUTTON_RELEASE
    def SELECT_press(self,pressed):
        self.Joypad[2] = self.BUTTON_PRESS if pressed else self.BUTTON_RELEASE
    def START_press(self,pressed):
        self.Joypad[3] = self.BUTTON_PRESS if pressed else self.BUTTON_RELEASE
    def UP_press(self,pressed):
        self.Joypad[4] = self.BUTTON_PRESS if pressed else self.BUTTON_RELEASE
    def DOWN_press(self,pressed):
        self.Joypad[5] = self.BUTTON_PRESS if pressed else self.BUTTON_RELEASE
    def LEFT_press(self,pressed):
        self.Joypad[6] = self.BUTTON_PRESS if pressed else self.BUTTON_RELEASE
    def RIGTH_press(self,pressed):
        self.Joypad[7] = self.BUTTON_PRESS if pressed else self.BUTTON_RELEASE

    def Joypad_Count_ZERO(self):
        self.Joypad_Count = 0
    
    def Read(self):
        #print self.Joypad_Count
        '''try:
            return self.padkey.get(addr)()
        except:
            print "Invalid PPU Read - %s" %hex(addr)
            print (traceback.print_exc())
            return 0'''

        joypad_info = self.Joypad[self.Joypad_Count]
        self.Joypad_Count = (self.Joypad_Count + 1) & 7
        return joypad_info

JOYPAD_type = nb.deferred_type()
JOYPAD_type.define(JOYPAD.class_type.instance_type)


if __name__ == '__main__':
    JOYPAD = JOYPAD()











        
