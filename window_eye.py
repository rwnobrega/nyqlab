from PyQt5 import QtCore, QtWidgets

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

import numpy as np
import scipy as sp


class WindowEye(QtWidgets.QDialog):
    def __init__(self, parent):
        super().__init__(parent)

        self.parent = parent

        self.initUI()
        self.plot()

    def initUI(self):
        self.setWindowTitle('Eye diagram')

        # Figure
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)

        self.setLayout(layout)
        self.resize(400, 400)

    def plot(self):
        sps = self.parent.system.sps
        Ns = self.parent.system.n_symbols
        s = self.parent.system.data_t[2]
        r = self.parent.system.data_t[5]
        samp_inst = 0.5

        t = np.arange(-2, sps + 2) / sps

        ax = self.figure.add_subplot(1, 1, 1)
        ax.axhline(0.0, color='k')
        ax.axvline(samp_inst, color='k', linewidth=2)

        for i in range(Ns - 1):
            ax.plot(t, s[i*sps + sps//2 - 2: (i+1)*sps + sps//2 + 2], 'b-', linewidth=2)
            ax.plot(t, r[i*sps + sps//2 - 2: (i+1)*sps + sps//2 + 2], 'r-', linewidth=2)

        ax.grid()
        ax.margins(0.05)
        ax.xaxis.set_ticks([0.00, 0.25, 0.50, 0.75, 1.00])
        ax.set_xlabel('$t / T_\mathrm{s}$')

        plt.tight_layout()
        self.canvas.draw()

    def closeEvent(self, event):
        plt.close(self.figure)
