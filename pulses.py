import collections

import numpy as np

from PyQt5 import QtCore, QtWidgets


class Pulse:
    def widget(self):
        try:
            return globals()[self.__class__.__name__ + '_Widget'](self)
        except KeyError:
            return QtWidgets.QLabel('<i>No options available for this pulse.</i>')


class Pulse_Widget(QtWidgets.QWidget):
    update_signal = QtCore.pyqtSignal()

    def __init__(self, pulse):
        super().__init__()
        self.pulse = pulse
        self.initUI()


class ShortPulse(Pulse):
    filt_len = 1
    ax_t_lim = [-0.25, 1.25, -0.25, 1.25]
    ax_f_lim = [-10.0, 10.0, -0.25, 1.25]


class LongPulse(Pulse):
    filt_len = 64
    ax_t_lim = [-7.5, +7.5, -0.5, 1.25]
    ax_f_lim = [-1.5, 1.5, -0.25, 1.25]


# Short pulses

class RectangularNRZ_Pulse(ShortPulse):
    def pulse(self, t):
        return 1.0 * ((0.0 <= t) & (t < 1.0))


class RectangularRZ_Pulse(ShortPulse):
    def pulse(self, t):
        return 1.0 * ((0.0 <= t) & (t < 0.5))


class Manchester_Pulse(ShortPulse):
    ax_t_lim = [-0.5, 1.5, -1.25, 1.25]

    def pulse(self, t):
        return  1.0 * ((0.0 <= t) & (t < 0.5)) + \
               -1.0 * ((0.5 <= t) & (t < 1.0))


class Wal2_Pulse(ShortPulse):
    ax_t_lim = [-0.5, 1.5, -1.25, 1.25]

    def pulse(self, t):
        return -1.0 * ((0.0  <= t) & (t < 0.25)) + \
                1.0 * ((0.25 <= t) & (t < 0.75)) + \
               -1.0 * ((0.75 <= t) & (t < 1.00))


class Triangular_Pulse(ShortPulse):
    def pulse(self, t):
        return (1.0 - abs(2.0*t - 1.0)) * ((0.0 <= t) & (t < 1.0))


# Long pulses

class Sinc_Pulse(LongPulse):
    def pulse(self, t):
        t0 = self.filt_len / 2
        t -= t0
        return np.sinc(t) * ((-t0 <= t) & (t < t0))


class Sinc_Pulse_Widget(Pulse_Widget):
    def initUI(self):
        self.filt_len_text = QtWidgets.QLineEdit(str(self.pulse.filt_len))
        self.filt_len_text.editingFinished.connect(
            lambda: self._update('filt_len', int(self.filt_len_text.text()))
        )

        layout = QtWidgets.QGridLayout()
        layout.addWidget(QtWidgets.QLabel('Filter length [Ts]:'), 0, 0, 1, 1)
        layout.addWidget(self.filt_len_text, 0, 1, 1, 2)
        self.setLayout(layout)

        self._update('filt_len', self.pulse.filt_len)

    def _update(self, key, value):
        if key == 'filt_len':
            self.pulse.filt_len = value
            self.filt_len_text.setText(str(value))
        self.update_signal.emit()


class SquaredSinc_Pulse(LongPulse):
    def pulse(self, t):
        t0 = self.filt_len / 2
        t -= t0
        return np.sinc(t)**2 * ((-t0 <= t) & (t < t0))


class SquaredSinc_Pulse_Widget(Sinc_Pulse_Widget):
    pass


class RaisedCosine_Pulse(LongPulse):
    rolloff = 0.5

    def pulse(self, t):
        t0 = self.filt_len / 2
        t -= t0
        r = self.rolloff + 1.0e-12  # Because of numerical issues
        p = np.sinc(t) * (np.cos(np.pi*r*t)) / (1.0 - 4.0 * r**2 * t**2)
        return p * ((-t0 <= t) & (t < t0))


class RaisedCosine_Pulse_Widget(Pulse_Widget):
    def initUI(self):
        self.filt_len_text = QtWidgets.QLineEdit()
        self.filt_len_text.editingFinished.connect(
            lambda: self._update('filt_len', int(self.filt_len_text.text()))
        )

        self.rolloff_text = QtWidgets.QLineEdit()
        self.rolloff_text.editingFinished.connect(
            lambda: self._update('rolloff', float(self.rolloff_text.text()))
        )

        self.rolloff_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.rolloff_slider.setRange(0, 100)
        self.rolloff_slider.valueChanged[int].connect(
            lambda: self._update('rolloff', self.rolloff_slider.value() / 100)
        )

        layout = QtWidgets.QGridLayout()
        layout.addWidget(QtWidgets.QLabel('Filter length [Ts]:'), 0, 0, 1, 1)
        layout.addWidget(self.filt_len_text, 0, 1, 1, 2)
        layout.addWidget(QtWidgets.QLabel('Rolloff factor:'), 1, 0, 1, 1)
        layout.addWidget(self.rolloff_text, 1, 1, 1, 1)
        layout.addWidget(self.rolloff_slider, 1, 2, 1, 1)
        self.setLayout(layout)

        self._update('filt_len', self.pulse.filt_len)
        self._update('rolloff', self.pulse.rolloff)

    def _update(self, key, value):
        if key == 'filt_len':
            self.pulse.filt_len = value
            self.filt_len_text.setText(str(value))
        elif key == 'rolloff':
            self.pulse.rolloff = float(value)
            self.rolloff_text.setText(str(value))
            self.rolloff_slider.setValue(int(100 * value))
        self.update_signal.emit()


class RootRaisedCosine_Pulse(LongPulse):
    rolloff = 0.5

    def pulse(self, t):
        t0 = self. filt_len / 2
        t -= t0
        r = self.rolloff + 1.0e-12  # Because of numerical issues

        @np.vectorize
        def _pulse(t):
            if t == 0.0:
                return 1.0 - r + 4.0*r/np.pi
            else:
                return (np.sin(np.pi*(1.0 - r)*t) + (4.0*r*t)*np.cos(np.pi*(1.0 + r)*t)) / (np.pi*t*(1.0 - (4.0*r*t)**2))

        p = _pulse(t) * ((-t0 <= t) & (t < t0))

        return p


class RootRaisedCosine_Pulse_Widget(RaisedCosine_Pulse_Widget):
    pass


collection = collections.OrderedDict([
    ('Rectangular NRZ', RectangularNRZ_Pulse()),
    ('Rectangular RZ', RectangularRZ_Pulse()),
    ('Biphase (Manchester)', Manchester_Pulse()),
    ('Wal-2', Wal2_Pulse()),
    ('Triangular', Triangular_Pulse()),
    ('Sinc', Sinc_Pulse()),
    ('Squared sinc', SquaredSinc_Pulse()),
    ('Raised-cosine', RaisedCosine_Pulse()),
    ('Root-raised-cosine', RootRaisedCosine_Pulse())
])
