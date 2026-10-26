#!/usr/bin/env python3
"""
Diagnostic script: runs all 17 tests in test_institution_provisioning.py
using python -m pytest and measures execution and process termination.
"""
import subprocess
import sys
import time

def main():
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/test_institution_provisioning.py",
        "-q",
    ]
    print(f"Executing: {' '.join(cmd)}")
    start = time.perf_counter()
    try:
        proc = subprocess.run(cmd, cwd="backend", capture_output=True, text=True, timeout=90)
        elapsed = time.perf_counter() - start
        print(f"Elapsed: {elapsed:.2f}s, ReturnCode: {proc.returncode}")
        print("STDOUT:\n" + proc.stdout)
        print("STDERR:\n" + proc.stderr)
    except subprocess.TimeoutExpired as te:
        elapsed = time.perf_counter() - start
        print(f"TIMEOUT EXPIRED after {elapsed:.2f}s!")
        if te.stdout:
            print("STDOUT:\n" + (te.stdout.decode() if isinstance(te.stdout, bytes) else str(te.stdout)))
        if te.stderr:
            print("STDERR:\n" + (te.stderr.decode() if isinstance(te.stderr, bytes) else str(te.stderr)))

if __name__ == "__main__":
    main()
