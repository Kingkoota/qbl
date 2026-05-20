# Chapter 3: Type System

## 3.1 Overview

QBL's type system enforces quantum mechanical constraints at compile time:

- **No-cloning theorem** → linear types for quantum values
- **Measurement irreversibility** → affine consumption on measure
- **Dimensional consistency** → gates must match register dimension

## 3.2 Type Hierarchy

```
Type
├── Quantum[d, n]        — n qudits of dimension d (linear)
│   ├── qubit[n]         — Quantum[2, n]
│   └── qudit<13>[n]     — Quantum[13, n]
├── Classical[d, n]      — n d-valued registers (unrestricted)
│   ├── cbit[n]          — Classical[2, n]
│   └── cdit<13>[n]      — Classical[13, n]
├── Gate[d, k, p]        — k-qudit gate with p parameters
├── Channel[d, k]        — CPTP map on k qudits
└── Protocol[d]          — Named protocol specification
```

## 3.3 Linearity Rules

| Type | Linearity | Copy | Discard | Reason |
|------|-----------|------|---------|--------|
| Quantum[d,n] | Linear | ✗ | ✗ | No-cloning theorem |
| Classical[d,n] | Unrestricted | ✓ | ✓ | Classical info copyable |
| Gate[d,k,p] | Unrestricted | ✓ | ✓ | Gates are reusable |

### 3.3.1 No-Clone Enforcement

```qbl
qubit q[1]
// ERROR: Cannot copy quantum state
// qubit r = q     // Compile error: linear type copied

// OK: Move semantics
qubit r <- q       // q is consumed, r owns the state

// ERROR: Use after consumption
// H(q)            // Compile error: q already consumed
```

### 3.3.2 Measurement Consumption

```qbl
qudit<13> q[1]
cdit<13> c[1]

H(q[0])
c[0] = measure(q[0])   // q[0] consumed

// ERROR: Post-measurement gate
// SHIFT(q[0])          // Compile error: q[0] consumed by measurement
```

## 3.4 Dimension Checking

Gates and operations must match the dimension of their targets:

```qbl
qubit q[2]         // d=2
qudit<13> r[2]     // d=13

H(q[0])            // OK: H is defined for d=2
QFT(r[0])          // OK: QFT works for any d

// ERROR: Dimension mismatch
// SHIFT(q[0])     // Compile error: SHIFT requires d>2 target
// H(r[0])         // Compile error: H is d=2 only; use QFT for d=13

// OK: Generic gates adapt to dimension
QFT(q[0])          // QFT at d=2 = Hadamard
QFT(r[0])          // QFT at d=13 = 13-point Fourier transform
```

## 3.5 Entanglement Tracking

The type system tracks entanglement groups:

```qbl
qudit<13> q[3]

// After entangle: q[0] and q[1] form a composite system
entangle(q[0], q[1])

// Type of q[0] is now: Quantum[13, 1] ∩ Entangled({q[0], q[1]})
// Measuring q[0] affects q[1]

c[0] = measure(q[0])  // Collapses both q[0] AND q[1]
```

## 3.6 Type Declarations

```qbl
// Explicit dimension
qubit q[4]              // 4 qubits (d=2)
qudit<13> r[3]          // 3 qudits (d=13)
qudit<7> s[2]           // 2 qudits (d=7)

// Classical registers (match quantum dimension)
cbit c[4]               // 4 classical bits
cdit<13> d[3]           // 3 classical 13-level registers

// Type aliases
type EPR = Entangled[2, 2]          // Bell pair
type Bell13 = Entangled[13, 2]      // d=13 Bell pair
type GHZ13_5 = Entangled[13, 5]     // 5-qudit GHZ state

// Generic functions
def swap<d>(a: Quantum[d,1], b: Quantum[d,1]) {
    SUM(a, b)
    SUM(b, a)  // Uses inverse
    SUM(a, b)
}
```

## 3.7 Standard Type Constructors

| Constructor | Expansion | Description |
|-------------|-----------|-------------|
| `qubit[n]` | `Quantum[2, n]` | n qubits |
| `qudit<d>[n]` | `Quantum[d, n]` | n d-level qudits |
| `cbit[n]` | `Classical[2, n]` | n classical bits |
| `cdit<d>[n]` | `Classical[d, n]` | n d-level classical |
| `Gate<d,k>` | `Unitary[d^k × d^k]` | k-qudit gate at dimension d |

## 3.8 Subtyping

```
Quantum[d, n] <: Measurable[d, n]
Classical[d, n] <: Copyable
Gate[d, k, 0] <: Clifford[d, k]   (if gate is Clifford)
```
