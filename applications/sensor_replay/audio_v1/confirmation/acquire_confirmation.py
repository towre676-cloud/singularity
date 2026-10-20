import pathlib,json,urllib.request,struct,zlib,hashlib,concurrent.futures,time
ROOT=pathlib.Path(__file__).resolve().parent;DATA=ROOT.parents[1]/'audio_data'
p=json.loads((ROOT/'protocol.json').read_text());records=p['source_member_plan']

def acquire(t):
 dest=DATA/'source_members'/('v2_'+t['state']+'_'+str(t['grid_index'])+'.deflate')
 if dest.exists():comp=dest.read_bytes()
 else:
  lo=t['header'];hi=lo+30+len(t['name'].encode())+4096+t['compressed']
  for trial in range(3):
   try:
    req=urllib.request.Request(t['archive_url'],headers={'Range':f'bytes={lo}-{hi-1}'})
    with urllib.request.urlopen(req,timeout=120) as r:
     assert r.status==206
     block=r.read()
    hdr=struct.unpack('<IHHHHHIIIHH',block[:30]);assert hdr[0]==0x04034b50 and hdr[3]==8
    comp=block[30+hdr[-2]+hdr[-1]:30+hdr[-2]+hdr[-1]+t['compressed']]
    raw=zlib.decompress(comp,-15);assert len(raw)==t['size'] and zlib.crc32(raw)==t['crc32']
    dest.write_bytes(comp);break
   except Exception:
    if trial==2:raise
    time.sleep(1)
 raw=zlib.decompress(comp,-15);assert len(raw)==t['size'] and zlib.crc32(raw)==t['crc32']
 d=dict(t,compressed_path=str(dest.relative_to(DATA)),compressed_sha256=hashlib.sha256(comp).hexdigest(),raw_sha256=hashlib.sha256(raw).hexdigest(),raw_bytes=len(raw))
 print('acquired',t['name'],flush=True);return d
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:recs=list(pool.map(acquire,records))
a={'dataset':'MAFAULDA prospective tie-union confirmation','official_source':p['source_page'],'protocol_sha256':hashlib.sha256((ROOT/'protocol.json').read_bytes()).hexdigest(),'records':recs,'compressed_bytes':sum(r['compressed'] for r in recs)}
(DATA/'acquisition_v2.json').write_text(json.dumps(a,indent=2));print('DONE',len(recs),a['compressed_bytes'])
