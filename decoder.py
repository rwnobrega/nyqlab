import numpy as np

from PyQt5 import QtCore, QtWidgets

import signaling


class Decoder:
    def widget(self):
        try:
            return globals()[self.__class__.__name__ + '_Widget'](self)
        except KeyError:
            return QtWidgets.QLabel('<i>No options available for this decoder.</i>')


class Decoder_Widget(QtWidgets.QWidget):
    update_signal = QtCore.pyqtSignal()

    def __init__(self, decoder):
        super().__init__()
        self.decoder = decoder
        self.initUI()


class Simple_Decoder(Decoder):
    def process(self, y):
        return self.system.signaling.decode(y)


choices = [
    ('Slicer + Inverse encoder', Simple_Decoder()),
]
