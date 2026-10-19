"""JSON-configured optional PyTorch experiments."""
import argparse
import json


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    try:
        from .runner import run
    except ModuleNotFoundError as exc:
        if exc.name == "torch":
            parser.error(
                "training requires PyTorch; install the optional dependencies "
                'with pip install -e ".[training]"'
            )
        raise
    with open(args.config) as file:
        config = json.load(file)
    print(json.dumps(run(config, args.output), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
