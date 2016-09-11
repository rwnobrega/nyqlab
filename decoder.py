import numpy as np

from PyQt4 import QtCore, QtGui

import signaling


class Decoder:
    def widget(self):
        try:
            return globals()[self.__class__.__name__ + '_Widget'](self)
        except KeyError:
            return QtGui.QLabel('<i>No options available for this decoder.</i>')


class Decoder_Widget(QtGui.QWidget):
    update_signal = QtCore.pyqtSignal()

    def __init__(self, Decoder):
        super().__init__()
        self.Decoder = Decoder
        self.initUI()


class Simple_Decoder(Decoder):
    signaling = list(signaling.collection.values())[0]

    def process(self, y):
        return self.signaling.decode(y)


choices = [
    ('Slicer + Uncoder', Simple_Decoder()),
]
