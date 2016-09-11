from PyQt4 import QtCore, QtGui

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar

import numpy as np
import scipy as sp


class WindowPulse(QtGui.QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

        self.initUI()
        self.plot()

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

    def plot(self):
        pulse = self.parent.system.pulse
        sps = self.parent.system.sps
        filt_len = self.parent.system.pulse.filt_len

        ax_t = self.figure.add_subplot(1, 2, 1)
        ax_f = self.figure.add_subplot(1, 2, 2)

        N = sps * filt_len // 2
        tx = np.arange(-N, N) / sps
        fx = np.arange(-N, N) * (sps / N)

        p = pulse.pulse(tx)
        P = sp.fftpack.fftshift(sp.fftpack.fft(p)) / sps

        ax_t.plot(tx, p, 'k-', linewidth=2)
        ax_f.plot(fx, abs(P), 'k-', linewidth=2)

        ax_t.grid()
        ax_t.margins(0.05)
        ax_t.set_xlim(-pulse.tx_lim, pulse.tx_lim)
        ax_t.set_xlabel('$t / T_\mathrm{s}$')
        ax_f.grid()
        ax_f.margins(0.05)
        ax_f.set_xlim(-pulse.fx_lim, pulse.fx_lim)
        ax_f.set_xlabel('$f / R_\mathrm{s}$')

        plt.tight_layout()
        self.canvas.draw()

    def closeEvent(self, event):
        plt.close(self.figure)
