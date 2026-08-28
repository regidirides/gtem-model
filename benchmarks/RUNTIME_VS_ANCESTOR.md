# Runtime: GTEM against TUNAMI-EVAC1 (2012)

Measured August 2026 on an idle 20-core Apple Silicon machine. Identical
scenario in both models: **Arahama, 2,271 pedestrians, 67 simulated minutes**,
matched departure times. Engine only — setup plus the simulation loop, no
figures and no PDF. Mean of three runs, except GTEM at `dt = 1` (one run).

Reproduce with the harnesses in `tools/`; see the bottom of this page.

## One run

| model | timestep | ticks | setup | simulation | total |
|---|---|---|---|---|---|
| TUNAMI-EVAC1 | 1 s | 4,140 | **0.8 s** | 318.5 s | **319.3 s** |
| GTEM v1.0.0 | 10 s | 402 | 36.1 s | **110.3 s** | **146.4 s** |
| GTEM v1.0.0 | 1 s | 4,020 | 36.7 s | 1,397.0 s | 1,433.7 s |

The user-facing command `python main.py --config …` takes **184 s** on average
(174–192 s over three runs). The difference from 146 s is JVM startup, the five
figures and the PDF report, which the ancestor's harness does not produce.

## The honest reading

**GTEM finishes a run 2.2× faster, but its engine is slower.**

| measure | TUNAMI-EVAC1 | GTEM | |
|---|---|---|---|
| Wall clock, each model's own timestep | 319 s | 146 s | GTEM **2.2× faster** |
| Simulation loop only | 318.5 s | 110.3 s | GTEM **2.9× faster** |
| **At the same timestep (`dt = 1 s`)** | **318.5 s** | **1,397 s** | GTEM **4.4× slower** |
| Throughput | 29,517 agent-steps/s | 8,274 agent-steps/s | GTEM **3.6× slower** |
| Setup | 0.8 s | 36.1 s | GTEM **47× slower** |

The wall-clock gain comes from GTEM advancing 10 simulated seconds per tick
where the ancestor advances one. It does about a tenth of the work, a little
under four times more slowly, and comes out ahead. **It is a modelling choice
that pays off, not a faster engine.**

Two costs are worth naming:

- **Setup is 47× slower.** GTEM re-reads the shapefiles and rebuilds the network
  on every `setup`; the ancestor loads its GIS data once when the model opens and
  then only re-places agents. For a batch of *n* replicates GTEM pays that 36 s
  *n* times. Caching the parsed network across runs in a worker process is the
  obvious optimisation and has not been done.
- **Per-agent-step cost is 3.6× higher.** Not diagnosed. GTEM does more per step
  — density accounting per link, per-outcome bookkeeping, conservation checks —
  so some of this buys the correctness guarantees the ancestor lacks.

## A batch of four replicates

| | wall clock | note |
|---|---|---|
| TUNAMI-EVAC1, sequential | 21.3 min | extrapolated from the measured single run |
| GTEM, `--workers 1` | 12.0 min | measured |
| GTEM, `--workers 4` | **3.1 min** | measured, **3.8× scaling** |

This is where GTEM wins clearly. `batch_main.py` runs replicates in separate
processes, so a 4-worker batch scales almost linearly. The ancestor's harness as
driven here is sequential — NetLogo's BehaviorSpace can run experiments in
parallel, and that was **not** tested, so the first row understates what the
ancestor could do with its own tooling.

Replicates are not optional: `validation/` and `docs/VERIFICATION.md` both show
that a single run is not a result. On the reference area about 40 replicates are
needed, which at these rates is roughly **31 minutes** for GTEM on four workers.

## What is not measured here

- **Route pre-computation.** GTEM solves routes once with a multi-source
  Dijkstra and caches them by a hash of the network; the timings above use a warm
  cache, which is the normal case. The ancestor runs A\* per agent inside the
  simulation loop, so part of its per-step cost is routing that GTEM has already
  done. This is a real GTEM design gain and it is *not* separated out above.
- **Larger networks.** Arahama is small: 235 nodes, 311 links. Chimbote_Zona1 has
  4,468 nodes and 17,261 agents. Scaling behaviour was not compared, because the
  ancestor cannot read the Chimbote data.
- **The tsunami.** The ancestor also reads 301 inundation grids during the run.
  That work is inside its 318 s and GTEM does none of it.

## Reproducing

```bash
# TUNAMI-EVAC1 under NetLogo 6.2.2 (see validation/README.md for the setup)
python tools/time_tunami.py <model.nlogo> time_tunami.json 3

# GTEM, engine only
python tools/time_gtem.py examples/arahama_matched.txt time_gtem.json 3

# batch
python batch_main.py --input <scenarios.csv> --output BatchW4 --seed 7 --workers 4

python tools/plot_runtime_comparison.py runtime.json runtime_comparison
```
