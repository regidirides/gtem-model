# Verification

Evidence that GTEM computes what it claims to compute. Every figure here is
measured output.

**Verification is not validation.** Nothing on this page shows that GTEM
reproduces a real evacuation — see [validation/](../validation/).

Measured on macOS 15, Apple M1 Ultra, Python 3.10.6, NetLogo 7.0.4 with its
bundled OpenJDK 17.0.2.

---

## 1. Automated tests

```
$ python -m pytest tests/ -m "not engine"
66 passed in 46s

$ python -m pytest tests/
90 passed in ~23 min
```

| suite | tests | protects |
|---|---|---|
| `test_scale` | 6 | isotropy, no rounding, independence from display settings |
| `test_scale_sanity` | 3 | walking time against an analytically known answer |
| `test_routing` | 5 | shortest paths, unroutable nodes reported, equivalence |
| `test_departure` | 4 | Rayleigh sampler mean, distribution shape |
| `test_config_validation` | 21 | every invalid parameter rejected by name |
| `test_outcomes` | 9 | conservation, arrival-time boundaries, determinism |
| `test_warnings` | 10 | input problems announced; a clean folder is silent |
| `test_text_strings` | 28 | the English and Spanish tables stay in step; no user-facing prose is hardcoded |
| `test_english_only` | 4 | code and documentation contain no Spanish outside the fenced string table |

Engine tests **skip** rather than fail when NetLogo is absent, so a contributor
without it still gets a useful run.

---

## 2. Distance scale

The single length scale is isotropic and unrounded. Verified two ways.

### Against the network geometry

Comparing each link's length in patch units × metres-per-patch against its true
length in metres, over all 4,046 links of the reference area:

| | |
|---|---|
| median ratio | **1.0005** |
| overall error | **−0.13%** |
| east-west vs north-south | 1.0008 |

The sub-1.0 tail is road curvature — the stored length follows the polyline
while the straight-line distance does not — so the median is the clean signal.

### Against an analytically known answer

`data/Synthetic_Corridor` contains two straight 1,000 m corridors, one
east-west and one north-south. An adult at the free-flow speed of 1.33 m/s
covers 1,000 m in **751.88 s = 12.5313 min**.

| corridor | n | mean | error |
|---|---|---|---|
| east-west | 20 | 12.5333 min | **+0.02%** |
| north-south | 20 | 12.5333 min | **+0.02%** |

The two corridors agree to **0.000%**, so the world is isotropic end to end, not
merely in the coordinate arithmetic. The residual is one sub-tick of
discretisation and shrinks when the timestep is halved.

---

## 3. Outcome accounting

Reference area, 3,100 agents, 23-minute arrival time:

**2,555 evacuated + 545 caught in transit + 0 stranded = 3,100 requested.**

Conservation is asserted at every exit path from the simulation loop; a
violation fails the run.

### Arrival-time sweep

| arrival (min) | ticks | evacuated % | not evacuated % | sum |
|---|---|---|---|---|
| 10 | 60 | 18.26 | 81.74 | 100.00 |
| 15 | 90 | 50.39 | 49.61 | 100.00 |
| 20 | 120 | 74.84 | 25.16 | 100.00 |
| 23 | 138 | 82.35 | 17.65 | 100.00 |
| 25 | 150 | 85.65 | 14.35 | 100.00 |
| 30 | 180 | 93.45 | 6.55 | 100.00 |
| 40 | 240 | 99.32 | 0.68 | 100.00 |

Evacuated % is monotonically non-decreasing, not-evacuated % non-increasing,
the two sum to exactly 100% at every point, and the run ends at exactly
`arrival × 60 / dt` ticks.

---

## 4. Routing

Route pre-computation uses one multi-source Dijkstra seeded from every safe zone
simultaneously, rather than one search per origin–destination pair.

| | per-pair search | multi-source |
|---|---|---|
| routes found | 3,584 | 3,584 |
| time | 45.32 s | **0.009 s** |
| maximum cost difference | — | 5.0 × 10⁻¹² |
| identical next hop | — | **3584 / 3584 (100%)** |

Study-area data is verified **bit-identical** after a full run with route
recomputation enabled: computed tables are written to `cache/`, never to
`data/`. Nodes with no route to any safe zone are written to
`unroutable_nodes.csv` rather than silently dropped — 884 of them on the
reference area.

---

## 5. Reproducibility

- The same seed and configuration produce **byte-identical CSV outputs**.
- Different seeds produce different results, which guards against a fixed seed
  silently forcing identical runs.
- Agent placement is re-seeded from the run's seed immediately before agents are
  created, so results do not depend on what the driver read beforehand.

Across 100 replicates of the reference area: SD 0.82 percentage points, range
80.10%–84.52%.

---

## 6. How many replicates a result needs

100 replicates, 100 of 100 successful, 34.4 minutes on four workers.

| | |
|---|---|
| mean evacuated | 82.44% |
| SD | 0.82 pp |
| coefficient of variation at n = 100 | 0.99% |

| criterion | replicates |
|---|---|
| CV stays within 10% of its final value | **40** |
| 95% confidence interval of the mean within ±0.25 pp | **41** |
| within ±0.50 pp | 11 |
| within ±0.10 pp | 256 |

Two independent criteria agree on about 40. The coefficient of variation is
accumulated from run 1 onward (runs 1–2, 1–3, 1–4 …), never in disjoint bins:
binning hides the fact that an estimate is still moving.

---

## 7. Performance

| | |
|---|---|
| model load and setup | 2.6 s |
| route pre-computation, 4,473 nodes | 0.009 s |
| one run, 3,100 agents, 23 simulated minutes | 81.4 s |

Runtime is dominated by the simulation loop.

---

## 8. Behaviour on bad input

| case | exit code | files written |
|---|---|---|
| zero population | 2 | 0 |
| timestep out of range | 2 | 0 |
| arrival time ≤ 0 | 2 | 0 |
| duplicate configuration key | 2 | 0 |
| unknown configuration key | 2 | 0 |
| missing or incomplete area | 2 | 0 |
| geographic (lat/lon) coordinate system | 2 | 0 |
| area with no safe zone | 1 | 0 |
| single agent | 0 | 14 |
| failure during reporting | 1 | partial, plus `FAILED.txt` |

**No invalid input produces an output folder that could be mistaken for a
result.**

### The timestep changes results

46.0% evacuated at a 10-second timestep against 56.0% at 2 seconds, same
scenario and seed. Runs with different timesteps are **not comparable**, and
the batch runner refuses to aggregate them.

---

## What is not verified

| item | status |
|---|---|
| Execution on Windows and Linux | The code is platform-aware and a CI workflow is provided, but neither has been executed. |
| Peak memory | Not instrumented. |
| Runtime across network sizes | Measured on one network only. |
| Scaling beyond ~3,000 agents | Not tested. |
| The density–speed relation against independent data | The relation follows Mas et al. (2015); its constants have not been re-derived here. |
| **Agreement with an observed evacuation** | **First comparison made, not passed.** Arahama 2011: observed ~90% saved and 520 at the shelter; GTEM gives 83.4% and concentrates arrivals on one destination where the record shows three. See [validation/](../validation/). |
