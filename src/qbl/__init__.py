"""QBL — Qubit Language"""
from qbl.parser import Lexer, Parser, Program
from qbl.simulator import Simulator, ExecutionResult
from qbl.compiler import OpenQASMCompiler
from qbl.qudit import (
    QuditSimulator, QuditState, QuditRegister,
    shift_gate, clock_gate, qudit_fourier, weyl_operator,
    controlled_increment, controlled_phase, qudit_swap,
    modular_multiply, rotation_gate, entangle_pair,
    qudit_teleportation, repetition_code_13,
    D as DIMENSION_13
)


def parse(source: str) -> Program:
    """Parse QBL source code into an AST."""
    tokens = Lexer(source).tokenize()
    return Parser(tokens).parse()


def simulate(source: str, shots: int = 1, seed: int = None) -> list:
    """Parse and simulate QBL source code."""
    program = parse(source)
    sim = Simulator(seed=seed)
    return sim.run(program, shots=shots)


def compile_to_qasm(source: str) -> str:
    """Parse and compile QBL source to OpenQASM 3.0."""
    program = parse(source)
    compiler = OpenQASMCompiler()
    return compiler.compile(program)


def qudit_simulate(registers: list, dimension: int = 13, seed: int = None):
    """Create a dimension-13 qudit simulator and state."""
    regs = [QuditRegister(name, size, dimension) for name, size in registers]
    sim = QuditSimulator(dimension=dimension, seed=seed)
    state = QuditState.initialize(regs, dimension)
    return sim, state


__version__ = "0.3.0"
__all__ = [
    'parse', 'simulate', 'compile_to_qasm', 'qudit_simulate',
    'Lexer', 'Parser', 'Simulator', 'OpenQASMCompiler',
    'QuditSimulator', 'QuditState', 'QuditRegister',
    'shift_gate', 'clock_gate', 'qudit_fourier', 'weyl_operator',
    'controlled_increment', 'controlled_phase', 'qudit_swap',
    'modular_multiply', 'rotation_gate', 'entangle_pair',
    'qudit_teleportation', 'repetition_code_13', 'DIMENSION_13'
]
