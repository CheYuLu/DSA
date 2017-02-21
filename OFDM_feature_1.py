#!/usr/bin/env python
##################################################
# Gnuradio Python Flow Graph
# Title: OFDM_feature_1
# Generated: Tue May 21 16:22:52 2013
##################################################

execfile("/home/nxglab/.grc_gnuradio/absolute.py")
from gnuradio import gr
from gnuradio.gr import firdes

import absolute

class OFDM_feature_1(gr.hier_block2):

	def __init__(self, CP=191):
		gr.hier_block2.__init__(
			self, "OFDM_feature_1",
			gr.io_signature(1, 1, gr.sizeof_gr_complex*1),
			gr.io_signature(1, 1, gr.sizeof_float*1),
		)

		##################################################
		# Parameters
		##################################################
		self.CP = CP

		##################################################
		# Variables
		##################################################
		self.delay = delay = 4*CP+2

		##################################################
		# Blocks
		##################################################
		self.gr_multiply_xx_0 = gr.multiply_vcc(1)
		self.gr_moving_average_xx_1 = gr.moving_average_ff(CP, 1, 4000)
		self.gr_moving_average_xx_0 = gr.moving_average_ff(CP, 1, 4000)
		self.gr_delay_0 = gr.delay(gr.sizeof_gr_complex*1, delay)
		self.gr_conjugate_cc_0 = gr.conjugate_cc()
		self.gr_complex_to_float_0 = gr.complex_to_float(1)
		self.gr_add_xx_0 = gr.add_vff(1)
		self.absolute_1 = absolute()
		self.absolute_0 = absolute()

		##################################################
		# Connections
		##################################################
		self.connect((self.gr_complex_to_float_0, 0), (self.gr_moving_average_xx_0, 0))
		self.connect((self.gr_complex_to_float_0, 1), (self.gr_moving_average_xx_1, 0))
		self.connect((self.gr_moving_average_xx_0, 0), (self.absolute_0, 0))
		self.connect((self.gr_moving_average_xx_1, 0), (self.absolute_1, 0))
		self.connect((self.absolute_0, 0), (self.gr_add_xx_0, 0))
		self.connect((self.absolute_1, 0), (self.gr_add_xx_0, 1))
		self.connect((self.gr_add_xx_0, 0), (self, 0))
		self.connect((self.gr_multiply_xx_0, 0), (self.gr_complex_to_float_0, 0))
		self.connect((self.gr_conjugate_cc_0, 0), (self.gr_multiply_xx_0, 0))
		self.connect((self, 0), (self.gr_multiply_xx_0, 1))
		self.connect((self, 0), (self.gr_delay_0, 0))
		self.connect((self.gr_delay_0, 0), (self.gr_conjugate_cc_0, 0))

	def get_CP(self):
		return self.CP

	def set_CP(self, CP):
		self.CP = CP
		self.gr_moving_average_xx_0.set_length_and_scale(self.CP, 1)
		self.gr_moving_average_xx_1.set_length_and_scale(self.CP, 1)
		self.set_delay(4*self.CP+2)

	def get_delay(self):
		return self.delay

	def set_delay(self, delay):
		self.delay = delay
		self.gr_delay_0.set_delay(self.delay)


