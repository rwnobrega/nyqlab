import numpy as np


class ThresholdDetector:
    def __init__(self, thresholds, values):
        self.thresholds = thresholds
        self.values = values

    def detect(self, y):
        x_hat = np.empty_like(y)
        for k in range(len(y)):
            for (i, th) in enumerate(self.thresholds):
                if y[k] < th:
                    x_hat[k] = self.values[i]
                    break
                x_hat[k] = self.values[-1]

        return x_hat
