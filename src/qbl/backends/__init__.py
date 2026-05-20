"""
QBL Backends — Compilation and Simulation Targets

Backend hierarchy:
  StatevectorBackend  — exact simulation (numpy, d-agnostic)
  OpenQASMBackend     — compile to OpenQASM 3.0 (d=2 only currently)
  PulseBackend        — hardware pulse generation (superconducting, trapped ion, etc.)
  NoiseBackend        — density matrix simulation with decoherence
"""

from qbl.simulator import Simulator  # qubit statevector
from qbl.qudit import QuditSimulator  # qudit statevector
from qbl.compiler import OpenQASMCompiler


class BackendRegistry:
    """Registry of available compilation/simulation backends."""
    
    _backends = {}
    
    @classmethod
    def register(cls, name: str, backend_class):
        cls._backends[name] = backend_class
    
    @classmethod
    def get(cls, name: str):
        if name not in cls._backends:
            available = list(cls._backends.keys())
            raise KeyError(f"Unknown backend: {name}. Available: {available}")
        return cls._backends[name]
    
    @classmethod
    def list_all(cls) -> list:
        return list(cls._backends.keys())


# Register built-in backends
BackendRegistry.register('statevector_qubit', Simulator)
BackendRegistry.register('statevector_qudit', QuditSimulator)
BackendRegistry.register('openqasm', OpenQASMCompiler)
