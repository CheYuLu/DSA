#!/usr/bin/env python
##################################################
# Gnuradio Python Flow Graph
# Title: absolute
# Generated: Tue May 21 15:45:04 2013
##################################################

from gnuradio import gr
from gnuradio.gr import firdes

class absolute(gr.hier_block2):

	def __init__(self):
		gr.hier_block2.__init__(
			self, "absolute",
			gr.io_signature(1, 1, gr.sizeof_float*1),
			gr.io_signature(1, 1, gr.sizeof_float*1),
		)

		##################################################
		# Variables
		##################################################
		self.samp_rate = samp_rate = 32000

		##################################################
		# Blocks
		##################################################
		self.gr_multiply_const_vxx_0 = gr.multiply_const_vff((0, ))
		self.gr_max_xx_0 = gr.max_ff(1)

		##################################################
		# Connections
		##################################################
		self.connect((self, 0), (self.gr_multiply_const_vxx_0, 0))
		self.connect((self.gr_multiply_const_vxx_0, 0), (self.gr_max_xx_0, 1))
		self.connect((self, 0), (self.gr_max_xx_0, 0))
		self.connect((self.gr_max_xx_0, 0), (self, 0))

	def get_samp_rate(self):
		return self.samp_rate

	def set_samp_rate(self, samp_rate):
		self.samp_rate = samp_rate


