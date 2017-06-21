import collections

import numpy as np

from PyQt5 import QtCore, QtWidgets


def slicer(y, thresholds, values):
    x_hat = np.empty_like(y)
    for k in range(len(y)):
        for (i, th) in enumerate(thresholds):
            if y[k] < th:
                x_hat[k] = values[i]
                break
            x_hat[k] = values[-1]
    return x_hat


class SignalingScheme:
    def widget(self):
        try:
            return globals()[self.__class__.__name__ + '_Widget'](self)
        except KeyError:
            return QtWidgets.QLabel('<i>No options available for this signaling scheme.</i>')

    def detect(self, y):
        return slicer(x, self.thresholds, self.values)


class Unipolar_Signaling(SignalingScheme):
    def __init__(self):
        self.thresholds = [0.5]
        self.values = [0.0, 1.0]
        SignalingScheme.__init__(self)

    def encode(self, bits):
        return 1.0 * bits

    def decode(self, x):
        return x.astype(int)

    def acorr(self, ell):
        if ell == 0:
            return 0.5
        else:
            return 0.25


class Polar_Signaling(SignalingScheme):
    def __init__(self):
        self.thresholds = [0.0]
        self.values = [-1.0, 1.0]
        SignalingScheme.__init__(self)

    def encode(self, bits):
        return 2.0 * bits - 1.0

    def decode(self, x):
        return (x >= 0).astype(np.int)

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

    def decode(self, x):
        return np.abs(x).astype(int)

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

    def decode(self, x):  # Not optimal!
        bits_hat = np.zeros(np.size(x))
        x_hat = self.detect(x)
        for i in range(len(x_hat)):
            bits_hat[i] = (x_hat[i] != x_hat[i - 1]).astype(int)
        return bits_hat


collection = collections.OrderedDict([
    ('Polar', Polar_Signaling()),
    ('Unipolar', Unipolar_Signaling()),
    ('Alternate Mark Inversion (AMI)', AMI_Signaling()),
    ('Multi-Level Transmit 3 (MLT-3)', MLT3_Signaling())
])
