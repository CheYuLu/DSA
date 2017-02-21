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

import random
import time
import datetime
import struct
import sys
import os
import itertools
import xlwt
import urllib2, urllib

# from current dir
from receive_path import receive_path
from transmit_path import transmit_path
from uhd_interface import uhd_receiver
from uhd_interface import uhd_transmitter

#print os.getpid()
#raw_input('Attach and press enter')
rx_callback_enable = 1 
vestigial_band = 0
found_seq = 0
timer = 0
tmp = -1
freq = 0
trans_status = 0 #beacon:0    data:1
get_ack = 0
ackcheck = 0
reset = 0
t1 = 0
t2 = 0
sb = 0
sd = 0
randombackoff = 0
ttRB = 0
difscount = 0
DIFS = 0.004
available1 = 0
available2 = 0
#...................... for test........
payload_test = 97
rece_ack = 0
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
    pkt_size = 100
    seq0 = ncycle([0, 0, 0, 1, 2], 1)
    seq1 = ncycle([1, 1, 0, 1, 2, 2, 0], 1)
    seq2 = ncycle([2, 2, 2, 1, 2, 0, 0, 1], 1)
    seqs = [seq0, seq1, seq2]
    
    def rx_callback(ok, ack):
        global rx_callback_enable
        global trans_status
        global get_ack
        global t1,t2
        global rece_ack
        if (ok and rx_callback_enable == 1):
            try:
                if 97 <= ord(ack) <= 122:
                    rece_ack = ord(ack)
            except:
                pass
            trans_status = 1
            
            
            
               
        '''
        if (ok and rx_callback_enable == 1):
            #print "Receiving ACK ", ack[0:10], report_time()
            #if (ack[5] == '0'):
            #    debug.output('A'+ack[7:10]+' '+time_seg()+'\n')
            #elif (ack[5] == '1'):
            #    debug.output('D'+ack[7:10]+' '+time_seg()+'\n')
            #???bout.waitime = -1
            myPay.updateACK(int(ack[0:10]), int(ack[10:]))    #modifiy the packet size in term of the remaning time
            line = myPay.getPayload()
            FreCtrl.updateFreq()
            get_ack = 1           #receive ack or not

            if line:          #receive ack of data from RX
                trans_status = 1
                line = myPay.wrapper(line)
                FreCtrl.printSpace()
                print "Data#", int(line[1:11])#, " ", " size = ", len(line)#, report_time()
                #print "carrier sense level ", tb.carrier_level(), " over threshold", tb.carrier_threshold()
                #tb.send_pkt(line)
                #time.sleep(0.01)             #time for TX turn to RX
                #tb.send_pkt(line)
                #t3 = datetime.datetime.now()#.microsecond
                #print "TT == ", t3-t2
            #???bout.waitime = datetime.datetime.now()
        '''
    #def tcpb():
    #    global trans_status, t1, t2, sb, sd, available1, available2
    #    if trans_status == 0:
    #        payload = myPay.get_syncBeacon()
            #debug.output(payload + ' ' + time_seg()+'\n')
    #       tb.send_pkt(payload)
    #        sb += 1        #total times of sending
    #    else:
    #        line = myPay.getPayload()
    #        line = myPay.wrapper(line)
    #        FreCtrl.printSpace()
    #        tb.send_pkt(line)
    #        sb += 1
        #??? print sb
  
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


    
    myPay = payload_mgr('./send_file/send_file', maxium_resend, pkt_size, hop_interval)
    debug = write_info('./tx_info.txt')
    FreCtrl = frequency_mgr(seqs)
    FreCtrl.check_main() #check whethetr the channel you post with the flag is in the seqs
    FreCtrl.set_frequency(tb)
    bout = time_out()    #it is a thread for sending packet
    startRun = datetime.datetime.now()
    tb.start()    # Starts executing the flow graph (runs in separate threads)


    while True:
        #???bout.waitime = -1
        global rx_callback_enable, trans_status, get_ack, randombackoff, ttRB, difscount, DIFS
        trans_status = 0   #at the new frame, start with a beacon 
        rx_callback_enable = 0
        myPay.startSlot = datetime.datetime.now()
        #??? time.sleep(0.010) #wait 10ms to detect
        #??? FreCtrl.printSpace() feel that is not necessary
        #print "ack status=", get_ack
        if (tb.rxpath.variable_function_probe_0 == 0):          #frequency assigned by controller
            print "TV is absent... start..."
            #???bout.set_waitime()
            rx_callback_enable = 1    #the right timing to receive
            time.sleep(hop_interval/1000)
        else: 
            print "TV is present...wait..."
            FreCtrl.set_frequency(tb)
        #???rx_callback_enable = not bool(tb.rxpath.variable_function_probe_0)
        
        

    tb.wait()     # wait for it to finish
    

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
        self.source.set_sample_rate(640000)#rx sample rate
        self.sink.set_sample_rate(1500000)
        self.rxpath = receive_path(callback, options)
        self.txpath = transmit_path(options)
        self.connect(self.source, self.rxpath)
        self.connect(self.txpath, self.sink)
        self.source.set_antenna("RX2")       #set the receive antenna
        # it is the init frequency from the flag
        global freq
        freq = options.tx_freq# - 12e6

    def send_pkt(self, payload='', eof=False):
        self.txpath.send_pkt(payload, eof)


    def set_tx_freq(self, tx_freq):
        self.sink.set_freq(tx_freq)

    def set_rx_freq(self, rx_freq):
        self.source.set_freq(rx_freq)


# /////////////////////////////////////////////////////////////////////////////
#                           Time Out
# /////////////////////////////////////////////////////////////////////////////            

class time_out(gr.gr_threading.Thread):
    def __init__(self, todo):
        global send_only_once
        gr.gr_threading.Thread.__init__(self)
        self.ishalf = False
        self.waitime = -1
        self.todo = todo
        self.start()

    def set_waitime(self):
        self.todo()
        self.waitime = datetime.datetime.now()

    def run(self):
        while True:
            global trans_status, t1, t2, sb, sd, available1, available2, rece_ack
            ''' 
            if trans_status == 0:
                payload = myPay.get_syncBeacon()
                #debug.output(payload + ' ' + time_seg()+'\n')
                tb.send_pkt(payload)
                sb += 1        #total times of sending
            else:
                line = myPay.getPayload()
                line = myPay.wrapper(line)
                FreCtrl.printSpace()
                tb.send_pkt(line)
                sb += 1
                #??? print sb
            '''
            if trans_status == 0:
                payload = myPay.get_syncBeacon()
                tb.send_pkt(payload)
            else:
                if ((rece_ack - 1) == payload_test):
                    payload_test = rece_ack
                    tb.send_pkt(chr(payload_test))
                else:
                    tb.send_pkt(chr(payload_test))
            #???if ( self.waitime != -1 and (datetime.datetime.now() - self.waitime ).microseconds % 1e6 > 50000):               
            #???    self.set_waitime()
            time.sleep(0.0001) #counter may do the job also, stop for listen.


# /////////////////////////////////////////////////////////////////////////////
#                           payload generator
# /////////////////////////////////////////////////////////////////////////////            
# Beacon: | B | remain time (three digit) |
# Data: | End of file | packet sequence (ten digit) | payload |

class payload_mgr:

    def __init__(self, FileName, maxium_resend, size, interval):
        self.SrcFile = open(FileName,'r')
        self.SrcFile.seek(0)
        self.pktsize = size
        self.seq = 0
        self.rcvd_ack = 0
        self.last_payload = ""
        self.maxium_resend = maxium_resend
        self.retx = 0
        self.eof = 0
        self.startSlot = 0
        self.startTx = 0
        self.hop_interval = interval
        self.size = size

    def get_syncBeacon(self):
        rt = str(abs(self.getRemainTime()))
        while(len(rt) < 3):
            rt = '0' + rt
        return "B"+rt

    def getPayload(self):
        #print "current seq:", self.seq, "receive seq:", self.rcvd_ack
        if(self.seq == 0):
            self.startTx = datetime.datetime.now().second*1e6 + datetime.datetime.now().microsecond
        elif(self.seq == self.retx and self.eof == 1):
           self.reset()
        if(self.seq != self.rcvd_ack and self.retx <= self.maxium_resend):
           self.retx = self.retx + 1
           self.SrcFile.seek(self.SrcFile.tell() - (self.pktsize - self.size))
           #print "( retransmit : ",self.pktsize - self.size,")"
           self.last_payload = self.last_payload[0:self.size] + self.SrcFile.read(max(self.size - len(self.last_payload), 0))
           return self.last_payload

        self.last_payload = self.SrcFile.read(self.size) 
        self.seq = self.seq + 1
        self.retx = 0
        return self.last_payload

    def wrapper(self, payload):
        strseq = str(self.seq)
        while(len(strseq) < 10):
            strseq = '0' + strseq
        if (self.SrcFile.read(1) == ''):
            self.eof = 1
            return '1' + strseq + payload
        else:
            self.SrcFile.seek(self.SrcFile.tell() - 1)
            return '0' + strseq + payload

    def updateACK(self, pktn, remainTime):
        self.rcvd_ack = pktn
        if(remainTime < 16):
           self.size = int(4*remainTime^2)
        else:
           self.size = self.pktsize # 1000

    def reset(self):
        self.eof = 0
        self.seq = 0
        self.rcvdACK = 0
        now = datetime.datetime.now().minute*60*1e6 + datetime.datetime.now().second*1e6 + datetime.datetime.now().microsecond
        print "start: ", self.startTx, " - ", now 
        print "===============end of file ", (now - self.startTx), " us )==================="

    def getRemainTime(self):
        return int( self.hop_interval - (datetime.datetime.now() - self.startSlot).microseconds %10e6/1000 )

# /////////////////////////////////////////////////////////////////////////////
#                           band hopping
# /////////////////////////////////////////////////////////////////////////////               
class frequency_mgr:

    def __init__(self, seqs):
        global freq
        self.frequency = freq + random.randint(0,2)*12e6
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
        #...................this one is from multi_tx....
        global freq
        if(self.seq_num == -1):            
            self.frequency = freq + ((self.frequency + random.randint(1,2)*2e7) - freq ) % 60e6
            self.seq_num = ((self.frequency - freq)/2e7)
        else:
            self.frequency = freq + self.seqs[int(self.seq_num)].next()*20000000
            self.last_frequency = self.frequency
        self.frequency = freq
        print "\n"
        self.printSpace()
        print  "========== TX at ", int(self.frequency/1e6),"MHz ==========" 
        self.statGuard = False
        tb.set_tx_freq(self.frequency)
        tb.set_rx_freq(self.frequency)
        #..............................................
    def query_database(self, tb):
        global freq, ackcheck, dbcheck, reset
        crowdName = "TX"
        longitude = 121.536498
        latitude = 25.019243
        url = 'http://140.112.175.176:6730/post.php?agent=TX&lon=121.536&lat=25.0192&';
        a = datetime.datetime.now()
        date = str(a.year)+'-'+str(a.month)+'-'+str(a.day);
        timeArray = time.strptime(str(a), "%Y-%m-%d %H:%M:%S.%f")
        timeStamp = int(time.mktime(timeArray))
        rssi = tb.rxpath.probe.level()
        tUrl = url + '&data_date='+date+'&data_datetime='+str(timeStamp)+'&createtime='+str(timeStamp)+'&cht=';
        if(tb.rxpath.variable_function_probe_0 == 0):            #primary user is available
            if(ackcheck==0):
                mydata=[('24','zero'),('26','one'),('28', 'two')]    #The first is the var name the second is the value
                mydata=urllib.urlencode(mydata)
    	        path='http://140.112.175.176:6730/test.php'    #the url you want to POST to
    	        req=urllib2.Request(path, mydata)
    	        req.add_header("Content-type", "application/x-www-form-urlencoded")
     	        page=urllib2.urlopen(req).read()
                if(int(str(page))==24):
                    self.frequency = freq - 12e6
                elif(int(str(page))==26):
                    self.frequency = freq 
                elif(int(str(page))==28):
                    self.frequency = freq + 12e6
                else:
                    self.frequency = freq - 12e6 + (reset%3)*12e6
                    reset = reset + 1
                cha = 2*(self.frequency - freq + 12e6)/12e6 + 24
                response = urllib2.urlopen(tUrl+str(int(cha))+'&status='+str(0))
            else:
                cha = 2*(self.last_frequency - freq + 12e6)/12e6 + 24
                #print str(cha)
                response = urllib2.urlopen(tUrl+str(int(cha))+'&status='+str(0))
                self.frequency = self.last_frequency
        else:
            cha = 2*(self.frequency - freq + 12e6)/12e6 + 24
            response = urllib2.urlopen(tUrl+str(int(cha))+'&status='+str(1))
            mydata=[('24','zero'),('26','one'),('28', 'two')]    #The first is the var name the second is the value
    	    mydata=urllib.urlencode(mydata)
    	    path='http://140.112.175.176:6730/test.php'    #the url you want to POST to
    	    req=urllib2.Request(path, mydata)
    	    req.add_header("Content-type", "application/x-www-form-urlencoded")
     	    page=urllib2.urlopen(req).read()
            if(int(str(page))==24):
                self.frequency = freq - 12e6
            elif(int(str(page))==26):
                self.frequency = freq 
            elif(int(str(page))==28):
                self.frequency = freq + 12e6
            else:
                self.frequency = freq - 12e6 + (reset%3)*12e6
                reset = reset + 1
            self.last_frequency = self.frequency
            ackcheck=1
        #self.frequency = freq

        print "\n"
        self.printSpace()
        print  "========== TX at ", int(self.frequency/1e6),"MHz ==========" 
        self.statGuard = False
        tb.set_tx_freq(self.frequency)#+2e6)
        tb.set_rx_freq(self.frequency)
    def updateFreq(self):
        if(not self.statGuard):
            self.statFreq[int((self.frequency - freq)/12e6)] = self.statFreq[int((self.frequency - freq)/12e6)] + 1
            self.statGuard = True

    def check_main(self):
        global freq
        if (self.seq_num == (self.frequency - freq)/12000000):
           self.seq_num = -1

    def printSpace(self):
        global freq
        a = int((self.frequency-freq)/12e6)
        for x in range(a):
            print "                                 ",
  
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
