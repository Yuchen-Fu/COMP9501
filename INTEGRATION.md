# Integration of the research and course branches

Integrated on **15 November 2026 (UTC+08:00)** from:

- Completed research: `b68610c09b763fdf70a44bc3509377a8701fd122` on
  `claude/cloud-setup-port-gnn-research-o13ou8`.
- Course implementation: `1637accdfe8d05fcf3b7a6d0d1043c1ba231a364` on
  `course/port-counts-factorial`.
- Common ancestor: `a5f660056fd54661dc7902133e6dd82c20a23bc9`.

Both histories are retained through a merge. There were no textual merge
conflicts, but there were important setup and scientific-protocol differences.

## Resolutions

| Issue | Integrated behavior |
|---|---|
| Course setup generated `data/course-graph.pt`, while the completed pipeline expected `data/hi_small.pt` | Shared setup atomically prepares `data/hi_small.pt`; the optional runner uses it by default and accepts an explicit `--data` path. |
| Course implementation imported a pinned external `GINe` model | Shared setup downloads that exact source to `data/reference/models.py` and verifies its SHA-256. The completed trainer remains unchanged. |
| Default package cache was unwritable in the managed environment | Setup respects a supplied `UV_CACHE_DIR`, otherwise uses `/tmp/comp9501-uv-cache`. |
| Course note described an incomplete two-run pilot | `COURSE_PROJECT.md` now links the completed 25-run study and identifies the 100-epoch implementation as a separate optional protocol. |
| The two runners have different scoring, epoch selection, subgroup definitions, and output schemas | Completed results stay in `results/runs/`; optional results stay in `results/factorial/`. They are never pooled. |
| Optional artifact reuse could accept incompatible records | The optional runner validates protocol, cell, seed, budget, features, hyperparameters, and graph/model fingerprints before reuse or reporting. Input files are hashed once per invocation. |
| Optional reporting duplicated the ratio calculation | It uses the completed analyzer's audited Fieller helper instead of a separate clipped-discriminant implementation. |
| Download archive and checksums predated the merge | Publication records are rebuilt to include both implementations and this integration record. |

The full protocol comparison and commands are in
[COURSE_PROJECT.md](COURSE_PROJECT.md). No 100-epoch full-data runs were started
by this integration. The optional implementation adds reproducible follow-up
code, not additional experimental evidence.

## Preserved scientific record

The canonical `src/train.py`, `src/prepare.py`, `src/analyze.py`, `run_all.sh`,
the 25 completed run JSONs and prediction archives, and `results/summary.json`
are byte-identical to the completed research branch. The research conclusions
and graphical slide outputs are unchanged.

`results/run_manifest.json` retains the historical setup hash used at completion.
The merged setup is a post-completion infrastructure change. Its new hash and
the integration parent commits are recorded separately; they are not presented
as the code that generated the completed results. The historical setup can be
recovered from commit `b68610c`.

## Verification

Shared setup was executed successfully against the pinned cached archive and
the canonical prepared graph. Both archive and model-source checksums passed,
and the pinned CPU environment imported successfully.

An isolated 216-transaction fixture exercised creation of `data/hi_small.pt`,
atomic output replacement, and a second setup that retained the graph. Package
installation was stubbed for that fixture; preparation used the real installed
interpreter and unchanged feature builder. The full prepared graph remained
byte-identical and all fixture outputs were removed.

Focused optional-runner checks are retained in `scripts/test_factorial.py`.
They use temporary toy inputs and do not create research results. The completed
study can be verified independently with `scripts/audit_results.py`.

**Final checks passed:** eight optional-runner tests covered sampled-edge ordering,
missing targets, as-of-transaction groups, incomplete reports, incompatible
records, cross-run consistency, Fieller reporting, and checkpoint resumption.
The actual pinned GINe on a 16-edge, two-epoch test fixture produced exactly the
same result and model-state tensors after a checkpoint resume as an uninterrupted test run. Those test
outputs were temporary and cannot pass the real 100-epoch metadata checks.

The full completed-results audit was also rerun after integration: **25 runs,
125 saved epoch predictions, 2,638 numerical comparisons, and 39,682 Fieller
membership checks passed**. The numerical summary checksum is unchanged.

```bash
.venv/bin/python -I scripts/test_factorial.py
.venv/bin/python -I scripts/audit_results.py
```

The publication commit records both histories. Both branch references are
intended to point to that integrated commit, so either checkout exposes the
same code, results, documentation, and presentation.
