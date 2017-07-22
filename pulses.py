import collections

import numpy as np

from PyQt5 import QtCore, QtWidgets


class Pulse:
    filt_len = 1
    ax_t_lim = [-0.5, 1.5, -0.25, 1.25]
    ax_f_lim = [-10.0, 10.0, -0.25, 1.25]

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


# Pulses

class RectangularNRZ_Pulse(Pulse):
    def pulse(self, tx):
        return 1.0 * ((0.0 <= tx) & (tx < 1.0))


class RectangularRZ_Pulse(Pulse):
    def pulse(self, tx):
        return 1.0 * ((0.0 <= tx) & (tx < 0.5))


class Manchester_Pulse(Pulse):
    ax_t_lim = [-0.5, 1.5, -1.25, 1.25]

    def pulse(self, tx):
        return  1.0 * ((0.0 <= tx) & (tx < 0.5)) + \
               -1.0 * ((0.5 <= tx) & (tx < 1.0))


class Wal2_Pulse(Pulse):
    ax_t_lim = [-0.5, 1.5, -1.25, 1.25]

    def pulse(self, tx):
        return -1.0 * ((0.0  <= tx) & (tx < 0.25)) + \
                1.0 * ((0.25 <= tx) & (tx < 0.75)) + \
               -1.0 * ((0.75 <= tx) & (tx < 1.00))


class Triangular_Pulse(Pulse):
    def pulse(self, tx):
        return (1.0 - abs(2.0*tx - 1.0)) * ((0.0 <= tx) & (tx < 1.0))


class Sinc_Pulse(Pulse):
    def __init__(self, filt_len=64):
        self.filt_len = filt_len
        self.update_properties()

    def pulse(self, tx):
        t0 = self.filt_len / 2
        tx -= t0
        return np.sinc(tx) * ((-t0 <= tx) & (tx < t0))

    def update_properties(self):
        filt_len = self.filt_len
        self.ax_t_lim = [filt_len / 2 - 7.5, filt_len / 2 + 7.5, -0.5, 1.25]
        self.ax_f_lim = [-1.5, 1.5, -0.25, 1.25]


class Sinc_Pulse_Widget(Pulse_Widget):
    def initUI(self):
        self.filt_len_text = QtWidgets.QLineEdit(str(self.pulse.filt_len))
        self.filt_len_text.editingFinished.connect(self.onChange_filt_len_text)

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(QtWidgets.QLabel('Filter length [Ts]:'), 1)
        layout.addWidget(self.filt_len_text, 2)

        self.setLayout(layout)

    def onChange_filt_len_text(self):
        self.pulse.filt_len = int(self.filt_len_text.text())
        self.pulse.update_properties()
        self.filt_len_text.setText(str(self.pulse.filt_len))
        self.update_signal.emit()


class SquaredSinc_Pulse(Pulse):
    def __init__(self, filt_len=64):
        self.filt_len = filt_len
        self.update_properties()

    def pulse(self, tx):
        t0 = self.filt_len / 2
        tx -= t0
        return np.sinc(tx)**2 * ((-t0 <= tx) & (tx < t0))

    def update_properties(self):
        filt_len = self.filt_len
        self.ax_t_lim = [filt_len / 2 - 7.5, filt_len / 2 + 7.5, -0.5, 1.25]
        self.ax_f_lim = [-1.5, 1.5, -0.25, 1.25]


class SquaredSinc_Pulse_Widget(Sinc_Pulse_Widget):
    pass


class RaisedCosine_Pulse(Pulse):
    def __init__(self, filt_len=64, rolloff=0.5):
        self.filt_len = filt_len
        self.rolloff = rolloff
        self.update_properties()

    def pulse(self, tx):
        t0 = self.filt_len / 2
        tx -= t0
        r = self.rolloff + 1.0e-12  # Because of numerical issues
        p = np.sinc(tx) * (np.cos(np.pi*r*tx)) / (1.0 - 4.0 * r**2 * tx**2)
        return p * ((-t0 <= tx) & (tx < t0))

    def update_properties(self):
        filt_len = self.filt_len
        self.ax_t_lim = [filt_len / 2 - 7.5, filt_len / 2 + 7.5, -0.5, 1.25]
        self.ax_f_lim = [-1.5, 1.5, -0.25, 1.25]


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

        layout0 = QtWidgets.QHBoxLayout()
        layout0.addWidget(QtWidgets.QLabel('Filter length [Ts]:'), 1)
        layout0.addWidget(self.filt_len_text, 2)

        layout1 = QtWidgets.QHBoxLayout()
        layout1.addWidget(QtWidgets.QLabel('Rolloff factor:'), 1)
        layout1.addWidget(self.rolloff_text, 1)
        layout1.addWidget(self.rolloff_slider, 2)

        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(layout0)
        layout.addLayout(layout1)
        self.setLayout(layout)

        self._update('filt_len', self.pulse.filt_len)
        self._update('rolloff', self.pulse.rolloff)

    def _update(self, key, value):
        if key == 'filt_len':
            self.pulse.filt_len = value
            self.pulse.update_properties()
            self.filt_len_text.setText(str(value))
        elif key == 'rolloff':
            self.pulse.rolloff = float(value)
            self.rolloff_text.setText(str(value))
            self.rolloff_slider.setValue(int(100 * value))
        self.update_signal.emit()

class RootRaisedCosine_Pulse(Pulse):
    def __init__(self, filt_len=64, rolloff=0.5):
        self.filt_len = filt_len
        self.rolloff = rolloff
        self.update_properties()

    def pulse(self, tx):
        t0 = self. filt_len / 2

        tx -= t0
        r = self.rolloff + 1.0e-12  # Because of numerical issues

        @np.vectorize
        def _pulse(tx):
            if tx == 0.0:
                return 1.0 - r + 4.0*r/np.pi
            else:
                return (np.sin(np.pi*(1.0 - r)*tx) + (4.0*r*tx)*np.cos(np.pi*(1.0 + r)*tx)) / (np.pi*tx*(1.0 - (4.0*r*tx)**2))

        p = _pulse(tx) * ((-t0 <= tx) & (tx < t0))

        return p

    def update_properties(self):
        filt_len = self.filt_len
        self.ax_t_lim = [filt_len / 2 - 7.5, filt_len / 2 + 7.5, -0.5, 1.25]
        self.ax_f_lim = [-1.5, 1.5, -0.25, 1.25]


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
