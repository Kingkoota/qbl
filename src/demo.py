#!/usr/bin/env python3
"""
QBL Demo — Demonstrates the Qubit Language in action.

Runs three example programs:
1. Bell State (entanglement)
2. Quantum Teleportation
3. GHZ State with conditional correction

Shows both simulation results and OpenQASM 3.0 compilation output.
"""

import sys
sys.path.insert(0, '/home/user/surething/cells/9aac62c1-42fd-4cf7-b972-cc3600decbc8/workspace/src')

import numpy as np
from qbl import parse, simulate, compile_to_qasm
from qbl.simulator import Simulator


def print_section(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


# ============================================================
# EXAMPLE 1: Bell State
# ============================================================

bell_state_qbl = """
// Bell State — Maximum entanglement between two qubits
qubit q[2]
cbit c[2]

gate {
    H(q[0])
    CNOT(q[0], q[1])
}

assert entangled(q[0], q[1])

c[0] = measure(q[0])
c[1] = measure(q[1])
"""

print_section("EXAMPLE 1: Bell State (Entanglement)")
print("QBL Source:")
print(bell_state_qbl)

# Simulate
print("--- Simulation (10 shots) ---")
program = parse(bell_state_qbl)
sim = Simulator(seed=42)
results = sim.run(program, shots=10)

counts = {"00": 0, "01": 0, "10": 0, "11": 0}
for r in results:
    bits = "".join(str(b) for b in r.classical_bits['c'])
    counts[bits] += 1

print(f"Measurement outcomes: {counts}")
print(f"(Bell state always gives correlated results: 00 or 11)")

# Compile
print("\n--- Compiled to OpenQASM 3.0 ---")
qasm = compile_to_qasm(bell_state_qbl)
print(qasm)


# ============================================================
# EXAMPLE 2: Quantum Teleportation
# ============================================================

teleport_qbl = """
// Quantum Teleportation Protocol
// Teleports state of q[0] to q[2] using entangled pair q[1],q[2]
qubit q[3]
cbit c[2]

// Prepare entangled pair (q[1], q[2])
gate {
    H(q[1])
    CNOT(q[1], q[2])
}

// Prepare q[0] in some state (RX rotation)
RX(q[0], 1.2)

// Bell measurement on q[0], q[1]
gate {
    CNOT(q[0], q[1])
    H(q[0])
}

c[0] = measure(q[0])
c[1] = measure(q[1])

// Conditional corrections on q[2]
if c[1] == 1 {
    X(q[2])
}
if c[0] == 1 {
    Z(q[2])
}
"""

print_section("EXAMPLE 2: Quantum Teleportation")
print("QBL Source:")
print(teleport_qbl)

print("--- Compiled to OpenQASM 3.0 ---")
qasm = compile_to_qasm(teleport_qbl)
print(qasm)

# Run simulation
print("\n--- Simulation (1 shot) ---")
results = simulate(teleport_qbl, shots=1, seed=7)
r = results[0]
print(f"Classical bits after teleportation: c = {r.classical_bits['c']}")
print(f"Measurement log: {r.measurement_log}")


# ============================================================
# EXAMPLE 3: GHZ State (3-qubit entanglement)
# ============================================================

ghz_qbl = """
// GHZ State — 3-qubit maximally entangled state
// |GHZ⟩ = (|000⟩ + |111⟩) / √2
qubit q[3]
cbit c[3]

gate {
    H(q[0])
    CNOT(q[0], q[1])
    CNOT(q[1], q[2])
}

c[0] = measure(q[0])
c[1] = measure(q[1])
c[2] = measure(q[2])
"""

print_section("EXAMPLE 3: GHZ State (3-Qubit Entanglement)")
print("QBL Source:")
print(ghz_qbl)

print("--- Simulation (20 shots) ---")
results = simulate(ghz_qbl, shots=20, seed=123)

counts = {}
for r in results:
    bits = "".join(str(b) for b in r.classical_bits['c'])
    counts[bits] = counts.get(bits, 0) + 1

print(f"Measurement outcomes: {counts}")
print(f"(GHZ state always gives 000 or 111 — all qubits correlated)")

print("\n--- Compiled to OpenQASM 3.0 ---")
qasm = compile_to_qasm(ghz_qbl)
print(qasm)


# ============================================================
# EXAMPLE 4: Statevector inspection (no measurement)
# ============================================================

superposition_qbl = """
// Equal superposition of 3 qubits
qubit q[3]
cbit c[3]

gate {
    H(q[0])
    H(q[1])
    H(q[2])
}
"""

print_section("EXAMPLE 4: Statevector Inspection")
print("QBL Source:")
print(superposition_qbl)

results = simulate(superposition_qbl, shots=1)
sv = results[0].final_statevector
print("Final statevector (amplitudes):")
for i, amp in enumerate(sv):
    if abs(amp) > 1e-10:
        bits = format(i, f'0{results[0].num_qubits}b')
        print(f"  |{bits}⟩ : {amp:.4f} (prob={abs(amp)**2:.4f})")

print("\n" + "="*60)
print("  QBL v0.1.0 — All examples completed successfully")
print("="*60)
