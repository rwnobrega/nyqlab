#!/usr/bin/env python3

import sys

import numpy as np
import scipy as sp

from PyQt4 import QtCore, QtGui

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt

#~plt.rc('font', **{'family':'serif', 'serif':['Times']})
#~plt.rc('text', usetex=True)
#~plt.rc('text.latex', preamble=r'\usepackage{bm}')

import sources, channels_frequency, channels_noise, signaling, pulses

from pulse_formatter import PulseFomatter
from matched_filter import MatchedFilter


class Window(QtGui.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Baseband transmission')

        # Figure
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)

        # Create tabs
        tabs = QtGui.QTabWidget()
        self.tab_source = QtGui.QWidget()
        self.tab_transmitter = QtGui.QWidget()
        self.tab_channel = QtGui.QWidget()
        self.tab_receiver = QtGui.QWidget()
        tabs.addTab(self.tab_source, 'Source')
        tabs.addTab(self.tab_transmitter, 'Transmitter')
        tabs.addTab(self.tab_channel, 'Channel')
        tabs.addTab(self.tab_receiver, 'Receiver')

        MODULES = {
            'Source': sources,
            'Signaling': signaling,
            'Pulse': pulses,
            'ChannelFrequency': channels_frequency,
            'ChannelNoise': channels_noise
        }

        combos = {}
        for key, module in MODULES.items():
            new_combo = QtGui.QComboBox(self)
            for k in module.collection:
                new_combo.addItem(k)
            activate_attr = getattr(self, 'onComboActivated_' + key)
            new_combo.activated[str].connect(activate_attr)
            combos[key] = new_combo

        def _populate_combo(layout, module_key, title):
            layout.addWidget(QtGui.QLabel(title))
            layout.addWidget(combos[module_key])
            dic = {}
            for i, (k, v) in enumerate(MODULES[module_key].collection.items()):
                dic[k] = v.widget()
                dic[k].setVisible(i == 0)
                if hasattr(dic[k], 'update_signal'):
                    dic[k].update_signal.connect(self.compute_and_plot)
                layout.addWidget(dic[k])
            return dic

        self.source = list(sources.collection.values())[0]
        self.pulse = list(pulses.collection.values())[0]
        self.signaling = list(signaling.collection.values())[0]
        self.channel_frequency = list(channels_frequency.collection.values())[0]
        self.channel_noise = list(channels_noise.collection.values())[0]

        # Source tab
        layout = QtGui.QVBoxLayout()
        self.sources = _populate_combo(layout, 'Source', 'Source:')
        layout.addStretch()
        self.tab_source.setLayout(layout)

        # Transmitter tab
        layout = QtGui.QVBoxLayout()
        self.signaling_schemes = _populate_combo(layout, 'Signaling', 'Signaling scheme:')
        layout.addSpacing(20)
        self.pulses = _populate_combo(layout, 'Pulse', 'Pulse:')
        self.tab_transmitter.setLayout(layout)
        layout.addStretch()

        # Channel tab
        layout = QtGui.QVBoxLayout()
        self.channels_frequency = _populate_combo(layout, 'ChannelFrequency', 'Frequency response:')
        layout.addSpacing(20)
        self.channels_noise = _populate_combo(layout, 'ChannelNoise', 'Noise:')
        layout.addStretch()
        self.tab_channel.setLayout(layout)

        # Receiver tab
        layout = QtGui.QVBoxLayout()
        checkbox_matched = QtGui.QCheckBox('Use matched filter')
        checkbox_matched.stateChanged.connect(self.onCheckbox_Matched)
        self.use_matched = False
        layout.addWidget(checkbox_matched)

        self.sampling_instant_text = QtGui.QLineEdit()
        self.sampling_instant_slider = QtGui.QSlider(QtCore.Qt.Horizontal)
        self.sampling_instant_slider.setRange(0, 100)
        layout_sampling = QtGui.QHBoxLayout()
        layout_sampling.addWidget(QtGui.QLabel('Sampling instant [% of Tb]:'), 1)
        layout_sampling.addWidget(self.sampling_instant_text, 1)
        layout_sampling.addWidget(self.sampling_instant_slider, 3)
        widget_sampling = QtGui.QWidget()
        widget_sampling.setLayout(layout_sampling)
        layout.addWidget(widget_sampling)
        layout.addStretch()
        self.tab_receiver.setLayout(layout)

        self.set_sampling_instant(50)
        self.sampling_instant_text.editingFinished.connect(self.onChange_SamplingText)
        self.sampling_instant_slider.valueChanged[int].connect(self.onChange_SamplingInstantSlider)

        # Options frame
        self.opt_panel = GeneralOptionsPanel(self)
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.opt_panel)
        frame_options = QtGui.QGroupBox(title='General options')
        frame_options.setLayout(layout)

        # What to show
        def _add_checkbox(layout, title, connect_addr, i, j):
            checkbox = QtGui.QCheckBox(title)
            checkbox.toggle()
            checkbox.stateChanged.connect(connect_addr)
            layout.addWidget(checkbox, i, j)

        layout = QtGui.QGridLayout()
        _add_checkbox(layout, 'Input symbols', self.onCheckbox_InSymbols, 0, 0)
        _add_checkbox(layout, 'Output symbols', self.onCheckbox_OutSymbols, 1, 0)
        _add_checkbox(layout, 'Sent signal', self.onCheckbox_Sent, 0, 1)
        _add_checkbox(layout, 'Received signal', self.onCheckbox_Received, 1, 1)
        self.ber_label = QtGui.QLabel('BER: 0.0')
        layout.addWidget(self.ber_label)
        frame_what_to_show = QtGui.QGroupBox(title='What to show')
        frame_what_to_show.setLayout(layout)

        # Extra plots
        button_pulse = QtGui.QPushButton('Pulse')
        button_pulse.clicked.connect(self.onPlotPulse)
        button_eye = QtGui.QPushButton('Eye diagram')
        button_eye.clicked.connect(self.onPlotEye)
        layout = QtGui.QHBoxLayout()
        layout.addWidget(button_pulse)
        layout.addWidget(button_eye)
        frame_extra_plots = QtGui.QGroupBox(title='Extra plots')
        frame_extra_plots.setLayout(layout)

        self.plot_sent = True
        self.plot_insymbols = True
        self.plot_received = True
        self.plot_outsymbols = True

        self.pulse_formatter = PulseFomatter(self.pulse, self.symbol_rate, self.sps)
        self.matched_filter = MatchedFilter(self.pulse, self.sps)

        # Main layout
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        widget_left = QtGui.QWidget()
        widget_left.setLayout(layout)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(tabs)
        layout.addWidget(frame_options)
        layout.addWidget(frame_what_to_show)
        layout.addWidget(frame_extra_plots)
        widget_right = QtGui.QWidget()
        widget_right.setLayout(layout)

        layout = QtGui.QHBoxLayout()
        layout.addWidget(widget_left, 2)
        layout.addWidget(widget_right, 1)
        self.setLayout(layout)

        self.compute_and_plot()

    def onComboActivated_Source(self, text):
        for k in sources.collection:
            self.sources[k].setVisible(k == text)
        self.source = sources.collection[text]
        self.compute_and_plot()

    def onComboActivated_Pulse(self, text):
        for k in pulses.collection:
            self.pulses[k].setVisible(k == text)
        self.pulse = pulses.collection[text]
        self.compute_and_plot()

    def onComboActivated_Signaling(self, text):
        self.signaling = signaling.collection[text]
        self.compute_and_plot()

    def onComboActivated_ChannelFrequency(self, text):
        self.channel_frequency = channels_frequency.collection[text]
        for k in channels_frequency.collection:
            self.channels_frequency[k].setVisible(k == text)
        self.compute_and_plot()

    def onComboActivated_ChannelNoise(self, text):
        self.channel_noise = channels_noise.collection[text]
        for k in channels_noise.collection:
            self.channels_noise[k].setVisible(k == text)
        self.compute_and_plot()

    def onCheckbox_InSymbols(self, state):
        self.plot_insymbols = (state == QtCore.Qt.Checked)
        self.update_visible()

    def onCheckbox_Sent(self, state):
        self.plot_sent = (state == QtCore.Qt.Checked)
        self.update_visible()

    def onCheckbox_Received(self, state):
        self.plot_received = (state == QtCore.Qt.Checked)
        self.update_visible()

    def onCheckbox_OutSymbols(self, state):
        self.plot_outsymbols = (state == QtCore.Qt.Checked)
        self.update_visible()

    def onCheckbox_Matched(self, state):
        self.use_matched = (state == QtCore.Qt.Checked)
        self.compute_and_plot()

    def set_sampling_instant(self, value):
        self.sampling_instant = value
        self.sampling_instant_text.setText(str(value))
        self.sampling_instant_slider.setValue(int(value))

    def onChange_SamplingText(self):
        self.set_sampling_instant(int(self.sampling_instant_text.text()))
        self.compute_and_plot()

    def onChange_SamplingInstantSlider(self, val):
        self.set_sampling_instant(val)
        self.compute_and_plot(skip_fourier=True)

    def onPlotPulse(self):
        self.pulse_window = PulseWindow(self.pulse, parent=self)
        self.pulse_window.exec_()

    def onPlotEye(self):
        self.eye_window = EyeWindow(self.r, self.s, self.sps, self.sampling_instant, parent=self)
        self.eye_window.exec_()

    def compute_and_plot(self, *args, **kwargs):
        self.compute(*args, **kwargs)
        self.plot()

    def compute(self, skip_fourier=False):
        self.pulse_formatter.pulse = self.pulse
        self.pulse_formatter.symbol_rate = self.symbol_rate
        self.pulse_formatter.sps = self.sps
        self.matched_filter.pulse = self.pulse
        self.matched_filter.sps = self.sps
        self.channel_noise.sps = self.sps

        np.random.seed(self.seed)

        sps = self.sps  # samples per symbol
        fs = sps * self.symbol_rate  # sampling frequency [Hz]
        filt_len = self.filt_len  # filter length [Ts]
        s_inst = self.sampling_instant/100  # sampling instant [Ts]

        self.b = self.source.data()

        M = len(self.b)
        self.tk = np.arange(1, M + 1) + s_inst - 0.5

        Nt = (M + 1) * sps
        self.t = np.arange(0, Nt) / fs - 0.5*sps / fs

        Nf = 2**16
        self.f = np.arange(-Nf//2, Nf//2) * (fs/Nf)

        self.x = self.signaling.encode(self.b)
        self.s = self.pulse_formatter.encode(self.x, filt_len)
        self.r = self.channel_noise.channel(self.channel_frequency.channel(self.s, fs))
        if self.use_matched:
            self.r = self.matched_filter.filter(self.r, filt_len)
        self.y = self.r[(self.tk*sps).astype(int)]
        self.x_hat = self.signaling.detect(self.y)
        self.b_hat = self.signaling.decode(self.x_hat)

        if not skip_fourier:
            #~self.S = sp.fftpack.fftshift(sp.fftpack.fft(self.s, Nf)) / Nt
            #~self.R = sp.fftpack.fftshift(sp.fftpack.fft(self.r, Nf)) / Nt
            Ts = 1 / self.symbol_rate

            _, self.psd_S = sp.signal.periodogram(self.s, fs, return_onesided=False, nfft=Nf)
            self.psd_S = sp.fftpack.fftshift(self.psd_S)
            self.psd_S = np.convolve(self.psd_S, np.ones(sps) / sps, mode='same')
            _, self.psd_R = sp.signal.periodogram(self.r, fs, return_onesided=False, nfft=Nf)
            self.psd_R = sp.fftpack.fftshift(self.psd_R)
            self.psd_R = np.convolve(self.psd_R, np.ones(sps) / sps, mode='same')

        self.ber = np.count_nonzero(self.b - self.b_hat) / M

    def plot(self):
        Rs = self.symbol_rate  # symbol rate [baud]
        Ts = 1 / Rs  # symbol duration [s]
        M = len(self.tk)

        self.ax1 = self.figure.add_subplot(2, 1, 1)
        self.ax2 = self.figure.add_subplot(2, 1 ,2)
        self.ax1.cla()
        self.ax2.cla()

        # plot data
        self.ax1.axhline(0.0, color='k')
        self.plot_s = self.ax1.plot(self.t, self.s, 'b', linewidth=2)
        self.plot_r = self.ax1.plot(self.t, self.r, 'r', linewidth=2)
        self.plot_x = self.ax1.stem(self.tk*Ts - Ts/2, self.x, markerfmt='bo', linefmt='b-', basefmt='b.')
        self.plot_y = self.ax1.stem(self.tk*Ts - Ts/2, self.y, markerfmt='ro', linefmt='r-', basefmt='r.')
        self.plot_S = self.ax2.plot(self.f, self.psd_S, 'b', linewidth=2)
        self.plot_R = self.ax2.plot(self.f, self.psd_R, 'r', linewidth=2)

        self.ax1.grid()
        self.ax1.margins(0.05)
        self.ax1.xaxis.set_ticks(np.arange(0, M+1)*Ts)
        self.ax1.set_xlim(-Ts/2, M*Ts + Ts/2)
        self.ax1.set_xlabel('$t$ [s]')

        self.ax2.grid()
        self.ax2.margins(0.05)
        self.ax2.set_xlim(-6*Rs, 6*Rs)
        self.ax2.set_xlabel('$f$ [Hz]')

        self.ber_label.setText('BER: {:e}'.format(self.ber))

        plt.tight_layout()
        self.update_visible()

    def update_visible(self):
        self.plot_s[0].set_visible(self.plot_sent)
        self.plot_S[0].set_visible(self.plot_sent)

        self.plot_r[0].set_visible(self.plot_received)
        self.plot_R[0].set_visible(self.plot_received)

        self.plot_x[0].set_visible(self.plot_insymbols)
        for l in self.plot_x[1]:
            l.set_visible(self.plot_insymbols)
        self.plot_x[2].set_visible(self.plot_insymbols)

        self.plot_y[0].set_visible(self.plot_outsymbols)
        for l in self.plot_y[1]:
            l.set_visible(self.plot_outsymbols)
        self.plot_y[2].set_visible(self.plot_insymbols)

        self.canvas.draw()

    def closeEvent(self, event):
        plt.close(self.figure)


class GeneralOptionsPanel(QtGui.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent

        self.options = {
            'seed': ('Random Seed', 0),
            'sps': ('Samples per symbol', 32),
            'symbol_rate': ('Symbol rate [baud]', 1.0),
            'filt_len': ('Filter length [Tb]', 256)
        }

        self.initUI()

    def initUI(self):
        layout = QtGui.QFormLayout()
        self.text = {}

        for key, val in self.options.items():
            self.text[key] = QtGui.QLineEdit()
            layout.addRow(val[0] + ':', self.text[key])
            self.set_text(key, val[1])
            self.text[key].editingFinished.connect(lambda key=key: self.onChange_text(key))

        self.setLayout(layout)

    def set_text(self, key, value):
        setattr(self.parent, key, value)
        self.text[key].setText(str(value))

    def onChange_text(self, key):
        type_ = type(self.options[key][1])
        new_value = type_(self.text[key].text())
        if new_value != getattr(self.parent, key):
            self.set_text(key, new_value)
            self.parent.compute_and_plot()
        else:
            self.set_text(key, new_value)


class PulseWindow(QtGui.QDialog):
    def __init__(self, pulse, parent=None):
        super().__init__(parent)
        self.pulse = pulse
        self.parent = parent
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Pulse')

        # Figure
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)

        self.setLayout(layout)
        self.resize(800, 400)

        self.plot()

    def plot(self):
        ax1 = self.figure.add_subplot(1, 2, 1)
        ax2 = self.figure.add_subplot(1, 2, 2)

        sps, filt_len = self.parent.sps, self.parent.filt_len
        N = sps * filt_len // 2
        tx = np.arange(-N, N) / sps
        fx = np.arange(-N, N) * (sps / N)

        p = self.pulse.pulse(tx)
        P = sp.fftpack.fftshift(sp.fftpack.fft(p)) / sps

        ax1.plot(tx, p, 'k-', linewidth=2)
        ax2.plot(fx, abs(P), 'k-', linewidth=2)

        ax1.grid()
        ax1.margins(0.05)
        ax1.set_xlim(-self.pulse.tx_lim, self.pulse.tx_lim)
        ax1.set_xlabel('$t / T_\mathrm{b}$')
        ax2.grid()
        ax2.margins(0.05)
        ax2.set_xlim(-self.pulse.fx_lim, self.pulse.fx_lim)
        ax2.set_xlabel('$f / R_\mathrm{b}$')

        plt.tight_layout()
        self.canvas.draw()

    def closeEvent(self, event):
        plt.close(self.figure)


class EyeWindow(QtGui.QDialog):
    def __init__(self, r, s, sps, sampling_instant, parent=None):
        super().__init__(parent)
        self.r = r
        self.s = s
        self.sps = sps
        self.s_inst = sampling_instant/100
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Eye diagram')

        # Figure
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)

        self.setLayout(layout)
        self.resize(400, 400)

        self.plot()

    def plot(self):
        ax = self.figure.add_subplot(1, 1, 1)

        sps = self.sps
        t = np.arange(-2, sps + 2) / sps
        M = len(self.r) // sps

        ax.axhline(0.0, color='k')
        ax.axvline(self.s_inst, color='k', linewidth=2)

        for i in range(M - 1):
            ax.plot(t, self.s[i*sps + sps//2 - 2: (i+1)*sps + sps//2 + 2], 'b-', linewidth=2)
            ax.plot(t, self.r[i*sps + sps//2 - 2: (i+1)*sps + sps//2 + 2], 'r-', linewidth=2)

        ax.grid()
        ax.margins(0.05)
        ax.xaxis.set_ticks([0.00, 0.25, 0.50, 0.75, 1.00])
        ax.set_xlabel('$t / T_\mathrm{b}$')

        plt.tight_layout()
        self.canvas.draw()

    def closeEvent(self, event):
        plt.close(self.figure)


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)

    main = Window()
    main.show()

    sys.exit(app.exec_())
