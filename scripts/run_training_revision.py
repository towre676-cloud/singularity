#!/usr/bin/env python3
"""Frozen discovery/confirmation program for the optional real-training lab."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import time

TASKS = {
    "modular_mlp": {"task":"modular_addition","p":31,
        "model":{"name":"mlp","hidden":128},"batch_size":128,
        "discovery_steps":1000,"confirmation_steps":12000,"eval_every":200},
    "modular_transformer":{"task":"modular_addition","p":31,
        "model":{"name":"transformer","d_model":32,"heads":4,"layers":1},
        "batch_size":128,"discovery_steps":600,"confirmation_steps":6000,"eval_every":100},
    "wikitext_byte":{"task":"byte_lm",
        "model":{"name":"transformer","d_model":48,"heads":4,"layers":2},
        "batch_size":16,"discovery_steps":300,"confirmation_steps":1500,"eval_every":100}
}
GRID = [
    {"lr":0.001,"weight_decay":0.1,"betas":[0.9,0.999]},
    {"lr":0.003,"weight_decay":0.3,"betas":[0.9,0.999]},
    {"lr":0.003,"weight_decay":0.1,"betas":[0.9,0.99]},
]
ARMS = ["baseline","cosine","layer_decay","meta"]
SEEDS = [1000,1001,1002]

def write(path, value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+"\n")

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":")).encode()).hexdigest()

def base_config(name, data_dir):
    spec=TASKS[name]
    cfg={k:v for k,v in spec.items() if k not in ("discovery_steps","confirmation_steps")}
    cfg.update({"optimizer":"adamw","eps":1e-8,"threads":1,"grad_clip":1.0,
        "eval_batch_size":128,"max_parameters":1000000,"layer_decay":0.8,
        "telemetry":{"sketch_dimension":16,"sketch_window":32,"sketch_seed":314159,"ffn_rank":False},
        "meta":{"every":100,"batch_size":64 if name!="wikitext_byte" else 16,
            "hyper_lr":0.1,"max_backtracks":6,"min_lr":0.0001,"max_lr":0.01,
            "min_weight_decay":0.0,"max_weight_decay":1.0,"grad_clip":1.0}})
    if spec["task"]=="modular_addition":
        cfg["split"]={"split_seed":1729,"train_orbits_per_label":8,
                      "tune_orbits_per_label":4,"test_orbits_per_label":4}
    else:
        cfg["data"]={f"{split}_path":str((data_dir/f"{split}.txt").resolve()) for split in ("train","tune","test")}
        cfg["data"]["seq_len"]=64
    return cfg

def protocol():
    return {"schema":"singularity.training-revision-protocol/1",
      "authored":"2026-10-19","discovery_seed":9000,"confirmation_seeds":SEEDS,
      "tasks":TASKS,"fixed_discovery_grid":GRID,"confirmation_arms":ARMS,
      "selection":"For each architecture, lowest final TUNE cross-entropy on seed9000 after fixed discovery cap; all candidates use baselineAdamW.",
      "primary_comparison":"meta minus selected fixed AdamW final TEST cross-entropy at equal optimizer updates; account for all extra computation.",
      "secondary_comparisons":"cosine and layer_decay versus selected fixed AdamW; report all arms and all seeds.",
      "grokking_definition":{"memorization":"TRAIN accuracy>=0.99 for3consecutive scheduled evaluations",
          "generalization":"TUNE accuracy>=0.95 for3consecutive scheduled evaluations",
          "scope":"Only modular tasks; uncrossed thresholds right-censored at declared step cap. A delay must separate thresholds to call delayed generalization."},
      "test_policy":"No TEST metrics in discovery or policy feedback. Confirmation TEST is evaluated once at end of each frozen run.",
      "diagnostic_panel":"Choose panel only on finalTUNE prediction blocks of frozen checkpoints; audit on separateTEST blocks without reselection. Exactfinite-table guarantee only.",
      "timing":"One CPUthread perrun. Sharedhost timings including monitoring, meta calls, evaluations and saving; not dedicated hardware speed benchmarks.",
      "scope":"Small realPyTorch models. ByteLM uses declared officialWikiText2 prefixes and byte-level loss, not standard word perplexity or pretrainedGPT2."}

def execute(cfg, out):
    from singularity.training.runner import run
    if (out/"summary.json").exists():
        raise FileExistsError(f"Refusing to overwrite completed run: {out}")
    print(json.dumps({"event":"run_started","output":str(out),"task":cfg["task"],"variant":cfg["variant"],"seed":cfg["seed"],"steps":cfg["steps"]}),flush=True)
    result=run(cfg,out)
    print(json.dumps({"event":"run_finished","output":str(out),"tune_loss":result["final_tune"]["loss"],"test":result["final_test"],"seconds":result["wall_seconds_including_monitoring"]}),flush=True)
    return result

def discovery(output, data_dir):
    frozen=protocol()
    path=output/"protocol.json"
    if path.exists():
        if json.loads(path.read_text()) != frozen:
            raise ValueError("Existing protocol differs")
    else:write(path,frozen)
    selections={}
    started=time.perf_counter()
    for name in TASKS:
        rows=[]
        for i,hp in enumerate(GRID):
            cfg={**base_config(name,data_dir),**hp,"variant":"baseline",
                 "seed":9000,"steps":TASKS[name]["discovery_steps"],"evaluate_test":False,
                 "protocol_sha256":digest(frozen),"phase":"discovery"}
            out=output/"discovery"/name/f"candidate_{i}"
            summary=execute(cfg,out)
            rows.append({"candidate":i,"hyperparameters":hp,"final_tune_loss":summary["final_tune"]["loss"],
                "wall_seconds":summary["wall_seconds_including_monitoring"],"plan_sha256":summary["plan_sha256"]})
        winner=min(rows,key=lambda row:(row["final_tune_loss"],row["candidate"]))
        selections[name]={"selected":winner,"all_candidates":rows}
    result={"protocol_sha256":digest(frozen),"selection_rule":frozen["selection"],
            "selections":selections,"discovery_total_seconds":time.perf_counter()-started,
            "test_evaluations":0}
    write(output/"selection.json",result)
    print(json.dumps({"event":"discovery_complete","selection":result}),flush=True)

def confirmation(output,data_dir):
    selection=json.loads((output/"selection.json").read_text())
    frozen=json.loads((output/"protocol.json").read_text())
    if digest(frozen)!=selection["protocol_sha256"] or frozen!=protocol():
        raise ValueError("Protocol no longer matches discovery")
    plans=[]
    for name in TASKS:
        hp=selection["selections"][name]["selected"]["hyperparameters"]
        for seed in SEEDS:
            for arm in ARMS:
                cfg={**base_config(name,data_dir),**hp,"variant":arm,"seed":seed,
                     "steps":TASKS[name]["confirmation_steps"],"evaluate_test":True,
                     "protocol_sha256":digest(frozen),"phase":"confirmation"}
                plans.append({"task_name":name,"arm":arm,"seed":seed,"config":cfg})
    frozen_plan={"protocol_sha256":digest(frozen),"selection_sha256":digest(selection),
                 "plans":plans,"test_metrics_used_for_selection":False}
    write(output/"confirmation_plan.json",frozen_plan)
    started=time.perf_counter()
    rows=[]
    for plan in plans:
        out=output/"confirmation"/plan["task_name"]/plan["arm"]/f"seed_{plan['seed']}"
        result=execute(plan["config"],out)
        rows.append({"task_name":plan["task_name"],"arm":plan["arm"],"seed":plan["seed"],**result})
        write(output/"confirmation_progress.json",{"completed":len(rows),"planned":len(plans),"runs":rows})
    write(output/"confirmation.json",{"protocol_sha256":digest(frozen),"confirmation_plan_sha256":digest(frozen_plan),
          "confirmation_total_seconds":time.perf_counter()-started,"runs":rows})
    print(json.dumps({"event":"confirmation_complete","runs":len(rows)}),flush=True)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("phase",choices=["discovery","confirmation"])
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--data-dir",type=Path,required=True)
    args=p.parse_args()
    (discovery if args.phase=="discovery" else confirmation)(args.output,args.data_dir)

