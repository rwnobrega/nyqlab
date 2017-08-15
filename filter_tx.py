import numpy as np

from PyQt5 import QtCore, QtWidgets

import pulses


class TransmitFilter:
    def widget(self):
        try:
            return globals()[self.__class__.__name__ + '_Widget'](self)
        except KeyError:
            return QtWidgets.QLabel('<i>No options available for this transmit filter.</i>')


class TransmitFilter_Widget(QtWidgets.QWidget):
    update_signal = QtCore.pyqtSignal()

    def __init__(self, tx_filter):
        super().__init__()
        self.tx_filter = tx_filter
        self.initUI()


# Pulse formatter

class PulseFormatter_TransmitFilter(TransmitFilter):
    pulse = list(pulses.collection.values())[0]

    def process(self, x):
        sps = self.system.sps
        filt_len = self.pulse.filt_len
        N = sps * filt_len

        t = np.arange(N) / sps
        p = self.pulse.pulse(t)
        w = np.zeros((len(x) + 2) * sps)
        w[sps : -sps : sps] = x

        s = np.convolve(w, p)

        if isinstance(self.pulse, pulses.ShortPulse):
            return s[: len(w)]
        else:
            return s[N//2 : len(w) + N//2]


class PulseFormatter_TransmitFilter_Widget(TransmitFilter_Widget):
    def initUI(self):
        self.pulses_combo = QtWidgets.QComboBox()
        self.pulses_combo.addItems(list(pulses.collection.keys()))
        self.pulses_combo.activated[str].connect(self.onChangePulse)

        layout_top = QtWidgets.QHBoxLayout()
        layout_top.addWidget(QtWidgets.QLabel('Pulse:'), 0)
        layout_top.addWidget(self.pulses_combo, 1)

        layout_pulses = QtWidgets.QVBoxLayout()
        self.pulse_widgets = {}
        for i, (key, val) in enumerate(pulses.collection.items()):
            w = val.widget()
            w.setVisible(i == 0)
            if hasattr(w, 'update_signal'):
                w.update_signal.connect(self.update_signal.emit)
            layout_pulses.addWidget(w)
            self.pulse_widgets[key] = w

        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(layout_top)
        layout.addLayout(layout_pulses)
        self.setLayout(layout)

    def onChangePulse(self, text):
        self.tx_filter.pulse = pulses.collection[text]
        for key in pulses.collection.keys():
            self.pulse_widgets[key].setVisible(key == text)
        self.update_signal.emit()


choices = [
    ('Pulse formatter', PulseFormatter_TransmitFilter()),
]

