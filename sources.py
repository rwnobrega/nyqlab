import collections

import numpy as np

from PyQt4 import QtCore, QtGui


class BitSource:
    def widget(self):
        try:
            return globals()[self.__class__.__name__ + '_Widget'](self)
        except KeyError:
            return QtGui.QLabel('<i>No options available for this source.</i>')


class BitSource_Widget(QtGui.QWidget):
    update_signal = QtCore.pyqtSignal()

    def __init__(self, source):
        super().__init__()
        self.source = source
        self.initUI()


# Random bits

class Random_BitSource(BitSource):
    def __init__(self, nbits=16):
        self.nbits = nbits

    def data(self):
        return np.random.randint(0, high=2, size=self.nbits)


class Random_BitSource_Widget(BitSource_Widget):
    def initUI(self):
        layout = QtGui.QHBoxLayout()

        self.nbits = QtGui.QLineEdit(str(self.source.nbits))
        self.nbits.editingFinished.connect(self.onChange)
        layout.addWidget(QtGui.QLabel('Number of bits:'))
        layout.addWidget(self.nbits)

        self.setLayout(layout)

    def onChange(self):
        new_nbits = int(self.nbits.text())
        self.nbits.setText(str(new_nbits))

        if new_nbits != self.source.nbits:
            self.source.nbits = new_nbits
            self.update_signal.emit()


# Fixed bit sequence

class Fixed_BitSource(BitSource):
    def __init__(self, bits=None):
        if bits is None:
            self.bits = np.array([0, 1])
        else:
            self.bits = bits

    def data(self):
        return self.bits


class Fixed_BitSource_Widget(BitSource_Widget):
    def initUI(self):
        layout = QtGui.QHBoxLayout()

        self.bits = QtGui.QLineEdit(''.join(str(x) for x in self.source.bits))
        self.bits.editingFinished.connect(self.onChange)
        layout.addWidget(QtGui.QLabel('Bit sequence:'))
        layout.addWidget(self.bits)

        self.setLayout(layout)

    def onChange(self):
        new_bits = np.array([int(s) for s in self.bits.text() if s.strip() != ''], dtype=int)
        self.bits.setText(''.join(str(x) for x in new_bits))

        if not np.array_equal(new_bits, self.source.bits):
            self.source.bits = new_bits
            self.update_signal.emit()


collection = collections.OrderedDict([
    ('Random bits', Random_BitSource()),
    ('Fixed bit sequence', Fixed_BitSource())
])
