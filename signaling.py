import collections

import numpy as np

from PyQt5 import QtCore, QtWidgets


def slicer(y, thresholds, values):
    thresholds = np.hstack([-np.inf, thresholds, np.inf])
    x_hat = np.empty_like(y)
    for t0, t1, v in zip(thresholds[:-1], thresholds[1:], values):
        x_hat[(t0 < y) & (y <= t1)] = v
    return x_hat

def unmap(x, values):
    bits = np.empty_like(x, dtype=np.int)
    for b, v in enumerate(values):
        bits[x == v] = b
    return bits


class SignalingScheme:
    def widget(self):
        try:
            return globals()[self.__class__.__name__ + '_Widget'](self)
        except KeyError:
            return QtWidgets.QLabel('<i>No options available for this signaling scheme.</i>')


class MemorylessSignalingScheme(SignalingScheme):
    def __init__(self, values, thresholds):
        self.values = np.array(values)
        self.thresholds = np.array(thresholds)

    def encode(self, bits):
        return self.values[bits]

    def decode(self, y):
        return unmap(slicer(y, self.thresholds, self.values), self.values)


class SequenceStateSignalingScheme(SignalingScheme):
    def __init__(self, finite_state_machine, ):
        self.finite_state_machine = finite_state_machine

    def encode(self, bits, initial_state=0):
        fsm = self.finite_state_machine
        state = initial_state
        x = np.empty_like(bits)
        for (i, b) in enumerate(bits):
            state, x[i] = fsm[state, b]
        return x

    def decode(self, y):
        raise NotImplementedError


class Unipolar_Signaling(MemorylessSignalingScheme):
    def __init__(self):
        super().__init__(values=[0.0, 1.0], thresholds=[0.5])

    def acorr(self, ell):
        if ell == 0:
            return 0.5
        else:
            return 0.25


class Polar_Signaling(MemorylessSignalingScheme):
    def __init__(self):
        super().__init__(values=[-1.0, 1.0], thresholds=[0.0])

    def acorr(self, ell):
        if ell == 0:
            return 1.0
        else:
            return 0.0


class AMI_Signaling(SequenceStateSignalingScheme):
    def __init__(self):
        fsm = {(0, 0): (0, 0.0), (0, 1): (1,  1.0),
               (1, 0): (1, 0.0), (1, 1): (0, -1.0)}
        super().__init__(finite_state_machine=fsm)

    def decode(self, y):  # Not optimal!
        values = [0.0, 1.0]
        thresholds = [0.5]
        return unmap(slicer(np.abs(y), thresholds, values), values)

    def acorr(self, ell):
        if ell == 0:
            return 0.5
        elif abs(ell) == 1:
            return -0.25
        else:
            return 0.0


class MLT3_Signaling(SequenceStateSignalingScheme):
    def __init__(self):
        fsm = {(0, 0): (0,  0.0), (0, 1): (1,  1.0),
               (1, 0): (1,  1.0), (1, 1): (2,  0.0),
               (2, 0): (2,  0.0), (2, 1): (3, -1.0),
               (3, 0): (3, -1.0), (3, 1): (0,  0.0)}
        super().__init__(finite_state_machine=fsm)

    def decode(self, y):  # Not optimal!
        values = [-1.0, 0.0, 1.0]
        thresholds = [-0.5, 0.5]
        bits_hat = np.zeros(np.size(y), dtype=np.int)
        x_hat = unmap(slicer(y, thresholds, values), values)
        for i in range(len(x_hat)):
            bits_hat[i] = (x_hat[i] != x_hat[i - 1])
        return bits_hat


collection = collections.OrderedDict([
    ('Polar (Antipodal)', Polar_Signaling()),
    ('Unipolar (On-off)', Unipolar_Signaling()),
    ('Alternate Mark Inversion (AMI)', AMI_Signaling()),
    ('Multi-Level Transmit 3 (MLT-3)', MLT3_Signaling())
])
