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
        self.combo.addItem('Channel')
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
        layout.addWidget(self.canvas)

        widget = QtWidgets.QWidget(self)
        self.setCentralWidget(widget)
        widget.setLayout(layout)
        self.resize(600, 400)

    def plot(self):
        self.ax_t.cla()
        self.ax_t.grid(True)
        self.ax_t.set_xlabel('$t / T_\mathrm{s}$')

        self.ax_f.cla()
        self.ax_f.grid(True)
        self.ax_f.set_xlabel('$f / R_\mathrm{s}$')

        if self.selected == 'TX pulse':
            self._plot_tx()
        elif self.selected == 'Channel':
            self._plot_ch()

        self.figure.subplots_adjust(left=0.10, right=0.95, top=0.94, bottom=0.15, wspace=0.40)
        self.canvas.draw()

    def _plot_tx(self):
        tx_pulse = self.system.blocks[2].box.pulse  # FIXME: Refactor

        sps = self.system.sps
        filt_len = tx_pulse.filt_len
        Nt = (filt_len + 2) * sps
        Nf = max(1024, Nt)

        # Time domain
        tx = np.arange(-sps, Nt - sps) / sps
        h_tx = tx_pulse.pulse(tx)

        # Frequency domain
        fx = np.arange(-Nf//2, Nf//2) * (sps / Nf)
        H_tx = np.fft.fftshift(np.fft.fft(h_tx, Nf)) / sps

        if tx_pulse.is_square:
            self.ax_t.step(tx + filt_len//2, h_tx, 'k-', linewidth=2, where='post')
        else:
            self.ax_t.plot(tx + filt_len//2, h_tx, 'k-', linewidth=2)
        self.ax_t.axis(tx_pulse.ax_t_lim)

        self.ax_f.plot(fx, abs(H_tx), 'k-', linewidth=2)
        self.ax_f.axis(tx_pulse.ax_f_lim)

    def _plot_ch(self):
        sps = self.system.sps
        N = 128*sps

        # Time domain
        tx = np.arange(-N//2, N//2) / sps

        impulse = np.zeros(N)
        impulse[N//2] = sps
        h_ch = self.system.blocks[3].box.process(impulse)  # FIXME: Refactor

        # Frequency domain
        fx = np.arange(-N//2, N//2) * (sps / N)
        H_ch = np.fft.fftshift(np.fft.fft(h_ch, N)) / sps

        self.ax_t.plot(tx, h_ch, 'k-', linewidth=2)
        self.ax_t.set_xlim([-2.0, 2.0])

        self.ax_f.plot(fx, abs(H_ch), 'k-', linewidth=2)
        self.ax_f.set_xlim([-6.0, 6.0])

    def onComboActivated(self, idx):
        self.selected = self.combo.currentText()
        self.plot()
