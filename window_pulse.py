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

        # Axis
        self.ax_t = self.figure.add_subplot(1, 2, 1)
        self.ax_f = self.figure.add_subplot(1, 2, 2)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(toolbar)
        layout.addWidget(self.canvas)

        widget = QtWidgets.QWidget(self)
        self.setCentralWidget(widget)
        widget.setLayout(layout)
        self.resize(600, 300)

    def plot(self):
        pulse = self.system.pulse
        sps = self.system.sps
        filt_len = self.system.pulse.filt_len
        Nt = (filt_len + 2) * sps
        Nf = max(1024, Nt)

        # Time domain
        tx = np.arange(-sps, Nt - sps) / sps
        p = pulse.pulse(tx)
        self.ax_t.cla()
        if pulse.is_square:
            self.ax_t.step(tx + filt_len//2, p, 'k-', linewidth=2, where='post')
        else:
            self.ax_t.plot(tx + filt_len//2, p, 'k-', linewidth=2)
        self.ax_t.grid(True)
        self.ax_t.set_xlabel('$t / T_\mathrm{s}$')
        self.ax_t.set_xlim(pulse.tx_lim)

        # Frequency domain
        fx = np.arange(-Nf//2, Nf//2) * (sps / Nf)
        P = np.fft.fftshift(np.fft.fft(p, Nf)) / sps
        self.ax_f.cla()
        self.ax_f.plot(fx, abs(P), 'k-', linewidth=2)
        self.ax_f.grid(True)
        self.ax_f.set_xlabel('$f / R_\mathrm{s}$')
        self.ax_f.set_xlim(pulse.fx_lim)

        self.canvas.draw()
        plt.tight_layout()
