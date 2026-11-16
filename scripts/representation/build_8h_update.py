"""Build the small additive update for the already downloaded study package."""
import hashlib
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[2]
files = {name: ROOT/'docs/portable'/name for name in ('README_8H.md','RUN_PROMPT_8H.txt')}
for name in ('scripts/representation/run_8h.py','scripts/representation/submit_8h.slurm',
             'results/representation_8h/protocol.json','results/representation_8h/planning_power.json'):
    files[name] = ROOT/name
destination = ROOT/'downloads/AML_EXPLICIT_PAIR_8H_UPDATE.zip'
checksums = [f'{hashlib.sha256(path.read_bytes()).hexdigest()}  {name}' for name,path in sorted(files.items())]
with zipfile.ZipFile(destination,'w',compression=zipfile.ZIP_DEFLATED) as archive:
    for name,path in sorted(files.items()):
        archive.write(path,name)
    archive.writestr('UPDATE_8H_SHA256SUMS','\n'.join(checksums)+'\n')
with zipfile.ZipFile(destination) as archive:
    assert archive.testzip() is None
digest=hashlib.sha256(destination.read_bytes()).hexdigest()
destination.with_suffix('.zip.sha256').write_text(f'{digest}  {destination.name}\n')
print(destination, destination.stat().st_size, digest)
