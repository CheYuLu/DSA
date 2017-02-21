#!/usr/bin/env python
#
# Copyright 2006,2007,2011 Free Software Foundation, Inc.
# 
# This file is part of GNU Radio
# 
# GNU Radio is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
# 
# GNU Radio is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with GNU Radio; see the file COPYING.  If not, write to
# the Free Software Foundation, Inc., 51 Franklin Street,
# Boston, MA 02110-1301, USA.
# 



# from current dir

import datetime
import time
import threading
import struct, sys
rece_ack = -1
pktno =0


class payload_mgr(threading.Thread):
    def __init__(self, lock, threadName):# FileName, maxium_resend, size, interval):
        threading.Thread.__init__(self)

        
        self.type = 0    #0:beacon, 1:data
        self.stop = 0
        self.lock = lock
        super(payload_mgr, self).__init__(name = threadName)

    def run(self):
        while 1:
            if self.stop == 0:
                if self.type == 0:
				    print "type 1"
                else:
					print "fuvking type 2"
                time.sleep(0.02)    #a cycle fo transmit and receive ack

    def resume(self):
        self.stop = 1
    def restart(self):
        self.stop = 0
# /////////////////////////////////////////////////////////////////////////////
#                                   main
# /////////////////////////////////////////////////////////////////////////////

def main(): 
    lock = threading.Lock()
    myPay = payload_mgr(lock, "thread")
    myPay.start()
    myPay.resume()
    myPay.type = 2
    myPay.restart()
    
    #while True:
        

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
