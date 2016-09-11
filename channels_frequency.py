import numpy as np
import scipy as sp

from PyQt4 import QtCore, QtGui


class ChannelFrequency:
    def widget(self):
        try:
            return globals()[self.__class__.__name__ + '_Widget'](self)
        except KeyError:
            return QtGui.QLabel('<i>No options available for this channel.</i>')


class ChannelFrequency_Widget(QtGui.QWidget):
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
        S = sp.fftpack.fftshift(sp.fftpack.fft(s)) / fs
        R0 = S * HC
        r = fs * sp.fftpack.ifft(sp.fftpack.ifftshift(R0))
        r = np.real(r)
        return r


class IdealLowpass_ChannelFrequency_Widget(ChannelFrequency_Widget):
    def initUI(self):
        layout = QtGui.QHBoxLayout()
        self.bandwidth = QtGui.QLineEdit(str(self.channel.bandwidth))
        self.bandwidth.editingFinished.connect(self.onChange)
        layout.addWidget(QtGui.QLabel('Bandwidth [Hz]:'))
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
        S = sp.fftpack.fftshift(sp.fftpack.fft(s)) / fs
        R0 = S * HC
        r = fs * sp.fftpack.ifft(sp.fftpack.ifftshift(R0))
        r = np.real(r)
        return r


class FirstOrderLowpass_ChannelFrequency_Widget(ChannelFrequency_Widget):
    def initUI(self):
        layout = QtGui.QHBoxLayout()
        self.cutoff_frequency = QtGui.QLineEdit(str(self.channel.cutoff_frequency))
        self.cutoff_frequency.editingFinished.connect(self.onChange)
        layout.addWidget(QtGui.QLabel('Cutoff frequency [Hz]:'))
        layout.addWidget(self.cutoff_frequency)
        self.setLayout(layout)

    def onChange(self):
        self.channel.cutoff_frequency = float(self.cutoff_frequency.text())
        self.cutoff_frequency.setText(str(self.channel.cutoff_frequency))
        self.update_signal.emit()


# Second order bandpass channel

class SecondOrderBandpass_ChannelFrequency(ChannelFrequency):
    def __init__(self, cutoff_frequency=2.0):
        self.cutoff_frequency = cutoff_frequency

    def process(self, s):
        fs = self.system.samp_freq
        Ns = len(s)
        f0 = self.cutoff_frequency
        f = np.arange(-Ns//2, Ns//2) * (fs/Ns)
        HC = (1j * 2.0 * np.pi * f) / (1.0 + 1j * 2.0 * np.pi * f/f0)
        S = sp.fftpack.fftshift(sp.fftpack.fft(s)) / fs
        R0 = S * HC
        r = fs * sp.fftpack.ifft(sp.fftpack.ifftshift(R0))
        r = np.real(r)
        return r


class SecondOrderBandpass_ChannelFrequency_Widget(ChannelFrequency_Widget):
    def initUI(self):
        layout = QtGui.QHBoxLayout()
        self.cutoff_frequency = QtGui.QLineEdit(str(self.channel.cutoff_frequency))
        self.cutoff_frequency.editingFinished.connect(self.onChange)
        layout.addWidget(QtGui.QLabel('Cutoff frequency [Hz]:'))
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
    ('Second order bandpass', SecondOrderBandpass_ChannelFrequency()),
]
