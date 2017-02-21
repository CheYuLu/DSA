#
# Copyright 2005,2006,2011 Free Software Foundation, Inc.
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
execfile("/home/george/.grc_gnuradio/featuredetect.py")
from gnuradio import gr
from gnuradio import eng_notation
from gnuradio import digital
from gnuradio.filter import firdes
import copy
import sys
import threading
import time

# /////////////////////////////////////////////////////////////////////////////
#                              receive path
# /////////////////////////////////////////////////////////////////////////////

class receive_path(gr.hier_block2):
    def __init__(self, rx_callback, options):

	gr.hier_block2.__init__(self, "receive_path",
				gr.io_signature(1, 1, gr.sizeof_gr_complex),
				gr.io_signature(1, 1, gr.sizeof_float*1))


        options = copy.copy(options)    # make a copy so we can destructively modify

        self._verbose     = options.verbose
        self._log         = options.log
        self._rx_callback = rx_callback      # this callback is fired when there's a packet available
        self.variable_function_probe_0 = variable_function_probe_0 = 0
        #self.samp_rate = samp_rate = 640000
        self.blocks_probe_signal_x_0 = blocks.probe_signal_f()
        def _variable_function_probe_0_probe():
            while True:
                val = self.blocks_probe_signal_x_0.level()
                try: self.set_variable_function_probe_0(val)
                except AttributeError, e: pass
                time.sleep(1.0/(1000000))
        _variable_function_probe_0_thread = threading.Thread(target=_variable_function_probe_0_probe)
        _variable_function_probe_0_thread.daemon = True
        _variable_function_probe_0_thread.start()
        self.featuredetect_0 = featuredetect(
            collectingtime=1,
        )

        # receiver
        self.ofdm_rx = digital.ofdm_demod(options,
                                          callback=self._rx_callback)

        # Carrier Sensing Blocks
        alpha = 1 # the time interval of collecting data
        thresh = 30   # in dB, will have to adjust
        self.probe = analog.probe_avg_mag_sqrd_c(thresh,alpha)
        self.csprobe = analog.probe_avg_mag_sqrd_c(25, alpha)

        self.connect((self, 0), self.ofdm_rx)
        self.connect(self.ofdm_rx, self.probe)
        self.connect((self, 0), (self.featuredetect_0, 0))
        self.connect((self.featuredetect_0, 0), (self.blocks_probe_signal_x_0, 0))
        self.connect((self.featuredetect_0, 0), (self, 0))

        # Display some information about the setup
        if self._verbose:
            self._print_verbage()

    def get_variable_function_probe_0(self):
        return self.variable_function_probe_0

    def set_variable_function_probe_0(self, variable_function_probe_0):
        self.variable_function_probe_0 = variable_function_probe_0
        #print variable_function_probe_0,
    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate

        
    def carrier_sensed(self):
        """
        Return True if we think carrier is present.
        """
        #return self.probe.level() > X
        return self.probe.unmuted()

    def carrier_threshold(self):
        """
        Return current setting in dB.
        """
        return self.probe.threshold()

    def set_carrier_threshold(self, threshold_in_db):
        """
        Set carrier threshold.

        @param threshold_in_db: set detection threshold
        @type threshold_in_db:  float (dB)
        """
        self.probe.set_threshold(threshold_in_db)
    
        
    def add_options(normal, expert):
        """
        Adds receiver-specific options to the Options Parser
        """
        normal.add_option("-W", "--bandwidth", type="eng_float",
                          default=500e3,
                          help="set symbol bandwidth [default=%default]")
        normal.add_option("-v", "--verbose", action="store_true", default=False)
        expert.add_option("", "--log", action="store_true", default=False,
                          help="Log all parts of flow graph to files (CAUTION: lots of data)")

    # Make a static method to call before instantiation
    add_options = staticmethod(add_options)


    def _print_verbage(self):
        """
        Prints information about the receive path
        """
        pass
