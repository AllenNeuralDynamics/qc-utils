"""Integration script: generate quality_control.json from procedures.json.

Usage:
    .venv/bin/python scripts/run_fiber_implant_qc.py
"""

from pathlib import Path

from qc_utils.spim.fib_utils import fiber_implant_qc

fiber_implant_qc(Path("tests/resources/procedures.json"), Path("."))
