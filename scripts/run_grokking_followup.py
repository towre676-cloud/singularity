#!/usr/bin/env python3
"""Declared follow-up: tune stronger AdamW decay, then confirm on new seeds."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import time
from run_training_revision import execute, digest, write

GRID=[{"lr":.001,"weight_decay":wd,"betas":[.9,.99]} for wd in (.3,1.,3.)]
SEEDS=[2000,2001,2002]
ARMS=["original_fixed","retuned_fixed","retuned_meta"]

def declaration():
    return {"schema":"singularity.grokking-followup/1","authored":"2026-10-19",
      "motivation":"The original discovery and confirmation TUNE curves show memorization without generalization. Expand decay range as a new declared experiment; retain the entire original study.",
      "task":"modular_addition","p":31,"split_seed":27183,"orbits_per_label":[8,4,4],
      "model":{"name":"mlp","hidden":128},"discovery_seed":9001,"discovery_grid":GRID,
      "discovery_steps":6000,"confirmation_seeds":SEEDS,"confirmation_steps":20000,
      "confirmation_arms":ARMS,"primary":"Retuned fixed AdamW versus original fixed AdamW final TEST loss/accuracy at equal updates; report all seeds.",
      "secondary":"Local differentiable tuner versus retuned fixed AdamW with same selected start settings.",
      "selection":"Lowest final TUNE loss from three fixed capped discovery runs, never TEST.",
      "timing":"All additional search and monitoring counted; shared CPU host.",
      "test_policy":"No discovery TEST evaluation; each confirmation run scores TEST once at completion.",
      "grokking_threshold":"TRAIN>=.99 and TUNE>=.95 each on3consecutive scheduled evals; report both confirmation times and censoring.",
      "scope":"Follow-up declared after observing original study TUNE failure, not an independent preregistration before all prior research."}

def base():
    return {"task":"modular_addition","p":31,"split":{"split_seed":27183,
      "train_orbits_per_label":8,"tune_orbits_per_label":4,"test_orbits_per_label":4},
      "model":{"name":"mlp","hidden":128},"optimizer":"adamw","eps":1e-8,
      "batch_size":128,"eval_every":200,"eval_batch_size":128,"threads":1,"grad_clip":1.,
      "max_parameters":1000000,"telemetry":{"sketch_dimension":16,"sketch_window":32,"sketch_seed":314159},
      "meta":{"every":100,"batch_size":64,"probe_seed":271828,"hyper_lr":.1,
        "max_backtracks":6,"min_lr":.0001,"max_lr":.01,"min_weight_decay":0.,"max_weight_decay":3.,"grad_clip":1.}}

def main(output,phase):
    protocol=declaration()
    path=output/"protocol.json"
    if path.exists() and json.loads(path.read_text())!=protocol:
        raise ValueError("Frozen follow-up protocol changed")
    write(path,protocol)
    h=digest(protocol)
    if phase=="discovery":
        rows=[]
        for i,hp in enumerate(GRID):
            cfg={**base(),**hp,"variant":"baseline","seed":9001,"steps":6000,
              "evaluate_test":False,"phase":"followup_discovery","protocol_sha256":h}
            summary=execute(cfg,output/"discovery"/f"candidate_{i}")
            rows.append({"candidate":i,"hyperparameters":hp,"tune_loss":summary["final_tune"]["loss"],
                 "tune_accuracy":summary["final_tune"]["accuracy"],"summary":summary})
        selected=min(rows,key=lambda row:(row["tune_loss"],row["candidate"]))
        write(output/"selection.json",{"protocol_sha256":h,"selected":selected,"all_candidates":rows,"test_evaluations":0})
    else:
        selection=json.loads((output/"selection.json").read_text())
        if selection["protocol_sha256"]!=h:raise ValueError("Selection and protocol disagree")
        plans=[]
        for seed in SEEDS:
            for arm in ARMS:
                hp={"lr":.001,"weight_decay":.1,"betas":[.9,.999]} if arm=="original_fixed" else selection["selected"]["hyperparameters"]
                cfg={**base(),**hp,"variant":"meta" if arm=="retuned_meta" else "baseline",
                  "seed":seed,"steps":20000,"evaluate_test":True,"phase":"followup_confirmation",
                  "protocol_sha256":h,"comparison_arm":arm}
                plans.append({"arm":arm,"seed":seed,"config":cfg})
        write(output/"confirmation_plan.json",{"protocol_sha256":h,"plans":plans})
        rows=[]
        started=time.perf_counter()
        for plan in plans:
            summary=execute(plan["config"],output/"confirmation"/plan["arm"]/f"seed_{plan['seed']}")
            rows.append({"arm":plan["arm"],"seed":plan["seed"],**summary})
            write(output/"confirmation_progress.json",{"planned":len(plans),"completed":len(rows),"runs":rows})
        write(output/"confirmation.json",{"protocol_sha256":h,"runs":rows,"wall_seconds":time.perf_counter()-started})

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase",choices=["discovery","confirmation"])
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    main(args.output,args.phase)
