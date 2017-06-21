import numpy as np

from PyQt5 import QtCore, QtWidgets

import signaling


class Encoder:
    def widget(self):
        try:
            return globals()[self.__class__.__name__ + '_Widget'](self)
        except KeyError:
            return QtWidgets.QLabel('<i>No options available for this encoder.</i>')


class Encoder_Widget(QtWidgets.QWidget):
    update_signal = QtCore.pyqtSignal()

    def __init__(self, encoder):
        super().__init__()
        self.encoder = encoder
        self.initUI()


class Simple_Encoder(Encoder):
    signaling = list(signaling.collection.values())[0]

    def process(self, y):
        self.system.signaling = self.signaling

        self.system.n_symbols = self.system.n_bits * 1 # TODO: Binary so far...
        return self.signaling.encode(y)


class Simple_Encoder_Widget(Encoder_Widget):
    def initUI(self):
        layout = QtWidgets.QHBoxLayout()

        self.combo = QtWidgets.QComboBox()
        self.combo.addItems(list(signaling.collection.keys()))
        self.combo.activated[str].connect(self.onChange)

        layout.addWidget(QtWidgets.QLabel('Signaling:'), 0)
        layout.addWidget(self.combo, 1)

        self.setLayout(layout)

    def onChange(self, text):
        self.encoder.signaling = signaling.collection[text]
        self.update_signal.emit()


choices = [
    ('Simple encoder', Simple_Encoder()),
]
