import numpy as np

from PyQt4 import QtCore, QtGui

import pulses


class TransmitFilter:
    def widget(self):
        try:
            return globals()[self.__class__.__name__ + '_Widget'](self)
        except KeyError:
            return QtGui.QLabel('<i>No options available for this transmit filter.</i>')


class TransmitFilter_Widget(QtGui.QWidget):
    update_signal = QtCore.pyqtSignal()

    def __init__(self, tx_filter):
        super().__init__()
        self.tx_filter = tx_filter
        self.initUI()


# Pulse formatter

class PulseFormatter_TransmitFilter(TransmitFilter):
    pulse = list(pulses.collection.values())[0]

    def process(self, x):
        self.system.pulse = self.pulse
        sps = self.system.sps
        filt_len = self.pulse.filt_len
        N = sps * filt_len

        tx = np.arange(N) / sps

        p = self.pulse.pulse(tx)
        w = np.zeros((len(x) + 2) * sps)
        w[sps : -sps : sps] = x

        s = np.convolve(w, p)

        return s[N//2 : len(w) + N//2]


class PulseFormatter_TransmitFilter_Widget(TransmitFilter_Widget):
    def initUI(self):
        self.combo = QtGui.QComboBox()
        self.combo.addItems(list(pulses.collection.keys()))
        self.combo.activated[str].connect(self.onChange)

        layoutH = QtGui.QHBoxLayout()
        layoutH.addWidget(QtGui.QLabel('Pulse:'), 0)
        layoutH.addWidget(self.combo, 1)

        layoutV = QtGui.QVBoxLayout()
        layoutV.addLayout(layoutH)
        self.pulse_widgets = {}
        for i, (key, val) in enumerate(pulses.collection.items()):
            w = val.widget()
            w.setVisible(i == 0)
            if hasattr(w, 'update_signal'):
                w.update_signal.connect(self.update_signal.emit)
            layoutV.addWidget(w)
            self.pulse_widgets[key] = w
        self.setLayout(layoutV)

    def onChange(self, text):
        self.tx_filter.pulse = pulses.collection[text]
        for key in pulses.collection.keys():
            self.pulse_widgets[key].setVisible(key == text)

        self.update_signal.emit()


choices = [
    ('Pulse formatter', PulseFormatter_TransmitFilter()),
]
