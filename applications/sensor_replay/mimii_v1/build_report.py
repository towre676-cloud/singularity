#!/usr/bin/env python3
"""Build source-bound MIMII figures, an illustrated HTML report and a compact PDF.

Presentation only: all choices come from the sealed selection snapshot. This
module does not fit, select, or replace a panel using confirmation outcomes.
"""
from __future__ import annotations

import argparse
import base64
from fractions import Fraction
import hashlib
import html
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
from matplotlib.transforms import Bbox
import numpy as np

ROOT = Path(__file__).resolve().parent
COLORS = {'ink':'#172c40','slate':'#60778b','teal':'#087e81','orange':'#c56935','red':'#b64b55','paper':'#fbfcfd','blue':'#3f68a5'}
OBJECTIVES = ['nominal','nuisance','robust','erasure_1','erasure_2']
LABELS = {'nominal':'By machine type','nuisance':'By type + noise','robust':'By type + noise + class','erasure_1':'Also lose any 1 mic','erasure_2':'Also lose any 2 mics'}


def read(root, name):
    return json.loads((root/name).read_text())


def frac(value):
    return float(Fraction(value))


def percent(value):
    return f'{100*value:.2f}%'


def channels(mask):
    return ', '.join(str(i+1) for i in range(8) if mask >> i & 1) if mask is not None else 'infeasible'


def panel_title(name, panel):
    names={'full':'Full array','microphone_1':'Mic 1','nominal_exact':'Exact nominal optimum','nuisance_exact':'Noise-aware optimum','robust_exact':'Class-robust optimum','erasure_1_exact':'1-erasure optimum','erasure_2_exact':'2-erasure optimum'}
    return names.get(name,name.replace('_',' ')) + f' ({panel["cost"]} mic' + ('' if panel['cost']==1 else 's') + ')'


def figure_data(snapshot, results):
    # Keep every primary objective visible, even when two have the same mask.
    keys = ['full','microphone_1','nominal_exact','nominal_greedy'] + [name+'_exact' for name in OBJECTIVES if name!='nominal' and name+'_exact' in results['panels']]
    return keys


def figures(root, protocol, snapshot, results):
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,
                         'axes.spines.right':False,'axes.labelcolor':COLORS['ink'],
                         'text.color':COLORS['ink'],'xtick.color':COLORS['slate'],
                         'ytick.color':COLORS['slate'],'axes.titleweight':'bold'})
    fig = plt.figure(figsize=(16,9),facecolor=COLORS['paper'])
    grid = fig.add_gridspec(2,2,left=.075,right=.965,bottom=.09,top=.84,hspace=.55,wspace=.30)
    fig.text(.075,.962,'Eight microphones. Every possible panel. A different machine to confirm it.',fontsize=20,weight='bold')
    fig.text(.075,.921,'Original MIMII | 1,536 real recordings | 512 stem groups | decisions locked before confirmation',fontsize=12,color=COLORS['slate'])

    panel_axes = {}
    ax = fig.add_subplot(grid[0,0]);panel_axes['scores']=[ax]
    keys = figure_data(snapshot,results)
    x = np.arange(len(keys)); width=.34
    selected = [100*results['panels'][key]['selection_balanced_accuracy'] for key in keys]
    confirmed = [100*results['panels'][key]['balanced_accuracy'] for key in keys]
    ax.bar(x-width/2,selected,width,color=COLORS['slate'],label='Selection: machine ID 04')
    ax.bar(x+width/2,confirmed,width,color=COLORS['teal'],label='Confirmation: machine ID 06')
    for i,(a,b) in enumerate(zip(selected,confirmed)):
        ax.text(i-width/2,a+1.4,f'{a:.1f}',ha='center',fontsize=8)
        ax.text(i+width/2,b+1.4,f'{b:.1f}',ha='center',fontsize=8,color=COLORS['teal'])
    labels=[]
    for key in keys:
        p=results['panels'][key]
        labels.append({'full':'Full','microphone_1':'Mic 1','nominal_exact':'Nominal','nominal_greedy':'Greedy/pruned','nuisance_exact':'Noise','robust_exact':'Class','erasure_1_exact':'Erase 1','erasure_2_exact':'Erase 2'}[key]+f'\n{p["cost"]} mic'+('' if p['cost']==1 else 's'))
    ax.set(xticks=x,xticklabels=labels,ylim=(0,110),ylabel='Balanced accuracy (%)')
    ax.set_title('A. Do the selected savings transfer?',loc='left',pad=30,fontsize=13)
    ax.legend(ncol=2,frameon=False,fontsize=8,loc='lower left',bbox_to_anchor=(0,1.005))
    ax.grid(axis='y',alpha=.16); ax.set_axisbelow(True)

    ax = fig.add_subplot(grid[0,1]);panel_axes['removals']=[ax]
    table = np.asarray([[frac(v) for v in row] for row in results['confirmation_all_mask_constraint_values_exact']])
    full=table[254]
    # Positive means removal harms the complete array, not that the microphone
    # alone is an accurate classifier or a universally informative sensor.
    changes=np.array([[100*(full[cell]-table[(255^(1<<j))-1,cell]) for j in range(8)] for cell in range(5,17)])
    lim=max(6.25,float(np.max(np.abs(changes))))
    im=ax.imshow(changes,cmap='RdBu_r',norm=TwoSlopeNorm(vmin=-lim,vcenter=0,vmax=lim),aspect='auto')
    for i in range(12):
        for j in range(8):
            v=changes[i,j]
            ax.text(j,i,f'{v:+.0f}' if abs(v)>.01 else '0',ha='center',va='center',fontsize=9,
                    color='white' if abs(v)>.65*lim else COLORS['ink'])
    rowlabels=[t.capitalize()+' '+f'{snr:+d}' for t in protocol['machine_types'] for snr in protocol['snr_db']]
    ax.set(xticks=range(8),xticklabels=range(1,9),yticks=range(12),yticklabels=rowlabels,xlabel='Microphone removed from full array')
    ax.tick_params(axis='y',labelsize=9)
    ax.set_title('B. Which removals hurt on confirmation?',loc='left',fontsize=13,pad=30)
    cb=fig.colorbar(im,ax=ax,fraction=.025,pad=.02)
    cb.set_label('Balanced accuracy lost (points)',fontsize=8); cb.ax.tick_params(labelsize=8)
    panel_axes['removals'].append(cb.ax)

    ax = fig.add_subplot(grid[1,0]);panel_axes['frontier']=[ax]
    styles=[('robust','Class constraints',COLORS['teal'],'o'),('erasure_1','Survive 1 erasure',COLORS['blue'],'s'),('erasure_2','Survive 2 erasures',COLORS['orange'],'^')]
    margins=[0,2,5,10]
    for objective,label,color,marker in styles:
        rows=[next(r for r in results['margin_sensitivity'] if r['objective']==objective and abs(100*frac(r['margin_exact'])-m)<1e-9) for m in margins]
        vals=[r['minimum_cost'] if r['minimum_cost'] is not None else 9 for r in rows]
        ax.plot(margins,vals,color=color,marker=marker,label=label,linewidth=2,markersize=6)
    ax.set(xticks=margins,ylim=(.5,9.6),yticks=range(1,10),yticklabels=[str(i) for i in range(1,9)]+['No panel'],xlabel='Allowed loss from full array (percentage points)',ylabel='Minimum selected microphones')
    ax.set_title('C. Exact development cost of stronger requirements',loc='left',fontsize=13,pad=12)
    ax.legend(loc='best',frameon=False,fontsize=8)
    ax.grid(alpha=.15); ax.axvline(2,color=COLORS['slate'],linestyle=':',alpha=.5)

    ax = fig.add_subplot(grid[1,1]);panel_axes['aliases']=[ax]
    eq=results['selection_equivalence_classes_on_confirmation']
    counts=[sum(len(v['selection_equivalent_masks'])==1 for v in eq),
            sum(len(v['selection_equivalent_masks'])>1 and not v['split_on_confirmation'] for v in eq),
            sum(v['split_on_confirmation'] for v in eq)]
    labels=['One mask\nper trace','Multiple masks,\nstill agree','Multiple masks,\nnow disagree']
    bars=ax.bar(range(3),counts,color=[COLORS['slate'],COLORS['teal'],COLORS['orange']],width=.55)
    for b,v in zip(bars,counts):ax.text(b.get_x()+b.get_width()/2,v+max(1,max(counts)*.025),str(v),ha='center',fontsize=13,weight='bold')
    ax.set(xticks=range(3),xticklabels=labels,ylim=(0,max(5,max(counts)*1.25)),ylabel='Selection prediction-trace classes')
    title=('D. Every selection prediction trace is distinct' if not any(len(v['selection_equivalent_masks'])>1 for v in eq) else 'D. Do selection aliases split on confirmation?')
    ax.set_title(title,loc='left',fontsize=13,pad=12)
    ax.grid(axis='y',alpha=.16);ax.set_axisbelow(True)
    fig.text(.075,.025,'Every plotted confirmation outcome is descriptive on four fixed held-out machines. Noise mixtures stay grouped; no new placement or hardware benefit is inferred.',fontsize=10,color=COLORS['slate'])
    fig.savefig(root/'mimii_results.png',dpi=240,facecolor=fig.get_facecolor())
    export_panels(fig,root,panel_axes)
    plt.close(fig)

    fig,axes=plt.subplots(1,2,figsize=(16,7),facecolor=COLORS['paper'],gridspec_kw={'width_ratios':[1.05,1]})
    fig.subplots_adjust(left=.09,right=.96,top=.82,bottom=.14,wspace=.30)
    fig.suptitle('Simple microphones and erased channels: the controls remain visible',fontsize=20,weight='bold',x=.09,ha='left')
    ax=axes[0]; y=np.arange(9)
    names=[f'single_microphone_{i}' for i in range(1,9)]+['full']
    a=np.array([results['panels'][k]['selection_balanced_accuracy'] for k in names])*100
    b=np.array([results['panels'][k]['balanced_accuracy'] for k in names])*100
    ax.plot(a,y,'o',color=COLORS['slate'],label='Selection')
    ax.plot(b,y,'o',color=COLORS['teal'],label='Confirmation')
    for i,(v,w) in enumerate(zip(a,b)):
        ax.plot([v,w],[i,i],color='#cdd8df',zorder=0)
        ax.text(max(v,w)+1.2,i,f'{w:.1f}%',va='center',fontsize=9,color=COLORS['teal'])
    ax.set(yticks=y,yticklabels=[f'Microphone {i}' for i in range(1,9)]+['Full eight'],xlabel='Balanced accuracy (%)',xlim=(0,110))
    ax.invert_yaxis();ax.set_title('Every singleton, fixed before confirmation',loc='left',pad=14)
    ax.legend(frameon=False,loc='lower left');ax.grid(axis='x',alpha=.15)
    ax=axes[1]
    keys=['full']+[k+'_exact' for k in OBJECTIVES if k+'_exact' in results['panels']]
    for key in keys:
        p=results['panels'][key]
        vals=[100*results['erasure_sensitivity'][key][str(e)]['worst_pooled_balanced_accuracy'] for e in [0,1,2]]
        ax.plot([0,1,2],vals,'o-',label=panel_title(key,p),linewidth=1.8,markersize=5)
    ax.set(xticks=[0,1,2],xlabel='Maximum selected channels erased',ylabel='Worst pooled confirmation balanced accuracy (%)',ylim=(0,105))
    ax.set_title('Worst survivor, not an average erasure',loc='left',pad=14)
    ax.legend(frameon=False,fontsize=8,loc='lower left');ax.grid(alpha=.15)
    fig.savefig(root/'mimii_controls.png',dpi=160,facecolor=fig.get_facecolor())
    export_panels(fig,root,{'singletons':[axes[0]],'erasures':[axes[1]]})
    plt.close(fig)


def export_panels(fig,root,panels):
    visibility=[text.get_visible() for text in fig.texts]
    for text in fig.texts:
        text.set_visible(False)
    try:
        fig.canvas.draw()
        renderer=fig.canvas.get_renderer()
        for name,axes in panels.items():
            extent=Bbox.union([ax.get_tightbbox(renderer) for ax in axes])
            extent=extent.transformed(fig.dpi_scale_trans.inverted()).expanded(1.035,1.055)
            fig.savefig(root/f'mimii_panel_{name}.png',dpi=220,bbox_inches=extent,facecolor=fig.get_facecolor())
    finally:
        for text,visible in zip(fig.texts,visibility):
            text.set_visible(visible)


def prose(protocol,snapshot,results):
    full=results['panels']['full']
    nominal=results['panels']['nominal_exact']
    rows=results['selection_equivalence_classes_on_confirmation']
    multi=[v for v in rows if len(v['selection_equivalent_masks'])>1]
    split=[v for v in multi if v['split_on_confirmation']]
    allties=all(v['exact_mask']==v['pruned_greedy_mask'] for v in snapshot['objectives'].values())
    exactbetter=[name for name,v in snapshot['objectives'].items() if v['exact_mask'] is not None and v.get('greedy_feasible',True) and v['greedy_mask'].bit_count()>v['minimum_cost']]
    greedy_failed=[name for name,v in snapshot['objectives'].items() if not v.get('greedy_feasible',True)]
    delta=nominal['balanced_accuracy']-full['balanced_accuracy']
    advantage=('The exact finite search exposes the complete 255-panel design space, certifies every minimum channel count and identifies when requested erasure robustness is impossible. '
               'Every proposed stream reduction comes with a checkable finite optimum and its transfer limits. ')
    passed_reductions=[(objective,results['panels'][objective+'_exact'])
                       for objective in OBJECTIVES if objective+'_exact' in results['panels']
                       and results['panels'][objective+'_exact']['cost']<8
                       and results['panels'][objective+'_exact']['confirmation_contracts_pass'][objective]]
    if passed_reductions:
        objective,candidate=passed_reductions[-1]
        advantage+=f"The predeclared {LABELS[objective].lower()} optimum uses {candidate['cost']} of eight streams and preserves its own contract on the protected confirmation panel. "
    elif results['panels']['nominal_greedy']['cost']<8 and results['panels']['nominal_greedy']['confirmation_contracts_pass']['nominal']:
        candidate=results['panels']['nominal_greedy']
        advantage+=f"The predeclared greedy/pruned panel retains {candidate['cost']} of eight recorded streams (75% fewer) and passes the protected type-specific margin at {percent(candidate['balanced_accuracy'])} balanced accuracy. The exact tie choice fails. "
    elif delta>=-.02 and nominal['confirmation_contracts_pass']['nominal']:
        advantage+=f'The nominal optimum uses {nominal["cost"]} of eight streams and preserves its type-specific margin on this protected confirmation panel. '
    else:
        advantage+=f'The nominal optimum uses {nominal["cost"]} of eight streams, but fails its protected type-specific confirmation contract. '
    advantage+='All reported panels fail the simultaneous absolute class-recall floor. This finite physical replay does not establish hardware savings or generalization to an industrial machine population.'
    outcome=f'The full array scores {percent(full["balanced_accuracy"])} balanced accuracy on the 384 protected recordings. The nominal development optimum, microphones {channels(nominal["mask"])}, scores {percent(nominal["balanced_accuracy"])} ({100*delta:+.2f} percentage points).'
    alias=(f'All {len(rows)} masks have different complete selection prediction traces. No empirical alias class of distinct panels occurs, so this study supplies no alias-splitting witness on confirmation.' if not multi else f'Among {len(rows)} distinct selection prediction traces, {len(multi)} contain multiple microphone masks. Of those multi-mask classes, {len(split)} split into different prediction traces on confirmation. These are empirical output aliases, not physically identical microphones.')
    cost_ties=all(v['minimum_cost']==(v['pruned_greedy_mask'].bit_count() if v['pruned_greedy_mask'] is not None else None) for v in snapshot['objectives'].values())
    baseline=('Exact selection and optimally pruned greedy tie on minimum channel count under every feasible objective, with matching infeasibility elsewhere.' if cost_ties else 'Exact and optimally pruned greedy do not tie on minimum channel count under every objective; the full comparison retains the differences.')
    if not allties:
        baseline+=' Equally cheap nominal masks differ; the complete table reports each protected outcome.'
    if exactbetter:baseline+=' Ordinary greedy uses more channels under '+', '.join(LABELS[n].lower() for n in exactbetter)+'.'
    else:baseline+=' Exact selection has no channel-count advantage over ordinary greedy.'
    if greedy_failed:baseline+=' Both erasure objectives are infeasible.'
    return advantage,outcome,alias,baseline


def observability_summary(root):
    path=root/'observability.json'
    if not path.exists():
        return ''
    d=json.loads(path.read_text())
    unsupported=sum(not any(row[j] for row in d['separates']) for j in range(len(d['distinctions'])))
    infeasible=[str(int(k)-1) for k,v in d['outcomes'].items() if not v['feasible']]
    text=f"The empirical development-box test finds {unsupported} of {len(d['distinctions'])} type-by-noise class distinctions without any individually separating microphone. "
    if infeasible:
        text+='Its complete separation requirement is infeasible at erasure budgets '+', '.join(infeasible)+'. '
    else:
        text+='The core solver and exhaustive oracle agree on the retained finite multicover optima. '
    return text+'This is a limit of the conservative empirical-box certificate, not proof of physical indistinguishability.'


def table_rows(snapshot,results):
    rows=[]
    for objective in OBJECTIVES:
        d=snapshot['objectives'][objective]
        for method,field in [('Exact','exact_mask'),('Greedy','greedy_mask'),('Pruned greedy','pruned_greedy_mask')]:
            mask=d[field]
            if mask is None:
                rows.append([LABELS[objective],method,'No panel','-','-','-'])
                continue
            name=objective+'_'+method.lower().replace(' ','_')
            p=results['panels'][name]
            passed=p['confirmation_contracts_pass'][objective]
            display_method=method+'*' if method=='Greedy' and not d.get('greedy_feasible',True) else method
            rows.append([LABELS[objective],display_method,channels(mask),str(mask.bit_count()),percent(p['balanced_accuracy']), 'Pass' if passed else 'Fail'])
    return rows


def html_report(root,protocol,snapshot,results):
    advantage,outcome,alias,baseline=prose(protocol,snapshot,results)
    box_summary=observability_summary(root)
    encoded={fn:base64.b64encode((root/fn).read_bytes()).decode() for fn in ['mimii_results.png','mimii_controls.png']}
    trs=''.join('<tr>'+''.join('<td>'+html.escape(v)+'</td>' for v in row)+'</tr>' for row in table_rows(snapshot,results))
    pertype=[]
    for t in protocol['machine_types']:
        p=results['panels']['nominal_exact']['by_machine_type'][t];f=results['panels']['full']['by_machine_type'][t]
        pertype.append(f'<tr><td>{t.capitalize()}</td><td>{percent(f["balanced_accuracy"])}</td><td>{percent(p["balanced_accuracy"])}</td><td>{percent(p["class_recall"][0])}</td><td>{percent(p["class_recall"][1])}</td></tr>')
    cellrows=[]
    for t in protocol['machine_types']:
        for snr in protocol['snr_db']:
            key=f'{t}/snr{snr}'
            p=results['panels']['nominal_exact']['by_type_snr'][key]
            f=results['panels']['full']['by_type_snr'][key]
            cellrows.append(f'<tr><td>{t.capitalize()} / {snr:+d} dB</td><td>{percent(f["balanced_accuracy"])}</td><td>{percent(p["balanced_accuracy"])}</td><td>{percent(p["class_recall"][0])}</td><td>{percent(p["class_recall"][1])}</td></tr>')
    doc=f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>MIMII: complete array-selection audit</title><style>
body{{background:#eef3f5;color:#172c40;margin:0;font:17px/1.65 system-ui,sans-serif}}main{{max-width:1180px;margin:28px auto;padding:48px 55px;background:white;border-radius:12px}}h1{{font-size:43px;line-height:1.13;max-width:24ch;letter-spacing:-1px}}h2{{font-size:25px;margin-top:38px}}.eyebrow{{color:#087e81;font-size:13px;font-weight:750;letter-spacing:2px}}.lead{{font-size:22px;max-width:85ch}}.advantage{{background:#e9f5f3;border-left:5px solid #087e81;padding:20px 26px}}.caption{{font-size:14px;color:#60778b}}img{{width:100%;height:auto}}figure{{margin:30px 0}}table{{border-collapse:collapse;width:100%;font-size:14px;margin:22px 0}}td,th{{padding:10px 9px;border-bottom:1px solid #dce4ea;text-align:left;vertical-align:top}}th{{background:#f0f5f7}}code{{font-size:13px;overflow-wrap:anywhere}}a{{color:#087e81}}@media(max-width:760px){{main{{padding:24px 17px;margin:0}}h1{{font-size:33px}}table{{display:block;overflow:auto}}}}@media print{{body{{background:white}}main{{padding:0;max-width:none}}tr,figure{{break-inside:avoid}}}}</style><main>
<div class="eyebrow">SINGULARITY | REAL INDUSTRIAL RECORDINGS | 20 OCTOBER 2026</div>
<h1>What survives when the machine changes?</h1>
<p class="lead">Eight synchronized microphones, all 255 nonempty panels, and machine identities held apart for training, selection and protected confirmation.</p>
<p class="advantage"><strong>Demonstrated advantage.</strong> {html.escape(advantage)}</p>
<p>{html.escape(outcome)} {html.escape(baseline)}</p>
<figure><img src="data:image/png;base64,{encoded['mimii_results.png']}" alt="Development and confirmation scores, channel-deletion contributions, exact erasure cost frontier, and development trace aliases"><figcaption class="caption">The microphone-removal heatmap uses the complete array as its reference. Positive values mean removal harms this fixed classifier on the protected recordings; negative values mean removal improves it. Channel importance is context dependent. SNR labels denote nominal archive mixture conditions; they are not measured per-recording ratios. Frontier costs use selection data only.</figcaption></figure>
<h2>The experiment is physical; the design is retrospective</h2>
<p>The original MIMII release supplies measured sound from fans, pumps, slide rails and valves, with nominal archive noise conditions labeled -6, 0 and +6 dB. The primary paper scales noise using model-average signal power, so the labels do not assert measured per-recording SNR. The predeclared subset contains sixteen normal and sixteen abnormal recording stems per machine identity, retaining every corresponding noise mixture. IDs 00 and 02 train the fixed per-type nearest-reference classifiers, ID 04 selects one common microphone mask, and ID 06 confirms it. Selection and confirmation each contain 128 stems and 384 mixtures across four machines. The entire dataset is balanced by construction; these are case-control scores, not natural fault prevalence.</p>
<p>Matching stems and their noise mixtures stay together, and an entire machine identity stays in one split. Hidden factory-noise segment identifiers and temporal session boundaries are not published, so independence of factory-noise sessions cannot be verified. One protected identity per type does not establish transfer to a population of machines.</p>
<h2>Every comparator remains visible</h2>
<p>The two-point nominal contract protects pooled and per-type balanced accuracy relative to the full array. Noise-aware selection adds type-by-noise cells; class-robust selection additionally protects normal and abnormal recall in each such cell. Erasure contracts test every survivor after one or two selected channels are lost, against the original intact-array thresholds. Empty survivors fail. Because accuracy can decrease after adding a microphone, this replay checks all masks rather than assuming monotonic coverage.</p>
<table><thead><tr><th>Selection requirement</th><th>Method</th><th>Microphones</th><th>Count</th><th>Confirmation balanced accuracy</th><th>Same confirmation contract</th></tr></thead><tbody>{trs}</tbody></table>
<p>An asterisk marks a terminal greedy mask that is infeasible on selection; its confirmation score is a diagnostic, not a successful selected design. A confirmation pass is descriptive on this protected subset, rather than a population noninferiority result. The comparison includes ordinary greedy, exact pruning of greedy, all eight singleton microphones, and the complete eight-channel array. No winner is replaced after confirmation. Relative preservation can pass against a weak full-array reference, so absolute class recall remains visible.</p>
<figure><img src="data:image/png;base64,{encoded['mimii_controls.png']}" alt="All eight singleton baselines and worst confirmation performance after channel erasures"><figcaption class="caption">Mic 1 is the representative single microphone fixed in advance. All other singletons are reported as controls. The worst-erasure plot minimizes over every allowed survivor; it does not average favorable deletion cases.</figcaption></figure>
<h2>Where the nominal panel succeeds or fails</h2>
<table><thead><tr><th>Protected machine type</th><th>Full array</th><th>Nominal panel</th><th>Normal recall</th><th>Abnormal recall</th></tr></thead><tbody>{''.join(pertype)}</tbody></table>
<h2>Class failures within each noise condition</h2>
<table><thead><tr><th>Protected type / nominal noise</th><th>Full array</th><th>Nominal panel</th><th>Normal recall</th><th>Abnormal recall</th></tr></thead><tbody>{''.join(cellrows)}</tbody></table>
<p>{html.escape(alias)} An exact certificate for the selection table cannot resolve alternatives whose complete observed outputs agree. The new machine supplies additional information, while the locked protocol prevents using that information to rewrite the original choice.</p>
<h2>What the mathematics certifies</h2>
<p>Every nonempty microphone subset corresponds to exactly one mask from 1 through 255. Given the saved numerical predictions, class recalls and balanced accuracies are exact fractions. Exhaustive feasibility and minimization by channel count, then integer mask, certify the complete finite optimum or infeasibility for each declared objective. The existing Singularity robust-coverage engine also analyzes independent per-channel interval separation under empirical development boxes. That conditional multicover theorem is kept distinct from the nonmonotone fused-classifier erasure calculation. Overlap of empirical boxes is failure of a sufficient certificate, not proof that physical faults cannot be observed.</p>
<p>{html.escape(box_summary)}</p>
<p>With sixteen examples per class in a type-by-noise cell, a single error changes balanced accuracy by 3.125 points and class recall by 6.25 points. A two-point cell margin therefore permits no additional error. Sensitivity at zero, two, five and ten points exposes this granularity. Paired bootstrap differences resample complete stems with all mixtures together, conditional on the four protected machines.</p>
<h2>Provenance and replay</h2>
<p>The protocol was externally frozen before signals in commit <code>30132a5f7e332c832dc7ad471937a97b3483aa6f</code>. Selective ZIP64 retrieval acquired 1,536 declared members, totaling 2,852,963,714 compressed audio bytes and 3,932,282,880 uncompressed WAV bytes. Source receipts retain original member identities, offsets, CRC32 and individual compressed/raw SHA-256 values. Whole-archive MD5 values are publisher metadata; partial retrieval does not verify those complete archives. An independent Python WAV and NumPy FFT/Welch route replays every selected raw member and all 159,744 descriptors, agreeing with the production feature extractor to maximum absolute discrepancy 1.4433e-15 under the declared 2e-11 tolerances.</p>
<p>The retained package contains the protocol and two locks, exact source-member plan, feature array, all-mask predictions, complete objective certificates, sensitivity tables and an independent checker. The original MAFAULDA files are preserved unchanged. The recording source is <a href="https://zenodo.org/records/3384388">MIMII public 1.0</a>, DOI 10.5281/zenodo.3384388, by Harsh Purohit and colleagues at Hitachi, Ltd., released under CC BY-SA 4.0. The <a href="https://arxiv.org/html/1909.09347v1">primary paper</a> describes acquisition and mixing. This supervised cross-machine stress test differs from the original per-ID normal-only anomaly benchmark.</p>
<p class="caption">No new sensor positions, phase beamformer, hardware savings, energy reduction, latency reduction or field deployment benefit is established by these prerecorded measurements. The demonstrated contribution is a bounded physical replay with an exhaustive, auditable design frontier and explicit transfer limits.</p>
</main></html>'''
    (root/'MIMII_Array_Research.html').write_text(doc)


def pdf_report(root,protocol,snapshot,results):
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    font=Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
    bold=Path('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf')
    pdfmetrics.registerFont(TTFont('MimiiSans',str(font)))
    pdfmetrics.registerFont(TTFont('MimiiSansBold',str(bold)))
    pdfmetrics.registerFontFamily('MimiiSans',normal='MimiiSans',bold='MimiiSansBold')
    ink=colors.HexColor(COLORS['ink']);teal=colors.HexColor(COLORS['teal']);slate=colors.HexColor(COLORS['slate'])
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='MTitle',fontName='MimiiSansBold',fontSize=25,leading=29,textColor=ink,spaceAfter=12))
    styles.add(ParagraphStyle(name='MHead',fontName='MimiiSansBold',fontSize=15,leading=20,textColor=ink,spaceBefore=14,spaceAfter=9))
    styles.add(ParagraphStyle(name='MBody',fontName='MimiiSans',fontSize=9.2,leading=13,textColor=ink,spaceAfter=8))
    styles.add(ParagraphStyle(name='MLead',fontName='MimiiSans',fontSize=11,leading=16,textColor=ink,spaceAfter=10))
    styles.add(ParagraphStyle(name='MSmall',fontName='MimiiSans',fontSize=7.8,leading=11,textColor=slate,spaceAfter=8))
    styles.add(ParagraphStyle(name='MCell',fontName='MimiiSans',fontSize=8,leading=11,textColor=ink))
    advantage,outcome,alias,baseline=prose(protocol,snapshot,results)
    story=[]
    p=lambda text,style='MBody':Paragraph(text,styles[style])
    def plot_image(name,maxheight):
        im=Image(str(root/name));factor=min(174*mm/im.imageWidth,maxheight*mm/im.imageHeight)
        im.drawWidth=im.imageWidth*factor;im.drawHeight=im.imageHeight*factor
        return im
    story += [p('SINGULARITY / PHYSICAL SENSOR REPLAY / 20 OCTOBER 2026','MSmall'),p('What survives when<br/>the machine changes?','MTitle'),p('Eight synchronized microphones. Every one of the 255 possible panels. Protected confirmation on different machine identities.','MLead')]
    box=Table([[p('<b>Demonstrated advantage.</b> '+html.escape(advantage),'MBody')]],colWidths=[174*mm])
    box.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#e9f5f3')),('BOX',(0,0),(-1,-1),.5,teal),('LEFTPADDING',(0,0),(-1,-1),11),('RIGHTPADDING',(0,0),(-1,-1),11),('TOPPADDING',(0,0),(-1,-1),10),('BOTTOMPADDING',(0,0),(-1,-1),3)]))
    story+=[box,Spacer(1,10),p(html.escape(outcome)),plot_image('mimii_panel_scores.png',95),p('The primary masks were chosen on machine ID 04 and locked before prediction on ID 06. Type-specific requirements can fail even when a pooled score improves.','MSmall'),p(html.escape(baseline)),PageBreak()]
    story += [p('Every comparator, under the same rules','MTitle'),p('The nominal objective protects pooled and per-type balanced accuracy. Noise-aware selection adds each type-by-noise cell. Class robustness also protects normal and abnormal recall in every such cell. Erasure objectives test every allowed surviving panel against the intact full-array thresholds.','MBody')]
    headers=['Requirement','Method','Microphones','Mics','Confirm. BA','Contract']
    rows=[[p(v,'MCell') for v in headers]]+[[p(html.escape(v),'MCell') for v in row] for row in table_rows(snapshot,results)]
    table=Table(rows,colWidths=[43*mm,24*mm,36*mm,11*mm,27*mm,23*mm],repeatRows=1)
    table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#edf4f6')),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),('LINEBELOW',(0,0),(-1,-1),.25,colors.HexColor('#d7e2e7')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#fbfcfd')])]))
    story += [table,Spacer(1,12),p('An asterisk marks a greedy terminal mask that failed selection. Pass/fail applies to the same objective on the protected confirmation table. It is a descriptive finite-panel result, not a population noninferiority claim. No channel selection is changed after confirmation. Equal-cost microphones are a declared proxy; physical price, energy and latency have not been measured.','MSmall'),p('The sample granularity matters','MHead'),p('Each type-by-noise cell has sixteen normal and sixteen abnormal examples. One additional mistake changes balanced accuracy by 3.125 percentage points and class recall by 6.25 points. A two-point cell margin therefore permits no additional error. Relative preservation is also separate from an absolute recall floor: matching a weak full-array reference is not sufficient fault detection.'),PageBreak()]
    story += [p('The useful channels depend on context','MTitle'),plot_image('mimii_panel_singletons.png',126),p('All singleton controls were declared in advance. Mic 1 is the representative baseline. Reporting all controls prevents a favorable reduced panel from hiding a better simple microphone.','MSmall')]
    rows=[[p(v,'MCell') for v in ['Protected type','Full array BA','Nominal BA','Normal recall','Abnormal recall']]]
    for t in protocol['machine_types']:
        z=results['panels']['nominal_exact']['by_machine_type'][t];f=results['panels']['full']['by_machine_type'][t]
        rows.append([p(v,'MCell') for v in [t.capitalize(),percent(f['balanced_accuracy']),percent(z['balanced_accuracy']),percent(z['class_recall'][0]),percent(z['class_recall'][1])]])
    t=Table(rows,colWidths=[35*mm]*5);t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#edf4f6')),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8),('LINEBELOW',(0,0),(-1,-1),.25,colors.HexColor('#d7e2e7'))]))
    story += [t,Spacer(1,14),p('The nominal-panel class recalls remain visible even when an aggregate accuracy looks favorable. These numbers describe one protected machine per type, with all noise mixtures grouped by stem.','MSmall'),PageBreak()]
    story += [p('Channels contribute different information','MTitle'),plot_image('mimii_panel_removals.png',96),p('Positive values are balanced-accuracy points lost when removing a microphone from the full array; negative values mean removal improves this fixed classifier. SNR labels identify nominal archive mixture conditions, not measured per-recording ratios.','MSmall'),plot_image('mimii_panel_aliases.png',83),p(html.escape(alias)),p('Equal complete selection traces are empirical aliases. A split on confirmation does not establish acoustic equality or physical nonidentifiability.','MSmall'),PageBreak()]
    story += [p('The cost of surviving missing channels','MTitle'),plot_image('mimii_panel_frontier.png',94),p('The frontier is selected entirely from development data. No panel means all 255 nonempty possibilities fail the stated requirement. Costs cannot fall when an erasure requirement becomes stronger.','MSmall'),plot_image('mimii_panel_erasures.png',118),p('The confirmation curve uses the worst survivor after at most the specified number of lost channels. An empty survivor has no diagnostic input. This is a descriptive stress test, not a hardware failure-rate estimate.','MSmall'),PageBreak()]
    story += [p('What is certified - and what is measured','MTitle'),p('A complete finite optimization certificate','MHead'),p('Every nonempty subset of eight microphones has one mask in 1 through 255. Given the saved numerical predictions, class recall and balanced accuracy are rational counts. Checking every mask and ordering feasible panels by channel count, then integer mask, proves the stated finite optimum or infeasibility. It does not prove that this empirical table represents every physical operating condition.'),p('Erasures are a different question from multicover','MHead'),p('The fused nearest-reference classifier can get worse after adding a channel. Its erasure certificate therefore checks every survivor explicitly. The existing Singularity robust-coverage engine is reused separately for per-channel separation of empirical normal/abnormal descriptor boxes. The multicover theorem applies to that fixed separation relation. Box overlap means its sufficient certificate fails; it is not proof that physical conditions are indistinguishable. '+html.escape(observability_summary(root))),p('Physical provenance and the protected split','MHead'),p('The official MIMII public 1.0 release supplies ten-second, eight-channel recordings at 16 kHz and sixteen bits. Its -6/0/+6 dB archive labels are nominal mixture conditions based on model-average signal power, not measured per-recording SNR guarantees. The deterministic subset has 512 recording stems and 1,536 noise mixtures across four types and four machine IDs. IDs 00/02 train, 04 selects and 06 confirms. Corresponding stems retain all three noise mixtures together. Hidden factory-noise source identities and temporal sessions are unavailable, so their independence is unverified.'),p('The protocol was externally frozen before signal acquisition in repository commit 30132a5f7e332c832dc7ad471937a97b3483aa6f. Selective ZIP64 retrieval acquired 2,852,963,714 compressed audio bytes and 3,932,282,880 raw WAV bytes. The source manifest preserves original identities, archive offsets, lengths, CRC32 and compressed/raw SHA-256 hashes. Whole-archive MD5 values remain publisher metadata rather than verified checksums of a complete download. A second raw-feature route uses Python WAV decoding and an explicit NumPy FFT/Welch implementation. It verifies all selected members and reproduces all 159,744 descriptors to maximum absolute discrepancy 1.4433e-15, within 2e-11 tolerances.'),p('The paired bootstrap resamples whole stems with every mixture together, stratified by type and class. Its intervals are conditional on four fixed protected machines. They do not estimate uncertainty over new machines. This balanced supervised identity-transfer stress test is distinct from the original normal-only per-ID anomaly benchmark.'),p('Source attribution and reproducibility','MHead'),p('Harsh Purohit and colleagues, Hitachi, Ltd. (2019). MIMII Dataset: Sound Dataset for Malfunctioning Industrial Machine Investigation and Inspection. DOI 10.5281/zenodo.3384388. CC BY-SA 4.0. Official record: https://zenodo.org/records/3384388. Primary paper: https://arxiv.org/html/1909.09347v1. The retained repository package includes protocol, source receipts, features, all-mask predictions, certificates, sensitivity analyses and an independent verifier. The earlier MAFAULDA studies remain unchanged.','MSmall')]
    out=root.parents[2]/'output'/'pdf'/'mimii_array_research.pdf'
    out.parent.mkdir(parents=True,exist_ok=True)
    def footer(canvas,doc):
        canvas.setStrokeColor(colors.HexColor('#d7e2e7'));canvas.line(18*mm,15*mm,192*mm,15*mm)
        canvas.setFont('MimiiSans',7);canvas.setFillColor(slate)
        canvas.drawString(18*mm,11*mm,'Singularity | MIMII array study | finite certificates and physical transfer')
        canvas.drawRightString(192*mm,11*mm,str(doc.page))
    doc=SimpleDocTemplate(str(out),pagesize=A4,rightMargin=18*mm,leftMargin=18*mm,topMargin=17*mm,bottomMargin=22*mm,title='MIMII: complete microphone-array audit',author='Singularity project contributors')
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    return out


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=ROOT)
    args=parser.parse_args();root=args.root.resolve()
    protocol=read(root,'protocol.json');snapshot=read(root,'selection_snapshot.json');results=read(root,'results.json')
    if results['selection_lock_sha256']!=hashlib.sha256((root/'selection_lock.json').read_bytes()).hexdigest():
        raise ValueError('Results selection-lock digest mismatch')
    figures(root,protocol,snapshot,results)
    html_report(root,protocol,snapshot,results)
    out=pdf_report(root,protocol,snapshot,results)
    print(json.dumps({'figures':['mimii_results.png','mimii_controls.png'],'html':str(root/'MIMII_Array_Research.html'),'pdf':str(out)}))


if __name__=='__main__':
    main()
