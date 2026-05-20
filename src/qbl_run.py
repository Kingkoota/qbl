#!/usr/bin/env python3
"""
QBL Runner — Fully automated execution pipeline.

Usage:
    python qbl_run.py <file.qbl>                  # Run with defaults
    python qbl_run.py <file.qbl> --shots 1000     # Custom shot count
    python qbl_run.py <file.qbl> --compile        # Output OpenQASM only
    python qbl_run.py <file.qbl> --watch          # Auto-rerun on file change
    python qbl_run.py <file.qbl> --all            # Simulate + compile + stats
"""

import sys
import os
import time
import json
import argparse
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).parent))

from qbl import parse, simulate, compile_to_qasm
from qbl.simulator import Simulator


def run_simulation(source: str, shots: int = 100, seed: int = None, verbose: bool = True) -> dict:
    """Run full simulation and return structured results."""
    program = parse(source)
    sim = Simulator(seed=seed)
    results = sim.run(program, shots=shots)
    
    # Aggregate measurement outcomes
    outcome_counts = Counter()
    for r in results:
        for reg_name, bits in r.classical_bits.items():
            key = f"{reg_name}={''.join(str(b) for b in bits)}"
            outcome_counts[key] += 1
    
    # Compute probabilities
    probabilities = {k: v / shots for k, v in outcome_counts.items()}
    
    # Statevector from last shot (pre-measurement)
    # Run once without measurement to get clean statevector
    sv_results = sim.run(program, shots=1)
    
    output = {
        "shots": shots,
        "outcomes": dict(outcome_counts),
        "probabilities": probabilities,
        "num_qubits": results[0].num_qubits,
        "measurement_log_sample": results[0].measurement_log,
    }
    
    if verbose:
        print(f"\n╔══════════════════════════════════════════════╗")
        print(f"║        QBL AUTOMATED EXECUTION REPORT        ║")
        print(f"╠══════════════════════════════════════════════╣")
        print(f"║  Qubits: {output['num_qubits']:<5}  Shots: {shots:<10}         ║")
        print(f"╠══════════════════════════════════════════════╣")
        print(f"║  MEASUREMENT OUTCOMES:                        ║")
        
        for outcome, count in sorted(outcome_counts.items(), key=lambda x: -x[1]):
            prob = count / shots
            bar = "█" * int(prob * 20)
            print(f"║   {outcome:<12} : {count:>5} ({prob:>6.1%}) {bar:<20} ║")
        
        print(f"╠══════════════════════════════════════════════╣")
        
        # Entropy calculation
        import math
        entropy = -sum(p * math.log2(p) for p in probabilities.values() if p > 0)
        print(f"║  Shannon Entropy: {entropy:.4f} bits                 ║")
        print(f"╚══════════════════════════════════════════════╝")
    
    return output


def run_compile(source: str, output_path: str = None, verbose: bool = True) -> str:
    """Compile QBL to OpenQASM 3.0."""
    qasm = compile_to_qasm(source)
    
    if output_path:
        Path(output_path).write_text(qasm)
        if verbose:
            print(f"[✓] Compiled to: {output_path}")
    
    if verbose:
        print(f"\n┌─── OpenQASM 3.0 Output ───────────────────────┐")
        for line in qasm.split('\n'):
            print(f"│ {line:<47}│")
        print(f"└────────────────────────────────────────────────┘")
    
    return qasm


def watch_and_run(filepath: str, shots: int = 100):
    """Watch a .qbl file and auto-rerun on changes."""
    path = Path(filepath)
    print(f"[⟳] Watching {path.name} for changes... (Ctrl+C to stop)")
    
    last_mtime = 0
    run_count = 0
    
    while True:
        try:
            mtime = path.stat().st_mtime
            if mtime > last_mtime:
                last_mtime = mtime
                run_count += 1
                
                print(f"\n{'─'*50}")
                print(f"[Run #{run_count}] Detected change at {time.strftime('%H:%M:%S')}")
                print(f"{'─'*50}")
                
                source = path.read_text()
                
                try:
                    run_simulation(source, shots=shots)
                    run_compile(source, verbose=True)
                    print(f"\n[✓] Execution successful")
                except Exception as e:
                    print(f"\n[✗] Error: {e}")
            
            time.sleep(0.5)
        
        except KeyboardInterrupt:
            print(f"\n[■] Stopped after {run_count} runs.")
            break


def run_full_pipeline(source: str, filepath: str = "stdin", shots: int = 100, 
                      seed: int = None, output_dir: str = None):
    """Full automated pipeline: parse → validate → simulate → compile → report."""
    
    print(f"╔══════════════════════════════════════════════╗")
    print(f"║       QBL FULL AUTOMATED PIPELINE            ║")
    print(f"╠══════════════════════════════════════════════╣")
    print(f"║  Source: {filepath:<36} ║")
    print(f"║  Time:   {time.strftime('%Y-%m-%d %H:%M:%S'):<36} ║")
    print(f"╚══════════════════════════════════════════════╝")
    
    # Step 1: Parse
    print(f"\n[1/4] Parsing...")
    try:
        program = parse(source)
        n_decl = len(program.declarations)
        n_stmt = len(program.statements)
        n_func = len(program.functions)
        print(f"      ✓ {n_decl} declarations, {n_stmt} statements, {n_func} functions")
    except Exception as e:
        print(f"      ✗ Parse error: {e}")
        return None
    
    # Step 2: Validate
    print(f"\n[2/4] Validating...")
    from qbl.parser import QubitDecl, CbitDecl
    total_qubits = sum(d.size for d in program.declarations if isinstance(d, QubitDecl))
    total_cbits = sum(d.size for d in program.declarations if isinstance(d, CbitDecl))
    print(f"      ✓ {total_qubits} qubits, {total_cbits} classical bits")
    print(f"      ✓ State space: 2^{total_qubits} = {2**total_qubits} amplitudes")
    
    # Step 3: Simulate
    print(f"\n[3/4] Simulating ({shots} shots)...")
    result = run_simulation(source, shots=shots, seed=seed, verbose=True)
    
    # Step 4: Compile
    print(f"\n[4/4] Compiling to OpenQASM 3.0...")
    qasm = run_compile(source, verbose=True)
    
    # Save outputs if dir specified
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        
        # Save QASM
        qasm_path = os.path.join(output_dir, Path(filepath).stem + ".qasm")
        Path(qasm_path).write_text(qasm)
        
        # Save results JSON
        json_path = os.path.join(output_dir, Path(filepath).stem + "_results.json")
        Path(json_path).write_text(json.dumps(result, indent=2, default=str))
        
        print(f"\n[✓] Outputs saved to: {output_dir}/")
        print(f"    • {Path(qasm_path).name}")
        print(f"    • {Path(json_path).name}")
    
    print(f"\n{'═'*50}")
    print(f"  PIPELINE COMPLETE — All stages passed")
    print(f"{'═'*50}")
    
    return result


def main():
    parser = argparse.ArgumentParser(
        description="QBL — Fully Automated Qubit Language Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python qbl_run.py bell.qbl                    # Simulate with 100 shots
  python qbl_run.py bell.qbl --shots 1000       # 1000 shots
  python qbl_run.py bell.qbl --compile          # Compile to OpenQASM only
  python qbl_run.py bell.qbl --all              # Full pipeline
  python qbl_run.py bell.qbl --watch            # Auto-rerun on file change
  python qbl_run.py bell.qbl --all --output ./results
        """
    )
    
    parser.add_argument("file", help="Path to .qbl source file")
    parser.add_argument("--shots", type=int, default=100, help="Number of simulation shots (default: 100)")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility")
    parser.add_argument("--compile", action="store_true", help="Compile to OpenQASM 3.0")
    parser.add_argument("--watch", action="store_true", help="Watch file and auto-rerun on changes")
    parser.add_argument("--all", action="store_true", help="Run full pipeline (parse + validate + simulate + compile)")
    parser.add_argument("--output", type=str, default=None, help="Output directory for results")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    
    args = parser.parse_args()
    
    filepath = Path(args.file)
    if not filepath.exists():
        print(f"Error: File not found: {filepath}")
        sys.exit(1)
    
    source = filepath.read_text()
    
    if args.watch:
        watch_and_run(str(filepath), shots=args.shots)
    elif args.all:
        run_full_pipeline(source, str(filepath), shots=args.shots, 
                         seed=args.seed, output_dir=args.output)
    elif args.compile:
        qasm = run_compile(source)
        if args.json:
            print(json.dumps({"qasm": qasm}))
    else:
        result = run_simulation(source, shots=args.shots, seed=args.seed)
        if args.json:
            print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
