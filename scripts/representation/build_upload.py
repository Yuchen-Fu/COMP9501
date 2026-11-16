"""Build the self-contained server upload from this repository (stdlib only)."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[2]


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(8 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'AML_EXPLICIT_PAIR_STUDY.zip')
    args = parser.parse_args()
    files = {}
    docs = ROOT / 'docs/portable'
    for path in docs.rglob('*'):
        if path.is_file():
            files[str(path.relative_to(docs))] = path
    for pattern in ('src/representation_*.py', 'src/train.py', 'src/prepare.py', 'scripts/representation/*'):
        for path in ROOT.glob(pattern):
            if path.is_file() and path.name != 'build_upload.py':
                files[str(path.relative_to(ROOT))] = path
    for relative in ('data/hi_small.pt', 'results/representation_followup/protocol.json',
                     'results/representation_followup/planning_power.json'):
        files[relative] = ROOT / relative
    protocol = json.loads(files['results/representation_followup/protocol.json'].read_text())
    if sha(files['data/hi_small.pt']) != protocol['data']['sha256']:
        raise ValueError('Prepared data does not match the frozen protocol')
    required = ['README.md', 'RUN_PROMPT.txt', 'PROTOCOL.md', 'VALIDATION.md', 'DATA_PROVENANCE.md']
    if any(name not in files for name in required):
        raise ValueError('Missing required handoff documentation')
    prefix = 'AML_EXPLICIT_PAIR_STUDY/'
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix('.zip.tmp')
    checksums = []
    with zipfile.ZipFile(temporary, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=4, allowZip64=True) as archive:
        for name, path in sorted(files.items()):
            archive.write(path, prefix + name)
            checksums.append(f'{sha(path)}  {name}')
        archive.writestr(prefix + 'PACKAGE_SHA256SUMS', '\n'.join(checksums) + '\n')
        archive.writestr(prefix + 'PACKAGE_INFO.json', json.dumps({
            'created_utc': datetime.now(timezone.utc).isoformat(), 'n_payload_files': len(files),
            'production_training_started': False, 'data_included': True,
            'note': 'Checksums cover the payload files, excluding these generated package metadata files.'}, indent=2) + '\n')
    with zipfile.ZipFile(temporary) as archive:
        bad = archive.testzip()
        if bad:
            raise ValueError(f'ZIP CRC check failed: {bad}')
    temporary.replace(args.output)
    digest = sha(args.output)
    args.output.with_suffix('.zip.sha256').write_text(f'{digest}  {args.output.name}\n')
    print(json.dumps({'zip': str(args.output), 'bytes': args.output.stat().st_size,
                      'sha256': digest, 'payload_files': len(files), 'crc_check': 'passed'}, indent=2))


if __name__ == '__main__':
    main()
