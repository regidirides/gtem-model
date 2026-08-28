# Validation

> **GTEM has not been validated against an observed evacuation.**
>
> A benchmark now exists, and GTEM has been compared against it. Under matched
> assumptions GTEM lands close to the ancestor, and both fall short of the
> observed figure. This folder records the benchmark, the comparison, and what
> is still missing.

## Why this matters

Everything in [`docs/VERIFICATION.md`](../docs/VERIFICATION.md) is
**verification**: evidence that the model computes what it claims to compute —
that distances are right, that every person is accounted for, that the same seed
reproduces the same answer.

**Validation** is a different and harder question: does the model reproduce what
actually happened? Until that is answered, GTEM results should be used to
*compare planning options*, not to predict outcomes. See
[`docs/LIMITATIONS.md`](../docs/LIMITATIONS.md).

## The benchmark: Arahama, 11 March 2011

GTEM descends from **TUNAMI-EVAC1** (Mas, 2012), which *was* validated against
the 2011 evacuation of Arahama, Sendai. That model, its Arahama data and the
supporting PhD thesis are public:
<https://github.com/erick2307/TUNAMI-EVAC>. `data/Arahama_Zona1` is the same
study area — the extents overlap by 87.5% and both use Japan Plane Rectangular
CS X.

### The observed record

From the thesis (Chapter 4), attributed to local media and to the city office
census taken before and after the earthquake:

| quantity | observed |
|---|---|
| Population of the study area | 2,271 |
| Share saved from the tsunami | **about 90%** |
| Sheltered at the Elementary School (the vertical-evacuation building) | **520 people** |
| Recorded tsunami arrival | **67 minutes** after the earthquake |

### The scenario that reproduces it

| setting | value |
|---|---|
| People | 2,271 — of whom **631 on foot and 410 vehicles carrying four each** |
| Departure times | see below — **not** a single Rayleigh with mean 14 |
| Tsunami arrival | 67 min |
| Replicates | 250–1,000 |

#### The departure-time model is a mixture, not one curve

The ancestor's `u = 14` is **not** the mean departure time. It is the lower bound
of a family of curves. At setup the model builds the list of whole minutes from
`min(u, ETA)` to `max(u, ETA)` — with `u = 14` and `ETA = 67` that is
`[14, 15, … 67]` — and **each agent draws its own Rayleigh mean uniformly from
that list**, then draws its departure time from that curve. This is the "Time
Decision Curves" construction described in the thesis.

The effective distribution therefore has a mean of about **40 minutes**, not 14,
and a much heavier tail:

| | mean | median | 90th percentile | left within 20 min |
|---|---|---|---|---|
| Ancestor (mixture, u = 14, ETA = 67) | 39.9 min | 34 min | 78 min | 27% |
| GTEM (single Rayleigh, `departure_mean`) | as set | 0.94 × mean | 1.71 × mean | — |

**GTEM has no equivalent of this mixture.** Its `departure_mean` is one Rayleigh
for the whole population. That is a fourth regression relative to the ancestor,
and it matters: departure timing is the assumption GTEM's own documentation
calls the most influential in the model.

### What TUNAMI-EVAC1 reported

Over 1,000 repetitions (thesis Table 4.2): **82.11% safe (S.D. 3.03%)**, 17.89%
casualties, and **497.55 sheltered in the evacuation buildings** against the 520
observed — a close match on the quantity that was independently recorded.

## What happened when GTEM was run against it

Re-run in August 2026. TUNAMI-EVAC1 was executed under NetLogo 6.2.2 with the
scenario above; GTEM was given the same population, the same departure mean and
the same arrival time.

| run | reached safety |
|---|---|
| Observed 2011 | ~90% |
| TUNAMI-EVAC1, validated configuration (631 walking + 410 vehicles) | 81.5% |
| TUNAMI-EVAC1, all 2,271 on foot | 79.5% |
| **GTEM 1.0.0, all on foot, departure mean matched at 40 min** | **83.4%** |
| GTEM 1.0.0, all on foot, `departure_mean = 14` | 100%, complete at 58.5 min |

The 81.5% reproduction sits inside one standard deviation of the published
82.11% ± 3.03%, so the ancestor was reproduced faithfully.

**Under matched departure assumptions GTEM gives 83.4%** — about two points
above the ancestor's validated configuration and four above its pedestrian-only
run. All three sit below the ~90% observed.

The final row is kept as a warning. Setting `departure_mean = 14` because the
ancestor's parameter is named `u = 14` produces 100% evacuated and looks like a
dramatic divergence between the models. It is not: it is a 26-minute head start
created by mistaking the lower bound of a mixture for its mean. **Departure
timing dominates this comparison**, which is exactly what GTEM's documentation
says about sensitivity — here it is, measured.

### Where the remaining difference could come from

The residual gap is a few percentage points, not the tens implied earlier. None
of the following is yet quantified:

1. **No vehicles.** 1,640 of the 2,271 people were in cars in the validated
   scenario; GTEM walks them. Note the ancestor's own pedestrian-only run
   (79.5%) is *below* its with-vehicle run (81.5%), so on this network vehicles
   helped rather than hindered.
2. **A different congestion law.** TUNAMI-EVAC1 reduces speed by a Gaussian in
   local density measured in a 5 m cone; GTEM uses the piecewise law of Mas et
   al. (2015).
3. **No casualty mechanism.** GTEM stops the clock at the arrival time and calls
   everyone still walking *caught in transit*. TUNAMI-EVAC1 propagates the wave
   over 301 inundation grids and resolves whether each person is overtaken, so
   its "safe" count is a stricter quantity than GTEM's.
4. **Uniform population placement.** Arahama's block layer is building
   footprints with no population attribute, so GTEM spreads people evenly.

## What is still missing

| requirement | status |
|---|---|
| Road network and safe zones | present |
| Projected metric CRS | present (Japan Plane Rectangular CS X) |
| Population total and arrival time | **now known** — 2,271 and 67 min |
| Departure-time distribution | **now known** — a mixture of Rayleigh curves from 14 to 67 min, effective mean ~40 min |
| Aggregate observed outcome | **now known** — ~90% saved, 520 at the shelter |
| Resident population *per block* | **missing.** Only the area total is known. |
| Per-person observed timings or routes | **missing.** |
| Time-varying inundation in GTEM | **missing.** The ancestor's 301 grids exist; GTEM accepts only a single arrival time. |

## What would close the gap

1. Offer the ancestor's mixed departure model as an option, so the comparison
   does not depend on collapsing it to a single mean. This is the change most
   likely to matter and the cheapest of the four.
2. Restore vehicles, or restrict the comparison to a pedestrian-only sub-case
   for which an observed figure exists.
3. Test GTEM's congestion law against the ancestor's on the same network and
   report which better matches the observed clearance.
4. Distribute the 2,271 people across blocks using building floor area, which
   the Arahama layer does carry, instead of uniformly.

Reaching a similar aggregate number under matched assumptions is **not**
validation: it is one scenario, one seed, and an aggregate. No statement that
GTEM is "validated" would be true.

## Sources

- Mas, E. (2012). *PhD Thesis*, Tohoku University. In the TUNAMI-EVAC
  repository under `resources/`.
- Mas, E., Suppasri, A., Imamura, F. & Koshimura, S. (2015). Agent-based
  Simulation of the 2011 Great East Japan Earthquake/Tsunami Evacuation.
  *Journal of Natural Disaster Science*, 34, 41.

## Contributing a validation case

If you hold observed evacuation data for a coastal area, that is the single most
useful contribution to this project. See the README for contact details.
