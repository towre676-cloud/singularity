"""JSON-configured optional PyTorch experiments."""
import argparse
import json

from .runner import run


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    with open(args.config) as file:
        config = json.load(file)
    print(json.dumps(run(config, args.output), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
