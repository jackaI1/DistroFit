"""Write a synthetic measurement CSV too large to hold comfortably in memory at once.

The rows are written in chunks, so the generator itself never holds more than one chunk.
Use it to try ``compare_distributions.py fit --sample-size`` on a big file.
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def write_large_csv(path, rows, *, seed=11, chunk=250_000):
    if rows < 1:
        raise ValueError("Rows must be a positive whole number.")
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)
    with target.open("w", encoding="utf-8", newline="") as out:
        out.write("Cycle,Gamma_Measurement\n")
        for start in range(0, rows, chunk):
            count = min(chunk, rows - start)
            frame = pd.DataFrame({"Cycle": np.arange(start, start + count),
                                  "Gamma_Measurement": np.round(rng.gamma(2, 2, count), 6)})
            frame.to_csv(out, header=False, index=False)
    return target


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", type=int, default=2_000_000)
    parser.add_argument("--out", type=Path, required=True, help="CSV file to create")
    args = parser.parse_args(argv)
    write_large_csv(args.out, args.rows)
    print(f"Wrote {args.rows} rows to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
