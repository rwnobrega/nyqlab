from PyQt5 import QtGui, QtWidgets

import matplotlib
matplotlib.use("Qt5Agg")

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

import numpy as np


class WindowPulse(QtWidgets.QMainWindow):
    def __init__(self, parent, system):
        super().__init__(parent)

        self.parent = parent
        self.system = system

        self.initUI()
        self.plot()

    def initUI(self):
        self.setWindowTitle('NyqLab: Pulse')

        # Figure
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        toolbar = NavigationToolbar(self.canvas, self)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(toolbar)
        layout.addWidget(self.canvas)

        widget = QtWidgets.QWidget(self)
        self.setCentralWidget(widget)
        widget.setLayout(layout)
        self.resize(800, 400)

    def plot(self):
        pulse = self.parent.system.pulse
        sps = self.parent.system.sps
        filt_len = self.parent.system.pulse.filt_len

        Nt = (filt_len + 2) * sps
        Nf = max(1024, Nt)

        tx = np.arange(-sps, Nt - sps) / sps
        fx = np.arange(-Nf//2, Nf//2) * (sps / Nf)

        p = pulse.pulse(tx)
        P = np.fft.fftshift(np.fft.fft(p, Nf)) / sps

        ax_t = self.figure.add_subplot(1, 2, 1)
        ax_f = self.figure.add_subplot(1, 2, 2)

        if pulse.is_square:
            ax_t.step(tx + filt_len//2, p, 'k-', linewidth=2, where='post')
        else:
            ax_t.plot(tx + filt_len//2, p, 'k-', linewidth=2)
        ax_f.plot(fx, abs(P), 'k-', linewidth=2)

        ax_t.grid(True)
        ax_t.margins(0.05)
        ax_t.set_xlim(pulse.tx_lim)
        ax_t.set_xlabel('$t / T_\mathrm{s}$')
        ax_f.grid(True)
        ax_f.margins(0.05)
        ax_f.set_xlim(pulse.fx_lim)
        ax_f.set_xlabel('$f / R_\mathrm{s}$')

        plt.tight_layout()
        self.canvas.draw()
