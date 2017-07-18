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
        s_inst = self.parent.system.sampling_instant

        t = np.arange(-sps, 2*sps) / sps

        ax = self.figure.add_subplot(1, 1, 1)
        ax.axhline(0.0, color='k', linewidth=3)
        ax.axvline(0.5, color='k', linewidth=3)

        for i in range(1, min(Ns, 100)):
            ax.plot(t - s_inst, s[i*sps - sps//2: (i+2)*sps + sps//2], 'b-', linewidth=2)
            ax.plot(t - s_inst, r[i*sps - sps//2: (i+2)*sps + sps//2], 'r-', linewidth=2)

        ax.grid()
        ax.margins(0.05)
        ax.xaxis.set_ticks(np.arange(-1.0, 2.0, step=0.25))
        ax.set_xlim([-0.1, 1.1])
        ax.set_xlabel('$t / T_\mathrm{s}$')

        plt.tight_layout()
        self.canvas.draw()

    def closeEvent(self, event):
        plt.close(self.figure)
