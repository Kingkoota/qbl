"""
QBL Compiler — Compiles QBL AST to OpenQASM 3.0

This is the bridge between QBL's human-friendly syntax and the industry-standard
quantum assembly language that runs on real IBM/Google/etc hardware.
"""

from typing import List
from qbl.parser import (
    Program, QubitDecl, CbitDecl, GateBlock, GateCall,
    Measurement, Condition, AssertEntangled, QubitRef, FunctionDef
)


class OpenQASMCompiler:
    """Compiles QBL programs to OpenQASM 3.0 source."""
    
    def __init__(self):
        self.output_lines: List[str] = []
        self.indent_level = 0
    
    def _emit(self, line: str):
        indent = "  " * self.indent_level
        self.output_lines.append(f"{indent}{line}")
    
    def _qubit_ref_str(self, ref: QubitRef) -> str:
        if ref.index is not None:
            return f"{ref.name}[{ref.index}]"
        return ref.name
    
    def compile(self, program: Program) -> str:
        """Compile a full QBL program to OpenQASM 3.0."""
        self.output_lines = []
        
        # Header
        self._emit("OPENQASM 3.0;")
        self._emit("include \"stdgates.inc\";")
        self._emit("")
        
        # Declarations
        for decl in program.declarations:
            if isinstance(decl, QubitDecl):
                self._emit(f"qubit[{decl.size}] {decl.name};")
            elif isinstance(decl, CbitDecl):
                self._emit(f"bit[{decl.size}] {decl.name};")
        
        if program.declarations:
            self._emit("")
        
        # Functions (as gate definitions in QASM)
        for func in program.functions:
            self._compile_function(func)
        
        # Statements
        for stmt in program.statements:
            self._compile_statement(stmt)
        
        return "\n".join(self.output_lines)
    
    def _compile_function(self, func: FunctionDef):
        """Compile a QBL function to an OpenQASM gate definition."""
        params = ", ".join(f"qubit {p}" for p in func.params)
        self._emit(f"gate {func.name}({params}) {{")
        self.indent_level += 1
        for stmt in func.body:
            self._compile_statement(stmt)
        self.indent_level -= 1
        self._emit("}")
        self._emit("")
    
    def _compile_statement(self, stmt):
        """Compile a single statement."""
        if isinstance(stmt, GateBlock):
            self._emit("// gate block")
            for op in stmt.operations:
                self._compile_gate_call(op)
        
        elif isinstance(stmt, GateCall):
            self._compile_gate_call(stmt)
        
        elif isinstance(stmt, Measurement):
            qubit_str = self._qubit_ref_str(stmt.source_qubit)
            self._emit(f"{stmt.target_cbit}[{stmt.target_index}] = measure {qubit_str};")
        
        elif isinstance(stmt, Condition):
            self._emit(f"if ({stmt.cbit_name}[{stmt.cbit_index}] {stmt.operator} {stmt.value}) {{")
            self.indent_level += 1
            for s in stmt.body:
                self._compile_statement(s)
            self.indent_level -= 1
            if stmt.else_body:
                self._emit("} else {")
                self.indent_level += 1
                for s in stmt.else_body:
                    self._compile_statement(s)
                self.indent_level -= 1
            self._emit("}")
        
        elif isinstance(stmt, AssertEntangled):
            # Assertions don't compile to QASM — they're simulation-only
            qubits_str = ", ".join(self._qubit_ref_str(q) for q in stmt.qubits)
            self._emit(f"// ASSERT: entangled({qubits_str})")
    
    def _compile_gate_call(self, gate: GateCall):
        """Compile a gate call to OpenQASM syntax."""
        targets = ", ".join(self._qubit_ref_str(t) for t in gate.targets)
        
        # Map QBL gate names to OpenQASM equivalents
        gate_map = {
            'H': 'h',
            'X': 'x',
            'Y': 'y',
            'Z': 'z',
            'S': 's',
            'T': 't',
            'CNOT': 'cx',
            'CZ': 'cz',
            'SWAP': 'swap',
            'RX': 'rx',
            'RY': 'ry',
            'RZ': 'rz',
            'TOFFOLI': 'ccx',
        }
        
        qasm_name = gate_map.get(gate.gate_name, gate.gate_name.lower())
        
        if gate.params:
            params_str = ", ".join(str(p) for p in gate.params)
            self._emit(f"{qasm_name}({params_str}) {targets};")
        else:
            self._emit(f"{qasm_name} {targets};")
