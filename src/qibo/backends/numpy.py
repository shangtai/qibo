from abc import abstractmethod
from qibo.backends import abstract
from qibo.config import raise_error, log


class NumpyBackend(abstract.AbstractBackend):

    def __init__(self):
        super().__init__()
        import numpy as np
        self.backend = np
        self.name = "numpy"
        self.np = np

        from qibo.backends import matrices
        self.matrices = matrices.NumpyMatrices(self.dtypes('DTYPECPX'))
        self.numeric_types = (np.int, np.float, np.complex, np.int32,
                              np.int64, np.float32, np.float64,
                              np.complex64, np.complex128)
        self.tensor_types = (np.ndarray,)
        self.Tensor = np.ndarray
        self.random = np.random
        self.newaxis = np.newaxis
        self.oom_error = MemoryError
        self.optimization = None
        self.einsum_module = None

    def set_device(self, name):
        log.warning("Numpy does not support device placement. "
                    "Aborting device change.")

    def cast(self, x, dtype='DTYPECPX'):
        if isinstance(dtype, str):
            dtype = self.dtypes(dtype)
        if isinstance(x, self.backend.ndarray):
            return x.astype(dtype)
        return self.backend.array(x, dtype=dtype)

    def diag(self, x, dtype='DTYPECPX'):
        if isinstance(dtype, str):
            dtype = self.dtypes(dtype)
        return self.backend.diag(x).astype(dtype)

    def reshape(self, x, shape):
        return self.backend.reshape(x, shape)

    def stack(self, x, axis=0):
        return self.backend.stack(x, axis=axis)

    def concatenate(self, x, axis=0):
        return self.backend.concatenate(x, axis=axis)

    def expand_dims(self, x, axis):
        return self.backend.expand_dims(x, axis)

    def copy(self, x):
        return self.backend.copy(x)

    def range(self, start, finish, step, dtype=None):
        if isinstance(dtype, str):
            dtype = self.dtypes(dtype)
        return self.backend.arange(start, finish, step, dtype=dtype)

    def eye(self, dim, dtype='DTYPECPX'):
        if isinstance(dtype, str):
            dtype = self.dtypes(dtype)
        return self.backend.eye(dim, dtype=dtype)

    def zeros(self, shape, dtype='DTYPECPX'):
        if isinstance(dtype, str):
            dtype = self.dtypes(dtype)
        return self.backend.zeros(shape, dtype=dtype)

    def ones(self, shape, dtype='DTYPECPX'):
        if isinstance(dtype, str):
            dtype = self.dtypes(dtype)
        return self.backend.ones(shape, dtype=dtype)

    def zeros_like(self, x):
        return self.backend.zeros_like(x)

    def ones_like(self, x):
        return self.backend.ones_like(x)

    def real(self, x):
        return self.backend.real(x)

    def imag(self, x):
        return self.backend.imag(x)

    def conj(self, x):
        return self.backend.conj(x)

    def mod(self, x, y):
        return self.backend.mod(x, y)

    def right_shift(self, x, y):
        return self.backend.right_shift(x, y)

    def exp(self, x):
        return self.backend.exp(x)

    def sin(self, x):
        return self.backend.sin(x)

    def cos(self, x):
        return self.backend.cos(x)

    def pow(self, base, exponent):
        return base ** exponent

    def square(self, x):
        return x ** 2

    def sqrt(self, x):
        return self.backend.sqrt(x)

    def log(self, x):
        return self.backend.log(x)

    def abs(self, x):
        return self.backend.abs(x)

    def trace(self, x):
        return self.backend.trace(x)

    def expm(self, x):
        from scipy import linalg
        return linalg.expm(x)

    def sum(self, x, axis=None):
        return self.backend.sum(x, axis=axis)

    def matmul(self, x, y):
        return self.backend.matmul(x, y)

    def outer(self, x, y):
        return self.backend.outer(x, y)

    def kron(self, x, y):
        return self.backend.kron(x, y)

    def einsum(self, *args):
        return self.backend.einsum(*args)

    def tensordot(self, x, y, axes=None):
        return self.backend.tensordot(x, y, axes=axes)

    def transpose(self, x, axes=None):
        return self.backend.transpose(x, axes)

    def inv(self, x):
        return self.backend.linalg.inv(x)

    def eigh(self, x):
        return self.backend.linalg.eigh(x)

    def eigvalsh(self, x):
        return self.backend.linalg.eigvalsh(x)

    def less(self, x, y):
        return self.backend.less(x, y)

    def array_equal(self, x, y):
        return self.np.array_equal(x, y)

    def unique(self, x, return_counts=False):
        # Uses numpy backend always (even on Tensorflow)
        return self.np.unique(x, return_counts=return_counts)

    def squeeze(self, x, axis=None):
        return self.backend.squeeze(x, axis=axis)

    def gather(self, x, indices=None, condition=None, axis=0):
        if indices is None:
            if condition is None:
                raise_error(ValueError, "Gather call requires either indices "
                                        "or condition.")
            indices = condition
        if axis < 0:
            axis += len(x.shape)
        idx = axis * (slice(None),) + (indices,)
        return x[idx]

    def gather_nd(self, x, indices):
        return x[tuple(indices)]

    def initial_state(self, nqubits, is_matrix=False):
        if is_matrix:
            state = self.zeros(2 * (2 ** nqubits,))
            state[0, 0] = 1
        else:
            state = self.zeros((2 ** nqubits,))
            state[0] = 1
        return state

    def transpose_state(self, pieces, state, nqubits, order): # pragma: no cover
        raise_error(NotImplementedError)

    def random_uniform(self, shape, dtype='DTYPE'):
        return self.backend.random.random(shape).astype(self.dtypes(dtype))

    def sample_shots(self, probs, nshots):
        return self.random.choice(range(len(probs)), size=nshots, p=probs)

    def sample_frequencies(self, probs, nshots):
        from qibo.config import SHOT_BATCH_SIZE
        def update_frequencies(nsamples, frequencies):
            samples = self.random.choice(range(len(probs)), size=nsamples, p=probs)
            res, counts = self.unique(samples, return_counts=True)
            frequencies[res] += counts
            return frequencies

        frequencies = self.zeros(int(probs.shape[0]), dtype=self.dtypes('DTYPEINT'))
        for _ in range(nshots // SHOT_BATCH_SIZE):
            frequencies = update_frequencies(SHOT_BATCH_SIZE, frequencies)
        frequencies = update_frequencies(nshots % SHOT_BATCH_SIZE, frequencies)
        return frequencies

    def compile(self, func):
        return func

    def device(self, device_name):
        class DummyModule:

            def __enter__(self, *args):
                pass

            def __exit__(self, *args):
                pass

        return DummyModule()

    def set_seed(self, seed):
        self.backend.random.seed(seed)

    def _get_default_einsum(self):
        # finds default einsum backend of the same engine to use for fall back
        # in the case of `controlled_by` gates used on density matrices where
        # matmul einsum does not work properly
        import sys
        module = sys.modules[self.__class__.__module__]
        engine = self.name.split("_")[0].capitalize()
        return getattr(module, f"{engine}DefaultEinsumBackend")

    def prepare_gate(self, gate):
        s = 1 + gate.density_matrix
        gate.tensor_shape = self.cast(s * gate.nqubits * (2,), dtype='DTYPEINT')
        gate.flat_shape = self.cast(s * (2 ** gate.nqubits,), dtype='DTYPEINT')
        if gate.is_controlled_by:
            gate.control_cache = self.einsum_module.ControlCache(gate)
            nactive = gate.nqubits - len(gate.control_qubits)
            targets = gate.control_cache.targets
            ncontrol = len(gate.control_qubits)
            if gate.density_matrix:
                # fall back to the 'defaulteinsum' backend when using
                # density matrices with `controlled_by` gates because
                # 'matmuleinsum' is not properly implemented for this case
                backend = self._get_default_einsum()
                gate.calculation_cache = backend.create_cache(
                    self, targets, nactive, ncontrol)
            else:
                gate.calculation_cache = self.create_cache(
                    targets, nactive, ncontrol)
        else:
            gate.calculation_cache = self.create_cache(gate.qubits, gate.nqubits)
        gate.calculation_cache.cast_shapes(
            lambda x: self.cast(x, dtype='DTYPEINT'))

    def state_vector_call(self, gate, state):
        state = self.reshape(state, gate.tensor_shape)
        if gate.is_controlled_by:
            ncontrol = len(gate.control_qubits)
            nactive = gate.nqubits - ncontrol
            state = self.transpose(state, gate.control_cache.order(False))
            # Apply `einsum` only to the part of the state where all controls
            # are active. This should be `state[-1]`
            state = self.reshape(state, (2 ** ncontrol,) + nactive * (2,))
            updates = self.gate_call(gate.calculation_cache.vector, state[-1],
                                     gate.matrix)
            # Concatenate the updated part of the state `updates` with the
            # part of of the state that remained unaffected `state[:-1]`.
            state = self.concatenate([state[:-1], updates[self.newaxis]], axis=0)
            state = self.reshape(state, gate.nqubits * (2,))
            # Put qubit indices back to their proper places
            state = self.transpose(state, gate.control_cache.reverse(False))
        else:
            einsum_str = gate.calculation_cache.vector
            state = self.gate_call(einsum_str, state, gate.matrix)
        return self.reshape(state, gate.flat_shape)

    def density_matrix_call(self, gate, state):
        state = self.reshape(state, gate.tensor_shape)
        if gate.is_controlled_by:
            ncontrol = len(gate.control_qubits)
            nactive = gate.nqubits - ncontrol
            n = 2 ** ncontrol
            state = self.transpose(state, gate.control_cache.order(True))
            state = self.reshape(state, 2 * (n,) + 2 * nactive * (2,))
            state01 = self.gather(state, indices=range(n - 1), axis=0)
            state01 = self.squeeze(self.gather(state01, indices=[n - 1], axis=1), axis=1)
            state01 = self.gate_call(gate.calculation_cache.right0,
                                     state01, self.conj(gate.matrix))
            state10 = self.gather(state, indices=range(n - 1), axis=1)
            state10 = self.squeeze(self.gather(state10, indices=[n - 1], axis=0), axis=0)
            state10 = self.gate_call(gate.calculation_cache.left0,
                                     state10, gate.matrix)

            state11 = self.squeeze(self.gather(state, indices=[n - 1], axis=0), axis=0)
            state11 = self.squeeze(self.gather(state11, indices=[n - 1], axis=0), axis=0)
            state11 = self.gate_call(gate.calculation_cache.right, state11, self.conj(gate.matrix))
            state11 = self.gate_call(gate.calculation_cache.left, state11, gate.matrix)

            state00 = self.gather(state, indices=range(n - 1), axis=0)
            state00 = self.gather(state00, indices=range(n - 1), axis=1)
            state01 = self.concatenate([state00, state01[:, self.newaxis]], axis=1)
            state10 = self.concatenate([state10, state11[self.newaxis]], axis=0)
            state = self.concatenate([state01, state10[self.newaxis]], axis=0)
            state = self.reshape(state, 2 * gate.nqubits * (2,))
            state = self.transpose(state, gate.control_cache.reverse(True))
        else:
            state = self.gate_call(gate.calculation_cache.right, state,
                                   self.conj(gate.matrix))
            state = self.gate_call(gate.calculation_cache.left, state, gate.matrix)
        return self.reshape(state, gate.flat_shape)


class NumpyDefaultEinsumBackend(NumpyBackend):
    """Gate application backend that based on default ``einsum``.

    This is the most efficient implementation for GPU, however its
    backpropagation is not working properly for complex numbers.
    The user should switch to :class:`qibo.core.einsum.MatmulEinsum`
    if automatic differentiation is required.
    """

    def __init__(self):
        super().__init__()
        from qibo.backends import einsum
        self.name = "numpy_defaulteinsum"
        self.custom_gates = False
        self.einsum_module = einsum

    def create_cache(self, qubits, nqubits, ncontrol=None):
        return self.einsum_module.DefaultEinsumCache(qubits, nqubits, ncontrol)

    def gate_call(self, cache, state, matrix):
        return self.einsum(cache, state, matrix)


class NumpyMatmulEinsumBackend(NumpyBackend):
    """Gate application backend based on ``matmul``.

    For Tensorflow this is more efficient than ``einsum`` on CPU but slower on GPU.
    The matmul version implemented here is not the most efficient possible.
    The implementation algorithm is the following.

    Assume that we are applying
    a two qubit gate of shape (4, 4) to qubits 0 and 3 of a five qubit state
    vector of shape 5 * (2,). We perform the following steps:

    * Reshape the state to (2, 4, 2, 2)
    * Transpose to (2, 2, 4, 2) to bring the target qubits in the beginning.
    * Reshape to (4, 8).
    * Apply the gate using the matmul (4, 4) x (4, 8).
    * Reshape to the original shape 5 * (2,) and traspose so that the final
      qubit order agrees with the initial.
    """

    def __init__(self):
        super().__init__()
        from qibo.backends import einsum
        self.name = "numpy_matmuleinsum"
        self.custom_gates = False
        self.einsum_module = einsum

    def create_cache(self, qubits, nqubits, ncontrol=None):
        return self.einsum_module.MatmulEinsumCache(qubits, nqubits, ncontrol)

    def gate_call(self, cache, state, matrix):
        if isinstance(cache, str):
            # `controlled_by` gate acting on density matrices
            # fall back to defaulteinsum because matmuleinsum is not properly
            # implemented. See `qibo.backends.numpy.NumpyBackend.prepare_gate`
            # for more details
            backend = self._get_default_einsum()
            return backend.gate_call(self, cache, state, matrix)

        shapes = cache["shapes"]

        state = self.reshape(state, shapes[0])
        state = self.transpose(state, cache["ids"])
        if cache["conjugate"]:
            state = self.reshape(self.conj(state), shapes[1])
        else:
            state = self.reshape(state, shapes[1])

        n = len(tuple(matrix.shape))
        if n > 2:
            dim = 2 ** (n // 2)
            state = self.matmul(self.reshape(matrix, (dim, dim)), state)
        else:
            state = self.matmul(matrix, state)

        state = self.reshape(state, shapes[2])
        state = self.transpose(state, cache["inverse_ids"])
        state = self.reshape(state, shapes[3])
        return state
