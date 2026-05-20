# QBL — Quantum Base Language

**The dimension-agnostic quantum programming standard.**

QBL is the first quantum programming language that treats Hilbert space dimension as a first-class parameter. Write quantum programs for qubits (d=2) and qudits (d=13) in a single unified grammar.

## Why QBL?

| Feature | QBL | OpenQASM | Q# | Qiskit | Silq |
|---------|-----|----------|-----|--------|------|
| Native qudit (d>2) | ✓ d=13 | ✗ | ✗ | ✗ | ✗ |
| Linear types (no-clone) | ✓ | ✗ | partial | ✗ | ✓ |
| Gate + pulse unified | ✓ | partial | ✗ | ✗ | ✗ |
| Error correction built-in | ✓ | ✗ | ✗ | library | ✗ |
| Hardware agnostic | ✓ | partial | ✗ | partial | ✗ |
| Real-time feedback | ✓ | ✓ | ✗ | ✗ | ✗ |

## Quick Start

```bash
pip install qbl-0.3.0-py3-none-any.whl
```

```python
import qbl

# Qubit mode (d=2)
results = qbl.simulate("""
    qubit q[2]
    cbit c[2]
    H(q[0])
    CNOT(q[0], q[1])
    c[0] = measure(q[0])
    c[1] = measure(q[1])
""", shots=1000)

# Qudit mode (d=13) 
sim, state = qbl.qudit_simulate([("q", 2)], dimension=13)
qbl.entangle_pair(state, sim, 0, 1)
print(sim.entanglement_entropy(state, 0))  # → ln(13) ≈ 2.565
```

## Architecture

```
qbl/
├── core/                    # Algebraic foundation
│   ├── algebra.py           # Hilbert spaces, traces, entropy
│   ├── gates.py             # Universal gate algebra (any d)
│   └── types.py             # Linear type system
├── parser.py                # Lexer + Parser → AST
├── simulator.py             # Qubit statevector backend
├── qudit.py                 # Dimension-13 qudit engine
├── compiler.py              # OpenQASM 3.0 backend
├── next_standard.py         # Patent-gap features
├── protocols/               # Teleportation, QKD, superdense coding
├── backends/                # Backend registry
├── cli.py                   # Command-line interface
└── qbl_run.py              # Automated runner

docs/
├── standard/                # QBL Language Standard
│   ├── INDEX.md             # Standard overview
│   └── chapters/
│       ├── 01-introduction.md
│       ├── 02-lexical.md
│       ├── 03-types.md
│       ├── 04-gates.md
│       ├── 05-measurement.md
│       ├── 06-protocols.md
│       ├── 07-error-correction.md
│       ├── 08-compilation.md
│       ├── 09-stdlib.md
│       └── 10-conformance.md
├── DESIGN.md                # Language design rationale
└── PATENT_LANDSCAPE.md      # Patent gap analysis

examples/
├── qubit/                   # d=2 examples
├── qudit/                   # d=13 examples
└── protocols/               # Protocol implementations
```

## Dimension 13: Why Prime Matters

| Property | d=2 (qubit) | d=13 (qudit) | Advantage |
|----------|-------------|--------------|-----------|
| Info per site | 1 bit | 3.7 bits | 3.7× density |
| Pauli operators | 3 | 168 | Richer error diagnosis |
| Weyl basis size | 4 | 169 | Complete operator basis |
| Bell pair entropy | ln(2) | ln(13) | Higher entanglement |
| MUBs available | 3 | 14 | Better QKD |
| Arithmetic | binary | mod-13 native | Shor's algorithm |

## Gate Set

### Dimension-Agnostic (work for any d)

```qbl
SHIFT(q, k)        // X^k: cyclic shift
CLOCK(q, k)        // Z^k: phase clock
QFT(q)             // Quantum Fourier Transform
WEYL(q, a, b)      // Displacement D(a,b)
SUM(q0, q1)        // Controlled addition (CNOT analog)
CPHASE(q0, q1)     // Controlled phase (CZ analog)
MULT(q, a)         // Modular multiplication
ROT(q, a, b, θ, φ) // Subspace rotation
```

### Qubit-Specific (d=2)

```qbl
H  X  Y  Z  S  T  CNOT  CZ  SWAP  TOFFOLI  RX  RY  RZ
```

## Version History

| Version | Date | Features |
|---------|------|----------|
| 0.1.0 | 2026-05-19 | Parser, simulator, compiler, Bell/GHZ demos |
| 0.2.0 | 2026-05-19 | CLI runner, 6 patent-gap features, distribution |
| 0.3.0 | 2026-05-20 | **Dimension-13 qudits**, core algebra, type system, protocols, full standard |

## Standard

The QBL Language Standard is defined in `docs/standard/`. It specifies:

- Complete syntax and grammar (EBNF)
- Linear type system with no-clone enforcement
- Gate algebra based on Weyl-Heisenberg group
- Measurement model (projective + POVM)
- Compilation pipeline (source → IR → backend)
- Standard library (gates, protocols, codes, analysis)
- Three conformance levels (Core, Standard, Full)

## License

Proprietary. Patent pending.

---

*Built by Kootaverse. The quantum standard starts here.*
