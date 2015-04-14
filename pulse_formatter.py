import numpy as np
import scipy as sp
import scipy.signal


class PulseFomatter:
    def __init__(self, pulse, symbol_rate, sps):
        self.pulse = pulse
        self.symbol_rate = symbol_rate
        self.sps = sps

    def encode(self, x, hd):
        sps = self.sps
        tp = np.arange(-hd*sps, hd*sps + 1) / sps

        p = self.pulse.pulse(tp)
        w = np.zeros(len(x) * sps)
        w[: : sps] = x

        s = sp.signal.fftconvolve(w, p)

        return s[(hd - 1)*sps : -hd*sps]
