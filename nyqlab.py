#!/usr/bin/env python3

import functools
import os
import sys

import numpy as np

from PyQt5 import QtCore, QtGui, QtWidgets

import matplotlib
matplotlib.use("Qt5Agg")

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar


import sources, encoder, tx_filter, channels_frequency, channels_noise, rx_filter, sampler, decoder

from system_simulator import SystemSimulator, Block
from system_diagram import SystemDiagram, BlockD, ConnectionD

from window_pulse import WindowPulse
from window_eye import WindowEye


class Window(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setupSystem()
        self.setupSystemDiagram()
        self.setupOptions()
        self.initUI()

        self.compute_and_plot()

    def setupSystem(self):
        blocks_s = [
            Block(sources, 'D'),
            Block(encoder, 'D'),
            Block(tx_filter, 'C'),
            Block(channels_frequency, 'C'),
            Block(channels_noise, 'C'),
            Block(rx_filter, 'C'),
            Block(sampler, 'D'),
            Block(decoder, 'D'),
        ]

        self.system = SystemSimulator(blocks_s)

        # Ugly monkey patch:
        for block in self.system.blocks:
            block.box.system = self.system

    def setupSystemDiagram(self):
        blocks_d = [
            BlockD('Source',                            (1, 0, 1, 1),           alias='Src'),
            BlockD('Encoder',                           (3, 0, 2, 1)),
            BlockD('Transmit filter',                   (8, 0, 2, 1),           alias='TX filter'),
            BlockD('Channel frequency response',        (10, 1.5, 2, 1),        alias='Freq'),
            BlockD('Channel noise',                     (10, 3, 2, 1),          alias='Noise'),
            BlockD('Receive filter',                    (8, 4.5, 2, 1),         alias='RX filter'),
            BlockD('Sampler',                           (5.5, 4.5, 2, 1)),
            BlockD('Decoder',                           (3, 4.5, 2, 1))
        ]

        connections_d = [
            ConnectionD('Bits',                         [(2, 0.5), (3, 0.5)],               (0x00, 0x00, 0x00)),
            ConnectionD('Input symbols',                [(5, 0.5), (8, 0.5)],               (0x00, 0x00, 0xFF)),
            ConnectionD('Sent signal',                  [(10, 0.5), (11, 0.5), (11, 1.5)],  (0x00, 0x00, 0xFF)),
            ConnectionD('Channel output (no noise)',    [(11, 2.5), (11, 3)],               (0x00, 0x80, 0x00)),
            ConnectionD('Received signal',              [(11, 4), (11, 5), (10, 5)],        (0xFF, 0x00, 0xFF)),
            ConnectionD('Receive filter output',        [(8, 5), (7.5, 5)],                 (0xFF, 0x00, 0x00), True),
            ConnectionD('Output symbols',               [(5.5, 5), (5, 5)],                 (0xFF, 0x00, 0x00)),
            ConnectionD('Estimated bits',               [(2, 5), (3.5, 5)],                 (0xD4, 0xAF, 0x37)),
        ]

        self.system_diagram = SystemDiagram(self, self.system, blocks_d, connections_d)

    def setupOptions(self):
        self.options_general = {
            'seed': 'Random Seed',
            'sps': 'Samples per symbol',
            'bit_rate': 'Bit rate [bit/s]',
        }

        self.show_n_symbols = 20
        self.show_psd = False
        self.options_visualization = {
            'show_n_symbols': 'Number of symbols to show',
            'show_psd': 'Show power spectral density',
        }

    def _getBlocksOptionsWidget(self, idx):
        block = self.system.blocks[idx]
        block_name = self.system_diagram.blocks_d[idx].name

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(QtWidgets.QLabel('<b>{}:</b>'.format(block_name)))

        combo = QtWidgets.QComboBox(self)
        for name, obj in block.module.choices:
            combo.addItem(name)
        combo.activated[int].connect(functools.partial(self.onBlockComboActivated, idx))
        layout.addWidget(combo)

        block_choice = []
        for idx_choice, (name, obj) in enumerate(block.module.choices):
            w = obj.widget()
            w.setVisible(idx_choice == 0)
            if hasattr(w, 'update_signal'):
                w.update_signal.connect(self.compute_and_plot)
            block_choice.append(w)
            layout.addWidget(w)

        layout.addStretch()

        widget = QtWidgets.QWidget()
        widget.setLayout(layout)

        return widget, block_choice

    def initUI(self):
        self.setWindowTitle('NyqLab')

        # Figure
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)

        # BER label
        self.ber_text = QtWidgets.QLabel('<b>BER</b>')

        # Axis
        self.ax_t = self.figure.add_subplot(2, 1, 1)
        self.ax_f = self.figure.add_subplot(2, 1, 2)
        self.update_axis(True)

        # Construct widgets for block options
        self.block_options = []
        self.block_choices = []
        for i in range(len(self.system.blocks)):
            widget, block_choice = self._getBlocksOptionsWidget(i)
            self.block_options.append(widget)
            self.block_choices.append(block_choice)

        # General options frame
        self.panel_options_general = PanelOptions(self, 'General options', self.system, self.options_general)
        self.panel_options_visualization = PanelOptions(self, 'Visualization options', self, self.options_visualization)

        # Toolbar
        action_options_general = QtWidgets.QAction(QtGui.QIcon.fromTheme('preferences-desktop'), 'General options', self)
        action_options_general.triggered.connect(self.showGeneralOptions)

        action_view_pulse = QtWidgets.QAction(QtGui.QIcon('media/pulse'), 'View pulse', self)
        action_view_pulse.triggered.connect(self.showWindowPulse)

        action_view_eye = QtWidgets.QAction(QtGui.QIcon('media/eye'), 'View eye diagram', self)
        action_view_eye.triggered.connect(self.showWindowEye)

        xtoolbar = QtWidgets.QToolBar()
        xtoolbar.addAction(action_options_general)
        xtoolbar.addAction(action_view_pulse)
        xtoolbar.addAction(action_view_eye)

        # Main layout
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        widget_right = QtWidgets.QWidget()
        widget_right.setLayout(layout)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(xtoolbar)
        layout.addWidget(self.system_diagram)
        for w in self.block_options:
            layout.addWidget(w)
        layout.addWidget(self.panel_options_general)
        layout.addWidget(self.panel_options_visualization)
        layout.addWidget(self.ber_text)

        widget_left = QtWidgets.QWidget()
        widget_left.setLayout(layout)

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(widget_left, 1)
        layout.addWidget(widget_right, 2)
        self.setLayout(layout)

        self.showBlockOption(0)

    def showBlockOption(self, idx):
        self.panel_options_general.setVisible(False)
        self.panel_options_visualization.setVisible(False)
        for (i, w) in enumerate(self.block_options):
            w.setVisible(i == idx)

    def showGeneralOptions(self):
        for (i, w) in enumerate(self.block_options):
            w.setVisible(False)
        self.panel_options_general.setVisible(True)
        self.panel_options_visualization.setVisible(True)

    def onBlockComboActivated(self, idx_block, idx_choice):
        block = self.system.blocks[idx_block]

        for (i, widget) in enumerate(self.block_choices[idx_block]):
            widget.setVisible(i == idx_choice)

        block.box = block.module.choices[idx_choice][1]
        block.box.system = self.system

        self.compute_and_plot()

    def toggleSignal(self, idx):
        self.system_diagram.connections_d[idx].visible ^= True
        self.update_visible()

    def showWindowPulse(self):
        self.pulse_window = WindowPulse(parent=self)
        self.pulse_window.exec_()

    def showWindowEye(self):
        self.eye_window = WindowEye(parent=self)
        self.eye_window.exec_()

    def compute_and_plot(self):
        self.compute()
        self.plot()

    def compute(self):
        self.system.processData()
        self.system.processSpectra()
        self.system.processAxes()

    def update_axis(self, first_run=False):
        Ns = self.show_n_symbols
        Ts = 1 / self.system.symbol_rate

        if first_run:
            axis_t = [-Ts, Ns*Ts, -1.5, 1.5]
            axis_f = [-5.0, 5.0, -0.5, 6.0]
        else:
            axis_t = self.ax_t.axis()
            axis_f = self.ax_f.axis()

        self.ax_t.cla()
        self.ax_t.grid(True)
        self.ax_t.margins(0.05)
        self.ax_t.set_xlabel('$t$ [s]')
        self.ax_t.axhline(0.0, color='k')
        self.ax_t.axis(axis_t)

        self.ax_f.cla()
        self.ax_f.grid(True)
        self.ax_f.margins(0.05)
        self.ax_f.set_xlabel('$f$ [Hz]')
        self.ax_f.axhline(0.0, color='k')
        self.ax_f.axis(axis_f)

    def plot(self):
        self.update_axis()

        self.plots_t = []
        self.plots_f = []
        for (data_t, data_f, block, connection) in zip(self.system.data_t, self.system.data_f, self.system.blocks, self.system_diagram.connections_d):
            color = tuple(x / 255 for x in connection.color)
            if block.out_type == 'C':
                lines_t = [self.ax_t.plot(self.system.t, data_t, color=color, linewidth=2)]
                lines_f = [self.ax_f.plot(self.system.f, data_f, color=color, linewidth=2)]
            elif block.out_type == 'D':
                x = np.repeat(self.system.tk, 2)
                y = np.dstack((np.zeros(data_t.shape[0]), data_t)).flatten()
                lines_t = [self.ax_t.step(x, y, color=color, linewidth=1),
                           self.ax_t.scatter(x[1::2], y[1::2], color=color, linewidth=1)]
                lines_f = []
            self.plots_t.append(lines_t)
            self.plots_f.append(lines_f)

        self.ber_text.setText('<b>BER</b>: {:.2E}'.format(self.system.ber))

        self.update_visible()

    def update_visible(self):
        for (lines_t, lines_f, connection) in zip(self.plots_t, self.plots_f, self.system_diagram.connections_d):
            plt.setp(lines_t + lines_f, visible=connection.visible)
        self.canvas.draw()

    def closeEvent(self, event):
        plt.close(self.figure)


class PanelOptions(QtWidgets.QWidget):
    def __init__(self, parent, label, obj, options):
        super().__init__(parent)
        self.parent = parent
        self.label = label
        self.obj = obj
        self.options = options

        self.initUI()

    def initUI(self):
        layout = QtWidgets.QFormLayout()
        layout.addRow(QtWidgets.QLabel('<b>{}:</b>'.format(self.label)), QtWidgets.QWidget())

        self.text = {}

        for key in self.options:
            label = self.options[key]
            self.text[key] = QtWidgets.QLineEdit()
            self.text[key].setText(str(getattr(self.obj, key)))
            self.text[key].editingFinished.connect(lambda key=key: self.onChange_text(key))
            layout.addRow(label + ':', self.text[key])

        self.setLayout(layout)

    def onChange_text(self, key):
        old_value = getattr(self.obj, key)
        new_value = (type(old_value))(self.text[key].text())
        if new_value != old_value:
            self.text[key].setText(str(new_value))
            setattr(self.obj, key, new_value)
            self.parent.update_axis(True)
            self.parent.compute_and_plot()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)

    main = Window()
    main.show()

    sys.exit(app.exec_())
