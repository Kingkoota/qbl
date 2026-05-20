# Chapter 8: Compilation Model

## 8.1 Pipeline

```
QBL Source (.qbl)
      │
      ├─── Lexer ──────────── Tokens
      │
      ├─── Parser ─────────── AST (Abstract Syntax Tree)
      │
      ├─── Type Checker ───── Typed AST + Linearity Verification
      │
      ├─── Optimizer ──────── Optimized IR (gate cancellation, fusion)
      │
      ├─── Backend Select ─── Target-specific compilation
      │         │
      │         ├── Statevector (d=2 or d=13)  → numpy execution
      │         ├── OpenQASM 3.0 (d=2)         → IBM/Google/IonQ hardware
      │         ├── Pulse (hardware-specific)    → waveform generation
      │         └── Qudit Native (d=13)         → trapped ion / transmon
      │
      └─── Output ─────────── Executable / Circuit / Waveforms
```

## 8.2 Intermediate Representation (IR)

### 8.2.1 Gate IR

```
%0 = alloc_qudit<13>[3]          // Allocate 3 qudits
%1 = qft %0[0]                   // QFT on qudit 0
%2 = shift %0[0], 7              // SHIFT by 7
%3 = sum %0[0], %0[1]            // SUM gate
%4 = measure %0[1] -> cdit<13>   // Measure
%5 = cond %4 == 0 { ... }        // Conditional
dealloc %0                        // Release
```

### 8.2.2 Optimization Passes

| Pass | Description | Example |
|------|-------------|---------|
| Gate cancellation | Remove U·U† pairs | QFT; QFT† → identity |
| Gate fusion | Merge adjacent single-qudit gates | SHIFT(3); SHIFT(5) → SHIFT(8) |
| Commutation | Reorder commuting gates for parallelism | Independent gates in parallel |
| Decomposition | Break multi-qudit gates into native set | DSWAP → 3×SUM |
| Constant folding | Evaluate known classical values at compile time | SHIFT(q, 3+4) → SHIFT(q, 7) |

## 8.3 Backend: Statevector Simulator

### 8.3.1 Qubit Mode (d=2)

```python
# State: numpy array of size 2^n (complex128)
# Gates: tensor contraction on selected qubit axes
# Measurement: probabilistic collapse with renormalization
```

### 8.3.2 Qudit Mode (d=13)

```python
# State: numpy array of size 13^n (complex128)
# Gates: tensor contraction on selected qudit axes  
# Measurement: d-outcome projection with renormalization
# Memory: 13^n × 16 bytes (128-bit complex)
#   n=1: 208 bytes
#   n=2: 2.7 KB
#   n=3: 35 KB
#   n=5: 5.9 MB
#   n=7: 1.0 GB
#   n=9: 169 GB (requires distributed simulation)
```

## 8.4 Backend: OpenQASM 3.0

```qasm
// QBL compiles qubit programs to OpenQASM 3.0
OPENQASM 3.0;
include "stdgates.inc";

qubit[3] q;
bit[3] c;

h q[0];
cx q[0], q[1];
cx q[1], q[2];

c[0] = measure q[0];
c[1] = measure q[1];
c[2] = measure q[2];
```

### 8.4.1 Qudit Compilation (d>2 → d=2 decomposition)

When targeting qubit-only hardware, d=13 qudits are decomposed:

```
1 qudit (d=13) → 4 qubits (2⁴=16 ≥ 13, with 3 unused states)
Encoding: |j⟩_13 → |j⟩_binary (j < 13), states 13-15 forbidden
```

Gate decomposition costs:
| Qudit Gate | Qubit Cost |
|-----------|------------|
| SHIFT | O(d) two-qubit gates |
| CLOCK | O(d) single-qubit phases |
| QFT | O(d²) gates |
| SUM | O(d²) two-qubit gates |

## 8.5 Backend: Pulse Level

```qbl
// Compile to hardware-specific microwave pulses
pulse(q[0], duration: 20ns) {
    waveform: drag(amp: 0.8, sigma: 5ns, beta: -0.3)
    freq: 5.123 GHz
    phase: 0.0
}
```

### 8.5.1 Hardware Targets

| Platform | Native d | Control |
|----------|----------|---------|
| Superconducting (IBM, Google) | 2 (up to ~5 levels accessible) | Microwave pulses |
| Trapped Ion (IonQ, Quantinuum) | 2 (up to ~13 levels accessible) | Laser pulses |
| Photonic (Xanadu, PsiQuantum) | ∞ (Fock states) | Beam splitters |
| Neutral Atom (QuEra) | 2-3 | Rydberg excitation |
| NV Center | 3 | Microwave + RF |

**Key insight:** Trapped ions naturally support d=13 via the 13 Zeeman/hyperfine levels of ions like ¹³⁷Ba⁺ or ¹⁷¹Yb⁺.

## 8.6 Compilation Flags

```bash
qbl compile program.qbl \
    --backend=statevector_qudit \
    --dimension=13 \
    --optimize=2 \
    --shots=1000 \
    --output=results.json
```

| Flag | Values | Default |
|------|--------|---------|
| `--backend` | statevector_qubit, statevector_qudit, openqasm, pulse | statevector_qudit |
| `--dimension` | 2, 3, 5, 7, 11, 13 | 13 |
| `--optimize` | 0 (none), 1 (basic), 2 (aggressive) | 1 |
| `--shots` | 1..10⁶ | 1024 |
| `--seed` | integer | random |
| `--target` | ibm_eagle, ionq_aria, generic | generic |
