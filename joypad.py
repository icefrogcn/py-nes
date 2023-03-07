# -*- coding: UTF-8 -*-

import time
import math

import keyboard
#JOYPAD
from nes import NES

class JOYPAD(NES):
    
    def __init__(self,debug = False):
         self.Joypad = [0x40] * 0x8
         #self.Joypad = [0x00] * 0x8
         self.Joypad_Count = 0
         self.padkey ={
             'enter':3,         #St
             '0':self.turnoff,
             }

    def Read(self):
        #print self.Joypad_Count
        '''try:
            return self.padkey.get(addr)()
        except:
            print "Invalid PPU Read - %s" %hex(addr)
            print (traceback.print_exc())
            return 0'''
        if keyboard.is_pressed('enter'):
            print "press"
            self.Joypad[3] = 0x41
        else:
            pass
            self.Joypad[3] = 0x40

        if keyboard.is_pressed('0'):
            print "turnoff"
            self.turnoff()


        joypad_info = self.Joypad[self.Joypad_Count]
        self.Joypad_Count = (self.Joypad_Count + 1) & 7
        return joypad_info

    def turnoff(self):
        NES.CPURunning = False
if __name__ == '__main__':
    JOYPAD = JOYPAD()











        
