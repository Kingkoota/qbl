"""QBL Core Module — The algebraic foundation."""
from qbl.core.algebra import (
    HilbertSpace, Dimension, DEFAULT_DIMENSION,
    root_of_unity, is_unitary, tensor_product, partial_trace,
    fidelity, von_neumann_entropy, purity
)
from qbl.core.gates import (
    # Universal (dimension-parameterized)
    identity, shift, clock, weyl, fourier,
    phase_gate, controlled_sum, controlled_phase_gate,
    swap, modular_multiply, rotation, diagonal_phase, t_gate,
    # Qubit convenience
    H, X, Y, Z, S, T, CNOT, CZ, RX, RY, RZ
)
from qbl.core.types import (
    QBLType, QuantumType, ClassicalType, GateType,
    TypeKind, Linearity, TypeEnvironment,
    qubit, qudit, qudit13, cbit, cdit
)
