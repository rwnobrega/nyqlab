import numpy as np
import scipy as sp
import scipy.signal


class PulseFomatter:
    def __init__(self, pulse, symbol_rate, sps):
        self.pulse = pulse
        self.symbol_rate = symbol_rate
        self.sps = sps

    def encode(self, x, filt_len):
        sps = self.sps
        N = sps * filt_len // 2

        tp = np.arange(-N, N + 1) / sps

        p = self.pulse.pulse(tp)
        w = np.zeros(len(x) * sps)
        w[: : sps] = x

        s = sp.signal.fftconvolve(w, p)

        return s[N - sps : -N]
