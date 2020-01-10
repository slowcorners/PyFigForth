"""
KBHIT.py
A Python class to implement kbhit() and getch()
  adapted by Shlomo Solomon from http://home.wlu.edu/~levys/software/kbhit.py
  NOTES- This version has been tested on LINUX, but should work on Windows too
       - the original code also had getarrow() which I deleted in this version
       - works with ASCII chars, ENTER, ESC, BACKSPACE - NOT with special keys
       - Does not work with IDLE.


>>>>> 2 ways to use in LINUX - the 2nd one is better!!
>>>>>>> 11111 >>>>>>>>>>>>>
from KBHIT import KBHit
kbd = KBHit()

Then use as follows:
    if kbd.kbhit():
        print kbd.getch()

optionally - add the following constants:
ENTER = 10
ESC = 27
BACKSPACE = 127
TAB = 9
>>>>>>>>>>>>>>>>>>>


>>>>>>> 22222 >>>>>>>>>>>>>
import KBHIT
kbd = KBHIT.KBHit()

Then use as follows:
    if kbd.kbhit():
        print kbd.getch()

the constants mentioned in the first method will be available as:
KBHIT.ENTER, etc
>>>>>>>>>>>>>>>>>>>


This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
"""

import os

if os.name == 'nt':  # Windows
    os = 'nt'
    import msvcrt
else:                # Posix (Linux, OS X)
    os = 'LINUX'
    import sys
    import termios
    import atexit
    from select import select

# special key definitions
ENTER = 10
ESC = 27
BACKSPACE = 127
TAB = 9

class KBHit:
    """ this class does the work """
    def __init__(self):
        """Creates a KBHit object to get keyboard input """

        if os == 'LINUX':
            # Save the terminal settings
            self.fd = sys.stdin.fileno()
            self.new_term = termios.tcgetattr(self.fd)
            self.old_term = termios.tcgetattr(self.fd)
    
            # New terminal setting unbuffered
            self.new_term[3] = (self.new_term[3] & ~termios.ICANON & ~termios.ECHO)
            termios.tcsetattr(self.fd, termios.TCSAFLUSH, self.new_term)
    
            # Support normal-terminal reset at exit
            atexit.register(self.set_normal_term)
    
    
    def set_normal_term(self):
        """ Resets to normal terminal.  On Windows does nothing """
        if os == 'LINUX':
            termios.tcsetattr(self.fd, termios.TCSAFLUSH, self.old_term)


    def getch(self):
        """ Returns a keyboard character after kbhit() has been called """
        if os == 'nt':
            return msvcrt.getch().decode('utf-8')
        else:
            return sys.stdin.read(1)

    def kbhit(self):
        """ Returns True if keyboard character was hit, False otherwise. """
        if os == 'nt':
            return msvcrt.kbhit()
        else:
            dr, dw, de = select([sys.stdin], [], [], 0)
            return dr != []
    
    
# Test
if __name__ == "__main__":
    """ main() tests the kbhit() and getch() functions """
    kbd = KBHit()
    print('Hit any key, or ESC to exit')

    while True:
        if kbd.kbhit():
            print("HIT "),
            char_hit = kbd.getch()
            if ord(char_hit) == ESC:
                print("ESC - ending test")
                break
            print(char_hit, ord(char_hit))
             
    kbd.set_normal_term()
