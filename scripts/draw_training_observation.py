#!/usr/bin/env python3
"""Draw actual finite checkpoint-observation results, without a learned embedding."""
from pathlib import Path
import argparse
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def draw(results, output):
    reports={}
    for name in ("modular_mlp","modular_transformer"):
        reports[name]=json.loads((results/"output_language"/f"{name}_output_language_report.json").read_text())
    # Counts come directly from the independently replayed observation receipts.
    # Read original accuracy receipts for the coarser observation language.
    coarse={}
    for name in reports:
        coarse[name]=json.loads((results/"diagnostic_panels"/f"{name}_panel_report.json").read_text())
    names=("modular_mlp","modular_transformer")
    accuracy_classes=[reports[name]['accuracy_language_full_signature_class_count'] for name in names]
    histogram_classes=[reports[name]['histogram_language_full_signature_class_count'] for name in names]
    full=[reports[name]['accounting']['full_construction_examples_per_checkpoint'] for name in names]
    selected=[reports[name]['accounting']['selected_construction_examples_per_checkpoint'] for name in names]
    if len(set(full))!=1 or len(set(selected))!=1:
        raise ValueError('Two-architecture shared-cost figure needs equal reported costs')
    numerator,denominator=coarse['modular_transformer']['selected_panel_cost']
    costs=[full[0],numerator/denominator,selected[0]]
    audits=[reports[name]['audit'] for name in names]
    counts={(a['construction_distinct_pairs_still_separated'],a['construction_distinct_pair_count']) for a in audits}
    if len(counts)!=1:raise ValueError('Audit counts differ; use separate annotations')
    separated,total=next(iter(counts))
    fig=plt.figure(figsize=(12.8,5.3),facecolor="#f4f6fb")
    gs=fig.add_gridspec(1,2,left=.065,right=.97,bottom=.20,top=.75,wspace=.24,width_ratios=[1.05,1])
    ax=fig.add_subplot(gs[0]);bx=fig.add_subplot(gs[1])
    ink="#14233d";teal="#087f8c";violet="#7553bc";gray="#9aa6ba"
    for a in (ax,bx):
        a.set_facecolor("#f4f6fb")
        for side in ("top","right","left"):a.spines[side].set_visible(False)
        a.spines["bottom"].set_color("#ccd2df")
        a.tick_params(colors=ink,length=0,labelsize=11)
        a.grid(axis="y",alpha=.15,color=ink);a.set_axisbelow(True)
    positions=[0,1];width=.30
    left=ax.bar([x-width/2 for x in positions],accuracy_classes,width,color=gray,label="Accuracy counts",zorder=3)
    right=ax.bar([x+width/2 for x in positions],histogram_classes,width,color=teal,label="Output histograms",zorder=3)
    ax.set_xticks(positions,["MLP","Causal transformer"]);ax.set_ylim(0,16.5);ax.set_yticks([0,4,8,12])
    ax.set_ylabel("Distinct observed checkpoint classes",color=ink,fontsize=11)
    ax.set_title("A richer observation resolves blindness",loc="left",fontweight="bold",color=ink,fontsize=13,pad=18)
    for bar in [*left,*right]:
        ax.text(bar.get_x()+bar.get_width()/2,bar.get_height()+.35,str(int(bar.get_height())),ha="center",color=ink,fontweight="bold",fontsize=14)
    ax.legend(frameon=False,ncol=1,loc="upper left",fontsize=10)
    bars=bx.bar([0,1,2],costs,color=[gray,violet,teal],width=.58,zorder=3)
    bx.set_xticks([0,1,2],["Full panel","Accuracy panel*","Histogram panel"])
    bx.set_ylim(0,285);bx.set_yticks([0,80,160,240]);bx.set_ylabel("Model input examples per checkpoint",color=ink,fontsize=11)
    bx.set_title("Exact selection over eight probe blocks",loc="left",fontweight="bold",color=ink,fontsize=13,pad=18)
    for bar in bars:bx.text(bar.get_x()+bar.get_width()/2,bar.get_height()+7,str(int(bar.get_height())),ha="center",color=ink,fontweight="bold",fontsize=15)
    fig.text(.065,.925,"The readout changes what you can see.",fontsize=23,fontweight="bold",color=ink)
    fig.text(.065,.86,"Real trained checkpoints  |  exact finite panels  |  separate audit examples",fontsize=12,color="#52657f")
    fig.text(.065,.102,f"Histogram panel: {separated} of {total} checkpoint pairs remain separated on audit examples, for each architecture.",fontsize=10.5,color=ink)
    fig.text(.065,.052,"* Accuracy panel applies to transformers; MLP accuracy cannot distinguish the 12 checkpoints. Greedy matches both optima.",fontsize=9,color="#52657f")
    output.parent.mkdir(parents=True,exist_ok=True)
    fig.savefig(output,format="svg",facecolor=fig.get_facecolor())
    fig.savefig(output.with_suffix(".png"),dpi=180,facecolor=fig.get_facecolor())
    plt.close(fig)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--results",type=Path,default=Path("applications/training_lab/results"));p.add_argument("--output",type=Path,default=Path("docs/assets/training-observations.svg"));a=p.parse_args();draw(a.results,a.output)
