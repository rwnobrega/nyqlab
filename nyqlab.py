#!/usr/bin/env python3

import functools
import sys

from PyQt5 import QtGui, QtWidgets

import sources, encoder, tx_filter, channels_frequency, channels_noise, rx_filter, sampler, decoder

from system_simulator import SystemSimulator, Block
from system_diagram import SystemDiagram, BlockD, ConnectionD

from window_scope import WindowScope
from window_pulse import WindowPulse


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setupSystem()
        self.setupSystemDiagram()
        self.setupOptions()
        self.initUI()
        self.compute()

        self.window_scope = WindowScope(parent=self, system=self.system)
        self.window_pulse = WindowPulse(parent=self, system=self.system)

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
        self.move(0, 0)

        # BER label
        self.ber_text = QtWidgets.QLabel()

        # Construct widgets for block options
        self.block_options = []
        self.block_choices = []
        for i in range(len(self.system.blocks)):
            widget, block_choice = self._getBlocksOptionsWidget(i)
            self.block_options.append(widget)
            self.block_choices.append(block_choice)

        # General options frame
        self.panel_options_general = PanelOptions(self, 'General options', self.system, self.options_general)

        # Toolbar
        action_options_general = QtWidgets.QAction(QtGui.QIcon.fromTheme('preferences-desktop'), 'General options', self)
        action_options_general.triggered.connect(self.showGeneralOptions)

        action_view_scope = QtWidgets.QAction(QtGui.QIcon.fromTheme('utilities-system-monitor'), 'Scope', self)
        action_view_scope.triggered.connect(self.showWindowScope)

        action_view_pulse = QtWidgets.QAction(QtGui.QIcon('media/pulse'), 'View pulse', self)
        action_view_pulse.triggered.connect(self.showWindowPulse)

        toolbar = QtWidgets.QToolBar()
        toolbar.addAction(action_options_general)
        toolbar.addAction(action_view_scope)
        toolbar.addAction(action_view_pulse)

        # Main layout
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(toolbar)
        layout.addWidget(self.system_diagram)
        for w in self.block_options:
            layout.addWidget(w)
        layout.addWidget(self.panel_options_general)
        layout.addWidget(self.ber_text)

        central_widget = QtWidgets.QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self.showBlockOption(0)

    def showBlockOption(self, idx):
        self.panel_options_general.setVisible(False)
        for (i, w) in enumerate(self.block_options):
            w.setVisible(i == idx)

    def showGeneralOptions(self):
        for (i, w) in enumerate(self.block_options):
            w.setVisible(False)
        self.panel_options_general.setVisible(True)

    def onBlockComboActivated(self, idx_block, idx_choice):
        block = self.system.blocks[idx_block]

        for (i, widget) in enumerate(self.block_choices[idx_block]):
            widget.setVisible(i == idx_choice)

        block.box = block.module.choices[idx_choice][1]
        block.box.system = self.system

        self.compute_and_plot()

    def toggleSignal(self, idx):
        self.system_diagram.connections_d[idx].visible ^= True
        self.window_scope.update_visible()

    def showWindowScope(self):
        self.window_scope.show()

    def showWindowPulse(self):
        self.window_pulse.show()

    def compute_and_plot(self):
        self.compute()
        self.window_scope.plot()
        self.window_pulse.plot()

    def compute(self):
        self.system.process()
        ber_str = '{:.2E}'.format(self.system.ber) if self.system.ber != 0 else '0'
        self.ber_text.setText('<b>BER</b>: {}'.format(ber_str))


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
            self.parent.compute_and_plot()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)

    main_window = MainWindow()
    main_window.show()
    main_window.showWindowScope()


    sys.exit(app.exec_())
