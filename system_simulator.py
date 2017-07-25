import numpy as np

from scipy.signal import welch


class Block:
    def __init__(self, module, out_type):
        self.module = module
        self.out_type = out_type
        self.box = module.choices[0][1]


class SystemSimulator:
    def __init__(self, blocks):
        self.blocks = blocks
        self.data_t = [None for _ in range(len(blocks))]
        self.data_f = [None for _ in range(len(blocks))]

        self._sps = 64
        self._bit_rate = 1.0
        self.update_secondary_properties()

        self.seed = 0
        self.n_fft = 2**16

    def process(self):
        self._processData()
        self._processSpectra()
        self._processAxes()

    def _processData(self):
        np.random.seed(self.seed)

        for (i, block) in enumerate(self.blocks):
            if i == 0:
                self.data_t[0] = self.blocks[0].box.process()  # Process source
            else:
                self.data_t[i] = block.box.process(self.data_t[i - 1])

        self.ber = sum(1*(self.data_t[0] != self.data_t[-1])) / self.n_symbols  # TODO: So far, binary only

    def _processSpectra(self):
        fa = self.samp_freq
        Nf = self.n_fft
        Nt = (self.n_symbols + 2) * self.sps

        for (i, block) in enumerate(self.blocks):
            if block.out_type == 'C':
                _, psd = welch(self.data_t[i], fs=fa, nperseg=min(Nf, Nt), return_onesided=False, nfft=Nf)
                self.data_f[i] = np.fft.fftshift(psd)

    def _processAxes(self):
        fa = self.samp_freq
        Ts = 1 / self.symbol_rate
        Nf = self.n_fft
        Nt = (self.n_symbols + 2) * self.sps

        self.t = np.arange(Nt) / fa - Ts
        self.tk = self.t[self.instants]
        self.f = np.arange(-Nf//2, Nf//2) * (fa / Nf)

    @property
    def sps(self):
        return self._sps

    @sps.setter
    def sps(self, value):
        self._sps = value
        self.update_secondary_properties()

    @property
    def bit_rate(self):
        return self._bit_rate

    @bit_rate.setter
    def bit_rate(self, value):
        self._bit_rate = value
        self.update_secondary_properties()

    def update_secondary_properties(self):
        self.symbol_rate = self.bit_rate * 1  # TODO: So far, binary only...
        self.samp_freq = self.sps * self.symbol_rate
