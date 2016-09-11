import numpy as np

from PyQt4 import QtCore, QtGui


class ChannelNoise:
    def widget(self):
        try:
            return globals()[self.__class__.__name__ + '_Widget'](self)
        except KeyError:
            return QtGui.QLabel('<i>No options available for this channel.</i>')


class ChannelNoise_Widget(QtGui.QWidget):
    update_signal = QtCore.pyqtSignal()

    def __init__(self, channel):
        super().__init__()
        self.channel = channel
        self.initUI()


# Ideal channel

class Bypass_ChannelNoise(ChannelNoise):
    def process(self, s, fs=None):
        return s


# AWGN channel

class AWGN_ChannelNoise(ChannelNoise):
    def __init__(self, snr_db=30.0, sps=1):
        self.snr_db = snr_db
        self.sps = sps

    def process(self, s, fs=None):
        snr = 10.0 ** (0.1 * self.snr_db)
        signal_power = np.mean(s**2)
        noise_power = self.sps * signal_power / snr
        w = np.random.normal(size=len(s)) * np.sqrt(noise_power)
        r = s + w
        return r


class AWGN_ChannelNoise_Widget(ChannelNoise_Widget):
    def initUI(self):
        layout = QtGui.QHBoxLayout()
        self.snr_db = QtGui.QLineEdit(str(self.channel.snr_db))
        self.snr_db.editingFinished.connect(self.onChange)
        layout.addWidget(QtGui.QLabel('SNR [dB]:'))
        layout.addWidget(self.snr_db)
        self.setLayout(layout)

    def onChange(self):
        self.channel.snr_db = float(self.snr_db.text())
        self.snr_db.setText(str(self.channel.snr_db))
        self.update_signal.emit()


choices = [
    ('[Bypass]', Bypass_ChannelNoise()),
    ('AWGN', AWGN_ChannelNoise())
]
