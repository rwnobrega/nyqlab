import numpy as np
import scipy as sp
import scipy.signal


class MatchedFilter:
    def __init__(self, pulse, sps):
        self.pulse = pulse
        self.sps = sps

    def filter(self, y, hd):
        sps = self.sps
        tq = np.arange(-hd*sps, hd*sps + 1) / sps

        q = self.pulse.pulse(-tq)
        q /= np.sum(np.abs(q)**2) / sps

        return sp.signal.fftconvolve(y, q, mode='same') / sps
