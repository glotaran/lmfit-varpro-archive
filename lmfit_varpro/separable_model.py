import warnings
import numpy as np

from .qr_decomposition import qr_coefficents
from .result import SeparableModelResult
from .util import dot


class SeparableModel(object):

    def c_matrix(self, parameter, *args, **kwargs):
        raise NotImplementedError

    def e_matrix(self, parameter, *args, **kwarg):
        raise NotImplementedError("'self.e_matrix' not defined in model.")

    def data(self, **kwargs):
        raise NotImplementedError

    def eval(self, parameter, *args, **kwargs):
        e = self.e_matrix(parameter, **kwargs)
        c = self.c_matrix(parameter, *args, **kwargs)
        noise = kwargs["noise"] if "noise" in kwargs else False
        res = dot(e, c)

        if noise:
            if "noise_seed" in kwargs:
                noise_seed = kwargs["noise_seed"]
                if not isinstance(noise_seed, int):
                    warnings.warn("Warning noise_seed should be integer, seed"
                                  " value of {} reduced to {}"
                                  .format(noise_seed, int(noise_seed)))
                    noise_seed = int(noise_seed)
                np.random.seed(noise_seed)
            std_dev = kwargs["noise_std_dev"] if "noise_std_dev" in kwargs \
                else 1.0
            res = np.random.normal(res, std_dev)
        return res

    def fit(self, initial_parameter, *args, **kwargs):
        result = SeparableModelResult(self, initial_parameter, *args,
                                      **kwargs)
        result.fit(initial_parameter, *args, **kwargs)
        return result

    def retrieve_e_matrix(self, parameter, data, *args, **kwargs):
        c_matrix = self.c_matrix(parameter, *args, **kwargs)
        #  e_matrix = []

        # We expect that the c matrix is grouped along the 0 dim of data,
        # whereas the e_matrix is grouped along dim 1
        # TODO: we only calculate 1 e matrix, instead one for each group.

        dim0 = len(c_matrix)
        dim1 = c_matrix[0].shape[1]
        dim2 = c_matrix[0].shape[0]

        e = np.empty((dim0, dim1), np.float64)
        for i in range(data.shape[0]):
            c = c_matrix[i]
            d = data[i, :]
            e[i, :] = qr_coefficents(c, d)[:dim1]

        return [e for _ in range(dim2)]
