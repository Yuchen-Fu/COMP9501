"""Export completed-study reports and metadata without large predictions or checkpoints."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--results', type=Path, default=ROOT/'results/representation_8h')
    parser.add_argument('--output', type=Path, default=ROOT/'AML_EXPLICIT_PAIR_8H_REVIEW.zip')
    args = parser.parse_args()
    if json.loads((args.results/'batch_status.json').read_text())['stage'] != 'complete':
        raise RuntimeError('This review export requires a completed batch.')
    files = [p for p in sorted(args.results.rglob('*')) if p.is_file()
             and not {'predictions','checkpoints','cache','reported','__pycache__'}.intersection(p.relative_to(args.results).parts)
             and p.suffix in {'.json','.md','.txt','.log','.out','.png','.pdf','.svg'}]
    checks = []
    temporary = args.output.with_suffix('.zip.tmp')
    with zipfile.ZipFile(temporary,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for path in files:
            name = 'results/'+args.results.name+'/'+str(path.relative_to(args.results))
            archive.write(path,name)
            checks.append(f'{hashlib.sha256(path.read_bytes()).hexdigest()}  {name}')
        archive.writestr('REVIEW_SHA256SUMS','\n'.join(checks)+'\n')
        archive.writestr('REVIEW_SCOPE.txt',
            'This archive contains reports, plots, run metadata and logs.\n'
            'It deliberately omits transaction-level probability archives and model checkpoints.\n'
            'It supports review of summary consistency and protocol compliance, not independent prediction-level recomputation.\n'
            'Keep the full results archive and checkpoints on the server.\n')
    temporary.replace(args.output)
    print(f'{args.output}: {args.output.stat().st_size/2**20:.2f} MiB; {len(files)} files')


if __name__ == '__main__':
    main()
