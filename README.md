# py-nes
NES(FC) Emulator in Python 2.7 + jitclass

#features
1. cpu6502 running
2. Limited graphics
3. Limited sound support
4. 1P control
5. interpreted way to implement the instructions too slow. 
6. support MAPPER in mapper...

#performance
1. CPU: 5ms / frame
2. PPU: 15~35ms / frame

need:
numba                         0.47.0
numpy                         1.16.6
opencv-python                 4.2.0.32
llvmlite                      0.31.0
python-rtmidi                 1.3.1



try:
nuitka --msvc=14.2 --module --show-progress --output-dir=out *.py