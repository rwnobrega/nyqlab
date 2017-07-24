import numpy as np

from PyQt5 import QtCore, QtWidgets


class ChannelFrequency:
    def widget(self):
        try:
            return globals()[self.__class__.__name__ + '_Widget'](self)
        except KeyError:
            return QtWidgets.QLabel('<i>No options available for this channel.</i>')


class ChannelFrequency_Widget(QtWidgets.QWidget):
    update_signal = QtCore.pyqtSignal()

    def __init__(self, channel):
        super().__init__()
        self.channel = channel
        self.initUI()


# Ideal channel

class Bypass_ChannelFrequency(ChannelFrequency):
    def process(self, s):
        return s


# Ideal lowpass channel

class IdealLowpass_ChannelFrequency(ChannelFrequency):
    def __init__(self, bandwidth=2.0):
        self.bandwidth = bandwidth

    def process(self, s):
        fs = self.system.samp_freq
        Ns = len(s)
        f = np.arange(-Ns//2, Ns//2) * (fs/Ns)
        Bt = self.bandwidth
        HC = 1.0 * ((-Bt <= f) & (f < Bt))
        S = np.fft.fftshift(np.fft.fft(s)) / fs
        R0 = S * HC
        r = fs * np.fft.ifft(np.fft.ifftshift(R0))
        r = np.real(r)
        return r


class IdealLowpass_ChannelFrequency_Widget(ChannelFrequency_Widget):
    def initUI(self):
        self.bandwidth_text = QtWidgets.QLineEdit()
        self.bandwidth_text.editingFinished.connect(
            lambda: self._update(float(self.bandwidth_text.text()))
        )

        self.bandwidth_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.bandwidth_slider.setRange(0, 100)
        self.bandwidth_slider.valueChanged[int].connect(
            lambda: self._update(self.bandwidth_slider.value() / 10)
        )

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(QtWidgets.QLabel('Bandwidth [Hz]:'), 1)
        layout.addWidget(self.bandwidth_text, 1)
        layout.addWidget(self.bandwidth_slider, 2)
        self.setLayout(layout)

        self._update(self.channel.bandwidth)

    def _update(self, value):
        self.channel.bandwidth = value
        self.bandwidth_text.setText(str(value))
        self.bandwidth_slider.setValue(int(10 * value))
        self.update_signal.emit()


# First order lowpass channel

class FirstOrderLowpass_ChannelFrequency(ChannelFrequency):
    def __init__(self, cutoff_frequency=5.0):
        self.cutoff_frequency = cutoff_frequency

    def process(self, s):
        fs = self.system.samp_freq
        Ns = len(s)
        f0 = self.cutoff_frequency
        f = np.arange(-Ns//2, Ns//2) * (fs/Ns)
        HC = 1.0 / (1.0 + 1j * 2.0 * np.pi * f/f0)
        S = np.fft.fftshift(np.fft.fft(s)) / fs
        R0 = S * HC
        r = fs * np.fft.ifft(np.fft.ifftshift(R0))
        r = np.real(r)
        return r


class FirstOrderLowpass_ChannelFrequency_Widget(ChannelFrequency_Widget):
    def initUI(self):
        self.cutoff_frequency_text = QtWidgets.QLineEdit()
        self.cutoff_frequency_text.editingFinished.connect(
            lambda: self._update(float(self.cutoff_frequency_text.text()))
        )

        self.cutoff_frequency_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.cutoff_frequency_slider.setRange(0, 200)
        self.cutoff_frequency_slider.valueChanged[int].connect(
            lambda: self._update(self.cutoff_frequency_slider.value() / 10)
        )

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(QtWidgets.QLabel('Cutoff frequency [Hz]:'), 1)
        layout.addWidget(self.cutoff_frequency_text, 1)
        layout.addWidget(self.cutoff_frequency_slider, 2)
        self.setLayout(layout)

        self._update(self.channel.cutoff_frequency)

    def _update(self, value):
        self.channel.cutoff_frequency = value + 1e-12  # Because of numerical issues
        self.cutoff_frequency_text.setText(str(value))
        self.cutoff_frequency_slider.setValue(int(10 * value))
        self.update_signal.emit()


choices = [
    ('[Bypass]', Bypass_ChannelFrequency()),
    ('Ideal lowpass', IdealLowpass_ChannelFrequency()),
    ('First order lowpass', FirstOrderLowpass_ChannelFrequency()),
]
