"""
QBL Core — Gate Algebra

Universal gate definitions for arbitrary dimension d.
All gates are parameterized by dimension, with d=2 (qubit) and d=13 (qudit)
as optimized special cases.

The gate hierarchy:
  Level 0: Identity
  Level 1: Generalized Pauli group (shift X, clock Z, Weyl displacements)
  Level 2: Clifford group (maps Paulis to Paulis under conjugation)
  Level 3: Universal gate set (Clifford + one non-Clifford gate)
"""

import numpy as np
from typing import List, Optional


# ============================================================
# LEVEL 1: GENERALIZED PAULI GROUP
# ============================================================

def identity(d: int) -> np.ndarray:
    """I_d: identity on C^d."""
    return np.eye(d, dtype=complex)


def shift(d: int, power: int = 1) -> np.ndarray:
    """
    X^k (generalized Pauli-X / shift operator).
    X^k|j⟩ = |j+k mod d⟩
    
    For d=2: X^1 = standard Pauli-X (bit flip)
    For d=13: X^1 = cyclic shift through 13 levels
    """
    k = power % d
    gate = np.zeros((d, d), dtype=complex)
    for j in range(d):
        gate[(j + k) % d, j] = 1.0
    return gate


def clock(d: int, power: int = 1) -> np.ndarray:
    """
    Z^k (generalized Pauli-Z / clock operator).
    Z^k|j⟩ = ω^(jk)|j⟩ where ω = e^(2πi/d)
    
    For d=2: Z^1 = standard Pauli-Z (phase flip)
    For d=13: Z^1 = diagonal with 13th roots of unity
    """
    omega = np.exp(2j * np.pi / d)
    k = power % d
    return np.diag([omega**(j * k) for j in range(d)])


def weyl(d: int, a: int, b: int) -> np.ndarray:
    """
    Weyl displacement operator D(a,b) = τ^(ab) X^a Z^b
    where τ = ω^((d+1)/2) for odd prime d.
    
    The d² Weyl operators {D(a,b)} form an orthogonal basis for
    all d×d matrices. For prime d, they generate the full Heisenberg group.
    """
    omega = np.exp(2j * np.pi / d)
    tau = omega ** ((d + 1) // 2) if d % 2 == 1 else omega ** (d // 2)
    return tau**(a * b) * (shift(d, a) @ clock(d, b))


def pauli_y(d: int) -> np.ndarray:
    """
    Generalized Y = XZ (up to phase).
    For d=2: standard Pauli-Y.
    """
    if d == 2:
        return np.array([[0, -1j], [1j, 0]], dtype=complex)
    return shift(d) @ clock(d)


# ============================================================
# LEVEL 2: CLIFFORD GROUP
# ============================================================

def fourier(d: int) -> np.ndarray:
    """
    Quantum Fourier Transform (generalized Hadamard).
    F|j⟩ = (1/√d) Σ_k ω^(jk)|k⟩
    
    For d=2: Hadamard gate H
    For d=13: 13-point DFT
    
    Clifford: F X F† = Z, F Z F† = X†
    """
    omega = np.exp(2j * np.pi / d)
    F = np.zeros((d, d), dtype=complex)
    for j in range(d):
        for k in range(d):
            F[j, k] = omega**(j * k) / np.sqrt(d)
    return F


def phase_gate(d: int, power: int = 1) -> np.ndarray:
    """
    Phase gate S^k: |j⟩ → ω^(kj(j-1)/2)|j⟩
    
    For d=2, k=1: S gate (π/2 phase)
    For d=13: generalized phase operation
    
    Clifford: S X S† = ωXZ
    """
    omega = np.exp(2j * np.pi / d)
    k = power % d
    return np.diag([omega**(k * j * (j - 1) // 2) for j in range(d)])


def controlled_sum(d: int) -> np.ndarray:
    """
    SUM gate (generalized CNOT).
    SUM|j⟩|k⟩ = |j⟩|j+k mod d⟩
    
    For d=2: CNOT gate
    For d=13: controlled mod-13 addition
    """
    gate = np.zeros((d**2, d**2), dtype=complex)
    for j in range(d):
        for k in range(d):
            row = j * d + ((j + k) % d)
            col = j * d + k
            gate[row, col] = 1.0
    return gate


def controlled_phase_gate(d: int) -> np.ndarray:
    """
    CZ gate (generalized controlled-Z).
    CZ|j⟩|k⟩ = ω^(jk)|j⟩|k⟩
    
    For d=2: CZ gate
    For d=13: controlled phase with 13th roots
    """
    omega = np.exp(2j * np.pi / d)
    gate = np.zeros((d**2, d**2), dtype=complex)
    for j in range(d):
        for k in range(d):
            idx = j * d + k
            gate[idx, idx] = omega**(j * k)
    return gate


def swap(d: int) -> np.ndarray:
    """
    SWAP gate for two d-level systems.
    SWAP|j⟩|k⟩ = |k⟩|j⟩
    """
    gate = np.zeros((d**2, d**2), dtype=complex)
    for j in range(d):
        for k in range(d):
            gate[k * d + j, j * d + k] = 1.0
    return gate


def modular_multiply(d: int, a: int) -> np.ndarray:
    """
    Modular multiplication: |j⟩ → |aj mod d⟩
    Requires gcd(a, d) = 1 (a coprime to d).
    
    For prime d (like 13), all a ∈ {1,...,d-1} are valid.
    """
    assert np.gcd(a % d, d) == 1, f"{a} not coprime to {d}"
    gate = np.zeros((d, d), dtype=complex)
    for j in range(d):
        gate[(a * j) % d, j] = 1.0
    return gate


# ============================================================
# LEVEL 3: UNIVERSAL GATE SET
# ============================================================

def rotation(d: int, level_a: int, level_b: int, theta: float, phi: float = 0.0) -> np.ndarray:
    """
    Rotation in |a⟩-|b⟩ subspace (non-Clifford for most angles).
    Together with Clifford gates, forms a universal gate set.
    
    R(a,b,θ,φ)|a⟩ = cos(θ/2)|a⟩ + e^(iφ)sin(θ/2)|b⟩
    R(a,b,θ,φ)|b⟩ = -e^(-iφ)sin(θ/2)|a⟩ + cos(θ/2)|b⟩
    """
    gate = np.eye(d, dtype=complex)
    gate[level_a, level_a] = np.cos(theta / 2)
    gate[level_a, level_b] = np.exp(1j * phi) * np.sin(theta / 2)
    gate[level_b, level_a] = -np.exp(-1j * phi) * np.sin(theta / 2)
    gate[level_b, level_b] = np.cos(theta / 2)
    return gate


def diagonal_phase(d: int, phases: List[float]) -> np.ndarray:
    """
    General diagonal unitary: |j⟩ → e^(iφ_j)|j⟩
    Non-Clifford unless phases are multiples of 2π/d.
    """
    assert len(phases) == d
    return np.diag([np.exp(1j * p) for p in phases])


def t_gate(d: int) -> np.ndarray:
    """
    T gate (π/4 for d=2, generalized for d>2).
    Non-Clifford gate needed for universality.
    
    For d=2: T = diag(1, e^(iπ/4))
    For d=13: T = diag(1, ω^(1/(2d)), ω^(2/(2d)), ...) — a fine-grained phase
    """
    if d == 2:
        return np.diag([1, np.exp(1j * np.pi / 4)])
    # For odd prime d: use ω^(1/2) analog
    # T|j⟩ = ω^(j³/3) |j⟩ (cubic phase gate)
    omega = np.exp(2j * np.pi / d)
    # Modular inverse of 3 mod d (exists since d prime and d≠3)
    inv3 = pow(3, d - 2, d) if d != 3 else 1
    return np.diag([omega**((j**3 * inv3) % d) for j in range(d)])


# ============================================================
# CONVENIENCE: STANDARD QUBIT GATES (d=2 specializations)
# ============================================================

def H() -> np.ndarray:
    """Hadamard = fourier(2)"""
    return fourier(2)

def X() -> np.ndarray:
    """Pauli-X = shift(2)"""
    return shift(2)

def Y() -> np.ndarray:
    """Pauli-Y"""
    return pauli_y(2)

def Z() -> np.ndarray:
    """Pauli-Z = clock(2)"""
    return clock(2)

def S() -> np.ndarray:
    """S gate"""
    return np.diag([1, 1j]).astype(complex)

def T() -> np.ndarray:
    """T gate"""
    return t_gate(2)

def CNOT() -> np.ndarray:
    """CNOT = controlled_sum(2)"""
    return controlled_sum(2)

def CZ() -> np.ndarray:
    """CZ = controlled_phase_gate(2)"""
    return controlled_phase_gate(2)

def RX(theta: float) -> np.ndarray:
    """Rotation around X."""
    return rotation(2, 0, 1, theta, phi=-np.pi/2) * np.exp(-1j * np.pi/4)  # Adjusted phase

def RY(theta: float) -> np.ndarray:
    """Rotation around Y."""
    return rotation(2, 0, 1, theta)

def RZ(theta: float) -> np.ndarray:
    """Rotation around Z."""
    return diagonal_phase(2, [0, theta])
