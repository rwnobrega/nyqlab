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
    b = np.empty_like(x)
    for i, v in enumerate(values):
        b[x == v] = i
    return b


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


class AMI_Signaling(SignalingScheme):
    def __init__(self):
        self.thresholds = [-0.5, 0.5]
        self.values = [-1.0, 0.0, 1.0]
        SignalingScheme.__init__(self)

    def encode(self, bits):
        x = np.zeros(np.size(bits))
        q = np.flatnonzero(bits)
        i = np.arange(len(q))
        x[q] = (-1.0)**i
        return x

    def decode(self, y):
        return np.abs(y).astype(int)

    def acorr(self, ell):
        if ell == 0:
            return 0.5
        elif abs(ell) == 1:
            return -0.25
        else:
            return 0.0


class MLT3_Signaling(SignalingScheme):
    def __init__(self):
        self.thresholds = [-0.5, 0.5]
        self.values = [-1.0, 0.0, 1.0]
        SignalingScheme.__init__(self)

    def encode(self, bits):
        x = np.zeros(np.size(bits))
        state = 0
        # State sequence: 0 (LM) -> 1 (MH) -> 2 (HM) -> 3 (ML) -> 0 (LM)
        for i, b in enumerate(bits):
            if b == 0:
                x[i] = x[i - 1]  # Note that if i = 0, then i - 1 = -1,
                                 # and x[-1] = 0 at this point
            else:
                state = (state + 1) % 4
                x[i] = [0, 1, 0, -1][state]
        return x

    def decode(self, y):  # Not optimal!
        bits_hat = np.zeros(np.size(y))
        x_hat = unmap(slicer(y, self.thresholds, self.values), self.values)
        for i in range(len(x_hat)):
            bits_hat[i] = (x_hat[i] != x_hat[i - 1]).astype(int)
        return bits_hat


collection = collections.OrderedDict([
    ('Polar', Polar_Signaling()),
    ('Unipolar', Unipolar_Signaling()),
    ('Alternate Mark Inversion (AMI)', AMI_Signaling()),
    ('Multi-Level Transmit 3 (MLT-3)', MLT3_Signaling())
])
