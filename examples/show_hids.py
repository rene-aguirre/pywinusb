#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
"""
Show all HID devices' information

Written By Rene Aguirre (https://github.com/rene-aguirre) ~2016
Updated by Gabriel Staples (https://www.ElectricRCAircraftGuy.com) 2 Feb 2017 
-added "User selection" and this_script_dir_path stuff to allow writing output to a file in the same
 dir as this python script, instead of just to the sys.stdout command prompt 
"""

#User selection:
PRINT_TO_FILE = True #set to True to print to a file in the same directory as this script, or False to print to the sys.stdout command prompt 

#Find directory of this python file  
#See: http://stackoverflow.com/a/5137509/4561887
#-this is necessary to force the file we will open below to open in the same directory as this 
# python script, NOT in the Present Working Directory where you are when you run the script 
import os 
this_script_dir_path = os.path.dirname(os.path.realpath(__file__))

#-------------------------------------------------------------------------
#Show all HID devices' information 
#-------------------------------------------------------------------------
import sys
import pywinusb.hid as hid

if __name__ == '__main__':
    if sys.version_info < (3,):
        import codecs
        output = codecs.getwriter('mbcs')(sys.stdout)
    else:
        # python3, you have to deal with encodings, try redirecting to any file
        if (PRINT_TO_FILE):
            output = open(this_script_dir_path + '\show_hids_RESULTS.txt', 'w')
        else:
            output = sys.stdout
    try:
        hid.core.show_hids(output = output)
    except UnicodeEncodeError:
        print("\nError: Can't manage encodings on terminal, try to run the script on PyScripter or IDLE")

