#!/usr/bin/env python3
"""Reacquire exact retained MAFAULDA members using official HTTP Range access.
By default downloads <=279,004,318 compressed signal bytes plus small ZIP-header
ranges, then checks each member's size, CRC32 and retained individual SHA-256.
Raw members stay in sibling audio_data, outside the distributable study directory.
"""
import argparse,concurrent.futures,hashlib,json,pathlib,struct,time,urllib.request,zlib
ROOT=pathlib.Path(__file__).resolve().parent;DATA=ROOT.parent/'audio_data'

def acquire(row,verify_cache=False):
 path=DATA/row['compressed_path'];path.parent.mkdir(parents=True,exist_ok=True)
 if path.exists():compressed=path.read_bytes()
 elif verify_cache:raise FileNotFoundError(path)
 else:
  lo=row['header'];end=lo+30+len(row['name'].encode())+4096+row['compressed']
  for attempt in range(3):
   try:
    req=urllib.request.Request(row['archive_url'],headers={'Range':f'bytes={lo}-{end-1}'})
    with urllib.request.urlopen(req,timeout=120) as response:
     if response.status!=206:raise RuntimeError('Official host ignored byte range; refusing full archive')
     block=response.read()
    header=struct.unpack('<IHHHHHIIIHH',block[:30])
    assert header[0]==0x04034b50 and header[3]==8
    start=30+header[-2]+header[-1]
    compressed=block[start:start+row['compressed']]
    assert hashlib.sha256(compressed).hexdigest()==row['compressed_sha256']
    path.write_bytes(compressed);break
   except Exception:
    if attempt==2:raise
    time.sleep(1)
 assert len(compressed)==row['compressed'] and hashlib.sha256(compressed).hexdigest()==row['compressed_sha256']
 raw=zlib.decompress(compressed,-15)
 assert len(raw)==row['raw_bytes']==row['size'] and zlib.crc32(raw)==row['crc32']
 assert hashlib.sha256(raw).hexdigest()==row['raw_sha256']
 print('verified',row['name'],flush=True)
 return len(compressed)

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--phase',choices=['original','confirmation','both'],default='both');parser.add_argument('--verify-cache',action='store_true');args=parser.parse_args()
 manifests=[]
 if args.phase in ['original','both']:manifests.append((ROOT/'source_subset_manifest.json',DATA/'acquisition.json'))
 if args.phase in ['confirmation','both']:manifests.append((ROOT/'confirmation/source_subset_manifest.json',DATA/'acquisition_v2.json'))
 rows=[]
 for src,dest in manifests:rows.extend(json.loads(src.read_text())['records'])
 assert sum(r['compressed'] for r in rows)<=300_000_000
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:total=sum(pool.map(lambda r:acquire(r,args.verify_cache),rows))
 for src,dest in manifests:dest.parent.mkdir(exist_ok=True);dest.write_bytes(src.read_bytes())
 print(json.dumps({'verified_members':len(rows),'compressed_signal_bytes':total,'raw_directory':str(DATA)},indent=2))
