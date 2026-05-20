# Chapter 10: Conformance

## 10.1 Implementation Levels

A QBL implementation SHALL declare conformance at one of these levels:

### Level 1: Core (Minimum Viable)

An implementation conforming to Level 1 MUST support:

- [ ] Lexing and parsing of all QBL syntax (Chapter 2)
- [ ] Type checking with linear type enforcement (Chapter 3)
- [ ] All single-qudit gates for d=2 AND d=13 (Chapter 4, §4.2-4.4)
- [ ] All two-qudit gates for d=2 AND d=13 (Chapter 4, §4.3.3-4.3.6)
- [ ] Projective measurement with probabilistic collapse (Chapter 5, §5.1)
- [ ] Conditional execution based on measurement results (Chapter 5, §5.3)
- [ ] Statevector simulation backend (Chapter 8, §8.3)
- [ ] At least n=5 qudits (d=13) or n=20 qubits (d=2)

### Level 2: Standard

An implementation conforming to Level 2 MUST support all Level 1 features PLUS:

- [ ] All protocols from the standard library (Chapter 6)
- [ ] At least one error correction code (Chapter 7)
- [ ] OpenQASM 3.0 compilation (Chapter 8, §8.4)
- [ ] Gate optimization passes (Chapter 8, §8.2.2)
- [ ] POVM measurements (Chapter 5, §5.2)
- [ ] At least n=9 qudits (d=13) or n=30 qubits (d=2)

### Level 3: Full

An implementation conforming to Level 3 MUST support all Level 2 features PLUS:

- [ ] Pulse-level programming (Chapter 8, §8.5)
- [ ] Autonomous error correction (Chapter 7, §7.3)
- [ ] Latency-bounded feedback (Chapter 5, §5.3.2)
- [ ] Multiple backend targets
- [ ] Hardware-specific compilation
- [ ] Arbitrary prime dimension d ≤ 23

## 10.2 Conformance Testing

### 10.2.1 Test Categories

| Category | Tests | Description |
|----------|-------|-------------|
| Syntax | 50+ | Parse all valid programs, reject invalid |
| Types | 30+ | Linear type enforcement, dimension checks |
| Gates | 100+ | Verify all gate matrices are unitary |
| Simulation | 50+ | Known algorithm outcomes (Bell, GHZ, teleportation) |
| Measurement | 20+ | Statistical distribution verification |
| Protocols | 10+ | End-to-end protocol correctness |

### 10.2.2 Required Test Programs

Every conforming implementation MUST correctly execute:

```qbl
// TEST 1: Bell state (d=2)
qubit q[2]; cbit c[2]
H(q[0]); CNOT(q[0], q[1])
c = measure_all(q)
// REQUIRE: c[0] == c[1] in all shots

// TEST 2: GHZ state (d=2)
qubit q[5]; cbit c[5]
H(q[0])
for i in 1..5 { CNOT(q[0], q[i]) }
c = measure_all(q)
// REQUIRE: all c[i] equal in each shot

// TEST 3: Dimension-13 superposition
qudit<13> q[1]; cdit<13> c[1]
QFT(q[0])
c[0] = measure(q[0])
// REQUIRE: uniform distribution over {0,...,12} across shots

// TEST 4: Dimension-13 entanglement
qudit<13> q[2]; cdit<13> c[2]
QFT(q[0]); SUM(q[0], q[1])
c = measure_all(q)
// REQUIRE: c[0] == c[1] in all shots

// TEST 5: Dimension-13 teleportation
qudit<13> q[3]; cdit<13> c[2]
SHIFT(q[0], 7)            // Prepare |7⟩
QFT(q[1]); SUM(q[1], q[2])  // Bell pair on (1,2)
// ... teleport protocol ...
// REQUIRE: measurement of q[2] yields 7

// TEST 6: No-clone rejection
qubit q[1]
// qubit r = q   // MUST be rejected at compile time

// TEST 7: Post-measurement rejection
qubit q[1]; cbit c[1]
c[0] = measure(q[0])
// H(q[0])       // MUST be rejected: q[0] consumed
```

## 10.3 Version Compatibility

- Programs written for QBL 0.x MAY not be compatible with 1.0
- Programs written for QBL 1.x MUST be compatible with all 1.y (y ≥ x)
- Implementations MUST report their conformance level and version

## 10.4 Extensions

Implementations MAY provide extensions beyond this standard:

- Additional dimensions (composite, non-prime)
- Noise simulation
- Distributed simulation
- Custom backends
- IDE integration

Extensions MUST be prefixed with `#[extension(...)]` and MUST NOT change the behavior of standard-conforming programs.

## 10.5 Intellectual Property

QBL language specification and reference implementation are proprietary.
Patent applications pending for:
- Dimension-agnostic quantum gate algebra framework
- Unified gate + pulse grammar for qudit systems
- Linear type enforcement for quantum resource management
- Autonomous error correction language constructs
- Latency-bounded feedback syntax
