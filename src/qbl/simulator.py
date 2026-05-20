"""
QBL Simulator — Statevector quantum simulator backend.

Executes QBL AST programs using numpy-based statevector simulation.
Supports all standard gates, measurement with collapse, and conditional logic.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

from qbl.parser import (
    Program, QubitDecl, CbitDecl, GateBlock, GateCall, 
    Measurement, Condition, AssertEntangled, QubitRef, PulseBlock
)


# ============================================================
# QUANTUM GATES (matrix definitions)
# ============================================================

# Pauli gates
I = np.eye(2, dtype=complex)
X_GATE = np.array([[0, 1], [1, 0]], dtype=complex)
Y_GATE = np.array([[0, -1j], [1j, 0]], dtype=complex)
Z_GATE = np.array([[1, 0], [0, -1]], dtype=complex)

# Hadamard
H_GATE = np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2)

# Phase gates
S_GATE = np.array([[1, 0], [0, 1j]], dtype=complex)
T_GATE = np.array([[1, 0], [0, np.exp(1j * np.pi / 4)]], dtype=complex)

# CNOT (applied via controlled operation logic, not as a raw 4x4)
CNOT_GATE = np.array([
    [1, 0, 0, 0],
    [0, 1, 0, 0],
    [0, 0, 0, 1],
    [0, 0, 1, 0]
], dtype=complex)

# SWAP
SWAP_GATE = np.array([
    [1, 0, 0, 0],
    [0, 0, 1, 0],
    [0, 1, 0, 0],
    [0, 0, 0, 1]
], dtype=complex)

# CZ
CZ_GATE = np.array([
    [1, 0, 0, 0],
    [0, 1, 0, 0],
    [0, 0, 1, 0],
    [0, 0, 0, -1]
], dtype=complex)


def rx_gate(theta: float) -> np.ndarray:
    """Rotation around X-axis."""
    return np.array([
        [np.cos(theta/2), -1j * np.sin(theta/2)],
        [-1j * np.sin(theta/2), np.cos(theta/2)]
    ], dtype=complex)


def ry_gate(theta: float) -> np.ndarray:
    """Rotation around Y-axis."""
    return np.array([
        [np.cos(theta/2), -np.sin(theta/2)],
        [np.sin(theta/2), np.cos(theta/2)]
    ], dtype=complex)


def rz_gate(theta: float) -> np.ndarray:
    """Rotation around Z-axis."""
    return np.array([
        [np.exp(-1j * theta/2), 0],
        [0, np.exp(1j * theta/2)]
    ], dtype=complex)


# ============================================================
# SIMULATOR STATE
# ============================================================

@dataclass
class SimulatorState:
    """Holds the quantum state during simulation."""
    num_qubits: int
    statevector: np.ndarray
    classical_bits: Dict[str, List[int]] = field(default_factory=dict)
    qubit_map: Dict[str, Tuple[int, int]] = field(default_factory=dict)  # name -> (start_idx, size)
    measurement_log: List[dict] = field(default_factory=list)
    
    @classmethod
    def initialize(cls, declarations: List) -> 'SimulatorState':
        """Create initial |0...0⟩ state from declarations."""
        total_qubits = 0
        qubit_map = {}
        classical_bits = {}
        
        for decl in declarations:
            if isinstance(decl, QubitDecl):
                qubit_map[decl.name] = (total_qubits, decl.size)
                total_qubits += decl.size
            elif isinstance(decl, CbitDecl):
                classical_bits[decl.name] = [0] * decl.size
        
        # Initialize to |0...0⟩
        statevector = np.zeros(2**total_qubits, dtype=complex)
        statevector[0] = 1.0
        
        return cls(
            num_qubits=total_qubits,
            statevector=statevector,
            classical_bits=classical_bits,
            qubit_map=qubit_map
        )
    
    def resolve_qubit_index(self, ref: QubitRef) -> int:
        """Convert a QubitRef to absolute qubit index."""
        start, size = self.qubit_map[ref.name]
        idx = ref.index if ref.index is not None else 0
        if idx >= size:
            raise RuntimeError(f"Qubit index {ref.name}[{idx}] out of range (size={size})")
        return start + idx


# ============================================================
# GATE APPLICATION
# ============================================================

def apply_single_qubit_gate(state: SimulatorState, gate: np.ndarray, qubit_idx: int):
    """Apply a single-qubit gate to the statevector."""
    n = state.num_qubits
    sv = state.statevector.reshape([2] * n)
    
    # Apply gate along the qubit axis
    sv = np.tensordot(gate, sv, axes=([1], [qubit_idx]))
    # Move the gate output axis back to the correct position
    sv = np.moveaxis(sv, 0, qubit_idx)
    
    state.statevector = sv.reshape(2**n)


def apply_two_qubit_gate(state: SimulatorState, gate_4x4: np.ndarray, q0_idx: int, q1_idx: int):
    """Apply a two-qubit gate to the statevector."""
    n = state.num_qubits
    sv = state.statevector.reshape([2] * n)
    
    gate_tensor = gate_4x4.reshape(2, 2, 2, 2)
    
    # Contract over the two qubit axes
    sv = np.tensordot(gate_tensor, sv, axes=([2, 3], [q0_idx, q1_idx]))
    # Move axes back into position
    # After tensordot, the first two axes are the gate output
    axes_order = list(range(n))
    # Remove q0 and q1, then insert at correct positions
    remaining = [i for i in range(n) if i not in (q0_idx, q1_idx)]
    # Build new order: gate outputs go to q0_idx and q1_idx positions
    new_order = [None] * n
    new_order[q0_idx] = 0
    new_order[q1_idx] = 1
    gate_out_idx = 2
    for i in range(n):
        if new_order[i] is None:
            new_order[i] = gate_out_idx
            gate_out_idx += 1
    
    sv = np.transpose(sv, new_order)
    state.statevector = sv.reshape(2**n)


def measure_qubit(state: SimulatorState, qubit_idx: int) -> int:
    """Measure a qubit, collapsing the statevector. Returns 0 or 1."""
    n = state.num_qubits
    probs = np.abs(state.statevector) ** 2
    
    # Calculate probability of measuring |1⟩ on this qubit
    prob_one = 0.0
    for i in range(2**n):
        if (i >> (n - 1 - qubit_idx)) & 1:
            prob_one += probs[i]
    
    # Probabilistic collapse
    result = 1 if np.random.random() < prob_one else 0
    
    # Collapse statevector
    for i in range(2**n):
        bit_val = (i >> (n - 1 - qubit_idx)) & 1
        if bit_val != result:
            state.statevector[i] = 0.0
    
    # Renormalize
    norm = np.linalg.norm(state.statevector)
    if norm > 0:
        state.statevector /= norm
    
    return result


def check_entanglement(state: SimulatorState, q0_idx: int, q1_idx: int) -> bool:
    """Check if two qubits are entangled (non-separable)."""
    n = state.num_qubits
    
    if n == 2:
        # For 2 qubits, check if state is a product state
        sv = state.statevector.reshape(2, 2)
        # Try to decompose as tensor product
        u, s, vh = np.linalg.svd(sv)
        # If Schmidt rank > 1, qubits are entangled
        return np.sum(s > 1e-10) > 1
    
    # For n > 2, compute reduced density matrix and check purity
    sv = state.statevector.reshape([2] * n)
    # Trace over all qubits except q0 and q1
    rho = np.tensordot(sv, sv.conj(), axes=0)  # Full density matrix in tensor form
    
    # Simplified check: compute concurrence for the two-qubit subsystem
    # For now, use Schmidt decomposition approach on the bipartition
    keep = sorted([q0_idx, q1_idx])
    trace_over = [i for i in range(n) if i not in keep]
    
    # Reshape for partial trace
    rho_full = np.outer(state.statevector, state.statevector.conj())
    dim = 2**n
    
    # Compute reduced density matrix for the two qubits
    rho_2q = np.zeros((4, 4), dtype=complex)
    for i in range(4):
        for j in range(4):
            for k in range(2**len(trace_over)):
                # Build full indices
                idx_i = _build_index(n, keep, trace_over, i, k)
                idx_j = _build_index(n, keep, trace_over, j, k)
                rho_2q[i, j] += rho_full[idx_i, idx_j]
    
    # Check purity of single-qubit reduced state (trace out one of the pair)
    rho_single = np.array([
        [rho_2q[0,0] + rho_2q[1,1], rho_2q[0,2] + rho_2q[1,3]],
        [rho_2q[2,0] + rho_2q[3,1], rho_2q[2,2] + rho_2q[3,3]]
    ])
    
    purity = np.real(np.trace(rho_single @ rho_single))
    # Pure (purity=1) means not entangled, mixed (purity<1) means entangled
    return purity < 0.99


def _build_index(n: int, keep: List[int], trace: List[int], keep_val: int, trace_val: int) -> int:
    """Build a full basis index from partial indices."""
    bits = [0] * n
    for i, qi in enumerate(keep):
        bits[qi] = (keep_val >> (len(keep) - 1 - i)) & 1
    for i, qi in enumerate(trace):
        bits[qi] = (trace_val >> (len(trace) - 1 - i)) & 1
    
    result = 0
    for b in bits:
        result = (result << 1) | b
    return result


# ============================================================
# EXECUTOR
# ============================================================

@dataclass
class ExecutionResult:
    """Result of running a QBL program."""
    classical_bits: Dict[str, List[int]]
    measurement_log: List[dict]
    final_statevector: np.ndarray
    entanglement_checks: List[dict] = field(default_factory=list)
    num_qubits: int = 0


class Simulator:
    """Executes QBL programs via statevector simulation."""
    
    def __init__(self, seed: Optional[int] = None):
        if seed is not None:
            np.random.seed(seed)
    
    def run(self, program: Program, shots: int = 1) -> List[ExecutionResult]:
        """Run a QBL program for the specified number of shots."""
        results = []
        
        for _ in range(shots):
            state = SimulatorState.initialize(program.declarations)
            self._execute_statements(state, program.statements)
            
            results.append(ExecutionResult(
                classical_bits=dict(state.classical_bits),
                measurement_log=state.measurement_log,
                final_statevector=state.statevector.copy(),
                num_qubits=state.num_qubits
            ))
        
        return results
    
    def _execute_statements(self, state: SimulatorState, statements: List):
        """Execute a list of statements."""
        for stmt in statements:
            self._execute_statement(state, stmt)
    
    def _execute_statement(self, state: SimulatorState, stmt):
        """Execute a single statement."""
        if isinstance(stmt, GateBlock):
            for op in stmt.operations:
                self._apply_gate(state, op)
        
        elif isinstance(stmt, GateCall):
            self._apply_gate(state, stmt)
        
        elif isinstance(stmt, Measurement):
            qubit_idx = state.resolve_qubit_index(stmt.source_qubit)
            result = measure_qubit(state, qubit_idx)
            state.classical_bits[stmt.target_cbit][stmt.target_index] = result
            state.measurement_log.append({
                'qubit': f"{stmt.source_qubit.name}[{stmt.source_qubit.index}]",
                'result': result
            })
        
        elif isinstance(stmt, Condition):
            cbit_val = state.classical_bits[stmt.cbit_name][stmt.cbit_index]
            
            if stmt.operator == '==' and cbit_val == stmt.value:
                self._execute_statements(state, stmt.body)
            elif stmt.operator == '!=' and cbit_val != stmt.value:
                self._execute_statements(state, stmt.body)
            elif stmt.else_body:
                self._execute_statements(state, stmt.else_body)
        
        elif isinstance(stmt, AssertEntangled):
            q0_idx = state.resolve_qubit_index(stmt.qubits[0])
            q1_idx = state.resolve_qubit_index(stmt.qubits[1])
            is_entangled = check_entanglement(state, q0_idx, q1_idx)
            state.measurement_log.append({
                'assertion': 'entangled',
                'qubits': [str(q) for q in stmt.qubits],
                'passed': is_entangled
            })
            if not is_entangled:
                raise RuntimeError(
                    f"Entanglement assertion failed: "
                    f"{stmt.qubits[0].name}[{stmt.qubits[0].index}] and "
                    f"{stmt.qubits[1].name}[{stmt.qubits[1].index}] are separable"
                )
    
    def _apply_gate(self, state: SimulatorState, gate_call: GateCall):
        """Apply a gate operation."""
        name = gate_call.gate_name
        
        # Single-qubit gates
        single_gates = {
            'H': H_GATE,
            'X': X_GATE,
            'Y': Y_GATE,
            'Z': Z_GATE,
            'S': S_GATE,
            'T': T_GATE,
        }
        
        if name in single_gates:
            idx = state.resolve_qubit_index(gate_call.targets[0])
            apply_single_qubit_gate(state, single_gates[name], idx)
            return
        
        # Parameterized single-qubit gates
        if name == 'RX':
            idx = state.resolve_qubit_index(gate_call.targets[0])
            theta = gate_call.params[0] if gate_call.params else 0.0
            apply_single_qubit_gate(state, rx_gate(theta), idx)
            return
        
        if name == 'RY':
            idx = state.resolve_qubit_index(gate_call.targets[0])
            theta = gate_call.params[0] if gate_call.params else 0.0
            apply_single_qubit_gate(state, ry_gate(theta), idx)
            return
        
        if name == 'RZ':
            idx = state.resolve_qubit_index(gate_call.targets[0])
            theta = gate_call.params[0] if gate_call.params else 0.0
            apply_single_qubit_gate(state, rz_gate(theta), idx)
            return
        
        # Two-qubit gates
        if name == 'CNOT':
            q0 = state.resolve_qubit_index(gate_call.targets[0])
            q1 = state.resolve_qubit_index(gate_call.targets[1])
            apply_two_qubit_gate(state, CNOT_GATE, q0, q1)
            return
        
        if name == 'CZ':
            q0 = state.resolve_qubit_index(gate_call.targets[0])
            q1 = state.resolve_qubit_index(gate_call.targets[1])
            apply_two_qubit_gate(state, CZ_GATE, q0, q1)
            return
        
        if name == 'SWAP':
            q0 = state.resolve_qubit_index(gate_call.targets[0])
            q1 = state.resolve_qubit_index(gate_call.targets[1])
            apply_two_qubit_gate(state, SWAP_GATE, q0, q1)
            return
        
        raise RuntimeError(f"Unknown gate: {name}")
