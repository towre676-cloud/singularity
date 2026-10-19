"""Command line: verify a package, or check a deployed model against it.

  python -m singularity.model_audit verify PACKAGE
  python -m singularity.model_audit check PACKAGE --byte-checkpoint PATH
  python -m singularity.model_audit check PACKAGE --hf-model DIR [--hf-tokenizer DIR]

``check`` rebuilds the package's declared pipeline around the supplied model,
so contract mismatches report identity differences (weights, tokenizer,
configuration). Exit status: 0 unchanged/verified, 1 changed/failed.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

from . import check_package, load_package, settings_from_contract, verify_package


def _local_hf_provenance(directory, declared):
    """Rebind a declared snapshot digest to the actual supplied local files.

    Repository names and revisions are acquisition metadata; the snapshot
    content digest is independently recomputed, so copying an expected label
    cannot make different local weights pass the identity comparison.
    """
    provenance = json.loads(json.dumps(declared))
    if "snapshot_manifest_sha256" not in provenance:
        return provenance
    suffixes = {".json", ".safetensors", ".bin", ".model", ".txt", ".tiktoken"}
    root = Path(directory)
    paths = sorted(p for p in root.rglob("*")
                   if p.is_file() and ".cache" not in p.parts and p.suffix in suffixes)
    if not paths or not any(p.suffix in {".safetensors", ".bin"} for p in paths):
        raise ValueError("local Hugging Face snapshot has no model weights")
    manifest = {}
    for path in paths:
        content = hashlib.sha256()
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                content.update(block)
        manifest[str(path.relative_to(root))] = {"bytes": path.stat().st_size, "sha256": content.hexdigest()}
    raw = json.dumps(manifest, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    provenance["snapshot_manifest_sha256"] = hashlib.sha256(raw).hexdigest()
    return provenance


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
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        dtypes = {"torch.float32": torch.float32, "torch.float16": torch.float16, "torch.bfloat16": torch.bfloat16}
        dtype_name = package["contract"].get("dtype", "torch.float32")
        if dtype_name not in dtypes:
            parser.error("unsupported package dtype: " + str(dtype_name))
        tokenizer = AutoTokenizer.from_pretrained(args.hf_tokenizer or args.hf_model,
                                                   local_files_only=True, trust_remote_code=False)
        model = AutoModelForCausalLM.from_pretrained(args.hf_model, torch_dtype=dtypes[dtype_name],
                                                     low_cpu_mem_usage=True, local_files_only=True,
                                                     trust_remote_code=False)
        provenance = _local_hf_provenance(args.hf_model, package["contract"].get("checkpoint_provenance", {}))
        adapter = HuggingFaceCausalAdapter(model, tokenizer, provenance=provenance, **settings)
    loaded = time.perf_counter()
    report = check_package(package, adapter.observe, adapter.contract(), missing=args.missing)
    report["seconds"] = {"startup_and_load": loaded - started, "check": time.perf_counter() - loaded}
    print(json.dumps({k: v for k, v in report.items() if k != "probes"}, indent=1))
    return 0 if report["verdict"] == "unchanged" else 1


if __name__ == "__main__":
    sys.exit(main())
