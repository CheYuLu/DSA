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
import time

import struct, sys
rece_ack = -1
waitime = 1000 #ms
pktno = 0
pktno_receive = ''
check_beacon_count =0;
class my_top_block(gr.top_block):
    def __init__(self, callback, options):
        
        gr.top_block.__init__(self)
        self.freq = options.tx_freq
        self.ch1 = 2360e6
        self.ch2 = 2380e6
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
        self.sink.set_sample_rate(640000)#rx sample rate
        self.source.set_sample_rate(1500000)
        self.rxpath = receive_path(callback, options)
        self.txpath = transmit_path(options)
        self.connect(self.source, self.rxpath)
        self.connect(self.txpath, self.sink)
    def set_tx_freq(self, tx_freq):
        self.sink.set_freq(tx_freq)

    def set_rx_freq(self, rx_freq):
        self.source.set_freq(rx_freq)

    def change_freq(self):
        self.freq =(self.freq>(self.ch1+self.ch2)/2)*self.ch1+(self.freq<(self.ch1+self.ch2)/2)*self.ch2
# /////////////////////////////////////////////////////////////////////////////
#                                   main
# /////////////////////////////////////////////////////////////////////////////

def main():
    def send_pkt(payload='', eof=False):
        return tb.txpath.send_pkt(payload, eof)
    f = open("receive_file",'w')
    global n_rcvd, n_right, check_beacon_count
        
    n_rcvd = 0
    n_right = 0
    def rx_callback(ok, payload):
        global n_rcvd, n_right, pktno, pktno_receive, check_beacon_count
        n_rcvd += 1
        #(pktno,) = struct.unpack('!H', payload[0:2])
        if ok:
            n_right += 1
        #print "ok: %r \t pktno: %d \t n_rcvd: %d \t n_right: %d" % (ok, pktno, n_rcvd, n_right)
            if payload[0] == 'B':

                check_beacon_count =0

                time.sleep(0.01)
                for i in range(0,100):   #if channel is fucking dirty, send more time, it is a know-how
                    send_pkt('A')
                waitime = float(payload[1:])
                #print " receiving beacon: "+payload[0:]
                #print "receiving beacon "
            elif payload[0] == 'D':
                print "    pkt #: " + payload[1:4] + "   packet content: " + payload[4:] + "   frequency(MHz): "+str(tb.freq/1e6)
                check_beacon_count=0
                   
                '''
                time.sleep(0.01)
                for n in range(1,4):
                    pktno_receive = pktno_receive + payload[n]

                if pktno == int(pktno_receive):
                    pktno = pktno + 1
                    f.write(payload[4:])

                for i in range(0,10):
                    send_pkt('a' + str(pktno_receive))
                    print "receiving data" + str(pktno_receive)
             
                pktno_receive = ''
               
            elif payload[0] == 'F':

                time.sleep(0.01)
                f.close()
                for i in range(0,10):
                    send_pkt('F') 
                print payload[0:]
            '''
            #printlst = list()
            #for x in payload[2:]:
            #    t = hex(ord(x)).replace('0x', '')
            #    if(len(t) == 1):
            #        t = '0' + t
            #    printlst.append(t)
            #printable = ''.join(printlst)
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
    tb = my_top_block(rx_callback, options)
    if options.from_file is None:
        if options.rx_freq is None:
            sys.stderr.write("You must specify -f FREQ or --freq FREQ\n")
            parser.print_help(sys.stderr)
            sys.exit(1)

    # build the graph(PHY)
    
    r = gr.enable_realtime_scheduling()
    if r != gr.RT_OK:
        print "Warning: failed to enable realtime scheduling"

    tb.start()                      # start flow graph

    nbytes = int(1e6 * options.megabytes)
    n = 0
    pktno = 0
    pkt_size = int(options.size)
    data1 = -1
    situation = 0
    
    while 1:
        check_beacon_count = check_beacon_count+1
        #print str(tb.freq)+" MHz"
        if (check_beacon_count > 1):
            tb.change_freq();
            tb.set_tx_freq(tb.freq)
            tb.set_rx_freq(tb.freq)
            check_beacon_count =0
            print "\n"
            print "             Dose not receive any beacons"
            print "\n"

            #myPay.
        #n += len(payload)
            #sys.stderr.write('.')
        #if options.discontinuous and pktno % 5 == 4:
        #    time.sleep(1)
        
        time.sleep(waitime/1000)
        #time.sleep(0.1)
        #check.beacon = ''
        #print "the end of the interval"    
            #pktno += 1
        
    send_pkt(eof=True)
    tb.wait()                       # wait for it to finish

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
