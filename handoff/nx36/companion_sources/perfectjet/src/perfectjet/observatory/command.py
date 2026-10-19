"""JSON batch interface to the same exact computations as the workbench."""
import argparse
import json
from pathlib import Path

from .workbench import evaluate, json_value


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request", type=Path, help="JSON request with operation and model")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        out = evaluate(json.loads(args.request.read_text(encoding="utf-8")))
    except (ValueError, KeyError, TypeError, IndexError) as error:
        parser.error(str(error))
    content = json.dumps(out, indent=2, default=json_value) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(content, encoding="utf-8")
    else:
        print(content, end="")


if __name__ == "__main__":
    main()
