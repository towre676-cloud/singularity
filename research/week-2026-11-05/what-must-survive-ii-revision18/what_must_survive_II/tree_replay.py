#!/usr/bin/env python3
"""Portable staging of historical tree scripts; original algorithms remain in src/.
Outputs and compiled binaries go under .tree_work (or --work-dir). No ~/wms needed.
"""
from pathlib import Path
import argparse,os,shutil,subprocess,sys,json,hashlib
PKG=Path(__file__).resolve().parent
DIRS=('cat','tree','mark','spine','ising','rec','root')

def prepare(work):
    work.mkdir(parents=True,exist_ok=True)
    replace=str(work.as_posix()).replace("'","\\'").replace('"','\\"')
    changes=[]
    for group in DIRS:
      for src in sorted((PKG/'src'/group).rglob('*')):
        if src.suffix not in ('.py','.cpp') or not src.is_file():continue
        target=work/src.relative_to(PKG/'src');target.parent.mkdir(parents=True,exist_ok=True)
        old=src.read_text();text=old.replace('/root/wms',replace).replace('~/wms',replace)
        if src.relative_to(PKG/'src').as_posix() in ('ising/mf.py','ising/ms.py'):
            text='import os\n'+text.replace('range(8,31)',"range(8,int(os.environ.get('WMS_MAX_ORDER','30'))+1)")
        if not target.exists() or target.read_text()!=text:target.write_text(text)
        if text!=old:changes.append(str(src.relative_to(PKG)))
    for fixture in (PKG/'data/tree_census').glob('d*.txt'):
        target=work/'spine'/fixture.name
        if not target.exists():shutil.copy2(fixture,target)
    (work/'STAGING.json').write_text(json.dumps({'package':str(PKG),'work':str(work),'source_changes':'author absolute paths replaced; mf/ms gain optional census-order environment bound','changed_paths':changes},indent=2)+'\n')

def build(work,target):
    src=(work/(target+'.cpp')).resolve();dest=(work/target).resolve()
    if not src.is_relative_to(work.resolve()) or not src.is_file():raise SystemExit('Unknown C++ target: '+target)
    digest=hashlib.sha256(src.read_bytes()).hexdigest();stamp=dest.with_suffix('.build-sha256')
    if not dest.exists() or not stamp.exists() or stamp.read_text()!=digest:
        compiler=shutil.which('g++')
        if not compiler:raise SystemExit('g++ with C++17 support is required for this optional legacy target.')
        subprocess.run([compiler,'-O2','-std=c++17',str(src),'-o',str(dest)],check=True)
        stamp.write_text(digest)
    return dest

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--work-dir',type=Path,default=PKG/'.tree_work');sub=ap.add_subparsers(dest='cmd',required=True)
    sub.add_parser('prepare');b=sub.add_parser('build');b.add_argument('target')
    c=sub.add_parser('census');c.add_argument('max_order',type=int)
    r=sub.add_parser('run');r.add_argument('--max-order',type=int);r.add_argument('script');r.add_argument('args',nargs=argparse.REMAINDER)
    args=ap.parse_args();work=args.work_dir.resolve();prepare(work)
    if args.cmd=='build':print(build(work,args.target))
    elif args.cmd=='census':
        exe=build(work,'spine/cc');env=dict(os.environ,DUMP='1')
        for n in range(8,args.max_order+1):
            with (work/'spine'/f'd{n}.txt').open('w') as f:subprocess.run([str(exe),str(n)],stdout=f,check=True,env=env,cwd=work/'spine')
            print('census',n,'written',flush=True)
    elif args.cmd=='run':
        script=(work/args.script).resolve()
        if not script.is_relative_to(work) or not script.is_file():raise SystemExit('Unknown historical script.')
        env=dict(os.environ)
        if args.max_order is not None:env['WMS_MAX_ORDER']=str(args.max_order)
        subprocess.run([sys.executable,str(script),*args.args],cwd=script.parent,env=env,check=True)
    else:print('Prepared',work)
if __name__=='__main__':main()
