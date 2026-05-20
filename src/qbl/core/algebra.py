"""
QBL Core — Dimension-Agnostic Algebra Engine

The algebraic heart of QBL. All quantum operations are expressed as
transformations on d-dimensional Hilbert spaces. d=2 (qubits) and d=13 (qudits)
are first-class citizens; arbitrary prime dimensions are supported.

This module defines the mathematical primitives that ALL backends consume.
"""

import numpy as np
from typing import Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class Dimension(Enum):
    """Supported native dimensions."""
    QUBIT = 2
    QUTRIT = 3
    QUDIT_5 = 5
    QUDIT_7 = 7
    QUDIT_11 = 11
    QUDIT_13 = 13  # Primary non-binary dimension
    
    @property
    def is_prime(self) -> bool:
        return True  # All supported dims are prime
    
    @property
    def omega(self) -> complex:
        """Primitive d-th root of unity."""
        return np.exp(2j * np.pi / self.value)


# Default dimension for qudit operations
DEFAULT_DIMENSION = 13


@dataclass(frozen=True)
class HilbertSpace:
    """
    Describes the Hilbert space for a quantum register.
    H = C^d ⊗ C^d ⊗ ... ⊗ C^d  (n copies)
    """
    dimension: int  # d (levels per site)
    num_sites: int  # n (number of qudits)
    
    @property
    def total_dim(self) -> int:
        """Total dimension: d^n"""
        return self.dimension ** self.num_sites
    
    @property
    def is_qubit_space(self) -> bool:
        return self.dimension == 2
    
    @property
    def info_content_bits(self) -> float:
        """Information capacity in bits: n * log2(d)"""
        return self.num_sites * np.log2(self.dimension)
    
    def tensor(self, other: 'HilbertSpace') -> 'HilbertSpace':
        """Tensor product of two spaces (must have same dimension)."""
        assert self.dimension == other.dimension, "Cannot tensor different dimensions"
        return HilbertSpace(self.dimension, self.num_sites + other.num_sites)


def root_of_unity(d: int) -> complex:
    """ω = e^(2πi/d)"""
    return np.exp(2j * np.pi / d)


def is_unitary(matrix: np.ndarray, tol: float = 1e-10) -> bool:
    """Check if a matrix is unitary."""
    n = matrix.shape[0]
    product = matrix @ matrix.conj().T
    return np.allclose(product, np.eye(n), atol=tol)


def tensor_product(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Kronecker (tensor) product of two operators."""
    return np.kron(a, b)


def partial_trace(rho: np.ndarray, dims: list, trace_over: list) -> np.ndarray:
    """
    Partial trace of density matrix.
    dims: list of subsystem dimensions [d1, d2, ...]
    trace_over: indices of subsystems to trace out
    """
    n = len(dims)
    rho_tensor = rho.reshape(dims + dims)
    
    # Contract pairs
    for idx in sorted(trace_over, reverse=True):
        rho_tensor = np.trace(rho_tensor, axis1=idx, axis2=idx + n - len(trace_over))
        n -= 1
    
    remaining_dim = int(np.sqrt(rho_tensor.size))
    return rho_tensor.reshape(remaining_dim, remaining_dim)


def fidelity(rho: np.ndarray, sigma: np.ndarray) -> float:
    """Quantum fidelity F(ρ,σ) = (Tr√(√ρ σ √ρ))²"""
    sqrt_rho = _matrix_sqrt(rho)
    inner = sqrt_rho @ sigma @ sqrt_rho
    sqrt_inner = _matrix_sqrt(inner)
    return float(np.real(np.trace(sqrt_inner)) ** 2)


def _matrix_sqrt(m: np.ndarray) -> np.ndarray:
    """Matrix square root via eigendecomposition."""
    eigvals, eigvecs = np.linalg.eigh(m)
    eigvals = np.maximum(eigvals, 0)
    return eigvecs @ np.diag(np.sqrt(eigvals)) @ eigvecs.conj().T


def von_neumann_entropy(rho: np.ndarray) -> float:
    """S(ρ) = -Tr(ρ log ρ)"""
    eigvals = np.linalg.eigvalsh(rho)
    eigvals = eigvals[eigvals > 1e-12]
    return -float(np.sum(eigvals * np.log(eigvals)))


def purity(rho: np.ndarray) -> float:
    """Tr(ρ²) — 1 for pure states, 1/d for maximally mixed."""
    return float(np.real(np.trace(rho @ rho)))
