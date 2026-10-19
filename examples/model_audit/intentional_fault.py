"""Replace tiny example weights, for the CI rejection demonstration only."""
import argparse
from transformers import AutoModelForCausalLM
import torch

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('model')
args = parser.parse_args()
model = AutoModelForCausalLM.from_pretrained(args.model, local_files_only=True, trust_remote_code=False)
with torch.no_grad():
    model.get_input_embeddings().weight[0].add_(1)
model.save_pretrained(args.model)
