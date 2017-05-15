from lmfit import Minimizer
import numpy as np

from .util import dot
from .qr_decomposition import qr_residual


class SeparableModelResult(Minimizer):

    def __init__(self, model, initial_parameter, *args, **kwargs):
        self.model = model
        super(SeparableModelResult, self).__init__(self._residual,
                                                   initial_parameter,
                                                   fcn_args=args,
                                                   fcn_kws=kwargs)

    def fit(self, *args, **kwargs):
        verbose = kwargs['verbose'] if 'verbose' in kwargs else 2
        res = self.minimize(method='least_squares',
                            ftol=kwargs.get('ftol', 1e-10),
                            gtol=kwargs.get('gtol', 1e-10),
                            verbose=verbose)

        self.best_fit_parameter = res.params

    def e_matrix(self, data, *args, **kwargs):
        return self.model.retrieve_e_matrix(self.best_fit_parameter,
                                            data, *args, **kwargs)

    def c_matrix(self, *args, **kwargs):
        return self.model.c_matrix(self.best_fit_parameter, *args, **kwargs)

    def eval(self, *args, **kwargs):
        e = self.e_matrix(*args, **kwargs)
        c = self.c_matrix(*args, **kwargs)
        return dot(e, c)

    def final_residual(self, *args, **kwargs):
        return np.asarray([r for r in
                           self._all_residuals(self.best_fit_parameter, *args,
                                               **kwargs)])

    def final_residual_svd(self, *args, **kwargs):
        residual = self.final_residual(*args, **kwargs)
        lsvd, svals, rsvd = np.linalg.svd(residual)
        return lsvd, svals, rsvd

    # @profile
    def _residual(self, parameter, *args, **kwargs):

        residuals = np.asarray(list(self._all_residuals(parameter, *args,
                                                        **kwargs))).flatten()
        return residuals

    def _all_residuals(self, parameter, *args, **kwargs):

        data_group = self.model.data(**kwargs)
        c_matrix_group = self.model.c_matrix(parameter,
                                             *args, **kwargs)
        for data, c_mat in iter(data_group, c_matrix_group):
            res = self._calculate_residual(data, c_mat)
            yield(res)

    def _calculate_residual(self, data, c_matrix):
        return qr_residual(c_matrix, data)


def iter(data, c_matrix):
    for i in range(len(data)):
        yield data[i], c_matrix[i]
