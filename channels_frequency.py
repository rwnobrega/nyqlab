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
        layout = QtWidgets.QHBoxLayout()
        self.bandwidth = QtWidgets.QLineEdit(str(self.channel.bandwidth))
        self.bandwidth.editingFinished.connect(self.onChange)
        layout.addWidget(QtWidgets.QLabel('Bandwidth [Hz]:'))
        layout.addWidget(self.bandwidth)
        self.setLayout(layout)

    def onChange(self):
        self.channel.bandwidth = float(self.bandwidth.text())
        self.bandwidth.setText(str(self.channel.bandwidth))
        self.update_signal.emit()


# First order lowpass channel

class FirstOrderLowpass_ChannelFrequency(ChannelFrequency):
    def __init__(self, cutoff_frequency=2.0):
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
        layout = QtWidgets.QHBoxLayout()
        self.cutoff_frequency = QtWidgets.QLineEdit(str(self.channel.cutoff_frequency))
        self.cutoff_frequency.editingFinished.connect(self.onChange)
        layout.addWidget(QtWidgets.QLabel('Cutoff frequency [Hz]:'))
        layout.addWidget(self.cutoff_frequency)
        self.setLayout(layout)

    def onChange(self):
        self.channel.cutoff_frequency = float(self.cutoff_frequency.text())
        self.cutoff_frequency.setText(str(self.channel.cutoff_frequency))
        self.update_signal.emit()


choices = [
    ('[Bypass]', Bypass_ChannelFrequency()),
    ('Ideal lowpass', IdealLowpass_ChannelFrequency()),
    ('First order lowpass', FirstOrderLowpass_ChannelFrequency()),
]
