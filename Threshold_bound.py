#!/usr/bin/env python
##################################################
# Gnuradio Python Flow Graph
# Title: Threshold_bound
# Author: sammui
# Description: output
# Generated: Tue May 21 16:38:35 2013
##################################################

from gnuradio import gr
from gnuradio.gr import firdes

class Threshold_bound(gr.hier_block2):

	def __init__(self, high=0, low=0):
		gr.hier_block2.__init__(
			self, "Threshold_bound",
			gr.io_signature(1, 1, gr.sizeof_float*1),
			gr.io_signature(1, 1, gr.sizeof_float*1),
		)

		##################################################
		# Parameters
		##################################################
		self.high = high
		self.low = low

		##################################################
		# Blocks
		##################################################
		self.gr_xor_xx_0 = gr.xor_ss()
		self.gr_threshold_ff_1 = gr.threshold_ff(low, low, 0)
		self.gr_threshold_ff_0 = gr.threshold_ff(high, high, 0)
		self.gr_short_to_float_0 = gr.short_to_float()
		self.gr_float_to_short_1 = gr.float_to_short()
		self.gr_float_to_short_0 = gr.float_to_short()
		self.gr_and_xx_0 = gr.and_ss()
		self.const_source_x_0 = gr.sig_source_s(0, gr.GR_CONST_WAVE, 0, 0, 1)

		##################################################
		# Connections
		##################################################
		self.connect((self, 0), (self.gr_threshold_ff_0, 0))
		self.connect((self, 0), (self.gr_threshold_ff_1, 0))
		self.connect((self.gr_threshold_ff_0, 0), (self.gr_float_to_short_0, 0))
		self.connect((self.gr_threshold_ff_1, 0), (self.gr_float_to_short_1, 0))
		self.connect((self.const_source_x_0, 0), (self.gr_xor_xx_0, 0))
		self.connect((self.gr_float_to_short_0, 0), (self.gr_xor_xx_0, 1))
		self.connect((self.gr_float_to_short_1, 0), (self.gr_and_xx_0, 1))
		self.connect((self.gr_and_xx_0, 0), (self.gr_short_to_float_0, 0))
		self.connect((self.gr_short_to_float_0, 0), (self, 0))
		self.connect((self.gr_xor_xx_0, 0), (self.gr_and_xx_0, 0))

	def get_high(self):
		return self.high

	def set_high(self, high):
		self.high = high
		self.gr_threshold_ff_0.set_hi(self.high)
		self.gr_threshold_ff_0.set_lo(self.high)

	def get_low(self):
		return self.low

	def set_low(self, low):
		self.low = low
		self.gr_threshold_ff_1.set_hi(self.low)
		self.gr_threshold_ff_1.set_lo(self.low)


