import collections

import numpy as np

from PyQt5 import QtCore, QtWidgets


class Pulse:
    filt_len = 1
    tx_lim = (-0.5, 1.5)
    fx_lim = (-15.0, 15.0)
    is_square = False

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
    is_square = True

    def pulse(self, tx):
        return 1.0 * ((0.0 <= tx) & (tx < 1.0))


class RectangularRZ_Pulse(Pulse):
    is_square = True

    def pulse(self, tx):
        return 1.0 * ((0.0 <= tx) & (tx < 0.5))


class Manchester_Pulse(Pulse):
    is_square = True

    def pulse(self, tx):
        return 1.0 * ((0.0 <= tx) & (tx < 0.5)) - 1.0*((0.5 <= tx) & (tx < 1.0))


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
        self.tx_lim = (filt_len / 2 - 15.0, filt_len / 2 + 15.0)
        self.fx_lim = (-1.5, 1.5)


class Sinc_Pulse_Widget(Pulse_Widget):
    def initUI(self):
        self.text_filt_len = QtWidgets.QLineEdit(str(self.pulse.filt_len))
        self.text_filt_len.editingFinished.connect(self.onChange_text_filt_len)

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(QtWidgets.QLabel('Filter length [Ts]:'), 1)
        layout.addWidget(self.text_filt_len, 2)

        self.setLayout(layout)

    def onChange_text_filt_len(self):
        self.pulse.filt_len = int(self.text_filt_len.text())
        self.pulse.update_properties()
        self.text_filt_len.setText(str(self.pulse.filt_len))
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
        self.tx_lim = (filt_len / 2 - 7.5, filt_len / 2 + 7.5)
        self.fx_lim = (-1.5, 1.5)


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
        self.tx_lim = (filt_len / 2 - 7.5, filt_len / 2 + 7.5)
        self.fx_lim = (-1.5, 1.5)


class RaisedCosine_Pulse_Widget(Pulse_Widget):
    def initUI(self):
        self.text_filt_len = QtWidgets.QLineEdit(str(self.pulse.filt_len))
        self.text_filt_len.editingFinished.connect(self.onChange_text_filt_len)

        self.text_rolloff = QtWidgets.QLineEdit(str(self.pulse.rolloff))
        self.text_rolloff.editingFinished.connect(self.onChange_text_rolloff)

        self.slider_rolloff = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider_rolloff.setRange(0, 100)
        self.slider_rolloff.setValue(int(100 * self.pulse.rolloff))
        self.slider_rolloff.valueChanged[int].connect(self.onChange_slider_rolloff)

        layout0 = QtWidgets.QHBoxLayout()
        layout0.addWidget(QtWidgets.QLabel('Filter length [Ts]:'), 1)
        layout0.addWidget(self.text_filt_len, 2)

        layout1 = QtWidgets.QHBoxLayout()
        layout1.addWidget(QtWidgets.QLabel('Rolloff factor:'), 1)
        layout1.addWidget(self.text_rolloff, 1)
        layout1.addWidget(self.slider_rolloff, 2)

        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(layout0)
        layout.addLayout(layout1)
        self.setLayout(layout)

    def onChange_text_filt_len(self):
        self.pulse.filt_len = int(self.text_filt_len.text())
        self.pulse.update_properties()
        self.text_filt_len.setText(str(self.pulse.filt_len))
        self.update_signal.emit()

    def onChange_text_rolloff(self):
        self.pulse.rolloff = float(self.text_rolloff.text())
        self.text_rolloff.setText(str(self.pulse.rolloff))
        self.slider_rolloff.setValue(int(100 * self.pulse.rolloff))
        self.update_signal.emit()

    def onChange_slider_rolloff(self):
        self.pulse.rolloff = float(self.slider_rolloff.value()) / 100
        self.text_rolloff.setText(str(self.pulse.rolloff))
        self.slider_rolloff.setValue(int(100 * self.pulse.rolloff))
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
        self.tx_lim = (filt_len / 2 - 7.5, filt_len / 2 + 7.5)
        self.fx_lim = (-1.5, 1.5)


class RootRaisedCosine_Pulse_Widget(RaisedCosine_Pulse_Widget):
    pass


collection = collections.OrderedDict([
    ('Rectangular NRZ', RectangularNRZ_Pulse()),
    ('Rectangular RZ', RectangularRZ_Pulse()),
    ('Biphase (Manchester)', Manchester_Pulse()),
    ('Triangular', Triangular_Pulse()),
    ('Sinc', Sinc_Pulse()),
    ('Squared sinc', SquaredSinc_Pulse()),
    ('Raised-cosine', RaisedCosine_Pulse()),
    ('Root-raised-cosine', RootRaisedCosine_Pulse())
])
