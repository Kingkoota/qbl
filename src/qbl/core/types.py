"""
QBL Core — Type System

Quantum type system with no-clone enforcement, linearity tracking,
and dimension-aware type checking.

Type Hierarchy:
  Quantum[d]     — d-dimensional quantum register (linear type, no-clone)
  Classical[d]   — d-valued classical register (copyable)
  Entangled[d,n] — n-particle entangled state (composite, non-separable)
  Mixed[d]       — density matrix state (for open systems)
"""

from dataclasses import dataclass, field
from typing import Optional, List, Set, FrozenSet
from enum import Enum, auto


class TypeKind(Enum):
    QUANTUM = auto()     # Pure quantum state (ket)
    CLASSICAL = auto()   # Classical measurement outcome
    ENTANGLED = auto()   # Multi-particle entangled state
    MIXED = auto()       # Density matrix (open system)
    GATE = auto()        # Unitary operator
    CHANNEL = auto()     # Quantum channel (CPTP map)


class Linearity(Enum):
    LINEAR = auto()      # Must be used exactly once (quantum)
    AFFINE = auto()      # Used at most once (consumed by measurement)
    UNRESTRICTED = auto() # Can be copied freely (classical)


@dataclass(frozen=True)
class QBLType:
    """Base type for all QBL values."""
    kind: TypeKind
    dimension: int  # d
    linearity: Linearity
    
    @property
    def is_quantum(self) -> bool:
        return self.kind in (TypeKind.QUANTUM, TypeKind.ENTANGLED, TypeKind.MIXED)
    
    @property
    def is_copyable(self) -> bool:
        return self.linearity == Linearity.UNRESTRICTED


@dataclass(frozen=True)
class QuantumType(QBLType):
    """Type for quantum registers: qubit[n] or qudit<d>[n]."""
    num_sites: int = 1
    
    def __post_init__(self):
        object.__setattr__(self, 'kind', TypeKind.QUANTUM)
        object.__setattr__(self, 'linearity', Linearity.LINEAR)
    
    @property
    def hilbert_dim(self) -> int:
        return self.dimension ** self.num_sites


@dataclass(frozen=True)
class ClassicalType(QBLType):
    """Type for classical registers: cbit[n] or cdit<d>[n]."""
    num_sites: int = 1
    
    def __post_init__(self):
        object.__setattr__(self, 'kind', TypeKind.CLASSICAL)
        object.__setattr__(self, 'linearity', Linearity.UNRESTRICTED)


@dataclass(frozen=True)
class GateType(QBLType):
    """Type for gate operations."""
    input_dims: tuple = ()   # (d1, d2, ...) dimensions of input qudits
    num_params: int = 0      # Number of continuous parameters
    
    def __post_init__(self):
        object.__setattr__(self, 'kind', TypeKind.GATE)
        object.__setattr__(self, 'linearity', Linearity.UNRESTRICTED)


# ============================================================
# TYPE CHECKER
# ============================================================

@dataclass
class TypeEnvironment:
    """Tracks types and linearity during compilation."""
    bindings: dict = field(default_factory=dict)  # name -> QBLType
    consumed: Set[str] = field(default_factory=set)  # consumed linear resources
    entangled_groups: List[FrozenSet[str]] = field(default_factory=list)
    
    def declare(self, name: str, typ: QBLType):
        """Declare a new variable."""
        if name in self.bindings:
            raise TypeError(f"Redeclaration of '{name}'")
        self.bindings[name] = typ
    
    def use(self, name: str) -> QBLType:
        """Use a variable (consumes if linear)."""
        if name not in self.bindings:
            raise TypeError(f"Undefined variable: '{name}'")
        
        typ = self.bindings[name]
        
        if name in self.consumed:
            raise TypeError(
                f"No-clone violation: '{name}' already consumed "
                f"(measured or transferred). Quantum states cannot be copied."
            )
        
        return typ
    
    def consume(self, name: str):
        """Mark a quantum variable as consumed (by measurement or transfer)."""
        typ = self.bindings.get(name)
        if typ and typ.linearity == Linearity.LINEAR:
            self.consumed.add(name)
    
    def mark_entangled(self, names: List[str]):
        """Record that these variables are entangled."""
        group = frozenset(names)
        self.entangled_groups.append(group)
    
    def check_gate_application(self, gate_type: GateType, target_names: List[str]):
        """Verify a gate can be applied to the given targets."""
        for i, name in enumerate(target_names):
            target_type = self.use(name)
            
            if not target_type.is_quantum:
                raise TypeError(
                    f"Gate applied to non-quantum type: '{name}' is {target_type.kind.name}"
                )
            
            if name in self.consumed:
                raise TypeError(
                    f"Gate applied to consumed qudit: '{name}' was already measured"
                )
            
            if i < len(gate_type.input_dims):
                expected_d = gate_type.input_dims[i]
                if target_type.dimension != expected_d:
                    raise TypeError(
                        f"Dimension mismatch: gate expects d={expected_d} "
                        f"but '{name}' has d={target_type.dimension}"
                    )
    
    def check_measurement(self, quantum_name: str, classical_name: str):
        """Verify measurement is valid."""
        q_type = self.use(quantum_name)
        c_type = self.use(classical_name)
        
        if not q_type.is_quantum:
            raise TypeError(f"Cannot measure non-quantum variable: '{quantum_name}'")
        
        if quantum_name in self.consumed:
            raise TypeError(f"Cannot measure already-consumed qudit: '{quantum_name}'")
        
        if c_type.kind != TypeKind.CLASSICAL:
            raise TypeError(f"Measurement target must be classical: '{classical_name}'")
        
        if q_type.dimension != c_type.dimension:
            raise TypeError(
                f"Dimension mismatch in measurement: "
                f"qudit d={q_type.dimension}, classical d={c_type.dimension}"
            )
        
        # Consume the quantum variable
        self.consume(quantum_name)


# ============================================================
# STANDARD TYPE CONSTRUCTORS
# ============================================================

def qubit(n: int = 1) -> QuantumType:
    """Type for n qubits."""
    return QuantumType(dimension=2, num_sites=n, kind=TypeKind.QUANTUM, linearity=Linearity.LINEAR)

def qudit(d: int, n: int = 1) -> QuantumType:
    """Type for n qudits of dimension d."""
    return QuantumType(dimension=d, num_sites=n, kind=TypeKind.QUANTUM, linearity=Linearity.LINEAR)

def qudit13(n: int = 1) -> QuantumType:
    """Type for n dimension-13 qudits."""
    return qudit(13, n)

def cbit(n: int = 1) -> ClassicalType:
    """Type for n classical bits."""
    return ClassicalType(dimension=2, num_sites=n, kind=TypeKind.CLASSICAL, linearity=Linearity.UNRESTRICTED)

def cdit(d: int, n: int = 1) -> ClassicalType:
    """Type for n classical d-valued registers."""
    return ClassicalType(dimension=d, num_sites=n, kind=TypeKind.CLASSICAL, linearity=Linearity.UNRESTRICTED)
