import argparse
import json
from .data import download
from .report import build_report


def main():
    parser = argparse.ArgumentParser(
        description="Reproduce the public battery fleet and thermal study"
    )
    parser.add_argument(
        "--data", default=".runtime/battery-data", help="Verified raw-data cache"
    )
    parser.add_argument("--out", help="New report directory")
    parser.add_argument("--download-only", action="store_true")
    parser.add_argument(
        "--fleet-only", action="store_true", help="Skip optional PyBaMM study"
    )
    args = parser.parse_args()
    if args.download_only:
        download(args.data)
    elif not args.out:
        parser.error("--out is required unless --download-only is used")
    else:
        result = build_report(args.data, args.out, thermal=not args.fleet_only)
        print(json.dumps(result["fleet"]))


if __name__ == "__main__":
    main()
