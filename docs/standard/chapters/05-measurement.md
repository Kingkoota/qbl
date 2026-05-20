# Chapter 5: Measurement & Control Flow

## 5.1 Projective Measurement

### 5.1.1 Standard Basis Measurement

```qbl
cdit<13> c[1]
qudit<13> q[1]

c[0] = measure(q[0])   // Outcome ∈ {0, 1, ..., 12}
```

**Semantics:**
1. Compute probabilities: p(j) = |⟨j|ψ⟩|² for j ∈ {0,...,d-1}
2. Sample outcome m according to distribution p
3. Collapse state: |ψ⟩ → |m⟩ (normalized)
4. Store result in classical register
5. **Consume** the quantum variable (linear type enforcement)

### 5.1.2 Partial Measurement

```qbl
qudit<13> q[3]
cdit<13> c[1]

c[0] = measure(q[1])   // Measure only q[1], q[0] and q[2] persist
// q[1] is consumed; q[0], q[2] still live (possibly collapsed)
```

### 5.1.3 Measure-All

```qbl
cdit<13> c[3]
c = measure_all(q)      // Measure all qudits in register
```

## 5.2 Generalized Measurements (POVM)

```qbl
// Define POVM elements (must sum to identity)
povm detection = {
    E0: 0.9 * |0><0| + 0.05 * |1><1|,   // "detected 0"
    E1: 0.05 * |0><0| + 0.9 * |1><1|,   // "detected 1"
    E_fail: 0.05 * I                      // "inconclusive"
}

outcome = povm_measure(q[0], detection)
```

## 5.3 Real-Time Control Flow

### 5.3.1 Conditional Execution

```qbl
c[0] = measure(q[0])

if c[0] == 7 {
    SHIFT(q[1], 3)       // Apply correction
} else if c[0] == 0 {
    // No correction needed
} else {
    CLOCK(q[1], c[0])    // General correction
}
```

### 5.3.2 Classical-Quantum Feedback

```qbl
// Latency-bounded feedback (hardware constraint)
feedback(latency: 500ns) {
    c[0] = measure(q[0])
    if c[0] != 0 {
        SHIFT(q[1], 13 - c[0])  // Undo shift
    }
}
```

### 5.3.3 While Loops

```qbl
// Repeat-until-success
cdit<13> result[1]
result[0] = 99  // sentinel

while result[0] != 0 {
    // Prepare fresh qudit
    qudit<13> trial[1]
    QFT(trial[0])
    CLOCK(trial[0], 5)
    result[0] = measure(trial[0])
}
```

### 5.3.4 Match Statement

```qbl
c[0] = measure(q[0])

match c[0] {
    0 => { /* identity */ }
    1..6 => { SHIFT(q[1], c[0]) }
    7..12 => { CLOCK(q[1], c[0] - 6) }
}
```

## 5.4 Barriers

```qbl
gate {
    QFT(q[0])
    QFT(q[1])
}

barrier(q)              // Prevent gate reordering across this point

gate {
    SUM(q[0], q[1])
}
```

## 5.5 Deferred Measurement Principle

QBL supports deferred measurement: measurements can be conceptually moved to the end of the circuit without changing outcomes, provided no classical feedforward is used.

```qbl
// These are equivalent when no feedback:
// Version A: immediate
c[0] = measure(q[0])
// ... no use of c[0] in gates ...
c[1] = measure(q[1])

// Version B: deferred
// Compiler may reorder measurements for optimization
#[defer_measurement]
gate {
    // all gates here
}
c = measure_all(q)
```

## 5.6 Non-Destructive Measurement

```qbl
// Measure in Fourier basis without destroying state
// (Uses ancilla + CNOT-analog)
qudit<13> ancilla[1]
SUM(q[0], ancilla[0])      // Copy phase info to ancilla
c[0] = measure(ancilla[0]) // Measure ancilla only
// q[0] still live (projected but not consumed)
```
