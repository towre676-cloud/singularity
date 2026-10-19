"""Create a reviewed reference for a local small HF snapshot; no network required.

--tiny creates a deterministic random GPT-2 architecture and byte BPE tokenizer,
NOT a pretrained quality benchmark. Omit --tiny to use a downloaded pretrained
snapshot, e.g. sshleifer/tiny-gpt2 at a pinned revision.
"""
import argparse
from pathlib import Path
import time

from singularity.model_audit import build_package, save_package, settings_from_contract
from singularity.model_audit.__main__ import _local_hf_provenance
from singularity.model_audit.adapters import HuggingFaceCausalAdapter
from singularity.model_audit.ci import write_json


def create(snapshot, output, tiny=False):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    torch.set_num_threads(1)
    if tiny:
        from tokenizers import Tokenizer, models, pre_tokenizers, decoders, trainers
        from transformers import GPT2Config, GPT2LMHeadModel, PreTrainedTokenizerFast
        core = Tokenizer(models.BPE())
        core.pre_tokenizer = pre_tokenizers.ByteLevel(add_prefix_space=False)
        core.decoder = decoders.ByteLevel()
        core.train_from_iterator(["the cat sat on the mat. café ﬁne\n" * 20],
            trainers.BpeTrainer(vocab_size=280, special_tokens=["<eos>"],
                                initial_alphabet=pre_tokenizers.ByteLevel.alphabet()))
        tokenizer = PreTrainedTokenizerFast(tokenizer_object=core, eos_token="<eos>", pad_token="<eos>")
        torch.manual_seed(19)
        model = GPT2LMHeadModel(GPT2Config(vocab_size=len(tokenizer), n_positions=64,
            n_embd=16, n_layer=1, n_head=2, bos_token_id=0, eos_token_id=0)).eval()
        model.save_pretrained(snapshot)
        tokenizer.save_pretrained(snapshot)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    model = AutoModelForCausalLM.from_pretrained(snapshot, local_files_only=True, trust_remote_code=False,
                                                torch_dtype=torch.float32, attn_implementation="eager")
    tokenizer = AutoTokenizer.from_pretrained(snapshot, local_files_only=True, trust_remote_code=False)
    provenance = _local_hf_provenance(snapshot, {"snapshot_manifest_sha256": ""})
    adapter = HuggingFaceCausalAdapter(model, tokenizer, max_context=64, batch_size=2, provenance=provenance)
    probes = [{"id": "short", "text": "the cat", "pad_to": 24},
              {"id": "unicode", "text": "café ﬁne", "pad_to": 24},
              {"id": "long", "text": "the cat sat on the mat. " * 3}]
    for p in probes:
        p["cost"] = len(adapter.encode(p["text"])[-64:])
    reference = adapter.observe(probes)
    clean = HuggingFaceCausalAdapter(model, tokenizer, max_context=64, batch_size=1, provenance=provenance).observe(probes)
    fault = HuggingFaceCausalAdapter(model, tokenizer, max_context=64, temperature=1.3, provenance=provenance)
    package = build_package(probes, reference, [clean], {"temperature_1.3": fault.observe(probes)},
        contract=adapter.contract(), requirement=2,
        metadata={"purpose": "CI developer example", "tiny_random_model": tiny,
                  "untested": "all faults except the declared temperature change", "cost_unit": "unpadded input tokens"})
    save_package(package, output / "reference.json")
    execution = {**settings_from_contract(package["contract"]), "dtype": "torch.float32",
                 "device": "cpu", "attention_backend": "eager", "batch_size": 2}
    write_json(output / "execution.json", execution)
    (output / "reference.sha256").write_text(package["package_sha256"] + "\n")
    write_json(output / "creation-cost.json", {"seconds_including_load": time.perf_counter()-started,
                "selected_tokens": sum(p["cost"] for p in package["probes"]), "selection": package["selection"]})
    return package


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--tiny", action="store_true")
    args = parser.parse_args()
    print(create(args.model, args.output, args.tiny)["package_sha256"])
