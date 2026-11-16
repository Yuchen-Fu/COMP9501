"""Run the frozen 25-job study sequentially, then audit, probe and export results.

Run this script inside a scheduler allocation or a persistent terminal on a compute
node. Repeating the same command resumes epoch checkpoints. It never silently
changes the device, batch size, seeds, hyperparameters or failed job.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
from importlib.metadata import version
import json
import os
from pathlib import Path
import platform
import shlex
import subprocess
import sys
import time
import zipfile

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "results/representation_followup"


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def atomic_json(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    temporary.replace(path)


def job_plan(protocol, device):
    python = sys.executable
    common = ["--device", device, "--protocol", str(OUTPUT / "protocol.json"),
              "--data", str(ROOT / protocol["data"]["path"]), "--out", str(OUTPUT / "runs")]
    for key in ("max_epochs", "min_epochs", "patience", "min_delta", "threads"):
        common += ["--" + key.replace("_", "-"), str(protocol["training"][key])]
    seeds_by_cell = protocol["analysis"]["seeds_by_cell"]
    # Interleave arms within seed blocks; selection and budget do not depend on outcomes.
    for seed in sorted(set().union(*(set(v) for v in seeds_by_cell.values()))):
        for cell in protocol["analysis"]["cells"]:
            if seed in seeds_by_cell[cell]:
                yield f"{cell}_s{seed}", [python, "-I", str(ROOT / "src/representation_train.py"),
                                         "--cell", cell, "--seed", str(seed), *common]


def current_status(jobs, active=None, stage="training"):
    completed, epochs, seconds = [], 0, []
    for tag, _ in jobs:
        path = OUTPUT / "runs" / f"{tag}.json"
        progress = OUTPUT / "runs" / f"{tag}.progress.json"
        if path.exists():
            record = json.loads(path.read_text())
            if record.get("status") == "complete":
                completed.append(tag)
        elif progress.exists():
            record = json.loads(progress.read_text())
        else:
            continue
        epochs += record.get("epochs_completed", 0)
        seconds.extend(x["sec"] for x in record.get("history", []) if x.get("sec", 0) > 0)
    return {"updated_utc": now(), "stage": stage, "active": active,
            "completed": len(completed), "required": len(jobs), "completed_jobs": completed,
            "epochs_completed": epochs,
            "mean_epoch_seconds_observed": sum(seconds) / len(seconds) if seconds else None,
            "note": "Stopping depends only on validation; a finish time is not fixed in advance."}


def run_command(command, label, jobs, stage):
    log_path = OUTPUT / "logs" / f"{label}.log"
    print(f"[{now()}] START {label}; log: {log_path.relative_to(ROOT)}", flush=True)
    env = os.environ.copy()
    env.update(PYTHONUNBUFFERED="1", OMP_NUM_THREADS="2", MKL_NUM_THREADS="2",
               OPENBLAS_NUM_THREADS="2", CUBLAS_WORKSPACE_CONFIG=env.get("CUBLAS_WORKSPACE_CONFIG", ":4096:8"),
               MPLCONFIGDIR=str(OUTPUT / "cache/matplotlib"))
    with log_path.open("a") as log:
        log.write(f"\n[{now()}] {shlex.join(command)}\n")
        log.flush()
        process = subprocess.Popen(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
        next_status = time.monotonic()
        try:
            while process.poll() is None:
                if time.monotonic() >= next_status:
                    status = current_status(jobs, label, stage)
                    status["pid"] = process.pid
                    atomic_json(OUTPUT / "batch_status.json", status)
                    print(f"[{now()}] {label}: {status['completed']}/{status['required']} runs complete; "
                          f"{status['epochs_completed']} epochs recorded.", flush=True)
                    next_status = time.monotonic() + 600
                time.sleep(5)
        except KeyboardInterrupt:
            process.terminate()
            process.wait()
            status = current_status(jobs, label, "interrupted")
            atomic_json(OUTPUT / "batch_status.json", status)
            raise
    if process.returncode:
        status = current_status(jobs, label, "failed")
        status.update(returncode=process.returncode, log=str(log_path.relative_to(ROOT)),
                      recovery="Read this log, resolve the environment problem, then repeat the identical batch command. Keep source/protocol and completed runs unchanged.")
        atomic_json(OUTPUT / "batch_status.json", status)
        raise RuntimeError(f"{label} failed (exit {process.returncode}). See {log_path}. No replacement run was started.")
    print(f"[{now()}] DONE {label}", flush=True)


def export_results():
    destination = ROOT / "AML_EXPLICIT_PAIR_RESULTS.zip"
    temporary = destination.with_suffix(".zip.tmp")
    files = sorted(p for p in OUTPUT.rglob("*") if p.is_file()
                   and "checkpoints" not in p.parts and "cache" not in p.parts
                   and p.suffix not in (".pt", ".tmp", ".lock")
                   and "__pycache__" not in p.parts)
    checksums = []
    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=4, allowZip64=True) as archive:
        for path in files:
            relative = path.relative_to(ROOT)
            archive.write(path, str(relative))
            checksums.append(f"{sha(path)}  {relative}")
        archive.writestr("RESULTS_SHA256SUMS", "\n".join(checksums) + "\n")
        archive.writestr("RETURN_README.txt", "Return this archive for analysis and presentation updates.\n"
                          "Model checkpoints remain on the server under results/representation_followup/runs/checkpoints.\n"
                          "Keep them until the study has been reviewed. This compact archive omits graph data and checkpoints.\n")
    temporary.replace(destination)
    print(f"Return archive: {destination} ({destination.stat().st_size / 2**20:.1f} MiB)", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cuda")
    parser.add_argument("--dry-run", action="store_true", help="Print the fixed job plan without creating files or starting jobs.")
    args = parser.parse_args()
    protocol = json.loads((OUTPUT / "protocol.json").read_text())
    jobs = list(job_plan(protocol, args.device))
    if args.dry_run:
        for tag, command in jobs:
            print(tag + ": " + shlex.join(command))
        print(f"{len(jobs)} fixed runs, then audit, linear probe and results export. Device: {args.device}.")
        return
    OUTPUT.mkdir(parents=True, exist_ok=True)
    # A second submission must not train into the same checkpoint directory.
    batch_lock = (OUTPUT / ".batch.lock").open("a")
    try:
        fcntl.flock(batch_lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError as error:
        raise RuntimeError("Another batch is already using this output directory. Read batch_status.json instead of submitting a duplicate.") from error
    (OUTPUT / "logs").mkdir(exist_ok=True)
    (OUTPUT / "cache/matplotlib").mkdir(parents=True, exist_ok=True)
    source_paths = sorted((ROOT / "src").glob("*.py")) + sorted((ROOT / "scripts/representation").glob("*.py"))
    manifest = {"device": args.device, "protocol_sha256": sha(OUTPUT / "protocol.json"),
                "python_version": platform.python_version(),
                "packages": {name: version(name) for name in ("torch", "torch-geometric", "pyg-lib", "numpy",
                                                              "scipy", "scikit-learn", "pandas", "matplotlib")},
                "sources": {str(path.relative_to(ROOT)): sha(path) for path in source_paths}}
    manifest_path = OUTPUT / "batch_manifest.json"
    if manifest_path.exists() and json.loads(manifest_path.read_text()) != manifest:
        raise RuntimeError("The device, source or protocol differs from this batch's manifest. Restore the original package before resuming.")
    atomic_json(manifest_path, manifest)
    common = ["--protocol", str(OUTPUT / "protocol.json"), "--data", str(ROOT / protocol["data"]["path"]), "--out", str(OUTPUT)]
    run_command([sys.executable, "-I", str(ROOT / "src/representation_diagnostics.py"), *common],
                "data_diagnostics", jobs, "preflight")
    run_command([sys.executable, "-I", str(ROOT / "scripts/representation/smoke.py"), "--device", args.device,
                 "--threads", str(protocol["training"]["threads"]), "--out", str(OUTPUT / "device_smoke.json"),
                 "--data", str(ROOT / protocol["data"]["path"])], "device_smoke", jobs, "preflight")
    for tag, command in jobs:
        run_command(command, tag, jobs, "training")
    run_command([sys.executable, "-I", str(ROOT / "src/representation_analyze.py"),
                 "--runs", str(OUTPUT / "runs"), *common], "analysis", jobs, "analysis")
    analysis = json.loads((OUTPUT / "analysis.json").read_text())
    if analysis.get("status") != "complete":
        raise RuntimeError("Primary analysis is incomplete; results cannot be marked complete.")
    run_command([sys.executable, "-I", str(ROOT / "src/representation_probe.py"), "--runs", str(OUTPUT / "runs"),
                 "--device", args.device, "--threads", str(protocol["training"]["threads"]), *common],
                "probe", jobs, "probe")
    atomic_json(OUTPUT / "batch_status.json", current_status(jobs, stage="complete"))
    export_results()


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, ValueError, OSError) as error:
        print(f"BATCH STOPPED: {error}", file=sys.stderr, flush=True)
        sys.exit(1)
