import numpy as np
import scipy as sp
import scipy.signal


class MatchedFilter:
    def __init__(self, pulse, sps):
        self.pulse = pulse
        self.sps = sps

    def filter(self, y, filt_len):
        sps = self.sps
        N = sps * filt_len // 2

        tq = np.arange(-N, N + 1) / sps

        q = self.pulse.pulse(-tq)
        q /= np.sum(np.abs(q)**2) / sps

        return sp.signal.fftconvolve(y, q, mode='same') / sps
