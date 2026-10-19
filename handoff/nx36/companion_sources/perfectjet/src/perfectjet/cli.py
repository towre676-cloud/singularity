"""Reproduce the retained calculations and inspect the equation atlas."""
import argparse,json
from fractions import Fraction
from pathlib import Path
from . import __version__


def encode(value):
    if isinstance(value,Fraction):return str(value)
    raise TypeError(type(value).__name__)


def report():
    from .transvectants import molecular_receipt
    from .rings import core_field_receipt
    from .collision import collision_receipt
    from .psg import flip_root
    from .exact import target_recovery,observable_space
    from .populations import SelectionPopulation
    from .semantics import PartialMachine
    from .polynomial import Poly,feature_closure
    from .dynamics import energy_balance
    from .jets import iterate_defect
    from .lattice import lattice_receipt
    from .realization import realization_receipt
    from .loci import partner_loci
    from .sieve import sieve_receipt
    from .parametric import surface_receipt
    from .strata import strata_receipt
    from .readout import readout_receipt
    from .decisions import decisions_receipt
    from .engine import engine_receipt
    from .invariants import invariants_receipt
    from .quadratic import quadratic_receipt
    from .deformation import deformation_receipt
    from .incidence import incidence_receipt
    p=SelectionPopulation([(2,1),(1,2),(2,2),(0,1)],(3,3),[4,3,5,0])
    machine=PartialMachine([0,0,1,1],[(2,),(3,),(2,),(3,)])
    reduced,mapping,blocks=machine.quotient()
    x=Poly.variable(0,1)
    return {"version":__version__,"molecular":molecular_receipt(),"core_field":core_field_receipt(),
            "collision":collision_receipt(),"PSG":flip_root(),
            "observability":{"hidden":target_recovery([[1,1]],[[1,-1]]),
                             "repaired":target_recovery([[1,1],[1,-1]],[[1,-1]]),
                             "observable_rows":observable_space([[1,0],[0,2]],[[1,0]])},
            "selection":{"count":p.count(),"optimum":p.optimum(),"attribution":p.attribution(),
                         "inclusion":p.inclusion_profile(),
                         "rank_unrank_replay":all(p.rank(p.unrank(i))==i for i in range(p.count()))},
            "SOE":{"blocks":blocks,"mapping":mapping,"reduced_states":len(reduced.observations)},
            "features":{"closed":feature_closure([Poly.constant(1,1),x],[2*x+1]),
                        "unclosed":feature_closure([x],[x*x])},
            "energy":energy_balance([[-1,0],[0,-2]],[[1,0],[0,1]],[1,1],[1,0]),
            "flip_defect":iterate_defect([0,-1,1,2],5),
            "lattice":lattice_receipt(),"realization":realization_receipt(),
            "partner_loci":partner_loci(),"sieve":sieve_receipt(),"partner_surface":surface_receipt(),
            "active_strata":strata_receipt(),"readout":readout_receipt(),"decisions":decisions_receipt(),
            "engine":engine_receipt(),"invariants":invariants_receipt(),"quadratic":quadratic_receipt(),"deformation":deformation_receipt(),"incidence":incidence_receipt(),
            "limitations":"No imported upstream solver or Lean theorem is claimed by this release."}


def main():
    import sys
    if len(sys.argv)>1 and sys.argv[1] in {"lab", "math-lab"}:
        if sys.argv[1]=="lab":
            from .observatory.workbench import main as lab
        else:
            from .mathlab import main as lab
        return lab(sys.argv[2:])
    if len(sys.argv)>1 and sys.argv[1]=="observatory":
        from .observatory.workbench import main as observatory
        return observatory(sys.argv[2:])
    if len(sys.argv)>1 and sys.argv[1]=="observe":
        from .observatory.command import main as observe
        return observe(sys.argv[2:])
    if len(sys.argv)>1 and sys.argv[1]=="math-bridges":
        from .applications.nfl_scouting.bridge_receipt import build_bridge_receipt
        parser=argparse.ArgumentParser(description="Synthetic and exact math-bridge receipts; no NFL gain claim")
        parser.add_argument("--output",type=Path)
        args=parser.parse_args(sys.argv[2:])
        content=json.dumps(build_bridge_receipt(),indent=2,default=encode)+"\n"
        if args.output:
            args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(content)
        else:print(content,end="")
        return
    if len(sys.argv)>1 and sys.argv[1]=="nfl-bridges":
        from .applications.nfl_scouting.bridges import main as bridges
        return bridges(sys.argv[2:])
    if len(sys.argv)>1 and sys.argv[1]=="nfl-burst":
        from .applications.nfl_scouting.burst_transfer import main as burst
        return burst(sys.argv[2:])
    if len(sys.argv)>1 and sys.argv[1]=="nfl":
        from .applications.nfl_scouting.pipeline import main as nfl
        return nfl(sys.argv[2:])
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command",choices=["report","psg","partners","collision","core-field","lattice","realization","loci","surface","strata","readout","decisions","engine","invariants","quadratic","deformation","incidence","sieve","atlas"])
    parser.add_argument("--output",type=Path)
    parser.add_argument("--conductor",type=int,default=7)
    parser.add_argument("--index",type=int,default=10**100)
    args=parser.parse_args()
    if args.command=="report":out=report()
    elif args.command=="psg":
        from .psg import flip_root
        out=flip_root()
    elif args.command=="partners":
        from .transvectants import census
        out=census()
    elif args.command=="collision":
        from .collision import CyclotomicCollision
        c=CyclotomicCollision(args.conductor)
        out={"conductor":args.conductor,"index":str(args.index),"coefficient":c.coefficient(args.index).record()}
    elif args.command=="core-field":
        from .rings import core_field_receipt
        out=core_field_receipt()
    elif args.command=="lattice":
        from .lattice import lattice_receipt
        out=lattice_receipt()
    elif args.command=="realization":
        from .realization import realization_receipt
        out=realization_receipt()
    elif args.command=="loci":
        from .loci import partner_loci
        out=partner_loci()
    elif args.command=="surface":
        from .parametric import surface_receipt
        out=surface_receipt()
    elif args.command=="strata":
        from .strata import strata_receipt
        out=strata_receipt()
    elif args.command=="readout":
        from .readout import readout_receipt
        out=readout_receipt()
    elif args.command=="decisions":
        from .decisions import decisions_receipt
        out=decisions_receipt()
    elif args.command=="engine":
        from .engine import engine_receipt
        out=engine_receipt()
    elif args.command=="invariants":
        from .invariants import invariants_receipt
        out=invariants_receipt()
    elif args.command=="quadratic":
        from .quadratic import quadratic_receipt
        out=quadratic_receipt()
    elif args.command=="incidence":
        from .incidence import incidence_receipt
        out=incidence_receipt()
    elif args.command=="deformation":
        from .deformation import deformation_receipt
        out=deformation_receipt()
    elif args.command=="sieve":
        from .sieve import sieve_receipt
        out=sieve_receipt()
    else:
        root=Path(__file__).resolve().parents[2]
        atlas=root/"data"/"equations.json"
        if not atlas.exists():parser.error("atlas data is available in the repository checkout")
        out=json.loads(atlas.read_text())
    content=json.dumps(out,indent=2,default=encode)+"\n"
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(content)
    else:print(content,end="")


if __name__=="__main__":main()
