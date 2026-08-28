# Benchmarks

How to reproduce the performance and convergence figures quoted in
[`docs/VERIFICATION.md`](../docs/VERIFICATION.md).

## Convergence: how many replicates does a result need?

```bash
python batch_main.py --input examples/convergence_study.csv --output ConvergenceStudy --seed 2026 --workers 4
```

Produces, in `Outputs/ConvergenceStudy/`:

| file | contents |
|---|---|
| `Aggregated_Summary.csv` | mean ± SD ± n per scenario |
| `Convergence.csv` | coefficient of variation accumulated from run 1 |
| `Figure_Convergence.png` | the CV curve, with the settling point marked |
| `Convergence_Summary.txt` | the replicate count needed for a stated precision |
| `Batch_Report.pdf` | all of the above as one document, with an explicit verdict on whether the batch was large enough |

On the reference area this settles at **n ≈ 40**, by two independent criteria.
Expect roughly 35 minutes on four workers.

## Runtime against network size

Every batch already records `Nodes`, `Links`, `Agents_Created`,
`Seconds_Setup`, `Seconds_Simulation` and `Seconds_Total` per run, and writes
`Figure_Runtime_Benchmark.png`.

To span a useful range of network sizes, batch across several areas — the
shipped ones range from 6 nodes (`Synthetic_NoSafeZone`) to 4,473
(`Chimbote_Zona1`).

## Reference timings

Measured on an Apple M1 Ultra, macOS 15, NetLogo 7.0.4.

| step | time |
|---|---|
| Model load and setup | 2.6 s |
| Route pre-computation (4,473 nodes) | 0.009 s |
| One run, 3,100 agents, 23 simulated minutes | 81 s |

Runtime is dominated by the simulation loop, not by setup or routing.
