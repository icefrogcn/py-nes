# -*- coding: UTF-8 -*-

import time
import rtmidi
import math
import numpy as np
import numba as nb
from numba import jit,jitclass
from numba import uint8,uint16,int32,float32
from numba.typed import Dict
from numba import types

from nes import NES
from memory import Memory

#ChannelWrite = np.zeros(0x4,np.uint8)

#APU
spec = [('tones',float32[:]),
        ('volume',uint16[:]),
        ('v',uint16[:]),
        ('lastFrame',uint16[:]),
        ('ChannelWrite',uint8[:]),
        ('SoundChannel',uint8[:]),
        ('SoundOn',uint8[:]),
        #('SoundBuffer', np.dtype([('f0', 'u1'), ('f1', 'f4'), ('f2', 'u1')])[:]),
        ('Frames',uint16),
        ('Sound',uint8[:]),
        ('doSound',uint8),
        ('vlengths',uint8[:]),
        ('pow2',int32[:])]
print('loading APU CLASS')
@jitclass(spec)
class APU(object):

    def __init__(self,memory = Memory(), debug = False):
        self.tones = np.zeros(0x4,np.float32)#[0] * 4
        self.volume = np.zeros(0x4,np.uint16)#[0] * 4
        self.v = np.zeros(0x4,np.uint16)#[0] * 4
        #self.Channel = np.zeros(0x4,np.uint16)#[0] * 4
        self.lastFrame = np.zeros(0x4,np.uint16)#[0] * 4
        self.ChannelWrite = np.zeros(0x4,np.uint8)#[0] * 4

        
        self.SoundChannel = np.zeros(0x4,np.uint8)#np.zeros((0x4),dtype = "u1, f4, u1")
        self.SoundOn = np.zeros(0x4,np.uint8)#np.zeros((0x4),dtype = "u1, f4, u1")
        #self.SoundBuffer = np.zeros(0x4,np.dtype([('f0', 'u1'), ('f1', 'f4'), ('f2', 'u1')]))
        #self.tones = [0] * 4
        #self.volume = [0] * 4
        #self.lastFrame = [0] * 4
        #self.ChannelWrite = [0] * 4

        self.Frames = 0

        #self.RAM = memory.RAM
        self.Sound = memory.RAM[2][0:0x100]
        #self.Sound = [0] * 0x16 #(0 To 0x15)
        #self.SoundCtrl = self.Sound[0x15]
        
        self.doSound = 1

        self.vlengths = np.array([5, 127, 10, 1, 19, 2, 40, 3, 80, 4, 30, 5, 7, 6, 13, 7, 6, 8, 12, 9, 24, 10, 48, 11, 96, 12, 36, 13, 8, 14, 16, 15],np.uint8) # As Long

        'DF: powers of 2'
        self.pow2 = np.array([2**i for i in range(31)] + [-2147483648],np.int32) #*(31) #As Long
        #pow2 = [2**i for i in range(32)]#*(31) #As Long
        #self.pow2 +=  [-2147483648] #       pass

    #def pAPUinit(self):
    #    'Lookup table used by nester.'
        #fillArray vlengths, 
    #    self.midiout = rtmidi.MidiOut()
    #    self.available_ports = self.midiout.get_ports()
    #    print self.available_ports
        #print self.midiout.getportcount()
        
    #    if self.available_ports:
    #        self.midiout.open_port(0)
    #    else:
    #        self.midiout.open_virtual_port("My virtual output")

    #    self.midiout.send_message([0xC0,80]) #'Square wave'
    #    self.midiout.send_message([0xC1,80]) #'Square wave'
    #    self.midiout.send_message([0xC2,87]) #Triangle wave
    #    self.midiout.send_message([0xC3,127]) #Noise. Used gunshot. Poor but sometimes works.'

    @property
    def SoundCtrl(self):
        return self.Sound[0x15]
    def SoundCtrl_W(self,value):
        self.Sound[0x15] = value
    #@property
    def chk_SoundCtrl(self,ch):
        return self.SoundCtrl and self.pow2[ch]
    
    def ShutDown(self):
        if self.available_ports:
            self.midiout.close_port()

    def Write(self,Address,value):
        if Address == 0x15:
            self.SoundCtrl_W(value)
        else:
            self.Sound[Address] = value
            n = Address >> 2
            if n < 4 :
                self.ChannelWrite[n] = 1
                self.SoundChannel[n] = 1
            
                
    def ExWrite(self, addr, data):
        if addr == 0x0:
            pass
    def SoundChannel_ZERO(self,ch):
        self.SoundChannel[ch] = 0
    def SoundChannel_ONE(self,ch):
        self.SoundChannel[ch] = 1
        
    def updateSounds(self):
        #print "Playing"
        self.Frames += 1
        #print self.Sound[0:0x16]
        #print self.ChannelWrite
        if self.doSound :
            self.PlayRect(0)
            self.PlayRect(1)
            self.PlayTriangle(2)
            self.PlayNoise(3)



    def playfun(self,ch,v):
        
        if self.SoundCtrl and self.pow2[ch] :
            #volume = v #'Get volume'
            length = self.vlengths[self.Sound[ch * 4 + 3] // 8] #'Get length'
            if v > 0 :
                frequency = ((self.Sound[ch * 4 + 2] & 15) * 128) if v == 5 else (self.Sound[ch * 4 + 2] + (self.Sound[ch * 4 + 3] & 7) * 256)  #'Get frequency'
                if frequency > 1 :
                    if self.ChannelWrite[ch] : #Ensures that a note doesn't replay unless memory written
                        #print 
                        self.ChannelWrite[ch] = 0
                        self.lastFrame[ch] = self.Frames + length
                        #Tone = self.getTone(frequency)
                        #print frequency,Tone
                        self.playTone(ch, self.getTone(frequency), v)
                    
                else:
                    self.stopTone(ch)
                
            else:
                self.stopTone(ch)
            
        else:
            self.ChannelWrite[ch] = 1
            self.stopTone(ch)

        if self.Frames >= self.lastFrame[ch]:
            self.stopTone(ch)
        
    
    def PlayRect(self,ch):
        volume = self.Sound[ch * 4 + 0] & 15
        self.playfun(ch,volume)
   
    
    def PlayTriangle(self,ch):
        v = 9 #'triangle'
        self.playfun(ch,v)

    def PlayNoise(self,ch):
        v = 5 #'Noise'
        self.playfun(ch,v)


    
    def playTone(self,channel, tone, v):
        if tone <> self.tones[channel] or v < self.v[channel] - 3 or v > self.v[channel] or v == 0 :
            self.stopTone(channel)
            if self.doSound and tone <> 0 and v > 0 :
                self.v[channel] = v
                self.volume[channel] = v * 127 / 15
                self.tones[channel] = tone
                self.ToneOn(channel, tone, self.volume[channel])
        #else:
            #self.SoundChannel[channel] = 0

    def ToneOn(self, channel, tone, volume):
        #if self.available_ports :
            tone = 0 if tone < 0 else tone
            tone = 255 if tone > 255 else tone
            #note_on = [0x90 + channel, tone, volume] # channel 1, middle C, velocity 112
            self.tones[channel] = tone
            #self.SoundOn[channel] = 0x90 + channel
            #self.midiout.send_message(note_on)
            #'midiOutShortMsg mdh, &H90 Or tone * 256 Or channel Or volume * 65536'

    def ToneOff(self, channel,tone):
        #if self.available_ports :
            tone = 0 if tone < 0 else tone
            tone = 255 if tone > 255 else tone
            #note_off = [0x80 + channel, tone, 0]
            #print type(note_off),note_off
            self.tones[channel] = tone
            #self.SoundOff[channel] = 0x80 + channel
            #self.midiout.send_message(note_off)




    def stopTone(self,channel):
        if self.tones[channel] <> 0:
            self.ToneOff(channel,self.tones[channel])
            self.tones[channel] = 0
            self.v[channel] = 0
            self.volume[channel] = 0

    def getTone(self, freq): #As Long
        if freq <= 0:
            return 0
        
        freq = 65536 / freq
        t = math.log(freq / 8.176) / math.log(1.059463)
        
        t = 1 if t < 1 else t
        t = 127 if t > 127 else t

        return t

    def playtest(self,mididev):
        pass

#'Calculates a midi tone given an nes frequency.
#'Frequency passed is actual interval in 1/65536's of a second (I hope)
@jit
def getTone(freq): #As Long
        if freq <= 0:
            return 0
        
        freq = 65536 / freq
        t = math.log(freq / 8.176) / math.log(1.059463)
        
        t = 1 if t < 1 else t
        t = 127 if t > 127 else t

        return t

APU_type = nb.deferred_type()
APU_type.define(APU.class_type.instance_type)

'''
MIDI instrument list. Ripped off some website I've forgotten which

0=Acoustic Grand Piano
1=Bright Acoustic Piano
2=Electric Grand Piano
3=Honky-tonk Piano
4=Rhodes Piano
5=Chorus Piano
6=Harpsi -chord
7=Clavinet
8=Celesta
9=Glocken -spiel
10=Music Box
11=Vibra -phone
12=Marimba
13=Xylo-phone
14=Tubular Bells
15=Dulcimer
16=Hammond Organ
17=Percuss. Organ
18=Rock Organ
19=Church Organ
20=Reed Organ
21=Accordion
22=Harmonica
23=Tango Accordion
24=Acoustic Guitar (nylon)
25=Acoustic Guitar (steel)
26=Electric Guitar (jazz)
27=Electric Guitar (clean)
28=Electric Guitar (muted)
29=Overdriven Guitar
30=Distortion Guitar
31=Guitar Harmonics
32=Acoustic Bass
33=Electric Bass (finger)
34=Electric Bass (pick)
35=Fretless Bass
36=Slap Bass 1
37=Slap Bass 2
38=Synth Bass 1
39=Synth Bass 2
40=Violin
41=Viola
42=Cello
43=Contra Bass
44=Tremolo Strings
45=Pizzicato Strings
46=Orchestral Harp
47=Timpani
48=String Ensemble 1
49=String Ensemble 2
50=Synth Strings 1
51=Synth Strings 2
52=Choir Aahs
53=Voice Oohs
54=Synth Voice
55=Orchestra Hit
56=Trumpet
57=Trombone
58=Tuba
59=Muted Trumpet
60=French Horn
61=Brass Section
62=Synth Brass 1
63=Synth Brass 2
64=Soprano Sax
65=Alto Sax
66=Tenor Sax
67=Baritone Sax
68=Oboe
69=English Horn
70=Bassoon
71=Clarinet
72=Piccolo
73=Flute
74=Recorder
75=Pan Flute
76=Bottle Blow
77=Shaku
78=Whistle
79=Ocarina
80=Lead 1 (square)
81=Lead 2 (saw tooth)
82=Lead 3 (calliope lead)
83=Lead 4 (chiff lead)
84=Lead 5 (charang)
85=Lead 6 (voice)
86=Lead 7 (fifths)
87=Lead 8 (bass + lead)
88=Pad 1 (new age)
89=Pad 2 (warm)
90=Pad 3 (poly synth)
91=Pad 4 (choir)
92=Pad 5 (bowed)
93=Pad 6 (metallic)
94=Pad 7 (halo)
95=Pad 8 (sweep)
96=FX 1 (rain)
97=FX 2 (sound track)
98=FX 3 (crystal)
99=FX 4 (atmo - sphere)
100=FX 5 (bright)
101=FX 6 (goblins)
102=FX 7 (echoes)
103=FX 8 (sci-fi)
104=Sitar
105=Banjo
106=Shamisen
107=Koto
108=Kalimba
109=Bagpipe
110=Fiddle
111=Shanai
112=Tinkle Bell
113=Agogo
114=Steel Drums
115=Wood block
116=Taiko Drum
117=Melodic Tom
118=Synth Drum
119=Reverse Cymbal
120=Guitar Fret Noise
121=Breath Noise
122=Seashore
123=Bird Tweet
124=Telephone Ring
125=Helicopter
126=Applause
127=Gunshot
'''
def play_note(note, length, track, base_num=0, delay=0, velocity=1.0, channel=0):

    bpm = 125

    meta_time = 60 / bpm * 1000 # 一拍多少毫秒，一拍等于一个四分音符

    major_notes = [0, 2, 2, 1, 2, 2, 2, 1]

    base_note = 60 # C4对应的数字

    track.append(Message('note_on', note=base_note + base_num*12 + sum(major_notes[0:note]), velocity=round(64*velocity), time=round(delay*meta_time), channel=channel))

    track.append(Message('note_off', note=base_note + base_num*12 + sum(major_notes[0:note]), velocity=round(64*velocity), time=round(meta_time*length), channel=channel))
    

if __name__ == '__main__':
    apu = APU()
    print NES.pow2
    
    midiout = rtmidi.MidiOut()
    available_ports = midiout.get_ports()
    print available_ports
    if available_ports:
        midiout.open_port(0)
    else:
        midiout.open_virtual_port("My virtual output")

    note_on = [0x90, 60, 112] # channel 1, middle C, velocity 112
    note_off = [0x80, 60, 0]
    midiout.send_message([192,127])
    midiout.send_message(note_on)
    time.sleep(0.5)
    midiout.send_message(note_off)

    del midiout










        
