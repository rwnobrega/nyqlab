import numpy as np

from PyQt5 import QtCore, QtWidgets

import pulses


class ReceiveFilter:
    def widget(self):
        try:
            return globals()[self.__class__.__name__ + '_Widget'](self)
        except KeyError:
            return QtWidgets.QLabel('<i>No options available for this receive filter.</i>')


class ReceiveFilter_Widget(QtWidgets.QWidget):
    update_signal = QtCore.pyqtSignal()

    def __init__(self, rx_filter):
        super().__init__()
        self.rx_filter = rx_filter
        self.initUI()


# Bypass

class Bypass_ReceiveFilter(ReceiveFilter):
    def process(self, y):
        return y


# Matched filter

class MatchedFilter_ReceiveFilter(ReceiveFilter):
    def process(self, y):
        pulse = self.system.blocks[2].box.pulse  # FIXME: Refactor
        sps = self.system.sps
        Ts = self.system.symbol_rate
        fa = self.system.samp_freq

        if isinstance(pulse, pulses.ShortPulse):
            N = (pulse.filt_len + 1) * sps
            delay = (N - 1) / fa - Ts
        else:
            N = pulse.filt_len * sps
            delay = (N - 1) / fa

        t = np.arange(N) / sps
        p = pulse.pulse(-t + delay)
        p /= np.sum(np.abs(p)**2) / sps

        r = np.convolve(y, p) / sps

        return r[N//2 - 1: len(y) + N//2 - 1]

choices = [
    ('[Bypass]', Bypass_ReceiveFilter()),
    ('Matched to transmit filter', MatchedFilter_ReceiveFilter()),
]
