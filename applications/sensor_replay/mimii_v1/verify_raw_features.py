#!/usr/bin/env python3
"""Independently replay original MIMII WAVs into the retained feature table.

Uses Python's wave parser and an explicit NumPy FFT Welch calculation. It never
imports the study runner, SciPy's WAV reader or scipy.signal.welch. No selection,
confirmation outcomes or classifier predictions are read or changed. Raw data
must first be acquired with acquire.py; this checker performs no networking.
"""
from __future__ import annotations
import argparse
import datetime
import hashlib
import io
import json
from pathlib import Path
import sys
import time
import wave
import zlib

import numpy as np

ROOT = Path(__file__).resolve().parent


def sha256(value):
    return hashlib.sha256(value).hexdigest()


def file_hash(path):
    return sha256(Path(path).read_bytes())


def independent_features(samples, protocol):
    """Whole-recording descriptors plus explicitly constructed Welch PSD.

    A periodic Hann window of length L is w[n]=(1-cos(2*pi*n/L))/2.
    Complete frames start 0, hop, 2*hop,...; each frame is detrended separately.
    The one-sided density is |rFFT(w*frame)|^2/(fs*sum(w^2)), doubled at strictly
    positive frequencies except Nyquist, and averaged over frames. No padding,
    periodic record extension or partial final frame is used.
    """
    spec = protocol['features']
    if spec['window'] != 'hann' or spec['detrend'] != 'constant':
        raise ValueError('This independent verifier implements only the frozen Hann/constant specification')
    fs = int(protocol['sample_rate_hz'])
    length = int(spec['nperseg'])
    hop = length - int(spec['noverlap'])
    if length % 2 or hop <= 0 or length > len(samples):
        raise ValueError('Unsupported FFT frame specification')
    x = np.asarray(samples, dtype=np.float64) / 32768.0
    x = x - np.sum(x, axis=0) / len(x)
    second = np.sum(x*x, axis=0) / len(x)
    rms = np.sqrt(second)
    absolute = np.sum(np.abs(x), axis=0) / len(x)
    floor = float(spec['log_floor'])
    kurtosis = (np.sum(x**4, axis=0)/len(x)) / np.maximum(rms**4, floor)
    crest = np.max(np.abs(x), axis=0) / np.maximum(rms, floor)
    crossings = np.count_nonzero(x[1:]*x[:-1] < 0, axis=0) / (len(x)-1)
    window = (1-np.cos(2*np.pi*np.arange(length, dtype=np.float64)/length))/2
    accumulator = np.zeros((length//2+1, x.shape[1]), dtype=np.float64)
    frame_count = 0
    for start in range(0, len(x)-length+1, hop):
        frame = x[start:start+length]
        detrended = frame - np.sum(frame, axis=0)/length
        transform = np.fft.rfft(detrended*window[:, None], axis=0)
        accumulator += transform.real**2 + transform.imag**2
        frame_count += 1
    power = accumulator / (frame_count*fs*np.sum(window*window))
    power[1:-1] *= 2
    frequencies = np.arange(length//2+1, dtype=np.float64) * (fs/length)
    centroid = np.sum(frequencies[:, None]*power, axis=0)/np.maximum(np.sum(power, axis=0), floor)/(fs/2)
    descriptors = np.stack([np.log10(np.maximum(rms, floor)),
                            np.log10(np.maximum(absolute, floor)), kurtosis, crest, crossings, centroid], axis=1)
    bands = []
    for lower, upper in spec['bands_hz']:
        included = (frequencies >= lower) & (frequencies < upper)
        energy = np.sum(power[included], axis=0)*(fs/length)
        bands.append(np.log10(np.maximum(energy, floor)))
    return np.column_stack([descriptors, np.asarray(bands).T]), frame_count


def locate_raw(row, data_root):
    candidates = [Path(row['raw_path'])]
    if 'wav_path' in row:
        candidates.append(data_root/row['wav_path'])
    for path in candidates:
        if path.is_file():
            return path
    raise FileNotFoundError(f"Original WAV is absent for {row['archive']}:{row['name']}. "
                            'Run acquire.py with the frozen source manifest before raw verification.')


def verify(root, limit=None, data_root=None):
    root = Path(root).resolve()
    data_root = Path(data_root).resolve() if data_root else root.parent/'mimii_data'
    protocol_path = root/'protocol.json'
    receipts_path = root/'source_receipts.json'
    features_path = root/'features.npz'
    provenance_path = root/'feature_provenance.json'
    protocol = json.loads(protocol_path.read_text())
    freeze = json.loads((root/'freeze_receipt.json').read_text())
    if freeze['protocol_sha256'] != file_hash(protocol_path):
        raise ValueError('Frozen protocol digest mismatch')
    receipts = json.loads(receipts_path.read_text())
    if receipts['protocol_sha256'] != file_hash(protocol_path):
        raise ValueError('Acquisition receipt protocol digest mismatch')
    provenance = json.loads(provenance_path.read_text())
    if provenance['features_sha256'] != file_hash(features_path):
        raise ValueError('Feature-table digest mismatch')
    if provenance['acquisition_manifest_sha256'] != file_hash(receipts_path):
        raise ValueError('Feature provenance source-receipt digest mismatch')
    records = receipts['records']
    identities = provenance['identities']
    arrays = np.load(features_path, allow_pickle=False)
    expected_shape = (len(records), len(protocol['channels']), protocol['features']['dimension_per_channel'])
    if arrays['X'].shape != expected_shape or len(identities) != len(records):
        raise ValueError('Source, provenance and feature dimensions disagree')
    if limit is not None and limit < 1:
        raise ValueError('--limit must be positive')
    count = min(limit, len(records)) if limit is not None else len(records)
    atol = rtol = 2e-11
    max_abs = 0.0
    max_relative = 0.0
    per_descriptor = np.zeros(expected_shape[-1], dtype=np.float64)
    compressed_checked = 0
    compressed_absent = 0
    raw_bytes = compressed_bytes = 0
    rows_checked = []
    start = time.perf_counter()
    for index, row in enumerate(records[:count]):
        identity = identities[index]
        mid = str(row['id']).zfill(2)
        group = '|'.join([row['machine_type'], mid, row['state'], row['stem']])
        comparisons = {'machine_type':row['machine_type'], 'machine_id':mid, 'state':row['state'],
                       'stem':row['stem'], 'group':group, 'name':row['name'],
                       'snr_db':int(row['snr_db']), 'y':int(row['state']=='abnormal')}
        for key, expected in comparisons.items():
            if arrays[key][index].item() != expected or identity[key] != expected:
                raise ValueError(f'Feature row {index} lost source identity {key}')
        raw_path = locate_raw(row, data_root)
        raw = raw_path.read_bytes()
        raw_digest = sha256(raw)
        if raw_digest != row['raw_sha256'] or raw_digest != identity['raw_sha256']:
            raise ValueError(f'Original WAV SHA256 mismatch at row {index}')
        if len(raw) != int(row['size']) or zlib.crc32(raw) != int(row['crc32']):
            raise ValueError(f'Original WAV size/ZIP CRC mismatch at row {index}')
        raw_bytes += len(raw)
        compressed_path = data_root/row['compressed_path']
        if compressed_path.is_file():
            compressed = compressed_path.read_bytes()
            if len(compressed) != int(row['compressed']) or sha256(compressed) != row['compressed_sha256']:
                raise ValueError(f'Compressed member size/SHA256 mismatch at row {index}')
            if int(row['compression']) == 8:
                inflated = zlib.decompress(compressed, -15)
            elif int(row['compression']) == 0:
                inflated = compressed
            else:
                raise ValueError('Unsupported original ZIP compression')
            if inflated != raw:
                raise ValueError(f'Compressed member does not reconstruct the retained WAV at row {index}')
            compressed_checked += 1
            compressed_bytes += len(compressed)
        else:
            compressed_absent += 1
        with wave.open(io.BytesIO(raw), 'rb') as wav:
            observed = (wav.getnchannels(), wav.getframerate(), wav.getsampwidth(), wav.getnframes(), wav.getcomptype())
            wanted = (len(protocol['channels']), int(protocol['sample_rate_hz']), int(protocol['sample_width_bytes']),
                      int(protocol['samples_per_recording']), 'NONE')
            if observed != wanted:
                raise ValueError(f'Original WAV format mismatch at row {index}: {observed}')
            pcm = wav.readframes(wav.getnframes())
        if len(pcm) != wanted[0]*wanted[2]*wanted[3]:
            raise ValueError('Truncated original PCM payload')
        samples = np.frombuffer(pcm, dtype='<i2').reshape(wanted[3], wanted[0])
        rebuilt, frames = independent_features(samples, protocol)
        target = arrays['X'][index]
        error = np.abs(rebuilt-target)
        if not np.isfinite(rebuilt).all() or not np.allclose(rebuilt, target, rtol=rtol, atol=atol):
            location = np.unravel_index(np.argmax(error), error.shape)
            raise ValueError(f'Raw feature replay failed at row {index}, channel/descriptor {location}: '
                             f'{rebuilt[location]} vs {target[location]}, difference {error[location]}')
        max_abs = max(max_abs, float(np.max(error)))
        max_relative = max(max_relative, float(np.max(error/np.maximum(np.abs(target), atol))))
        per_descriptor = np.maximum(per_descriptor, np.max(error, axis=0))
        rows_checked.append({'row':index, 'archive':row['archive'], 'name':row['name'],
                             'raw_sha256':raw_digest, 'welch_frames':frames})
        if (index+1)%64 == 0 or index+1 == count:
            print(f'independent raw feature replay {index+1}/{count}', flush=True)
    result = {
        'schema':'singularity.mimii-independent-raw-feature-verification/1',
        'status':'passed', 'complete_frozen_subset':count==len(records),
        'records_checked':count, 'records_in_frozen_subset':len(records),
        'features_per_recording':list(expected_shape[1:]), 'raw_bytes_verified':raw_bytes,
        'compressed_members_verified':compressed_checked, 'compressed_members_absent':compressed_absent,
        'compressed_bytes_verified':compressed_bytes, 'maximum_absolute_feature_difference':max_abs,
        'maximum_relative_feature_difference_with_absolute_floor':max_relative,
        'maximum_absolute_difference_by_descriptor':per_descriptor.tolist(),
        'comparison_tolerance':{'absolute':atol,'relative':rtol},
        'method':'Python wave PCM parser; explicit periodic Hann, framewise constant detrending, NumPy rFFT one-sided density, complete-frame arithmetic mean. No study-runner or SciPy reader/PSD import.',
        'protocol_sha256':file_hash(protocol_path), 'source_receipts_sha256':file_hash(receipts_path),
        'features_sha256':file_hash(features_path), 'feature_provenance_sha256':file_hash(provenance_path),
        'checker_sha256':file_hash(__file__), 'software':{'python':sys.version.split()[0],'numpy':np.__version__},
        'verified_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'seconds':time.perf_counter()-start, 'verified_recordings':rows_checked,
        'boundary':'Numerical agreement within declared tolerance independently replays the frozen descriptors. This is not a proof-assistant theorem, an independent physical acquisition, or a physical generalization test.'}
    name = 'raw_feature_verification.json' if limit is None else 'raw_feature_verification_partial.json'
    (root/name).write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False)+'\n')
    print(json.dumps({key:result[key] for key in ['status','records_checked','complete_frozen_subset',
        'maximum_absolute_feature_difference','compressed_members_verified','seconds']},indent=2))
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=ROOT)
    parser.add_argument('--data-root',type=Path,help='Optional location of acquired WAV/deflate cache')
    parser.add_argument('--limit',type=int,help='Only check the first N rows; emits a clearly partial receipt')
    args=parser.parse_args()
    try:
        verify(args.root,args.limit,args.data_root)
    except (FileNotFoundError,ValueError,wave.Error) as error:
        parser.exit(2,str(error)+'\n')


if __name__=='__main__':
    main()
