import collections

import numpy as np

from PyQt4 import QtCore, QtGui

from threshold_detector import ThresholdDetector


class SignalingScheme:
    def __init__(self):
        self.detector = ThresholdDetector(self.thresholds, self.values)

    def widget(self):
        try:
            return globals()[self.__class__.__name__ + '_Widget'](self)
        except KeyError:
            return QtGui.QLabel('<i>No options available for this signaling scheme.</i>')

    def detect(self, y):
        return self.detector.detect(y)


class Unipolar_Signaling(SignalingScheme):
    def __init__(self):
        self.thresholds = [0.5]
        self.values = [0.0, 1.0]
        SignalingScheme.__init__(self)

    def encode(self, bits):
        return 1.0 * bits

    def decode(self, x):
        return x.astype(int)


class Polar_Signaling(SignalingScheme):
    def __init__(self):
        self.thresholds = [0.0]
        self.values = [-1.0, 1.0]
        SignalingScheme.__init__(self)

    def encode(self, bits):
        return 2.0 * bits - 1.0

    def decode(self, x):
        return (0.5*(x + 1.0)).astype(int)


class AMI_Signaling(SignalingScheme):
    def __init__(self):
        self.thresholds = [-0.5, 0.5]
        self.values = [-1.0, 0.0, 1.0]
        SignalingScheme.__init__(self)

    def encode(self, bits):
        x = np.zeros(np.size(bits))
        q = np.nonzero(bits)
        i = np.arange(len(bits))
        x[q] = (-1.0)**i
        return x

    def decode(self, x):
        return np.abs(x).astype(int)


collection = collections.OrderedDict([
    ('Unipolar', Unipolar_Signaling()),
    ('Polar', Polar_Signaling()),
    ('AMI', AMI_Signaling())
])
