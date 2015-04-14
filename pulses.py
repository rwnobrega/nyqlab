import collections

import numpy as np

from PyQt4 import QtCore, QtGui


class Pulse:
    tx_lim, fx_lim = 1.5, 15.0

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

    def pulse(self, tx):
        return np.sinc(tx)


class SquaredSinc_Pulse(Pulse):
    tx_lim, fx_lim = 10.0, 1.5

    def pulse(self, tx):
        return np.sinc(tx)**2


class RaisedCosine_Pulse(Pulse):
    tx_lim, fx_lim = 10.0, 1.5
    rolloff = 0.5

    def pulse(self, tx):
        r = self.rolloff + 1.0e-12  # Because of numerical issues
        return np.sinc(tx) * (np.cos(np.pi*r*tx)) / (1.0 - 4.0 * r**2 * tx**2)


class RaisedCosine_Pulse_Widget(Pulse_Widget):
    def initUI(self):
        layout = QtGui.QHBoxLayout()

        self.rolloff = QtGui.QLineEdit(str(self.pulse.rolloff))
        self.rolloff.editingFinished.connect(self.onChange)
        layout.addWidget(QtGui.QLabel('Rolloff factor:'))
        layout.addWidget(self.rolloff)

        self.setLayout(layout)

    def onChange(self):
        self.pulse.rolloff = float(self.rolloff.text())
        self.rolloff.setText(str(self.pulse.rolloff))
        self.update_signal.emit()


class RootRaisedCosine_Pulse(Pulse):
    tx_lim, fx_lim = 10.0, 1.5
    rolloff = 0.5

    def pulse(self, tx):
        r = self.rolloff + 1.0e-12  # Because of numerical issues

        @np.vectorize
        def _pulse(tx):
            if tx == 0.0:
                return 1.0 - r + 4.0*r/np.pi
            else:
                return (np.sin(np.pi*(1.0 - r)*tx) + (4.0*r*tx)*np.cos(np.pi*(1.0 + r)*tx)) / (np.pi*tx*(1.0 - (4.0*r*tx)**2))

        return _pulse(tx)


class RootRaisedCosine_Pulse_Widget(Pulse_Widget):
    def initUI(self):
        layout = QtGui.QHBoxLayout()

        self.rolloff = QtGui.QLineEdit(str(self.pulse.rolloff))
        self.rolloff.editingFinished.connect(self.onChange)
        layout.addWidget(QtGui.QLabel('Rolloff factor:'))
        layout.addWidget(self.rolloff)

        self.setLayout(layout)

    def onChange(self):
        self.pulse.rolloff = float(self.rolloff.text())
        self.rolloff.setText(str(self.pulse.rolloff))
        self.update_signal.emit()


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
