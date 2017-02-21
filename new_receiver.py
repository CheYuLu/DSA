#!/usr/bin/env python
#
# Copyright 2005,2006,2009 Free Software Foundation, Inc.
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

# /////////////////////////////////////////////////////////////////////////////
#
#    This code sets up up a virtual ethernet interface (typically gr0),
#    and relays packets between the interface and the GNU Radio PHY+MAC
#
#    What this means in plain language, is that if you've got a couple
#    of USRPs on different machines, and if you run this code on those
#    machines, you can talk between them using normal TCP/IP networking.
#
# /////////////////////////////////////////////////////////////////////////////

# interpolation = 60
# decimation = 30
from gnuradio import gr
from gnuradio import eng_notation
from gnuradio.eng_option import eng_option
from optparse import OptionParser

from gnuradio import digital

from PIL import Image

import random
import time
import datetime
import struct
import sys
import os
import itertools
import urllib2, urllib

# from current dir
from receive_path import receive_path
from transmit_path import transmit_path
from uhd_interface import uhd_receiver
from uhd_interface import uhd_transmitter
from urlparse import urlparse

#print os.getpid()
#raw_input('Attach and press enter')
rx_callback_enable = 1 
vestigial_band = 0
found_seq = 0
timer = 0
tmp = -1
freq = 0
cnt = 1000
numrec = 0
#chlist = [533e6, 545e6, 557e6, 569e6, 581e6, 593e6, 635e6, 641e6, 689e6, 695e6]
chlist = [2330e6,2350e6,2370e6]
reset = 0
payload1 = 0
returnack = 0
# /////////////////////////////////////////////////////////////////////////////
#                                   main
# /////////////////////////////////////////////////////////////////////////////
def report_time():
    return "At time "+ str(datetime.datetime.now().minute) + ":" +\
    str(datetime.datetime.now().second) + ":" + str(datetime.datetime.now().microsecond)

def time_seg():
    return str(datetime.datetime.now().minute) + " " +\
    str(datetime.datetime.now().second) + " " + str(datetime.datetime.now().microsecond)

def main():

    
    def ncycle(iterable, n): 
        for item in itertools.cycle(iterable): 
            for i in range(n): 
                yield item 

    hop_interval = 1000.0 # ms
    maxium_resend = 100
    pkt_size = 10
    seq0 = ncycle([0, 0, 0, 1, 2], 1)
    seq1 = ncycle([1, 1, 0, 1, 2, 2, 0], 1)
    seq2 = ncycle([2, 2, 2, 1, 2, 0, 0, 1], 1)
    seqs = [seq0, seq1, seq2]
    
    def rx_callback(ok, payload):
        global rx_callback_enable, cnt, numrec, returnack
        if (ok and rx_callback_enable == 1):
            #if (len(payload) >= 1):
            if (payload[0] == 'B'):
                #FreCtrl.printSpace()
                #print "Receive Beacon"#, payload
                synch.Synch(int(payload[1:]))
                returnack = 1
                myPay.getACK(synch.getRemainTime())
                tb.send_pkt(myPay)
            else:
                if 97 <= ord(payload) <= 122:
                    if ord(payload) == 122:
                        tb.send_pkt(chr(97))
                    else:
                        tb.send_pkt((payload+1))
                #FreCtrl.printSpace()
                #print "Receive Data", int(payload[1:11])
                #myPay.updatePkt(payload[1:11], payload[12:])  #save the packet to the file
                
                
                #tb.send_pkt('0+', payload)
                #tb.send_pkt('1+', payload)
                #tb.send_pkt('2+', payload)
                #tb.send_pkt('3+', payload)
                #tb.send_pkt('4+', payload)

  
    parser = OptionParser(option_class=eng_option, conflict_handler="resolve")
    expert_grp = parser.add_option_group("Expert")
    parser.add_option("","--discontinuous", action="store_true", default=False,
                      help="enable discontinuous")
    parser.add_option("","--from-file", default=None,
                      help="input file of samples to demod")
    parser = OptionParser(option_class=eng_option, conflict_handler="resolve")
    expert_grp = parser.add_option_group("Expert")
    parser.add_option("-s", "--size", type="eng_float", default=40,
                      help="set packet size [default=%default]")
    parser.add_option("-M", "--megabytes", type="eng_float", default=1.0,
                      help="set megabytes to transmit [default=%default]")
    parser.add_option("","--discontinuous", action="store_true", default=False,
                      help="enable discontinuous mode")
    parser.add_option("","--from-file", default=None,
                      help="use intput file for packet contents")
    parser.add_option("","--to-file", default=None,
                      help="Output file for modulated samples")

    receive_path.add_options(parser, expert_grp)
    uhd_receiver.add_options(parser)
    digital.ofdm_demod.add_options(parser, expert_grp)
    transmit_path.add_options(parser, expert_grp)
    digital.ofdm_mod.add_options(parser, expert_grp)
    uhd_transmitter.add_options(parser)

    (options, args) = parser.parse_args ()
    if len(args) != 0:
        parser.print_help(sys.stderr)
        sys.exit(1)

    # Attempt to enable realtime scheduling
    r = gr.enable_realtime_scheduling()
    if r == gr.RT_OK:
        realtime = True
    else:
        realtime = False
        print "Note: failed to enable realtime scheduling"

    # build the graph (PHY)
    tb = my_top_block(rx_callback, options)
   

   
    synch = Synchronize(hop_interval)
    myPay = payload_mgr('./rcvd_file/rcvd_file.bmp')
    debug = write_info('./rx_info.txt')
    FreCtrl = frequency_mgr(seqs)
    FreCtrl.check_main() #check whethetr the channel you post with the flag is in the seqs
    FreCtrl.set_frequency(tb)
    startRun = datetime.datetime.now()
    tb.start()    # Start5 executing the flow graph (runs in separate threads)


    while True:#myPay.getSize() < 60000:
        global rx_callback_enable
        rx_callback_enable = 0
        synch.startSlot = datetime.datetime.now()
        FreCtrl.printSpace()
        if (tb.rxpath.variable_function_probe_0 == 0):
            print "Primary user is absent... start..."
            rx_callback_enable = 1
            time.sleep(synch.getInterval()/1000)
        else: 
            print "Primary user is present...wait..."
            FreCtrl.set_frequency(tb)
        

    #os.system('xdg-open ./rcvd_file/rcvd_file.bmp')

    tb.wait()                       # wait for it to finish
    

# /////////////////////////////////////////////////////////////////////////////
#                             the flow graph
# /////////////////////////////////////////////////////////////////////////////

class my_top_block(gr.top_block):

    def __init__(self, callback, options):
        gr.top_block.__init__(self)

        if(options.rx_freq is not None):
            self.source = uhd_receiver(options.args,
                                       options.bandwidth,
                                       options.rx_freq, options.rx_gain,
                                       options.spec, options.antenna,
                                       options.verbose)
        elif(options.from_file is not None):
            self.source = gr.file_source(gr.sizeof_gr_complex, options.from_file)
        else:
            self.source = gr.null_source(gr.sizeof_gr_complex)

        # Set up receive path
        # do this after for any adjustments to the options that may
        # occur in the sinks (specifically the UHD sink)
        if(options.tx_freq is not None):
            self.sink = uhd_transmitter(options.args,
                                        options.bandwidth,
                                        options.tx_freq, options.tx_gain,
                                        options.spec, options.antenna,
                                        options.verbose)
        elif(options.to_file is not None):
            self.sink = gr.file_sink(gr.sizeof_gr_complex, options.to_file)
        else:
            self.sink = gr.null_sink(gr.sizeof_gr_complex)
        self.source.set_sample_rate(1500000)#rx sample rate
        self.sink.set_sample_rate(640000)
        self.rxpath = receive_path(callback, options)
        self.txpath = transmit_path(options)
        self.connect(self.source, self.rxpath)
        self.connect(self.txpath, self.sink)
        self.source.set_antenna("RX2")
        global freq
        freq = options.tx_freq# - 12e6

    def send_pkt(self, payload='', eof=False):
        self.txpath.send_pkt(payload, eof)


    def set_tx_freq(self, tx_freq):
        self.sink.set_freq(tx_freq)

    def set_rx_freq(self, rx_freq):
        self.source.set_freq(rx_freq)


# /////////////////////////////////////////////////////////////////////////////
#                           Synchronize
# /////////////////////////////////////////////////////////////////////////////            

class Synchronize:
    def __init__(self, hop_interval, returnack):
        self.returnack = returnack
        self.startSlot = 0
        self.pending = False    #it is a protection that the time interval synchronization only does from the first beacon
        self.interval = hop_interval
        self.nextInterval = hop_interval
        self.hopInterval = hop_interval

    def Synch(self, txRT):    #txRT transmitter remaning time
        '''   cannot understand
        if not self.pending:
            self.nextInterval = ( datetime.datetime.now() - self.startSlot ).microseconds/1000 + txRT
            self.pending = True
            if self.nextInterval > self.interval*1.5:
                self.nextInterval = self.nextInterval - self.interval
            if self.nextInterval < self.interval*0.5:
                self.nextInterval = self.interval + self.nextInterval
            print "Sync to B", txRT, " = set to ", self.nextInterval
        '''
        if not self.pending:
            self.nextInterval = txRT
            self.pending = True
    def getInterval(self):
        if (self.returnack == 1):
            self.interval = self.nextInterval
            self.nextInterval = self.hopInterval
            self.pending = False
            self.returnack = 0
        else:
            self.interval = self.hopInterval
        return self.interval

    def getRemainTime(self):
        return int( max(0,self.hopInterval - (datetime.datetime.now() - self.startSlot).microseconds %10e6/1000) )



# /////////////////////////////////////////////////////////////////////////////
#                           payload generator
# /////////////////////////////////////////////////////////////////////////////            
# Beacon: | B | remain time (three digit) |
# Data: | End of file | packet sequence (ten digit) | payload |
# Beacon ACK = Data ACK = | received packet sequence (ten digit) | remain time (three digit) |

class payload_mgr:

    def __init__(self, FileName ):
        self.ToFile = open(FileName,'w')
        self.ToFile.seek(0)
        self.ToFile.write('B');
        self.rcvd_seq = 0

    def getACK(self, rt):          #return ack
        strseq = str(self.rcvd_seq)
        while(len(strseq) < 10):
            strseq = '0' + strseq

        rt = str(rt)
        while(len(rt) < 3):
            rt = '0' + rt
        return strseq + rt

    def updatePkt(self, seq, payload):
        if (seq <= self.rcvd_seq):
            return 
        self.rcvd_seq = seq
        self.ToFile.write(payload)

    def getSize(self):
        return os.path.getsize('./rcvd_file/rcvd_file.bmp')   #chosen data for transmission

    def reset(self):
        self.rcvd_seq = 0

# /////////////////////////////////////////////////////////////////////////////
#                           band hopping
# /////////////////////////////////////////////////////////////////////////////               
class frequency_mgr:

    def __init__(self, seqs):
        global freq
        self.frequency = freq + random.randint(0,2)*2e7
        self.last_frequency = 0
        self.seqs = seqs
        self.statFreq = [0, 0, 0]
        self.statGuard = False
        self.seq_num = -1 #indicate invalid/undetermined main channel


    def get_seq_num(self):
        return self.seq_num

    def set_seq_num(self, num):
        self.seq_num = num
    
    def get_frequency(self):
        return self.frequency

    def set_frequency(self, tb):
        global freq
        if(self.seq_num == -1):            
            self.frequency = freq + ((self.frequency + random.randint(1,2)*2e7) - freq ) % 60e6
            self.seq_num = ((self.frequency - freq)/2e7)
        else:
            self.frequency = freq + self.seqs[int(self.seq_num)].next()*20000000
            self.last_frequency = self.frequency
        self.statGuard = False
        tb.set_tx_freq(self.frequency)
        tb.set_rx_freq(self.frequency)
        
    def query_database(self, tb):
        global chlist, reset, payload1, freq
        mydata=[('24','zero'),('26','one'),('28', 'two')]    #The first is the var name the second is the value
        mydata=urllib.urlencode(mydata)
    	path='http://140.112.175.176:6730/test3.php'    #the url you want to POST to
    	req=urllib2.Request(path, mydata)
    	req.add_header("Content-type", "application/x-www-form-urlencoded")
     	page=urllib2.urlopen(req).read()

        path1='http://140.112.175.176:6730/test2.php?cht='+ str(page)    #the url you want to POST to
        req=urllib2.Request(path1)
        req.add_header("Content-type", "application/x-www-form-urlencoded")
        page1=urllib2.urlopen(req).read()
        #if(int(str(page))==24):
        #    self.frequency = 533e6
        #elif(int(str(page))==26):
        #    self.frequency = 545e6
        #elif(int(str(page))==28):
        #    self.frequency = 557e6
        #elif(int(str(page))==30):
        #    self.frequency = 569e6
        #elif(int(str(page))==32):
        #    self.frequency = 581e6
        #elif(int(str(page))==34):
        #    self.frequency = 593e6
        #elif(int(str(page))==41):
        #    self.frequency = 635e6
        #elif(int(str(page))==42):
        #    self.frequency = 641e6
        #elif(int(str(page))==50):
        #    self.frequency = 689e6
        #elif(int(str(page))==51):
        #    self.frequency = 695e6
        if(int(str(page))==2301):
            self.frequency = 2330e6
        elif(int(str(page))==2302):
            self.frequency = 2350e6
        elif(int(str(page))==2303):
            self.frequency = 2370e6
        elif(int(str(page)) == 41):
            self.frequency == 600e6
        else:
            self.frequency = chlist[reset%3]
            reset = reset + 1
            print "there is no channel assigned by controller"
        
        if page == "41":
            print "Primary user is present"
            print "\n"
            print "========================================================"
        elif page1 == "1":
            print "Primary user is detected"
            print "\n"
            print "========================================================"
        elif page1 == '0':
            print "receiving data:"+"\t"+ chr(payload1)
            print "\n"
            print  "TX is at ", int(self.frequency/1e6),"MHz"
            print "\n"
            print "========================================================" 
        self.statGuard = False
        tb.set_tx_freq(self.frequency)
        tb.set_rx_freq(self.frequency)#+2e6)

    def updateFreq(self):
        if(not self.statGuard):
            self.statFreq[int((self.frequency - freq)/2e7)] = self.statFreq[int((self.frequency - freq)/2e7)] + 1
            self.statGuard = True

    def check_main(self):
        global freq
        if (self.seq_num == (self.frequency - freq)/20000000):
           self.seq_num = -1

    def printSpace(self):
        global freq
        a = int((self.frequency-freq)/20e6)
        for x in range(a):
            print "                                     ",

class write_info:
    def __init__(self, fileName):
        self.infoFile = open(fileName, 'w')
        self.infoFile.seek(0)
    def output(self, string):
        self.infoFile.write(string)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
