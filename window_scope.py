from PyQt5 import QtGui, QtWidgets

import matplotlib
matplotlib.use("Qt5Agg")

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

import numpy as np


class WindowScope(QtWidgets.QMainWindow):
    def __init__(self, parent, system):
        super().__init__(parent)

        self.parent = parent
        self.system = system
        self.show_eye_diagram = False

        self.ax_t_lim_free = [-1.0, 21.0, -1.5, 1.5]
        self.ax_t_lim_eyed = [-0.1, 1.1, -1.5, 1.5]
        self.ax_f_lim = [-5.0, 5.0, -0.5, 6.0]

        self.initUI()
        self.plot()

    def initUI(self):
        self.setWindowTitle('NyqLab: Scope')

        # Figure
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        toolbar = NavigationToolbar(self.canvas, self)

        # Eye diagram toolbar button
        action_eye = QtWidgets.QAction(QtGui.QIcon('media/eye'), 'Scope', self)
        action_eye.triggered.connect(self.onEyeClick)
        toolbar.addAction(action_eye)

        # Axis
        self.ax_t = self.figure.add_subplot(2, 1, 1)
        self.ax_t.grid(True)
        self.ax_t.set_xlabel('$t / T_\mathrm{b}$')
        self.ax_t.axis(self.ax_t_lim_free)

        self.ax_f = self.figure.add_subplot(2, 1, 2)
        self.ax_f.axis(self.ax_f_lim)
        self.ax_f.grid(True)
        self.ax_f.set_xlabel('$f / R_\mathrm{b}$')

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(toolbar)
        layout.addWidget(self.canvas)

        widget = QtWidgets.QWidget(self)
        self.setCentralWidget(widget)
        widget.setLayout(layout)
        self.resize(800, 600)

    def plot(self):
        Ns = self.system.n_symbols
        sps = self.system.sps
        s_inst = self.system.sampling_instant

        # Time domain
        self.ax_t.lines = []
        self.ax_t.collections = []
        self.plots_t = []
        if not self.show_eye_diagram:
            self.ax_t.axhline(0.0, color='k')
            t = self.system.t
            # TODO: Should not need system diagram.
            for (data_t, block, connection) in zip(self.system.data_t, self.system.blocks, self.parent.system_diagram.connections_d):
                color = tuple(x / 255 for x in connection.color)
                if block.out_type == 'C':
                    lines_t = [self.ax_t.plot(t, data_t, color=color, linewidth=2)]
                elif block.out_type == 'D':
                    x = np.repeat(self.system.tk, 2)
                    y = np.dstack((np.zeros(data_t.shape[0]), data_t)).flatten()
                    lines_t = [self.ax_t.step(x, y, color=color, linewidth=1),
                               self.ax_t.scatter(x[1::2], y[1::2], color=color, linewidth=1)]
                self.plots_t.append(lines_t)
        else:
            self.ax_t.axhline(0.0, color='k', linewidth=3)
            self.ax_t.axvline(0.5, color='k', linewidth=3)
            t = np.arange(-sps, 2*sps) / sps - s_inst
            for (data_t, block, connection) in zip(self.system.data_t, self.system.blocks, self.parent.system_diagram.connections_d):
                color = tuple(x / 255 for x in connection.color)
                if block.out_type == 'C':
                    lines_t = [self.ax_t.plot(t, data_t[i*sps - sps//2: (i+2)*sps + sps//2], color=color, linewidth=2)
                               for i in range(1, min(Ns, 100))]
                elif block.out_type == 'D':
                    # TODO: Implement me.
                    lines_t = []
                self.plots_t.append(lines_t)

        # Frequency domain
        self.ax_f.lines = []
        self.plots_f = []
        self.ax_f.axhline(0.0, color='k')
        f = self.system.f
        for (data_f, block, connection) in zip(self.system.data_f, self.system.blocks, self.parent.system_diagram.connections_d):
            color = tuple(x / 255 for x in connection.color)
            if block.out_type == 'C':
                lines_f = [self.ax_f.plot(f, data_f, color=color, linewidth=2)]
            else:
                lines_f = []
            self.plots_f.append(lines_f)

        self.update_visible()

    def update_visible(self):
        for (lines_t, lines_f, connection) in zip(self.plots_t, self.plots_f, self.parent.system_diagram.connections_d):
            plt.setp(lines_t + lines_f, visible=connection.visible)
        self.canvas.draw()

    def onEyeClick(self, idx):
        self.show_eye_diagram ^= True
        if not self.show_eye_diagram:
            self.ax_t_lim_eyed = self.ax_t.axis()
            self.ax_t.axis(self.ax_t_lim_free)
        else:
            self.ax_t_lim_free = self.ax_t.axis()
            self.ax_t.axis(self.ax_t_lim_eyed)
        self.plot()
