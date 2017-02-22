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

from gnuradio import gr, blks2
from gnuradio import eng_notation
from gnuradio.eng_option import eng_option
from optparse import OptionParser

from gnuradio import digital

# from current dir
from receive_path import receive_path
from transmit_path import transmit_path
from uhd_interface import uhd_receiver
from uhd_interface import uhd_transmitter
import datetime
import time
import threading
import struct, sys
import urllib, urllib2

rece_ack = -1
pktno =0
pktno_receive = ''
# /////////////////////////////////////////////////////////////////////////////
#                           the flow graph
# /////////////////////////////////////////////////////////////////////////////     
class my_top_block(gr.top_block):
    def __init__(self, callback, options):
        gr.top_block.__init__(self)
        global pktno
        self.freq = options.tx_freq
        self.ch1 = 2360e6
        self.ch2 = 2380e6
        self.count_detect =0;
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

        # Set up receive path
        # do this after for any adjustments to the options that may
        # occur in the sinks (specifically the UHD sink)
        self.source.set_sample_rate(640000)#rx sample rate
        self.sink.set_sample_rate(1500000)
        self.rxpath = receive_path(callback, options)
        self.txpath = transmit_path(options)
        self.connect(self.source, self.rxpath)
        self.connect(self.txpath, self.sink)

    def set_tx_freq(self, tx_freq):
        self.sink.set_freq(tx_freq)

    def set_rx_freq(self, rx_freq):
        self.source.set_freq(rx_freq)

    def change_freq(self):
        #self.set_tx_freq( (self.freq>(self.ch1+self.ch2)/2)*self.ch1+(self.freq<(self.ch1+self.ch2)/2)*self.ch2 )
        #self.set_tx_freq( (self.freq>(self.ch1+self.ch2)/2)*self.ch1+(self.freq<(self.ch1+self.ch2)/2)*self.ch2 )
        self.freq =(self.freq>(self.ch1+self.ch2)/2)*self.ch1+(self.freq<(self.ch1+self.ch2)/2)*self.ch2
# /////////////////////////////////////////////////////////////////////////////
#                           payload generator and transmit
# /////////////////////////////////////////////////////////////////////////////            
# Beacon: | B | remain time (three digit) |
# Data: | End of file | packet sequence (ten digit) | payload |
class payload_mgr(threading.Thread):
    def __init__(self, tb, lock, threadName, startSlot, FileName):# FileName, maxium_resend, size, interval):
        threading.Thread.__init__(self)
        
        #self.seq = 0
        #self.rcvd_ack = 0
        #self.last_payload = ""
        #self.maxium_resend = maxium_resend
        #self.retx = 0
        #self.eof = 0
        #self.startSlot = 0
        #self.startTx = 0
        #self.hop_interval = interval
        #self.size = size
        #############################database info############################################################
        self.crowdName = "TX"
        self.longitude = 121.536498
        self.latitude = 25.019243
        self.url = 'http://140.112.175.176:6730/post.php?agent=TX&lon=121.536&lat=25.0192&';
        self.a = datetime.datetime.now()
        self.date = str(self.a.year)+'-'+str(self.a.month)+'-'+str(self.a.day);
        self.timeArray = time.strptime(str(self.a), "%Y-%m-%d %H:%M:%S.%f")
        self.timeStamp = int(time.mktime(self.timeArray))
        #rssi = tb.rxpath.probe.level()
        self.tUrl = self.url + '&data_date='+self.date+'&data_datetime='+str(self.timeStamp)+'&createtime='+str(self.timeStamp)+'&cht=';
        ######################################################################################################
        self.frequency = tb.freq
        self.alpha = 97
        self.stop = 0
        self.type = 0    #0:beacon, 1:data
        self.hop_interval = 500
        self.startSlot = startSlot
        self.tb = tb
        self.lock = lock
        self.feature_detect = 0
        super(payload_mgr, self).__init__(name = threadName)
        self.count = 0
        self.feature_count = 0

    def query_database(self):
        
        mydata=[('24','zero'),('26','one'),('28', 'two')]    #The first is the var name the second is the value
        mydata=urllib.urlencode(mydata)
        path='http://140.112.175.176:6730/test3.php'    #the url you want to POST to
        req=urllib2.Request(path, mydata)
        req.add_header("Content-type", "application/x-www-form-urlencoded")
        page=urllib2.urlopen(req).read()

        if(int(str(page))==2301):
            self.frequency = 2330e6#freq + 20e6
            sendpayload = 1
        elif(int(str(page))==2302):
            self.frequency = 2350e6#freq + 20e6
            sendpayload = 1
        elif(int(str(page))==2303):
            self.frequency = 2370e6#freq + 20e6
            sendpayload = 1
        elif(int(str(page)) == 41):
            self.frequency == 600e6

        if page == "41":
            print "Primary user is present"
            print "\n"
            print "========================================================"

        self.tb.set_tx_freq(self.frequency)
        self.tb.set_rx_freq(self.frequency)
        #print "freq:"+ str(self.frequency)

    def notification_for_primary(self, primary_exist):
        if self.frequency < 600e6:
            cha = 2*(self.frequency - 533e6)/12e6 + 24
        elif (self.frequency<650e6):
            cha = (self.frequency - 635e6)/6e6 + 41
        elif (self.frequency<699e6):
            cha = (self.frequency - 689e6)/6e6 + 50
        else:
            cha = (self.frequency - 2330e6)/20e6 + 2301

        if primary_exist == 0:
            response = urllib2.urlopen(self.tUrl+str(int(cha))+'&status='+str(0)+'&remark='+str(1111))
            #print "Primary user is absent... start..."
        else:
            response = urllib2.urlopen(self.tUrl+str(int(cha))+'&status='+str(1)+'&remark='+str(1111))
            print "Primary user is present... start..."

    def reset(self):    #parameter for the new timeslot
    	self.type = 0
    def pause(self):
        self.stop = 1

    def restart(self):
    	self.stop = 0

    def run(self):
        global pktno
        while 1:
            self.feature_detect = self.tb.rxpath.get_variable_function_probe_0()

            if self.frequency/1e6 != 600:
                if self.stop == 0:
       
                    if self.type == 0:
                        payload = 'B' + self.get_syncBeacon()
                        self.tb.txpath.send_pkt(payload)
                        #print "transmitting beacon" + payload + "   "+ str(self.tb.freq)
                    else:
                        payload = 'D' + self.getPayload() + chr(self.alpha)
                        self.tb.txpath.send_pkt(payload)
                        if (self.alpha == 122):
                            self.alpha = 97
                        elif (97 <= self.alpha <= 121):
                            self.alpha = self.alpha + 1
                        print "    pkt #: " + payload[1:4] + "   packet content: " + payload[4:] + "   frequency(MHz): " + str(self.frequency/1e6)
                    time.sleep(0.05)    #a cycle fo transmit and receive ack 

    def get_syncBeacon(self):
        rt = str(abs(self.getRemainTime()))
        while(len(rt) < 3):
            rt = '0' + rt
        return rt
    
    def getPayload(self):
        global pktno
        
        if pktno == 999:
            pktno = 0
        else:	
            pktno = pktno + 1     #up to 999 -> 3 bytes for sting
        pktno_str=''
        for i in range(0, 3-len(str(pktno))):
            pktno_str = '0' + pktno_str
        return pktno_str + str(pktno)

       
   
    def getRemainTime(self):
        return int( self.hop_interval - (datetime.datetime.now() - self.startSlot).microseconds %10e6/1000 ) #minisecond



# /////////////////////////////////////////////////////////////////////////////
#                                   main
# /////////////////////////////////////////////////////////////////////////////

def main():

    def rx_callback(ok, payload):
       
        global pktno, pktno_receive
        
        if ok:
            
            #if payload[0] == 'B':
            #    print '\t'+"receiving beacon" + payload[0:]

            if payload[0] == 'A':    #ack from beacon

                myPay.pause()
                myPay.type = 1
                myPay.restart()
                #print '\t'+"receiving ack from beacon"
            '''
            elif payload[0] == 'a':    #ack from data
                myPay.pause()

                for n in range(1,4):
                    pktno_receive = pktno_receive + payload[n]

                if pktno == int(pktno_receive):
                    myPay.retry = 0
                else:
                    myPay.retry = 1

                myPay.restart()
                print '\t'+"receiving ack from data" + payload[1:4]
            elif payload[0] == 'F':
            	print "missino completed"
            '''
            #print "\n"
    
        
    parser = OptionParser(option_class=eng_option, conflict_handler="resolve")
    expert_grp = parser.add_option_group("Expert")
    parser.add_option("","--discontinuous", action="store_true", default=True,
                      help="enable discontinuous")
    parser.add_option("-M", "--megabytes", type="eng_float", default=1.0,
                      help="set megabytes to transmit [default=%default]")
    parser.add_option("","--from-file", default=None,
                      help="input file of samples to demod")
    parser.add_option("-s", "--size", type="eng_float", default=400,
                      help="set packet size [default=%default]")

    receive_path.add_options(parser, expert_grp)
    uhd_receiver.add_options(parser)
    digital.ofdm_demod.add_options(parser, expert_grp)
    transmit_path.add_options(parser, expert_grp)
    digital.ofdm_mod.add_options(parser, expert_grp)
    uhd_transmitter.add_options(parser)

    (options, args) = parser.parse_args ()

    if options.from_file is None:
        if options.rx_freq is None:
            sys.stderr.write("You must specify -f FREQ or --freq FREQ\n")
            parser.print_help(sys.stderr)
            sys.exit(1)

    # build the graph(PHY)
    tb = my_top_block(rx_callback, options)
    lock = threading.Lock()
    myPay = payload_mgr(tb, lock, "thread", datetime.datetime.now(), "source_file")
    myPay.start()
        
    r = gr.enable_realtime_scheduling()
    if r != gr.RT_OK:
        print "Warning: failed to enable realtime scheduling"

    tb.start()                      # start flow graph

    while True:
        #???bout.waitime = -1
        #global rx_callback_enable, trans_status, get_ack, randombackoff, ttRB, difscount, DIFS
        #trans_status = 0   #at the new frame, start with a beacon 
        #rx_callback_enable = 0
        time.sleep(0.499)
        myPay.query_database()
        myPay.pause()
        time.sleep(0.001)
        detection = myPay.feature_detect
        myPay.reset()
        myPay.notification_for_primary(detection)
        myPay.pause()
        myPay.reset()
        myPay.startSlot = datetime.datetime.now()
        myPay.restart()

        #??? time.sleep(0.010) #wait 10ms to detect
        #??? FreCtrl.printSpace() feel that is not necessary
        #print "ack status=", get_ack
        #if (tb.rxpath.variable_function_probe_0 == 0):          #frequency assigned by controller
        #    print "TV is absent... start..."
            #???bout.set_waitime()
        #    rx_callback_enable = 1    #the right timing to receive
        #time.sleep(hop_interval/1000)
        #else: 
        #    print "TV is present...wait..."
        #    FreCtrl.set_frequency(tb)
        #???rx_callback_enable = not bool(tb.rxpath.variable_function_probe_0)
    '''
    nbytes = int(1e6 * options.megabytes)
    n = 0
    pktno = 0
    pkt_size = int(options.size)
    data1 = 97
    
    print pkt_size
    while n < nbytes:
        if options.from_file is None:
            data = (pkt_size - 2) * chr(pktno & 0xff) 
        else:
            data = source_file.read(pkt_size - 2)
            if data == '':
                break;

        payload = struct.pack('!H', pktno & 0xffff) + chr(data1)
        print "sending" + chr(data1)
        send_pkt(payload)
        data1 = data1 + 1
        if data1 == 123:
            data1 = 97
        #n += len(payload)
        sys.stderr.write('.')
        #time.sleep(1)
        #if options.discontinuous and pktno % 5 == 4:
        #    time.sleep(1)
        pktno += 1
    '''
    send_pkt(eof=True)
    #tb.wait()                       # wait for it to finish

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
