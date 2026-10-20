#!/usr/bin/env python3
"""Bounded selective retrieval from the author's original MIMII ZIP archives.

The HTTP range adapter is deliberately strict: an ignored, malformed, oversized,
or shifted range is never accepted as a member. ZIP64 central directories are
handled by Python's zipfile module. Raw data remain in ignored ../mimii_data.
"""
from __future__ import annotations
import argparse, concurrent.futures, datetime, hashlib, io, json, pathlib, re, email.utils, gzip
import struct, time, urllib.error, urllib.request, wave, zipfile, zlib, threading, collections, http.client
ROOT=pathlib.Path(__file__).resolve().parent
DATA=ROOT.parent/'mimii_data'
RECORD_URL='https://zenodo.org/api/records/3384388'
MAX_RANGE=8_000_000
_RATE_LOCK=threading.Lock()
_REQUEST_TIMES=collections.deque()

def rate_limit():
    # Bound all attempted HTTP ranges, including retries, below publisher quota.
    while True:
        with _RATE_LOCK:
            t=time.monotonic()
            while _REQUEST_TIMES and _REQUEST_TIMES[0]<t-60:_REQUEST_TIMES.popleft()
            if len(_REQUEST_TIMES)<100:
                _REQUEST_TIMES.append(t);return
            delay=60- (t-_REQUEST_TIMES[0])+0.01
        time.sleep(min(60,max(0.01,delay)))

def atomic_bytes(path,raw):
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_name(path.name+'.'+str(time.monotonic_ns())+'.tmp')
    temp.write_bytes(raw);temp.replace(path)

def sha256(data):return hashlib.sha256(data).hexdigest()
def dump(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,sort_keys=True,indent=2)+'\n')
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()

def index_bytes():
    path=ROOT/'central_indexes.json'
    return path.read_bytes() if path.exists() else gzip.decompress((ROOT/'central_indexes.json.gz').read_bytes())

def get_json(url):
    with urllib.request.urlopen(url,timeout=60) as r:
        raw=r.read(1_000_001)
    if len(raw)>1_000_000:raise ValueError('Metadata size budget exceeded')
    return json.loads(raw)

def ranged(url,lo,hi,total,attempts=4):
    """Read inclusive byte range; refuse full responses before consuming a body."""
    if not (0<=lo<=hi<total) or hi-lo+1>MAX_RANGE:raise ValueError('Invalid/budgeted range')
    n=hi-lo+1
    for attempt in range(attempts):
        try:
            rate_limit()
            req=urllib.request.Request(url,headers={'Range':f'bytes={lo}-{hi}','Accept-Encoding':'identity'})
            with urllib.request.urlopen(req,timeout=120) as r:
                expected=f'bytes {lo}-{hi}/{total}'
                if r.status!=206 or r.headers.get('Content-Range')!=expected:
                    raise ValueError(f'Host did not return requested range: {r.status}, {r.headers.get("Content-Range")}')
                if int(r.headers.get('Content-Length',n))!=n:raise ValueError('Range Content-Length mismatch')
                raw=r.read(n+1)
                if len(raw)<n:raise ConnectionError(f'Short HTTP range body: expected {n}, received {len(raw)} bytes')
                if len(raw)>n:raise ValueError('Oversized HTTP range body')
                return raw
        except (urllib.error.HTTPError,urllib.error.URLError,TimeoutError,ConnectionError,http.client.IncompleteRead) as e:
            if attempt==attempts-1:raise
            value=getattr(e,'headers',{}).get('Retry-After','2') if getattr(e,'headers',None) else '2'
            try:pause=max(1,float(value))
            except ValueError:
                when=email.utils.parsedate_to_datetime(value)
                pause=max(1,(when-datetime.datetime.now(datetime.timezone.utc)).total_seconds())
            deadline=time.monotonic()+pause
            while time.monotonic()<deadline:time.sleep(min(60,max(0.01,deadline-time.monotonic())))
    raise RuntimeError('unreachable')

class RangeArchive(io.RawIOBase):
    """Seekable bounded adapter used only to read ZIP metadata."""
    def __init__(self,url,size,budget=16_000_000):
        self.url=url;self.size=size;self.pos=0;self.budget=budget;self.bytes_read=0;self.requests=[]
    def readable(self):return True
    def seekable(self):return True
    def tell(self):return self.pos
    def seek(self,offset,whence=0):
        p=offset if whence==0 else self.pos+offset if whence==1 else self.size+offset
        if p<0:raise ValueError('Negative seek')
        self.pos=p;return p
    def read(self,n=-1):
        n=self.size-self.pos if n is None or n<0 else min(n,self.size-self.pos)
        if n<=0:return b''
        if n>MAX_RANGE or self.bytes_read+n>self.budget:raise ValueError('Central directory byte budget exceeded')
        lo=self.pos;raw=ranged(self.url,lo,lo+n-1,self.size)
        self.pos+=n;self.bytes_read+=n
        self.requests.append({'start':lo,'end':lo+n-1,'bytes':n,'sha256':sha256(raw)})
        return raw

def index_archives(record,archive_names):
    files={r['key']:r for r in record['files']};indexes=[]
    for name in archive_names:
        f=files[name];url=f'https://zenodo.org/records/3384388/files/{name}?download=1'
        a=RangeArchive(url,f['size'])
        with zipfile.ZipFile(a) as z:
            entries=[{'name':i.filename,'compressed':i.compress_size,'size':i.file_size,
                      'crc32':i.CRC,'header':i.header_offset,'compression':i.compress_type,
                      'flags':i.flag_bits} for i in z.infolist()]
        info={'archive':name,'archive_url':url,'archive_bytes':f['size'],
              'publisher_checksum':f['checksum'],'full_archive_checksum_verified':False,'members':entries,
              'index_bytes_fetched':a.bytes_read,'range_receipts':a.requests}
        indexes.append(info)
        print(json.dumps({'archive':name,'members':len(entries),'bytes':a.bytes_read,
                          'first':[r['name'] for r in entries[:10]]}),flush=True)
    return {'schema':'singularity.mimii-archive-index/1','acquired_utc':now(),
            'source_record':RECORD_URL,'archives':indexes}

def acquire_one(row,verify_cache=False):
    """Fetch one frozen member, verify ZIP metadata/CRC and hash compressed+WAV."""
    if not re.fullmatch(r'(?:-6|0|6)_dB_(?:fan|pump|slider|valve)\.zip',row['archive']):raise ValueError('Not an original MIMII archive identity')
    expected_url=f"https://zenodo.org/records/3384388/files/{row['archive']}?download=1"
    if row['archive_url']!=expected_url:raise ValueError('Not the frozen official archive URL')
    key=sha256((row['archive']+'\0'+row['name']).encode())
    dst=DATA/'compressed'/f'{key}.deflate';rawdst=DATA/'wav'/row['archive'].replace('.zip','')/row['name']
    if '..' in pathlib.PurePosixPath(row['name']).parts or row['name'].startswith('/'):
        raise ValueError('Unsafe archive path')
    if dst.exists():compressed=dst.read_bytes()
    elif verify_cache:raise FileNotFoundError(dst)
    else:
        lo=row['header'];total=row['archive_bytes'];url=row['archive_url']
        # One bounded request includes the local header, name, extra, and body.
        # The central directory fixes compressed length; allow <=4KiB ZIP extras.
        hi=min(total-1,lo+30+len(row['name'].encode('utf8'))+4096+row['compressed']-1)
        block=ranged(url,lo,hi,total)
        h=struct.unpack('<IHHHHHIIIHH',block[:30])
        if h[0]!=0x04034b50 or h[3]!=row['compression']:raise ValueError('Local ZIP header mismatch')
        start=30+h[-2]+h[-1]
        if start+row['compressed']>len(block):raise ValueError('Local extra field exceeds declared budget')
        name=block[30:30+h[-2]].decode('utf8' if h[2]&0x800 else 'cp437')
        if name!=row['name']:raise ValueError('Local ZIP member identity mismatch')
        compressed=block[start:start+row['compressed']]
        atomic_bytes(dst,compressed)
    if len(compressed)!=row['compressed']:raise ValueError('Compressed member size mismatch')
    if row['compression']==8:raw=zlib.decompress(compressed,-15)
    elif row['compression']==0:raw=compressed
    else:raise ValueError('Unsupported ZIP compression')
    if len(raw)!=row['size'] or zlib.crc32(raw)!=row['crc32']:raise ValueError('Member size/CRC mismatch')
    for field,value in [('raw_sha256',sha256(raw)),('compressed_sha256',sha256(compressed))]:
        if field in row and row[field]!=value:raise ValueError(field+' mismatch')
    with wave.open(io.BytesIO(raw)) as w:
        wav={'channels':w.getnchannels(),'sample_rate_hz':w.getframerate(),
             'sample_width_bytes':w.getsampwidth(),'frames':w.getnframes(),
             'compression':w.getcomptype()}
    if wav!={'channels':8,'sample_rate_hz':16000,'sample_width_bytes':2,'frames':160000,'compression':'NONE'}:
        raise ValueError(f'Unexpected original MIMII WAV format: {wav}')
    if verify_cache:
        if not rawdst.exists() or rawdst.read_bytes()!=raw:raise ValueError('Cached WAV differs from verified compressed member')
    else:atomic_bytes(rawdst,raw)
    return dict(row,raw_sha256=sha256(raw),compressed_sha256=sha256(compressed),
                compressed_path=str(dst.relative_to(DATA)),wav_path=str(rawdst.relative_to(DATA)),raw_path=str(rawdst),wav_format=wav)

def acquire_manifest(path,workers=3,verify_cache=False,reacquire=False):
    manifest=json.loads(path.read_text());rows=manifest['records']
    if verify_cache and reacquire:raise ValueError('Choose either --verify-cache or --reacquire')
    if reacquire and any('raw_sha256' not in r or 'compressed_sha256' not in r for r in rows):raise ValueError('--reacquire requires retained source receipts with member hashes')
    if sha256((ROOT/'protocol.json').read_bytes())!=manifest['protocol_sha256']:raise ValueError('Manifest protocol hash mismatch')
    retained=ROOT/'source_receipts.json'
    if retained.exists() and not verify_cache and not reacquire:raise FileExistsError('Retained source receipts exist; use --reacquire or --verify-cache')
    if verify_cache and retained.exists():
        prior=json.loads(retained.read_text())
        if path.resolve()!=retained.resolve() and prior.get('selected_source_manifest_sha256')!=sha256(path.read_bytes()):raise ValueError('Retained receipts are for a different manifest')
        if [(r['archive'],r['name']) for r in rows]!=[(r['archive'],r['name']) for r in prior['records']]:raise ValueError('Retained member identities differ')
        rows=prior['records']
    if sum(r['size'] for r in rows)>manifest.get('uncompressed_budget_bytes',4_100_000_000):raise ValueError('Raw member budget exceeded')
    total=sum(r['compressed']+4200 for r in rows)
    budget=manifest.get('compressed_transfer_budget_bytes',1_500_000_000)
    if total>budget:raise ValueError(f'Member transfer budget exceeded: {total}>{budget}')
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        records=[]
        for result in pool.map(lambda r:acquire_one(r,verify_cache),rows):
            records.append(result)
            if len(records)%16==0:
                print(json.dumps({'verified_members':len(records),'of':len(rows)}),flush=True)
                if not verify_cache and not reacquire:dump(DATA/'acquisition_progress.json',{'records':records,'source_manifest_sha256':sha256(path.read_bytes())})
    out=dict(manifest,records=records,verified_utc=now(),
             compressed_member_bytes=sum(r['compressed'] for r in rows),
             selected_source_manifest_sha256=sha256(path.read_bytes()))
    if not verify_cache and not reacquire:
        destination=ROOT/'source_receipts.json'
        if destination.exists():raise FileExistsError('Refusing to overwrite retained source receipts; use --verify-cache')
        dump(destination,out)
    print(json.dumps({'verified_members':len(records),'compressed_member_bytes':out['compressed_member_bytes']}),flush=True)

def select_plan(protocol_path):
    """Hash-select common recording stems across SNRs without reading signals."""
    if (ROOT/'source_subset_manifest.json').exists():raise FileExistsError('Refusing to overwrite frozen source subset manifest')
    protocol=json.loads(protocol_path.read_text())
    raw_index=index_bytes()
    index=json.loads(raw_index)
    archives={a['archive']:a for a in index['archives']}
    records=[];groups=[]
    count=protocol.get('stems_per_class_id',16)
    for typ in ['fan','pump','slider','valve']:
        for machine_id in ['00','02','04','06']:
            for state in ['normal','abnormal']:
                prefix=f'{typ}/id_{machine_id}/{state}/'
                by_snr={snr:{r['name']:r for r in archives[f'{snr}_dB_{typ}.zip']['members']
                              if r['name'].startswith(prefix) and r['name'].endswith('.wav')}
                        for snr in ['-6','0','6']}
                common=set.intersection(*(set(v) for v in by_snr.values()))
                if len(common)<count:raise ValueError(f'Not enough common source stems: {typ}/{machine_id}/{state}')
                def rank(name):
                    ns=protocol['selection_namespace']
                    return (sha256(f'{ns}|{typ}|{machine_id}|{state}|{pathlib.PurePosixPath(name).name}'.encode()),name)
                chosen=sorted(common,key=rank)[:count]
                for name in chosen:
                    group_id=f'{typ}|{machine_id}|{state}|{pathlib.PurePosixPath(name).name}'
                    groups.append({'recording_group':group_id,'type':typ,'machine_id':machine_id,'state':state,
                                   'common_stems_available':len(common),'rank_sha256':rank(name)[0]})
                    for snr in ['-6','0','6']:
                        a=archives[f'{snr}_dB_{typ}.zip'];r=by_snr[snr][name]
                        records.append(dict(r,archive=a['archive'],archive_url=a['archive_url'],archive_bytes=a['archive_bytes'],full_archive_checksum_verified=False,
                                            publisher_checksum=a['publisher_checksum'],type=typ,machine_id=machine_id,
                                            state=state,snr_db=int(snr),recording_group=group_id,machine_type=typ,id=machine_id,stem=pathlib.PurePosixPath(name).name))
    plan={'schema':'singularity.mimii-subset-plan/1','created_utc':now(),
          'protocol_sha256':sha256(protocol_path.read_bytes()),
          'central_indexes_sha256':sha256(raw_index),
          'selection_rule':protocol['member_sampling'],
          'compressed_transfer_budget_bytes':protocol['maximum_signal_compressed_bytes'],
          'uncompressed_budget_bytes':protocol['maximum_uncompressed_bytes'],'groups':groups,'records':records}
    if sum(r['compressed']+4200 for r in records)>plan['compressed_transfer_budget_bytes']:raise ValueError('Compressed source plan budget exceeded')
    if sum(r['size'] for r in records)>plan['uncompressed_budget_bytes']:raise ValueError('Raw source plan budget exceeded')
    dump(ROOT/'source_subset_manifest.json',plan)
    print(json.dumps({'selected_groups':len(groups),'members':len(records),'compressed_bytes':sum(r['compressed'] for r in records)}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--index',action='store_true');p.add_argument('--archives',nargs='+',default=[f'{snr}_dB_{typ}.zip' for typ in ['fan','pump','slider','valve'] for snr in ['-6','0','6']])
    p.add_argument('--select',type=pathlib.Path,help='Frozen protocol selecting source names, no WAV data');p.add_argument('--manifest',type=pathlib.Path);p.add_argument('--verify-cache',action='store_true');p.add_argument('--reacquire',action='store_true',help='Reacquire from retained hashes without changing frozen receipts');p.add_argument('--workers',type=int,default=3);args=p.parse_args()
    if args.index:
        if (ROOT/'central_indexes.json').exists() or (ROOT/'central_indexes.json.gz').exists() or (ROOT/'official_record.json').exists():raise FileExistsError('Refusing to overwrite retained official metadata/indexes')
        record=get_json(RECORD_URL);dump(ROOT/'official_record.json',record)
        dump(ROOT/'central_indexes.json',index_archives(record,args.archives))
    if args.select:select_plan(args.select)
    if args.manifest:acquire_manifest(args.manifest,args.workers,args.verify_cache,args.reacquire)
