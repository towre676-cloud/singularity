#!/usr/bin/env python3
"""Draw the retained predictive and deployment confirmation results."""
import argparse
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--results',type=Path,default=ROOT/'applications/training_lab/results')
    parser.add_argument('--output-dir',type=Path,default=ROOT/'docs/assets')
    args=parser.parse_args()
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    D=args.results
    output_dir=args.output_dir
    output_dir.mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'svg.fonttype':'none','svg.hashsalt':'singularity-confirmed-20261019','axes.spines.top':False,'axes.spines.right':False,'axes.spines.left':False,'axes.spines.bottom':False,'axes.labelcolor':'#182a45','text.color':'#182a45','xtick.color':'#182a45','ytick.color':'#182a45'})
    BG='#f4f7fc'; TEAL='#087f8c'; GRAY='#97a6bb'; PURPLE='#7853bc'
    def save(fig,name):
     for ext in ['svg','png']:
      p=output_dir/f'{name}.{ext}';fig.savefig(p,dpi=190,facecolor=BG,metadata={'Date':None} if ext=='svg' else {})
      if ext=='svg':p.write_text('\n'.join(line.rstrip() for line in p.read_text().splitlines())+'\n')
     plt.close(fig)
    x=json.loads((D/'predictive_mixture/results.json').read_text())
    fig,axes=plt.subplots(1,2,figsize=(13.5,5.2),gridspec_kw={'width_ratios':[1.3,1]},facecolor=BG)
    fig.subplots_adjust(left=.07,right=.97,top=.72,bottom=.23,wspace=.35)
    fig.text(.07,.91,'Better predictions from the models we already trained.',fontsize=23,weight='bold')
    fig.text(.07,.83,'Fresh WikiText passages | settings selected on TUNE before TEST | zero new neural updates',fontsize=12,color='#526984')
    ax=axes[0];ax.set_facecolor(BG)
    seedrows=x['per_seed']
    if isinstance(seedrows,dict):seedrows=list(seedrows.values())
    for i,row in enumerate(seedrows):
     n=row['neural']['nll_nats_per_byte'];m=row['mixture']['nll_nats_per_byte']
     ax.plot([0,1],[n,m],'-o',color=[TEAL,PURPLE,'#d77e31'][i],lw=2,ms=7,label=f"Seed {row['seed']}")
    ax.set_xticks([0,1],['Neural model','Neural + counts']);ax.set_xlim(-.2,1.2);ax.set_ylim(1.98,2.11);ax.grid(axis='y',color='#d6deea');ax.set_axisbelow(True);ax.set_ylabel('Test loss (nats per byte; lower is better)');ax.set_title('One neural forward pass',loc='left',weight='bold',pad=14);ax.legend(frameon=False,loc='upper right',fontsize=9)
    ax=axes[1];ax.set_facecolor(BG)
    sec=x['secondary_ensemble'];vals=[sec['neural_ensemble']['nll_nats_per_byte'],sec['ensemble_mixture']['nll_nats_per_byte']]
    ax.plot([0,1],vals,'-',color=TEAL,lw=2);ax.scatter([0,1],vals,color=[GRAY,TEAL],s=80);ax.set_xlim(-.25,1.25);ax.set_ylim(1.96,2.01);ax.set_xticks([0,1],['Neural ensemble','Ensemble + counts']);ax.grid(axis='y',color='#d6deea');ax.set_axisbelow(True);ax.set_title('Stronger control: three neural passes',loc='left',weight='bold',pad=14)
    for i,v in enumerate(vals):ax.text(i,v+.001,f'{v:.6f}',ha='center',weight='bold',fontsize=12)
    fig.text(.07,.10,'2.82% lower mean loss across all three seeds. The stronger ensemble also improves by 0.47%.',fontsize=12,weight='bold',color=TEAL)
    fig.text(.07,.045,'All 16 contiguous text blocks improve in both comparisons. Result scope: one fresh 32 KiB suffix and these frozen models.',fontsize=10,color='#526984')
    save(fig,'confirmed-prediction')
    t=json.loads((D/'checkpoint_confirmation/timing.json').read_text())
    fig,axes=plt.subplots(1,2,figsize=(13.5,5.2),facecolor=BG)
    fig.subplots_adjust(left=.07,right=.97,top=.72,bottom=.24,wspace=.35)
    fig.text(.07,.91,'A smaller smoke test. The same observed changes caught.',fontsize=21,weight='bold')
    fig.text(.07,.83,'Checkpoint excluded from selection | new perturbation strengths | 30 paired CPU measurements',fontsize=12,color='#526984')
    for ax in axes:ax.set_facecolor(BG);ax.grid(axis='y',color='#d6deea');ax.set_axisbelow(True)
    ax=axes[0];v=[t['summary']['full']['forwarded_input_tokens'],t['summary']['selected']['forwarded_input_tokens']]
    ax.bar([0,1],v,color=[GRAY,TEAL],width=.55);ax.set_xticks([0,1],['Full suite','Selected panel']);ax.set_ylim(0,39000);ax.set_ylabel('Forwarded input tokens');ax.set_title('8× less input work',loc='left',weight='bold',pad=14)
    for i,z in enumerate(v):ax.text(i,z+900,f'{z:,}',ha='center',weight='bold',fontsize=15)
    ax=axes[1];v=[t['summary']['full']['median_seconds']*1000,t['summary']['selected']['median_seconds']*1000]
    ax.bar([0,1],v,color=[GRAY,TEAL],width=.55);ax.set_xticks([0,1],['Full suite','Selected panel']);ax.set_ylim(0,165);ax.set_ylabel('Resident prediction time (ms)');ax.set_title(f"{t['ratio_full_median_over_selected_median']:.2f}× median prediction speedup",loc='left',weight='bold',pad=14)
    for i,z in enumerate(v):ax.text(i,z+4,f'{z:.1f} ms',ha='center',weight='bold',fontsize=15)
    fig.text(.07,.105,'All 8 declared changes detected on held-out checkpoint; clean clone unchanged. Simple one-block selectors tie.',fontsize=11,weight='bold',color=TEAL)
    fig.text(.07,.05,'Full context and batch shape retained. Excludes cold startup. Construction + complete audit amortize after 103 resident checks.',fontsize=10,color='#526984')
    save(fig,'confirmed-deployment')

if __name__=='__main__':
    main()
