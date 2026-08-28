# tools/

One-off helpers. **None of these is needed to run GTEM**, and none is exercised
by the test suite. They live here rather than in `Inputs/` so that the input
folders contain only data.

| script | purpose |
|---|---|
| `rebuild_network_from_raster.py` | Rebuilds a clean road-centreline network from a rasterised street layer, by skeletonising and simplifying. Kept for provenance: this is how the Arahama network was produced. |
| `rename_collapse_scenario.py` | Renames the files of a collapse scenario folder from `colapso1` to `colapso2`. Also `.ps1` for PowerShell. |
| `make_synthetic_zone.py` | Generates the synthetic test zones with analytically known answers. |
| `make_layers_panel.py` | Draws a study area's three input layers as one panel, read straight from the shapefiles. |
| `make_reduced_capacity_zone.py` | Derives a variant of a zone with `lanes` reduced on selected roads, either by lane count or by targeting the busiest corridors from a baseline congestion report. See the note below. |

## Figures for reports and talks

| script | purpose |
|---|---|
| `plot_convergence.py` | Convergence figure from a batch's `Master_Summary.csv`: accumulated CV with the tolerance band, running mean with its 95% CI, and the convergence point. Uses `src/aggregate.py`, so it cannot disagree with what GTEM reports. |
| `plot_evacuation_comparison.py` | Overlays cumulative evacuation curves from two or more runs, optionally with a mean-speed panel and an observed reference line. Reads both GTEM's CSV schema and the 2012 ancestor's. |
| `plot_capacity_response.py` | Dose-response of outcome, crowding and walking speed to `capacity_multiplier` across several runs. |
| `plot_runtime_comparison.py` | Runtime figure: where a single run's time goes, and how a batch scales. |

## Videos

| script | purpose |
|---|---|
| `record_demo.py` | Runs a normal simulation through `main.py` and captures per-tick agent positions. Wraps `collect_state`; nothing is reimplemented. |
| `build_demo_video.py` | A walkthrough from input folder to report, built from a captured run. |
| `build_capacity_video.py` | Two GTEM runs side by side that differ only in road capacity. |
| `build_side_by_side.py` | GTEM against the 2012 ancestor on a common time axis. |

## Comparison against TUNAMI-EVAC1 (2012)

These need **NetLogo 6.2.2** as well as 7.0.4, and a copy of
<https://github.com/erick2307/TUNAMI-EVAC>. Set `NETLOGO_622_HOME` and
`NETLOGO_JVM` if either is installed somewhere other than `/Applications`.

| script | purpose |
|---|---|
| `capture_tunami_positions.py` | Runs the ancestor and samples agent positions for the side-by-side video. |
| `time_tunami.py` | Times the ancestor's setup and simulation loop. |
| `time_gtem.py` | The same measurement for GTEM, so the two are comparable. |

Results are in [`../benchmarks/RUNTIME_VS_ANCESTOR.md`](../benchmarks/RUNTIME_VS_ANCESTOR.md).

> **On `make_reduced_capacity_zone.py`.** GTEM's per-road capacity is the `lanes`
> attribute, and `lanes` floors at 1. On Chimbote the busiest evacuation
> corridors are *already* single-lane, so narrowing the multi-lane roads moved
> the outcome by 0.17 points. Where a disruption is not confined to particular
> streets, `capacity_multiplier` in the configuration is the effective lever —
> it scales every road, and its effect is documented in
> [`../benchmarks/`](../benchmarks/).

`rebuild_network_from_raster.py` needs extra dependencies:

```bash
pip install -r ../requirements-tools.txt
```

## Demo video

Three steps, all reproducible:

```bash
python tools/record_demo.py --config demo.txt --output Outputs/DemoRun \
    --frames demo_frames.npz
python tools/make_layers_panel.py Chimbote_Zona1 layers.png
python tools/build_demo_video.py --frames demo_frames.npz --run Outputs/DemoRun \
    --zone Chimbote_Zona1 --config-text demo.txt --console demo_console.txt \
    --layers layers.png --output GTEM_demo.mp4
```

`record_demo.py` wraps `main.collect_state`, which `main.py` already calls after
every tick, so the recording is an ordinary run — nothing is reimplemented. The
per-tick reads use `map [t -> ... of t] sort <breed>` rather than
`[...] of <breed>`, because the latter consumes the random number stream and
would change the very run being recorded. Verified: a recorded run and a plain
`main.py` run with the same seed produce identical headline numbers.

The video is not committed. It is ~60 MB, and it can be rebuilt from the model
in about fifteen minutes.
