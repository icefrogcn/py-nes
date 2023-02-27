# -*- coding: UTF-8 -*-

import time
import math

#JOYPAD

class JOYPAD:



    
    def __init__(self,debug = False):
         self.Joypad = [0x40] * 0x8
         #self.Joypad = [0x00] * 0x8
         self.Joypad_Count = 0

    def Read(self):
        #print self.Joypad_Count
        joypad_info = self.Joypad[self.Joypad_Count]
        self.Joypad_Count = (self.Joypad_Count + 1) & 7
        return joypad_info


if __name__ == '__main__':
    JOYPAD = JOYPAD()











        
