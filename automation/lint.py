"""Parse delivered VBA/M source and enforce explicit variable declarations.

This catches syntax and wiring errors. It is not Microsoft's VBA compiler.
"""
from pathlib import Path
import sys

from pyopenvba.interpreter import parse_module
from pyopenvba.mlang import parse

ROOT = Path(__file__).resolve().parent


def lint():
    for path in sorted((ROOT / "vba").glob("*.bas")):
        code = path.read_text()
        if not code.startswith("Option Explicit\n"):
            raise ValueError(f"{path.name}: declare variables with Option Explicit")
        parse_module(code, name=path.stem, kind="form" if path.stem == "ReviewForm" else "standard")
        if "On Error Resume Next" in code:
            raise ValueError(f"{path.name}: do not hide failed updates")
    parse((ROOT / "power-query/LegacyImport.pq").read_text())
    print("VBA parser: 2 modules; M parser: 1 query; source rules passed")


if __name__ == "__main__":
    try:
        lint()
    except Exception as error:
        print(f"Automation lint failed: {error}", file=sys.stderr)
        raise SystemExit(1) from error
