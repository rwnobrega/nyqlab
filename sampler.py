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
    sampling_instant = 0

    def sampling_instants(self, r):
        sps = self.system.sps
        Ns = self.system.n_symbols
        s_inst = self.sampling_instant / 100
        tk = np.arange(round(s_inst * sps), len(r), step=sps) + sps
        return tk[:Ns]

    def process(self, r):
        instants = self.sampling_instants(r)
        self.system.instants = instants
        return r[instants]


class Simple_Sampler_Widget(Sampler_Widget):
    def initUI(self):
        self.sampling_instant_text = QtWidgets.QLineEdit(str(self.sampler.sampling_instant))
        self.sampling_instant_text.editingFinished.connect(self.onChange_text)

        self.sampling_instant_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.sampling_instant_slider.setRange(-50, 50)
        self.sampling_instant_slider.setValue(self.sampler.sampling_instant)
        self.sampling_instant_slider.valueChanged[int].connect(self.onChange_slider)

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(QtWidgets.QLabel('Sampling instant [% of Ts]:'), 1)
        layout.addWidget(self.sampling_instant_text, 1)
        layout.addWidget(self.sampling_instant_slider, 2)

        self.setLayout(layout)

    def onChange_text(self):
        self.sampler.sampling_instant = int(self.sampling_instant_text.text())
        self.sampling_instant_text.setText(str(self.sampler.sampling_instant))
        self.sampling_instant_slider.setValue(self.sampler.sampling_instant)
        self.update_signal.emit()

    def onChange_slider(self):
        self.sampler.sampling_instant = self.sampling_instant_slider.value()
        self.sampling_instant_text.setText(str(self.sampler.sampling_instant))
        self.sampling_instant_slider.setValue(self.sampler.sampling_instant)
        self.update_signal.emit()


choices = [
    ('Simple sampler', Simple_Sampler()),
]
