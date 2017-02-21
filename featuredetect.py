#!/usr/bin/env python
##################################################
# Gnuradio Python Flow Graph
# Title: featuredetect
# Generated: Tue May 21 16:57:23 2013
##################################################

execfile("/home/nxglab/.grc_gnuradio/OFDM_feature_1.py")
execfile("/home/nxglab/.grc_gnuradio/Threshold_bound.py")
execfile("/home/nxglab/.grc_gnuradio/absolute.py")

from gnuradio import gr
from gnuradio.gr import firdes
"""
import OFDM_feature_1
import Threshold_bound
import absolute
"""

class featuredetect(gr.hier_block2):

	def __init__(self, collectingtime=1):
		gr.hier_block2.__init__(
			self, "featuredetect",
			gr.io_signature(1, 1, gr.sizeof_gr_complex*1),
			gr.io_signature(1, 1, gr.sizeof_float*1),
		)

		##################################################
		# Parameters
		##################################################
		self.collectingtime = collectingtime

		##################################################
		# Variables
		##################################################
		self.CP = CP = 191

		##################################################
		# Blocks
		##################################################
		self.gr_multiply_xx_0 = gr.multiply_vff(1)
		self.gr_multiply_const_vxx_0 = gr.multiply_const_vff((0.05, ))
		self.gr_moving_average_xx_2 = gr.moving_average_ff(5*CP, 1, CP*5*21)
		self.gr_moving_average_xx_0 = gr.moving_average_ff(20, 1, 200)
		self.gr_feedforward_agc_cc_0 = gr.feedforward_agc_cc(1, 1)
		self.gr_delay_0 = gr.delay(gr.sizeof_float*1, 5*CP)
		self.absolute_0 = absolute()

		self.Threshold_bound_2 = Threshold_bound(
			high=200,
			low=70,
		)
		self.Threshold_bound_0 = Threshold_bound(
			high=20000,
			low=2000,
		)
		self.OFDM_feature_1_0 = OFDM_feature_1(
			CP=191,
		)

		##################################################
		# Connections
		##################################################
		self.connect((self.gr_moving_average_xx_0, 0), (self.gr_multiply_const_vxx_0, 0))
		self.connect((self.gr_multiply_const_vxx_0, 0), (self.absolute_0, 0))
		self.connect((self.absolute_0, 0), (self.gr_multiply_xx_0, 0))
		self.connect((self.gr_moving_average_xx_2, 0), (self.Threshold_bound_2, 0))
		self.connect((self, 0), (self.gr_feedforward_agc_cc_0, 0))
		self.connect((self.absolute_0, 0), (self.gr_delay_0, 0))
		self.connect((self.gr_delay_0, 0), (self.gr_multiply_xx_0, 1))
		self.connect((self.gr_feedforward_agc_cc_0, 0), (self.OFDM_feature_1_0, 0))
		self.connect((self.OFDM_feature_1_0, 0), (self.gr_moving_average_xx_0, 0))
		self.connect((self.gr_multiply_xx_0, 0), (self.Threshold_bound_0, 0))
		self.connect((self.Threshold_bound_0, 0), (self.gr_moving_average_xx_2, 0))
		self.connect((self.Threshold_bound_2, 0), (self, 0))

	def get_collectingtime(self):
		return self.collectingtime

	def set_collectingtime(self, collectingtime):
		self.collectingtime = collectingtime

	def get_CP(self):
		return self.CP

	def set_CP(self, CP):
		self.CP = CP
		self.gr_delay_0.set_delay(5*self.CP)
		self.gr_moving_average_xx_2.set_length_and_scale(5*self.CP, 1)


