"""Run the separate 15-run, four-GPU budget protocol with a hard time guard."""
import argparse
import fcntl
import importlib.util
from importlib.metadata import version
import json
import os
from pathlib import Path
import platform
import signal
import subprocess
import sys
import time
import zipfile

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'results/representation_8h'
spec = importlib.util.spec_from_file_location('batch_helpers', Path(__file__).with_name('run_batch.py'))
batch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(batch)
batch.OUTPUT = OUT


def parallel(commands, slots, deadline, jobs, stage, environment):
    """One child per GPU; only the coordinator writes the shared status file."""
    pending, active = list(commands), {}
    next_status = 0.
    try:
        while pending or active:
            if time.monotonic() >= deadline:
                raise TimeoutError('7h45m elapsed: preserving checkpoints; batch is incomplete.')
            for slot in slots:
                if slot in active or not pending:
                    continue
                label, command = pending.pop(0)
                log = (OUT / 'logs' / f'{label}.log').open('a')
                env = dict(environment)
                if slot != 'cpu':
                    env['CUDA_VISIBLE_DEVICES'] = slot
                log.write(f'\n{batch.now()} START {label}; GPU slot {slot}\n')
                log.flush()
                process = subprocess.Popen(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
                active[slot] = (label, process, log)
                print(f'{batch.now()} START {label}; slot {slot}', flush=True)
            for slot, (label, process, log) in list(active.items()):
                code = process.poll()
                if code is None:
                    continue
                log.close()
                del active[slot]
                if code:
                    raise RuntimeError(f'{label} failed ({code}); see {OUT}/logs/{label}.log')
                print(f'{batch.now()} DONE {label}', flush=True)
            if time.monotonic() >= next_status:
                status = batch.current_status(jobs, [v[0] for v in active.values()], stage)
                status['seconds_remaining_in_allocation_guard'] = max(0, deadline-time.monotonic())
                batch.atomic_json(OUT / 'batch_status.json', status)
                print(f"{status['completed']}/{status['required']} complete; stage={stage}", flush=True)
                next_status = time.monotonic()+600
            if pending or active:
                time.sleep(1)
    finally:
        for _, process, _ in active.values():
            process.terminate()
        for _, process, log in active.values():
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            log.close()


def export():
    target = ROOT / 'AML_EXPLICIT_PAIR_8H_RESULTS.zip'
    temporary = target.with_suffix('.zip.tmp')
    checks = []
    with zipfile.ZipFile(temporary, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=4) as archive:
        for path in sorted(OUT.rglob('*')):
            if not path.is_file() or 'checkpoints' in path.parts or 'cache' in path.parts or path.suffix in ('.pt','.tmp','.lock'):
                continue
            relative = str(path.relative_to(ROOT))
            archive.write(path, relative)
            checks.append(f'{batch.sha(path)}  {relative}')
        archive.writestr('RESULTS_SHA256SUMS', '\n'.join(checks)+'\n')
        archive.writestr('README.txt', 'Keep checkpoints on the server in results/representation_8h/runs/checkpoints.\nThis is the separate five-seed budget protocol, not the original ten-seed protocol.\n')
    temporary.replace(target)
    print(f'COMPLETE: {target}', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--device', choices=['cuda','cpu'], default='cuda', help='CPU is for local validation only.')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    protocol = json.loads((OUT/'protocol.json').read_text())
    jobs = list(batch.job_plan(protocol, args.device))
    if args.dry_run:
        for label, command in jobs:
            print(label, ' '.join(command))
        print(f'{len(jobs)} runs; four concurrent GPUs; 20–30 epochs; 7h45m internal guard.')
        return
    if args.device == 'cuda':
        import torch
        if torch.cuda.device_count() != 4:
            raise RuntimeError('This budget protocol requires exactly four allocated GPUs. Do not run on the login node.')
        if len({torch.cuda.get_device_name(i) for i in range(4)}) != 1:
            raise RuntimeError('All four GPUs must be the same model.')
        visible = os.environ.get('CUDA_VISIBLE_DEVICES')
        slots = visible.split(',') if visible else list(map(str, range(4)))
        if len(slots) != 4:
            raise RuntimeError('GPU visibility does not match the four-device allocation.')
    else:
        slots = ['cpu']
    OUT.mkdir(parents=True, exist_ok=True)
    lock = (OUT/'.batch.lock').open('a')
    fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    (OUT/'logs').mkdir(exist_ok=True)
    (OUT/'cache/matplotlib').mkdir(parents=True, exist_ok=True)
    sources = list((ROOT/'src').glob('representation_*.py')) + [ROOT/'src/train.py',Path(__file__),Path(__file__).with_name('run_batch.py'),Path(__file__).with_name('smoke.py')]
    manifest = {'device':args.device, 'protocol_sha256':batch.sha(OUT/'protocol.json'),
                'python_version':platform.python_version(),
                'packages':{p:version(p) for p in ['torch','torch-geometric','pyg-lib','numpy','scipy','scikit-learn','pandas','matplotlib']},
                'sources':{str(p.relative_to(ROOT)):batch.sha(p) for p in sources}}
    path = OUT/'batch_manifest.json'
    if path.exists() and json.loads(path.read_text()) != manifest:
        raise RuntimeError('Protocol, source or environment changed; cannot mix this batch.')
    batch.atomic_json(path,manifest)
    env = os.environ.copy()
    env.update(PYTHONUNBUFFERED='1',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',
               MPLCONFIGDIR=str(OUT/'cache/matplotlib'),CUBLAS_WORKSPACE_CONFIG=':4096:8')
    deadline = time.monotonic()+7.75*3600
    common = ['--data',str(ROOT/protocol['data']['path']),'--protocol',str(OUT/'protocol.json'),'--out',str(OUT)]
    python = sys.executable
    def terminate(_signal, _frame):
        raise TimeoutError('Scheduler termination: checkpoints retained; batch incomplete.')
    signal.signal(signal.SIGTERM,terminate)
    try:
        parallel([('data_diagnostics',[python,'-I',str(ROOT/'src/representation_diagnostics.py'),*common])],slots[:1],deadline,jobs,'preflight',env)
        # Every GPU executes the real sampler and a real-data batch before training.
        smoke = [(f'device_smoke_{i}',[python,'-I',str(ROOT/'scripts/representation/smoke.py'),
                  '--device',args.device,'--threads','2','--data',str(ROOT/protocol['data']['path']),
                  '--out',str(OUT/f'device_smoke_{i}.json')]) for i in range(len(slots))]
        parallel(smoke,slots,deadline,jobs,'preflight',env)
        parallel(jobs,slots,deadline,jobs,'training',env)
        parallel([('analysis',[python,'-I',str(ROOT/'src/representation_analyze.py'),'--runs',str(OUT/'runs'),*common])],slots[:1],deadline,jobs,'analysis',env)
        if json.loads((OUT/'analysis.json').read_text())['status'] != 'complete':
            raise RuntimeError('All15 runs are required before inference.')
        parallel([('probe',[python,'-I',str(ROOT/'src/representation_probe.py'),'--runs',str(OUT/'runs'),
                  '--device',args.device,'--threads','2',*common])],slots[:1],deadline,jobs,'probe',env)
        batch.atomic_json(OUT/'batch_status.json',batch.current_status(jobs,stage='complete'))
        export()
    except BaseException as error:
        status = batch.current_status(jobs,stage='incomplete')
        status['reason'] = str(error)
        batch.atomic_json(OUT/'batch_status.json',status)
        raise


if __name__ == '__main__':
    main()
