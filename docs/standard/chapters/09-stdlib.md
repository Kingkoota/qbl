# Chapter 9: Standard Library

## 9.1 Core Gates (`qbl.gates`)

### 9.1.1 Single-Qudit Gates

| Gate | Syntax | Action | Dimension |
|------|--------|--------|-----------|
| Identity | `I(q)` | No-op | any |
| Shift | `SHIFT(q, k=1)` | \|j⟩→\|j+k mod d⟩ | any |
| Clock | `CLOCK(q, k=1)` | \|j⟩→ω^(jk)\|j⟩ | any |
| QFT | `QFT(q)` | Fourier transform | any |
| Phase | `PHASE(q, k=1)` | \|j⟩→ω^(kj(j-1)/2)\|j⟩ | any |
| Rotation | `ROT(q, a, b, θ, φ)` | Rotate in \|a⟩-\|b⟩ subspace | any |
| Multiply | `MULT(q, a)` | \|j⟩→\|aj mod d⟩ | prime |
| Weyl | `WEYL(q, a, b)` | Displacement D(a,b) | any |
| Hadamard | `H(q)` | QFT specialized to d=2 | d=2 |
| Pauli-X | `X(q)` | Bit flip | d=2 |
| Pauli-Y | `Y(q)` | iXZ | d=2 |
| Pauli-Z | `Z(q)` | Phase flip | d=2 |
| T gate | `T(q)` | π/8 phase (d=2) / cubic phase (d>2) | any |
| S gate | `S(q)` | π/4 phase | d=2 |
| RX | `RX(q, θ)` | X-rotation | d=2 |
| RY | `RY(q, θ)` | Y-rotation | d=2 |
| RZ | `RZ(q, θ)` | Z-rotation | d=2 |

### 9.1.2 Two-Qudit Gates

| Gate | Syntax | Action | Dimension |
|------|--------|--------|-----------|
| SUM | `SUM(ctrl, tgt)` | \|j⟩\|k⟩→\|j⟩\|j+k mod d⟩ | any |
| CPHASE | `CPHASE(q0, q1)` | \|j⟩\|k⟩→ω^(jk)\|j⟩\|k⟩ | any |
| DSWAP | `DSWAP(q0, q1)` | \|j⟩\|k⟩→\|k⟩\|j⟩ | any |
| CNOT | `CNOT(ctrl, tgt)` | SUM for d=2 | d=2 |
| CZ | `CZ(q0, q1)` | CPHASE for d=2 | d=2 |
| SWAP | `SWAP(q0, q1)` | DSWAP for d=2 | d=2 |

### 9.1.3 Three-Qudit Gates

| Gate | Syntax | Action | Dimension |
|------|--------|--------|-----------|
| TOFFOLI | `TOFFOLI(c0,c1,tgt)` | Doubly-controlled NOT | d=2 |
| CSUM | `CSUM(c0,c1,tgt)` | Controlled-SUM | any |

## 9.2 Protocols (`qbl.protocols`)

| Protocol | Function | Description |
|----------|----------|-------------|
| Teleportation | `teleport(src -> dst via channel)` | Qudit state transfer |
| Superdense | `superdense.encode(q, a, b)` | d² message encoding |
| QKD | `qkd.prepare(level, basis)` | Key distribution |
| Distillation | `distill(pair_a, pair_b)` | Entanglement purification |

## 9.3 Error Correction (`qbl.codes`)

| Code | Declaration | Parameters |
|------|-------------|------------|
| Repetition | `code: repetition<d>(n)` | [[n,1,n]]_d |
| Steane | `code: steane<d>` | [[7,1,3]]_d |
| Surface | `code: surface<d>(L)` | [[L²,1,L]]_d |
| Color | `code: color<d>` | [[7,1,3]]_d |

## 9.4 Analysis (`qbl.analysis`)

| Function | Returns | Description |
|----------|---------|-------------|
| `entropy(q)` | float | Von Neumann entropy |
| `purity(q)` | float | Tr(ρ²) |
| `fidelity(q, target)` | float | State fidelity |
| `concurrence(q0, q1)` | float | Entanglement measure |
| `wigner(q)` | array | Discrete Wigner function |
| `negativity(q)` | float | Wigner negativity (non-classicality) |

## 9.5 Math (`qbl.math`)

| Function | Description |
|----------|-------------|
| `mod(a, d)` | Modular arithmetic |
| `gcd(a, b)` | Greatest common divisor |
| `modinv(a, d)` | Modular inverse (a⁻¹ mod d) |
| `is_prime(d)` | Primality test |
| `primitive_root(d)` | Find generator of Z_d* |
| `dft_matrix(d)` | d×d DFT matrix |
| `omega(d)` | Primitive d-th root of unity |

## 9.6 I/O (`qbl.io`)

| Function | Description |
|----------|-------------|
| `export_qasm(program)` | Compile to OpenQASM 3.0 |
| `export_json(results)` | Export measurement results |
| `export_svg(circuit)` | Circuit diagram |
| `import_qasm(file)` | Import from OpenQASM |
| `visualize(state)` | State visualization |
