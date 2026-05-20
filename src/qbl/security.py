"""
QBL Security — Input Validation & Resource Guards

Defensive layer that sits between user input and the QBL engine.
Prevents resource exhaustion, injection, and invalid states.
"""

import re
import numpy as np
from typing import Any, Optional
from qbl.errors import (
    ResourceExhaustion, InputSanitizationError, DimensionMismatch,
    InvalidGateError, InvalidStateError, SimulationLimitError
)


# ============================================================
# RESOURCE LIMITS
# ============================================================

class Limits:
    """Hard limits for resource allocation."""
    
    # Maximum qudits in a simulation
    MAX_QUBITS = 28            # 2^28 = 268M amplitudes (~4 GB)
    MAX_QUDITS_D13 = 7         # 13^7 = 62.7M amplitudes (~1 GB)
    MAX_QUDITS_GENERAL = 10    # Fallback for unknown d
    
    # Maximum memory allocation (bytes)
    MAX_MEMORY_BYTES = 4 * 1024**3  # 4 GB
    
    # Source code limits
    MAX_SOURCE_LENGTH = 1_000_000   # 1 MB source file
    MAX_GATES_PER_CIRCUIT = 100_000  # Circuit depth limit
    MAX_SHOTS = 10_000_000          # Max simulation shots
    MAX_DIMENSION = 23              # Maximum supported prime dimension
    
    # Supported prime dimensions
    SUPPORTED_PRIMES = {2, 3, 5, 7, 11, 13, 17, 19, 23}
    
    # Regex patterns for sanitization
    IDENTIFIER_PATTERN = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]{0,63}$')
    
    @classmethod
    def max_qudits_for_dimension(cls, d: int) -> int:
        """Maximum simulatable qudits for dimension d."""
        if d == 2:
            return cls.MAX_QUBITS
        elif d == 13:
            return cls.MAX_QUDITS_D13
        else:
            # General formula: d^n * 16 bytes < MAX_MEMORY
            import math
            max_n = int(math.log(cls.MAX_MEMORY_BYTES / 16) / math.log(d))
            return min(max_n, cls.MAX_QUDITS_GENERAL)


# ============================================================
# VALIDATION FUNCTIONS
# ============================================================

def validate_dimension(d: int, context: str = "") -> int:
    """Validate and return dimension, raising on invalid input."""
    if not isinstance(d, int):
        raise DimensionMismatch(0, 0, f"dimension must be int, got {type(d).__name__}")
    
    if d < 2:
        raise DimensionMismatch(2, d, f"minimum dimension is 2{f' ({context})' if context else ''}")
    
    if d > Limits.MAX_DIMENSION:
        raise ResourceExhaustion("dimension", d, Limits.MAX_DIMENSION)
    
    if d not in Limits.SUPPORTED_PRIMES:
        raise DimensionMismatch(
            0, d,
            f"dimension {d} is not a supported prime. Supported: {sorted(Limits.SUPPORTED_PRIMES)}"
        )
    
    return d


def validate_num_qudits(n: int, d: int, context: str = "") -> int:
    """Validate number of qudits is within simulatable range."""
    if not isinstance(n, int) or n < 1:
        raise ResourceExhaustion("qudits", n if isinstance(n, int) else 0, 1)
    
    max_n = Limits.max_qudits_for_dimension(d)
    if n > max_n:
        memory_needed = (d ** n) * 16
        raise SimulationLimitError(d, n, memory_needed)
    
    return n


def validate_qudit_index(index: int, num_qudits: int) -> int:
    """Validate qudit index is in bounds."""
    from qbl.errors import QuditIndexError
    if not isinstance(index, int):
        raise QuditIndexError(-1, num_qudits)
    if index < 0 or index >= num_qudits:
        raise QuditIndexError(index, num_qudits)
    return index


def validate_level(level: int, d: int, name: str = "level") -> int:
    """Validate a level value is in [0, d-1]."""
    if not isinstance(level, int):
        raise InputSanitizationError(name, f"must be int, got {type(level).__name__}")
    if level < 0 or level >= d:
        raise InputSanitizationError(name, f"must be in [0, {d-1}], got {level}")
    return level


def validate_unitary(matrix: np.ndarray, gate_name: str = "gate", tol: float = 1e-10) -> np.ndarray:
    """Validate a matrix is unitary (U†U = I)."""
    if not isinstance(matrix, np.ndarray):
        raise InvalidGateError(gate_name, "not a numpy array")
    
    if matrix.ndim != 2:
        raise InvalidGateError(gate_name, f"must be 2D, got {matrix.ndim}D")
    
    if matrix.shape[0] != matrix.shape[1]:
        raise InvalidGateError(gate_name, f"must be square, got shape {matrix.shape}")
    
    n = matrix.shape[0]
    product = matrix @ matrix.conj().T
    identity = np.eye(n)
    
    if not np.allclose(product, identity, atol=tol):
        max_deviation = np.max(np.abs(product - identity))
        raise InvalidGateError(
            gate_name,
            f"not unitary (max deviation from I: {max_deviation:.2e}, tolerance: {tol:.2e})"
        )
    
    return matrix


def validate_state_vector(state: np.ndarray, expected_dim: int = None) -> np.ndarray:
    """Validate a state vector is normalized and correct size."""
    if not isinstance(state, np.ndarray):
        raise InvalidStateError("State must be a numpy array")
    
    if state.ndim != 1:
        raise InvalidStateError(f"State must be 1D, got {state.ndim}D")
    
    if expected_dim is not None and state.shape[0] != expected_dim:
        raise InvalidStateError(
            f"State dimension mismatch: expected {expected_dim}, got {state.shape[0]}"
        )
    
    norm = np.linalg.norm(state)
    if not np.isclose(norm, 1.0, atol=1e-10):
        raise InvalidStateError(f"State not normalized: ||ψ|| = {norm:.10f}")
    
    if np.any(np.isnan(state)) or np.any(np.isinf(state)):
        raise InvalidStateError("State contains NaN or Inf values")
    
    return state


def validate_density_matrix(rho: np.ndarray, d: int = None) -> np.ndarray:
    """Validate a density matrix (Hermitian, PSD, trace 1)."""
    if not isinstance(rho, np.ndarray):
        raise InvalidStateError("Density matrix must be a numpy array")
    
    if rho.ndim != 2 or rho.shape[0] != rho.shape[1]:
        raise InvalidStateError(f"Density matrix must be square, got shape {rho.shape}")
    
    if d is not None and rho.shape[0] != d:
        raise InvalidStateError(f"Density matrix dimension mismatch: expected {d}×{d}")
    
    # Hermiticity
    if not np.allclose(rho, rho.conj().T, atol=1e-10):
        raise InvalidStateError("Density matrix is not Hermitian")
    
    # Trace 1
    trace = np.trace(rho)
    if not np.isclose(trace, 1.0, atol=1e-10):
        raise InvalidStateError(f"Density matrix trace is {trace:.10f}, expected 1.0")
    
    # Positive semi-definite
    eigvals = np.linalg.eigvalsh(rho)
    if np.any(eigvals < -1e-10):
        raise InvalidStateError(f"Density matrix has negative eigenvalue: {min(eigvals):.2e}")
    
    return rho


def validate_source(source: str) -> str:
    """Validate QBL source code input."""
    if not isinstance(source, str):
        raise InputSanitizationError("source", f"must be string, got {type(source).__name__}")
    
    if len(source) > Limits.MAX_SOURCE_LENGTH:
        raise ResourceExhaustion("source_bytes", len(source), Limits.MAX_SOURCE_LENGTH)
    
    if len(source.strip()) == 0:
        raise InputSanitizationError("source", "empty program")
    
    # Check for null bytes (potential injection)
    if '\x00' in source:
        raise InputSanitizationError("source", "contains null bytes")
    
    return source


def validate_identifier(name: str) -> str:
    """Validate a QBL identifier."""
    if not isinstance(name, str):
        raise InputSanitizationError("identifier", f"must be string, got {type(name).__name__}")
    
    if not Limits.IDENTIFIER_PATTERN.match(name):
        raise InputSanitizationError(
            "identifier",
            f"'{name}' is not a valid identifier (must match [a-zA-Z_][a-zA-Z0-9_]{{0,63}})"
        )
    
    return name


def validate_shots(shots: int) -> int:
    """Validate number of simulation shots."""
    if not isinstance(shots, int) or shots < 1:
        raise InputSanitizationError("shots", f"must be positive int, got {shots}")
    
    if shots > Limits.MAX_SHOTS:
        raise ResourceExhaustion("shots", shots, Limits.MAX_SHOTS)
    
    return shots


def validate_angle(theta: float, name: str = "angle") -> float:
    """Validate a rotation angle is finite."""
    if not isinstance(theta, (int, float)):
        raise InputSanitizationError(name, f"must be numeric, got {type(theta).__name__}")
    
    if np.isnan(theta) or np.isinf(theta):
        raise InputSanitizationError(name, f"must be finite, got {theta}")
    
    return float(theta)


def validate_coprime(a: int, d: int) -> int:
    """Validate a is coprime to d (for modular multiplication)."""
    if not isinstance(a, int):
        raise InputSanitizationError("multiplier", f"must be int, got {type(a).__name__}")
    
    a_mod = a % d
    if a_mod == 0:
        raise InputSanitizationError("multiplier", f"{a} is divisible by d={d}, not coprime")
    
    if np.gcd(a_mod, d) != 1:
        raise InputSanitizationError("multiplier", f"gcd({a_mod}, {d}) ≠ 1, not coprime")
    
    return a_mod


# ============================================================
# SAFE ALLOCATION
# ============================================================

def safe_allocate_state(d: int, n: int) -> np.ndarray:
    """Safely allocate a state vector with resource checking."""
    validate_dimension(d)
    validate_num_qudits(n, d)
    
    total_dim = d ** n
    memory_bytes = total_dim * 16  # complex128 = 16 bytes
    
    if memory_bytes > Limits.MAX_MEMORY_BYTES:
        raise SimulationLimitError(d, n, memory_bytes)
    
    state = np.zeros(total_dim, dtype=np.complex128)
    state[0] = 1.0  # Initialize to |0...0⟩
    return state
