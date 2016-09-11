import collections

import numpy as np

from PyQt4 import QtCore, QtGui


class Pulse:
    tx_lim, fx_lim = 1.5, 15.0
    filt_len = int(2 * tx_lim)

    def widget(self):
        try:
            return globals()[self.__class__.__name__ + '_Widget'](self)
        except KeyError:
            return QtGui.QLabel('<i>No options available for this pulse.</i>')


class Pulse_Widget(QtGui.QWidget):
    update_signal = QtCore.pyqtSignal()

    def __init__(self, pulse):
        super().__init__()
        self.pulse = pulse
        self.initUI()


# Pulses

class RectangularNRZ_Pulse(Pulse):
    def pulse(self, tx):
        return 1.0*((-0.5 <= tx) & (tx < 0.5))


class RectangularRZ_Pulse(Pulse):
    def pulse(self, tx):
        return 1.0*((-0.25 <= tx) & (tx < 0.25))


class Manchester_Pulse(Pulse):
    def pulse(self, tx):
        return 1.0*((-0.5 <= tx) & (tx < 0.0)) - 1.0*((0.0 <= tx) & (tx < 0.5))


class Triangular_Pulse(Pulse):
    def pulse(self, tx):
        return (1.0 - abs(2.0*tx))*((-0.5 <= tx) & (tx < 0.5))


class Sinc_Pulse(Pulse):
    tx_lim, fx_lim = 15.0, 1.5

    def __init__(self, filt_len=64):
        self.filt_len = filt_len

    def pulse(self, tx):
        return np.sinc(tx)


class Sinc_Pulse_Widget(Pulse_Widget):
    def initUI(self):
        self.text_filt_len = QtGui.QLineEdit(str(self.pulse.filt_len))
        self.text_filt_len.editingFinished.connect(self.onChange_text_filt_len)

        layout = QtGui.QHBoxLayout()
        layout.addWidget(QtGui.QLabel('Filter length [Ts]:'), 1)
        layout.addWidget(self.text_filt_len, 2)

        self.setLayout(layout)

    def onChange_text_filt_len(self):
        self.pulse.filt_len = int(self.text_filt_len.text())
        self.text_filt_len.setText(str(self.pulse.filt_len))
        self.update_signal.emit()


class SquaredSinc_Pulse(Pulse):
    tx_lim, fx_lim = 10.0, 2.5

    def __init__(self, filt_len=32):
        self.filt_len = filt_len

    def pulse(self, tx):
        return np.sinc(tx)**2


class SquaredSinc_Pulse_Widget(Sinc_Pulse_Widget):
    pass


class RaisedCosine_Pulse(Pulse):
    tx_lim, fx_lim = 10.0, 2.5

    def __init__(self, filt_len=64, rolloff=0.5):
        self.filt_len = filt_len
        self.rolloff = rolloff

    def pulse(self, tx):
        r = self.rolloff + 1.0e-12  # Because of numerical issues
        L = self.filt_len
        p = np.sinc(tx) * (np.cos(np.pi*r*tx)) / (1.0 - 4.0 * r**2 * tx**2)
        return ((-L//2 <= tx) & (tx <= L)) * p


class RaisedCosine_Pulse_Widget(Pulse_Widget):
    def initUI(self):
        self.text_filt_len = QtGui.QLineEdit(str(self.pulse.filt_len))
        self.text_filt_len.editingFinished.connect(self.onChange_text_filt_len)

        self.text_rolloff = QtGui.QLineEdit(str(self.pulse.rolloff))
        self.text_rolloff.editingFinished.connect(self.onChange_text_rolloff)

        self.slider_rolloff = QtGui.QSlider(QtCore.Qt.Horizontal)
        self.slider_rolloff.setRange(0, 100)
        self.slider_rolloff.setValue(int(100 * self.pulse.rolloff))
        self.slider_rolloff.valueChanged[int].connect(self.onChange_slider_rolloff)

        layout0 = QtGui.QHBoxLayout()
        layout0.addWidget(QtGui.QLabel('Filter length [Ts]:'), 1)
        layout0.addWidget(self.text_filt_len, 2)

        layout1 = QtGui.QHBoxLayout()
        layout1.addWidget(QtGui.QLabel('Rolloff factor:'), 1)
        layout1.addWidget(self.text_rolloff, 1)
        layout1.addWidget(self.slider_rolloff, 2)

        layout = QtGui.QVBoxLayout()
        layout.addLayout(layout0)
        layout.addLayout(layout1)
        self.setLayout(layout)

    def onChange_text_filt_len(self):
        self.pulse.filt_len = int(self.text_filt_len.text())
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
    tx_lim, fx_lim = 10.0, 2.5

    def __init__(self, filt_len=64, rolloff=0.5):
        self.filt_len = filt_len
        self.rolloff = rolloff

    def pulse(self, tx):
        r = self.rolloff + 1.0e-12  # Because of numerical issues

        @np.vectorize
        def _pulse(tx):
            if tx == 0.0:
                return 1.0 - r + 4.0*r/np.pi
            else:
                return (np.sin(np.pi*(1.0 - r)*tx) + (4.0*r*tx)*np.cos(np.pi*(1.0 + r)*tx)) / (np.pi*tx*(1.0 - (4.0*r*tx)**2))

        return _pulse(tx)


class RootRaisedCosine_Pulse_Widget(RaisedCosine_Pulse_Widget):
    pass


collection = collections.OrderedDict([
    ('Rectangular NRZ', RectangularNRZ_Pulse()),
    ('Rectangular RZ', RectangularRZ_Pulse()),
    ('Manchester', Manchester_Pulse()),
    ('Triangular', Triangular_Pulse()),
    ('Sinc', Sinc_Pulse()),
    ('Squared sinc', SquaredSinc_Pulse()),
    ('Raised-cosine', RaisedCosine_Pulse()),
    ('Root-raised-cosine', RootRaisedCosine_Pulse())
])
