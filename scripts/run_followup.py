"""Run the frozen 15-run follow-up on four allocated GPUs, then analyze and probe."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "results/representation_8h/protocol.json"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "outputs/followup")
    parser.add_argument("--data", type=Path, default=ROOT / "data/hi_small.pt")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    args.out, args.data = args.out.resolve(), args.data.resolve()
    protocol = json.loads(PROTOCOL.read_text())
    common = ["--device", "cuda", "--protocol", str(PROTOCOL), "--data", str(args.data),
              "--out", str(args.out / "runs")]
    for key in ("max_epochs", "min_epochs", "patience", "min_delta", "threads"):
        common += ["--" + key.replace("_", "-"), str(protocol["training"][key])]
    jobs = []
    seeds = protocol["analysis"]["seeds_by_cell"]
    for seed in sorted({seed for group in seeds.values() for seed in group}):
        for cell in protocol["analysis"]["cells"]:
            if seed in seeds[cell]:
                jobs.append((f"{cell}_s{seed}", [sys.executable, "-I", str(ROOT / "src/representation_train.py"),
                                             "--cell", cell, "--seed", str(seed), *common]))
    if args.dry_run:
        for tag, command in jobs:
            print(tag, shlex.join(command))
        print(f"{len(jobs)} runs, four GPU workers; outputs: {args.out}")
        return

    import torch
    if torch.cuda.device_count() != 4 or len({torch.cuda.get_device_name(i) for i in range(4)}) != 1:
        raise RuntimeError("Allocate four GPUs of the same model before launching this protocol.")
    slots = os.environ.get("CUDA_VISIBLE_DEVICES", "0,1,2,3").split(",")
    if len(slots) != 4:
        raise RuntimeError("CUDA_VISIBLE_DEVICES must identify four allocated GPUs.")
    (args.out / "logs").mkdir(parents=True, exist_ok=True)
    environment = dict(os.environ, PYTHONUNBUFFERED="1", OMP_NUM_THREADS="2", MKL_NUM_THREADS="2",
                       OPENBLAS_NUM_THREADS="2", CUBLAS_WORKSPACE_CONFIG=":4096:8",
                       MPLCONFIGDIR=str(args.out / "cache/matplotlib"))

    def execute(tag, command, env):
        print(tag, flush=True)
        with (args.out / "logs" / f"{tag}.log").open("a") as log:
            subprocess.run(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)

    analysis_args = ["--data", str(args.data), "--protocol", str(PROTOCOL), "--out", str(args.out)]
    execute("diagnostics", [sys.executable, "-I", str(ROOT / "src/representation_diagnostics.py"),
                            *analysis_args], environment)

    def worker(index):
        env = dict(environment, CUDA_VISIBLE_DEVICES=slots[index])
        for tag, command in jobs[index::4]:
            execute(tag, command, env)

    with ThreadPoolExecutor(max_workers=4) as pool:
        for future in [pool.submit(worker, i) for i in range(4)]:
            future.result()
    execute("analysis", [sys.executable, "-I", str(ROOT / "src/representation_analyze.py"),
                         "--runs", str(args.out / "runs"), *analysis_args], environment)
    execute("probe", [sys.executable, "-I", str(ROOT / "src/representation_probe.py"),
                      "--runs", str(args.out / "runs"), "--device", "cuda", "--threads", "2",
                      *analysis_args], dict(environment, CUDA_VISIBLE_DEVICES=slots[0]))


if __name__ == "__main__":
    main()
