#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
"""
Show all HID devices information
"""
import pywinusb.hid as hid

def encoding_hack():
    "Setup display rough unicode decoder"
    # first be kind with local encodings
    import sys
    if sys.version_info >= (3,):
        # as is, don't handle unicodes
        unicode = str
        raw_input = input
    else:
        # allow to show encoded strings
        import codecs
        sys.stdout = codecs.getwriter('mbcs')(sys.stdout)
    print_all()

def print_all():
    hid.core.show_hids()

if __name__ == '__main__':
    encoding_hack()
    print_all()

