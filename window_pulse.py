from PyQt5 import QtGui, QtWidgets

import matplotlib
matplotlib.use("Qt5Agg")

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

import numpy as np

from rx_filter import Bypass_ReceiveFilter


class WindowPulse(QtWidgets.QMainWindow):
    def __init__(self, parent, system):
        super().__init__(parent)

        self.parent = parent
        self.system = system
        self.selected = 'TX pulse'

        self.initUI()
        self.plot()

    def initUI(self):
        self.setWindowTitle('NyqLab: Pulse')

        # Figure
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        toolbar = NavigationToolbar(self.canvas, self)

        # Combo
        self.combo = QtWidgets.QComboBox()
        self.combo.addItem('TX pulse')
        self.combo.addItem('Channel response')
        self.combo.addItem('Effective pulse')
        self.combo.activated[int].connect(self.onComboActivated)

        # Axis
        self.ax_t = self.figure.add_subplot(1, 2, 1)
        self.ax_f = self.figure.add_subplot(1, 2, 2)

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(toolbar)
        layout.addWidget(self.combo)
        widget_top = QtWidgets.QWidget()
        widget_top.setLayout(layout)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(widget_top)
        layout.addWidget(self.canvas, 1)

        widget = QtWidgets.QWidget(self)
        self.setCentralWidget(widget)
        widget.setLayout(layout)
        self.resize(600, 400)

    def compute(self):
        sps = self.system.sps
        Ns = 256
        N = (Ns + 2) * sps

        # Axes
        self.t = np.arange(-N//2, N//2) / sps
        self.f = np.arange(-N//2, N//2) * (sps / N)

        # Impulse responses
        impulse_d = np.zeros(Ns); impulse_d[Ns//2] = 1
        impulse_c = np.zeros(N); impulse_c[N//2] = sps
        self.h_tx = self.system.blocks[2].box.process(impulse_d)
        self.h_ch = self.system.blocks[3].box.process(impulse_c)
        self.h_rx = self.system.blocks[5].box.process(impulse_c)
        self.h_ep = self.system.blocks[5].box.process(self.system.blocks[3].box.process(self.h_tx))

        # Frequency responses
        self.H_tx = np.fft.fftshift(np.fft.fft(self.h_tx)) / sps
        self.H_ch = np.fft.fftshift(np.fft.fft(self.h_ch)) / sps
        self.H_rx = np.fft.fftshift(np.fft.fft(self.h_rx)) / sps
        self.H_ep = np.fft.fftshift(np.fft.fft(self.h_ep)) / sps

    def plot(self):
        self.compute()

        self.ax_t.cla()
        self.ax_t.grid(True)
        self.ax_t.set_xlabel('$t / T_\mathrm{s}$')

        self.ax_f.cla()
        self.ax_f.grid(True)
        self.ax_f.set_xlabel('$f / R_\mathrm{s}$')

        if self.selected == 'TX pulse':
            self._plot_tx()
        elif self.selected == 'Channel response':
            self._plot_ch()
        elif self.selected == 'Effective pulse':
            self._plot_ep()

        self.figure.subplots_adjust(left=0.10, right=0.95, top=0.94, bottom=0.15, wspace=0.40)
        self.canvas.draw()

    def _plot_tx(self):
        tx = self.system.blocks[2].box

        self.ax_t.plot(self.t + tx.pulse.filt_len/2, self.h_tx, 'k-', linewidth=2)
        self.ax_t.axis(tx.pulse.ax_t_lim)

        self.ax_f.plot(self.f, abs(self.H_tx), 'k-', linewidth=2)
        self.ax_f.axis(tx.pulse.ax_f_lim)

    def _plot_ch(self):
        self.ax_t.plot(self.t, self.h_ch, 'k-', linewidth=2)
        self.ax_t.set_xlim([-2.0, 2.0])

        self.ax_f.plot(self.f, abs(self.H_ch), 'k-', linewidth=2)
        self.ax_f.set_xlim([-6.0, 6.0])

    def _plot_ep(self):
        tx = self.system.blocks[2].box
        rx = self.system.blocks[5].box

        # FIXME: Refactor
        t_lim = tx.pulse.ax_t_lim[:]
        delay = tx.pulse.filt_len/2
        if not isinstance(rx, Bypass_ReceiveFilter):
            t_lim[0] -= 0.5
            t_lim[1] += 1.5
            delay += 0.5

        self.ax_t.plot(self.t + delay, self.h_ep, 'k-', linewidth=2)
        self.ax_t.axis(t_lim)

        self.ax_f.plot(self.f, abs(self.H_ep), 'k-', linewidth=2)
        self.ax_f.axis(tx.pulse.ax_f_lim)

    def onComboActivated(self, idx):
        self.selected = self.combo.currentText()
        self.plot()
