import numpy as np

from PyQt5 import QtCore, QtWidgets


class Sampler:
    def widget(self):
        try:
            return globals()[self.__class__.__name__ + '_Widget'](self)
        except KeyError:
            return QtWidgets.QLabel('<i>No options available for this sampling scheme.</i>')

class Sampler_Widget(QtWidgets.QWidget):
    update_signal = QtCore.pyqtSignal()

    def __init__(self, sampler):
        super().__init__()
        self.sampler = sampler
        self.initUI()


# Samplers

class Simple_Sampler(Sampler):
    def sampling_instants(self, r):
        sps = self.system.sps
        Ns = self.system.n_symbols
        s_inst = self.system.sampling_instant
        tk = np.arange(round(s_inst * sps), len(r), step=sps) + sps
        return tk[:Ns]

    def process(self, r):
        instants = self.sampling_instants(r)
        self.system.instants = instants
        return r[instants]


class Simple_Sampler_Widget(Sampler_Widget):
    def initUI(self):
        self.sampling_instant_text = QtWidgets.QLineEdit()
        self.sampling_instant_text.editingFinished.connect(
            lambda: self._update(int(self.sampling_instant_text.text()))
        )

        self.sampling_instant_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.sampling_instant_slider.setRange(-50, 50)
        self.sampling_instant_slider.valueChanged[int].connect(
            lambda: self._update(self.sampling_instant_slider.value())
        )

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(QtWidgets.QLabel('Sampling instant [% of Ts]:'), 1)
        layout.addWidget(self.sampling_instant_text, 1)
        layout.addWidget(self.sampling_instant_slider, 2)
        self.setLayout(layout)

        self._update(0)

    def _update(self, value):
        self.sampler.system.sampling_instant = value / 100
        self.sampling_instant_text.setText(str(value))
        self.sampling_instant_slider.setValue(value)
        self.update_signal.emit()


choices = [
    ('Simple sampler', Simple_Sampler()),
]
