# QBL Language Standard

## Document Status

| Field | Value |
|-------|-------|
| Title | QBL — Quantum Base Language Standard |
| Version | 0.3.0 |
| Status | Draft |
| Authors | Tane Norton |
| Date | 2026-05-20 |
| License | Proprietary (patent pending) |

## Abstract

QBL (Quantum Base Language) is a domain-specific programming language for quantum computing that operates natively across multiple Hilbert space dimensions. Unlike existing quantum languages limited to qubits (d=2), QBL treats dimension as a first-class parameter, with d=13 as the primary non-binary standard dimension.

This document defines the complete language specification: syntax, semantics, type system, gate algebra, measurement model, and compilation targets.

## Table of Contents

1. [Introduction](chapters/01-introduction.md)
2. [Lexical Structure](chapters/02-lexical.md)
3. [Type System](chapters/03-types.md)
4. [Gate Algebra](chapters/04-gates.md)
5. [Measurement & Control Flow](chapters/05-measurement.md)
6. [Protocols](chapters/06-protocols.md)
7. [Error Correction](chapters/07-error-correction.md)
8. [Compilation Model](chapters/08-compilation.md)
9. [Standard Library](chapters/09-stdlib.md)
10. [Conformance](chapters/10-conformance.md)
11. [Agentic Constructs](chapters/11-agentic.md)
12. [Quantum Commerce Operations](chapters/12-commerce.md)

## Scope

This standard specifies:

- The complete syntax and grammar of QBL source programs
- The type system including linear types for quantum resources
- The algebraic structure of supported gate sets for dimensions d=2 through d=13
- The measurement model with projective and generalized (POVM) measurements
- The compilation model from QBL source to executable quantum circuits
- The standard library of built-in gates, protocols, and error correction codes
- Conformance requirements for QBL implementations

## Normative References

- OpenQASM 3.0 Specification (Cross et al., 2022)
- Weyl-Heisenberg Group Theory for Prime Dimensions (Vourdas, 2004)
- Quantum Error Correction for Qudits (Gottesman, 1999)
- Discrete Wigner Functions (Gross, 2006)

## Terms and Definitions

| Term | Definition |
|------|-----------|
| **qubit** | A quantum system with d=2 (two-level) |
| **qudit** | A quantum system with d>2 (multi-level) |
| **dimension** | The number of orthogonal basis states per quantum register element |
| **shift operator** | Generalized Pauli-X: X\|j⟩ = \|j+1 mod d⟩ |
| **clock operator** | Generalized Pauli-Z: Z\|j⟩ = ω^j\|j⟩ |
| **Weyl operator** | Displacement D(a,b) = τ^(ab) X^a Z^b |
| **QFT** | Quantum Fourier Transform (generalized Hadamard for d>2) |
| **Clifford group** | Gates that map Pauli group to itself under conjugation |
| **agent** | An autonomous entity with quantum memory, goals, and tools |
| **swarm** | Coordinated group of agents with entangled communication |
| **consensus** | Multi-agent agreement protocol with quantum speedup |
| **tool** | Capability exposed to agents (quantum or classical) |
| **behavior** | Reactive rules defining agent responses to events |
