import numpy as np

from PyQt4 import QtCore, QtGui

import pulses


class ReceiveFilter:
    def widget(self):
        try:
            return globals()[self.__class__.__name__ + '_Widget'](self)
        except KeyError:
            return QtGui.QLabel('<i>No options available for this receive filter.</i>')


class ReceiveFilter_Widget(QtGui.QWidget):
    update_signal = QtCore.pyqtSignal()

    def __init__(self, tx_filter):
        super().__init__()
        self.tx_filter = tx_filter
        self.initUI()


# Bypass

class Bypass_ReceiveFilter(ReceiveFilter):
    def process(self, y):
        return y


# Matched filter

class MatchedFilter_ReceiveFilter(ReceiveFilter):
    def process(self, y):
        pulse = self.system.pulse
        sps = self.system.sps
        fa = self.system.samp_freq
        filt_len = pulse.filt_len
        N = sps * filt_len
        delay = (N - 1) / fa

        tx = np.arange(N) / sps

        p = pulse.pulse(-tx + delay)
        p /= np.sum(np.abs(p)**2) / sps

        r = np.convolve(y, p) / sps

        return r[N//2 - 1: len(y) + N//2 - 1]


choices = [
    ('[Bypass]', Bypass_ReceiveFilter()),
    ('Matched to transmit filter', MatchedFilter_ReceiveFilter()),
]
