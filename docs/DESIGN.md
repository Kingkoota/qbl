# QBL — Qubit Language

## What Exists (and their gaps)

| Language | Level | Gap |
|----------|-------|-----|
| OpenQASM 3.0 | Assembly | No pulse control, no real-time feedback, verbose |
| Q# | High-level | Microsoft ecosystem lock-in, no pulse access |
| Qiskit (Python) | Library | Not a language — Python overhead, no native types |
| Cirq (Python) | Library | Google-specific, research-focused |
| Silq | High-level | Academic, minimal adoption, no hardware target |
| QUA | Pulse-level | Proprietary (Quantum Machines only) |

## What's Missing: A Unified Qubit Language

No existing language combines:
1. **Readable syntax** (like Python) with **quantum-native types**
2. **Gate-level** AND **pulse-level** control in one grammar
3. **Real-time classical feedback** (measure → decide → act in nanoseconds)
4. **Hardware-agnostic** compilation (targets OpenQASM, QUA, or direct hardware)
5. **Built-in noise modeling** (simulate decoherence at language level)

## QBL Design Principles

1. **Qubits are first-class citizens** — not objects, not arrays, native types
2. **Dual-mode**: `gate { }` blocks for circuit logic, `pulse { }` blocks for waveform control
3. **Measure-and-branch natively** — `if measure(q)` is a language primitive
4. **Compiles to OpenQASM 3.0** as default backend
5. **Built-in simulator** — run without hardware

## Syntax Overview

```qbl
// Declare qubits
qubit q[3]
cbit c[3]

// Gate-level operation
gate {
    H(q[0])
    CNOT(q[0], q[1])
    CNOT(q[1], q[2])
}

// Measure with real-time feedback
c[0] = measure(q[0])
if c[0] == 1 {
    X(q[2])  // conditional correction
}

// Pulse-level control (hardware-specific optimization)
pulse(q[0], duration: 20ns) {
    waveform: gaussian(amp: 0.5, sigma: 5ns)
    freq: 5.1 GHz
    phase: 0.0
}

// Entanglement verification
assert entangled(q[0], q[1])  // built-in verification primitive
```

## Architecture

```
QBL Source (.qbl)
      │
      ▼
┌─────────────┐
│   Parser    │  (Tokenizer + AST)
└─────────────┘
      │
      ▼
┌─────────────┐
│  Analyzer   │  (Type check, qubit lifetime, no-clone enforcement)
└─────────────┘
      │
      ▼
┌─────────────────────┐
│  Backend Compiler    │
│  ├─ OpenQASM 3.0    │
│  ├─ Simulator (numpy)│
│  └─ (future: QUA)   │
└─────────────────────┘
```
