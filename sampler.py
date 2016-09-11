import numpy as np

from PyQt4 import QtCore, QtGui


class Sampler:
    def widget(self):
        try:
            return globals()[self.__class__.__name__ + '_Widget'](self)
        except KeyError:
            return QtGui.QLabel('<i>No options available for this sampling scheme.</i>')

class Sampler_Widget(QtGui.QWidget):
    update_signal = QtCore.pyqtSignal()

    def __init__(self, sampler):
        super().__init__()
        self.sampler = sampler
        self.initUI()


# Samplers

class Simple_Sampler(Sampler):
    sampling_instant = 50

    def sampling_instants(self, r):
        delay = self.system.delay
        sps = self.system.sps
        Ns = self.system.n_symbols
        s_inst = self.sampling_instant / 100
        tk = np.arange(round(s_inst * sps) + delay, len(r), step=sps)
        return tk[:Ns]

    def process(self, r):
        instants = self.sampling_instants(r)
        self.system.instants = instants
        return r[instants]


class Simple_Sampler_Widget(Sampler_Widget):
    def initUI(self):
        self.sampling_instant_text = QtGui.QLineEdit(str(self.sampler.sampling_instant))
        self.sampling_instant_text.editingFinished.connect(self.onChange_text)

        self.sampling_instant_slider = QtGui.QSlider(QtCore.Qt.Horizontal)
        self.sampling_instant_slider.setRange(0, 100)
        self.sampling_instant_slider.setValue(self.sampler.sampling_instant)
        self.sampling_instant_slider.valueChanged[int].connect(self.onChange_slider)

        layout = QtGui.QHBoxLayout()
        layout.addWidget(QtGui.QLabel('Sampling instant [% of Ts]:'), 1)
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
