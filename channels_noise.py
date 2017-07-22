import numpy as np

from PyQt5 import QtCore, QtWidgets


class ChannelNoise:
    def widget(self):
        try:
            return globals()[self.__class__.__name__ + '_Widget'](self)
        except KeyError:
            return QtWidgets.QLabel('<i>No options available for this channel.</i>')


class ChannelNoise_Widget(QtWidgets.QWidget):
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
    def __init__(self, snr_db=30.0):
        self.snr_db = snr_db

    def process(self, s, fs=None):
        sps = self.system.sps
        snr = 10.0 ** (0.1 * self.snr_db)
        signal_power = np.mean(s**2)
        noise_power = sps * signal_power / snr
        w = np.random.normal(size=len(s)) * np.sqrt(noise_power)
        r = s + w
        return r


class AWGN_ChannelNoise_Widget(ChannelNoise_Widget):
    def initUI(self):
        self.snr_db_text = QtWidgets.QLineEdit()
        self.snr_db_text.editingFinished.connect(
            lambda: self._update(float(self.snr_db_text.text()))
        )

        self.snr_db_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.snr_db_slider.setRange(-50, 500)
        self.snr_db_slider.valueChanged[int].connect(
            lambda: self._update(self.snr_db_slider.value() / 10)
        )

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(QtWidgets.QLabel('SNR [dB]:'), 1)
        layout.addWidget(self.snr_db_text, 1)
        layout.addWidget(self.snr_db_slider, 2)
        self.setLayout(layout)

        self._update(self.channel.snr_db)

    def _update(self, value):
        self.channel.snr_db = value
        self.snr_db_text.setText(str(value))
        self.snr_db_slider.setValue(int(10 * value))
        self.update_signal.emit()


choices = [
    ('[Bypass]', Bypass_ChannelNoise()),
    ('AWGN', AWGN_ChannelNoise())
]
