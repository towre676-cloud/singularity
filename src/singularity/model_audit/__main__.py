"""Command line: verify a package, or check a deployed model against it.

  python -m singularity.model_audit verify PACKAGE
  python -m singularity.model_audit check PACKAGE --byte-checkpoint PATH
  python -m singularity.model_audit check PACKAGE --hf-model DIR [--hf-tokenizer DIR]

``check`` rebuilds the package's declared pipeline around the supplied model,
so contract mismatches report identity differences (weights, tokenizer,
configuration). Exit status: 0 unchanged/verified, 1 changed/failed.
"""
import argparse
import json
import sys
import time

from . import check_package, load_package, settings_from_contract, verify_package


def main(argv=None):
    started = time.perf_counter()
    parser = argparse.ArgumentParser(prog="python -m singularity.model_audit", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("action", choices=("verify", "check"))
    parser.add_argument("package")
    parser.add_argument("--byte-checkpoint")
    parser.add_argument("--hf-model")
    parser.add_argument("--hf-tokenizer")
    parser.add_argument("--missing", nargs="*", default=(), help="probe ids whose results are unavailable")
    args = parser.parse_args(argv)
    package = load_package(args.package)
    if args.action == "verify":
        report = verify_package(package)
        print(json.dumps(report, indent=1))
        return 0 if report["verified"] else 1
    settings = settings_from_contract(package["contract"])
    if bool(args.byte_checkpoint) == bool(args.hf_model):
        parser.error("check needs exactly one of --byte-checkpoint or --hf-model")
    from .adapters import ByteTransformerAdapter, HuggingFaceCausalAdapter
    if args.byte_checkpoint:
        from ..training.runner import load_checkpoint
        model = load_checkpoint(args.byte_checkpoint)[0]
        newline = bytes.fromhex(package["contract"].get("newline", "0a")).decode()
        adapter = ByteTransformerAdapter(model, newline=newline, **settings)
    else:
        from transformers import AutoModelForCausalLM, AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained(args.hf_tokenizer or args.hf_model)
        model = AutoModelForCausalLM.from_pretrained(args.hf_model)
        adapter = HuggingFaceCausalAdapter(model, tokenizer, **settings)
    loaded = time.perf_counter()
    report = check_package(package, adapter.observe, adapter.contract(), missing=args.missing)
    report["seconds"] = {"startup_and_load": loaded - started, "check": time.perf_counter() - loaded}
    print(json.dumps({k: v for k, v in report.items() if k != "probes"}, indent=1))
    return 0 if report["verdict"] == "unchanged" else 1


if __name__ == "__main__":
    sys.exit(main())
