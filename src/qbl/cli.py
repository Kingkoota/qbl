"""
QBL CLI — Entry point for `qbl` command.

Usage:
    qbl run <file.qbl> [--shots N] [--seed N] [--all] [--watch] [--json] [--output DIR]
    qbl compile <file.qbl> [--output FILE]
    qbl check <file.qbl>
    qbl version
"""

import sys
import os
import json
import time
import argparse
import math
from pathlib import Path
from collections import Counter

from qbl import parse, simulate, compile_to_qasm
from qbl.simulator import Simulator


def run_simulation(source, shots=100, seed=None, verbose=True):
    program = parse(source)
    sim = Simulator(seed=seed)
    results = sim.run(program, shots=shots)
    
    outcome_counts = Counter()
    for r in results:
        for reg_name, bits in r.classical_bits.items():
            key = f"{reg_name}={''.join(str(b) for b in bits)}"
            outcome_counts[key] += 1
    
    probabilities = {k: v / shots for k, v in outcome_counts.items()}
    
    output = {
        "shots": shots,
        "outcomes": dict(outcome_counts),
        "probabilities": probabilities,
        "num_qubits": results[0].num_qubits,
    }
    
    if verbose:
        print(f"\n╔══════════════════════════════════════════════╗")
        print(f"║        QBL EXECUTION REPORT                  ║")
        print(f"╠══════════════════════════════════════════════╣")
        print(f"║  Qubits: {output['num_qubits']:<5}  Shots: {shots:<10}         ║")
        print(f"╠══════════════════════════════════════════════╣")
        for outcome, count in sorted(outcome_counts.items(), key=lambda x: -x[1]):
            prob = count / shots
            bar = "█" * int(prob * 20)
            print(f"║   {outcome:<12} : {count:>5} ({prob:>6.1%}) {bar:<20} ║")
        entropy = -sum(p * math.log2(p) for p in probabilities.values() if p > 0)
        print(f"╠══════════════════════════════════════════════╣")
        print(f"║  Shannon Entropy: {entropy:.4f} bits                 ║")
        print(f"╚══════════════════════════════════════════════╝")
    
    return output


def run_compile(source, output_path=None, verbose=True):
    qasm = compile_to_qasm(source)
    if output_path:
        Path(output_path).write_text(qasm)
        if verbose:
            print(f"[✓] Compiled to: {output_path}")
    if verbose:
        print(f"\n┌─── OpenQASM 3.0 ───────────────────────────────┐")
        for line in qasm.split('\n'):
            print(f"│ {line:<48}│")
        print(f"└─────────────────────────────────────────────────┘")
    return qasm


def run_full_pipeline(source, filepath="stdin", shots=100, seed=None, output_dir=None):
    print(f"╔══════════════════════════════════════════════╗")
    print(f"║       QBL FULL PIPELINE                      ║")
    print(f"╠══════════════════════════════════════════════╣")
    print(f"║  Source: {filepath:<36} ║")
    print(f"╚══════════════════════════════════════════════╝")
    
    print(f"\n[1/3] Parsing...")
    program = parse(source)
    print(f"      ✓ {len(program.declarations)} declarations, {len(program.statements)} statements")
    
    print(f"\n[2/3] Simulating ({shots} shots)...")
    result = run_simulation(source, shots=shots, seed=seed)
    
    print(f"\n[3/3] Compiling to OpenQASM 3.0...")
    qasm = run_compile(source)
    
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        qasm_path = os.path.join(output_dir, Path(filepath).stem + ".qasm")
        Path(qasm_path).write_text(qasm)
        json_path = os.path.join(output_dir, Path(filepath).stem + "_results.json")
        Path(json_path).write_text(json.dumps(result, indent=2, default=str))
        print(f"\n[✓] Saved: {qasm_path}, {json_path}")
    
    print(f"\n{'═'*50}")
    print(f"  PIPELINE COMPLETE")
    print(f"{'═'*50}")
    return result


def cli_main():
    parser = argparse.ArgumentParser(description="QBL — Qubit Language Runner")
    parser.add_argument("file", help="Path to .qbl source file")
    parser.add_argument("--shots", type=int, default=100)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--compile", action="store_true")
    parser.add_argument("--watch", action="store_true")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--output", type=str, default=None)
    parser.add_argument("--json", action="store_true")
    
    args = parser.parse_args()
    filepath = Path(args.file)
    if not filepath.exists():
        print(f"Error: {filepath} not found")
        sys.exit(1)
    
    source = filepath.read_text()
    
    if args.all:
        run_full_pipeline(source, str(filepath), args.shots, args.seed, args.output)
    elif args.compile:
        run_compile(source)
    else:
        result = run_simulation(source, args.shots, args.seed)
        if args.json:
            print(json.dumps(result, indent=2, default=str))


def main():
    if len(sys.argv) < 2:
        print_help()
        sys.exit(0)
    
    cmd = sys.argv[1]
    
    if cmd == "version":
        print("QBL v0.2.0 — The Next Quantum Programming Standard")
    elif cmd in ("run", "compile", "check"):
        sys.argv = [sys.argv[0]] + sys.argv[2:]
        if cmd == "compile":
            sys.argv.append("--compile")
        cli_main()
    elif cmd == "help" or cmd == "--help":
        print_help()
    else:
        # Treat first arg as file (backward compat)
        cli_main()


def print_help():
    print("""
QBL v0.2.0 — Qubit Language

Commands:
  qbl run <file.qbl> --all --shots 1000   Full pipeline
  qbl compile <file.qbl>                  Compile to OpenQASM
  qbl check <file.qbl>                    Parse & validate
  qbl version                             Version info
""")


if __name__ == "__main__":
    main()
