# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project uses [semantic versioning](https://semver.org/).

---

## [1.0.0] — 2026-08-31 — First stable release

The first public release of GTEM.

### What GTEM does

Simulates pedestrian tsunami evacuation over a graph-based road network.
Age-differentiated walking speeds fall with crowd density following
Mas et al. (2015); departure times are drawn from a Rayleigh distribution; and
the run is bounded by a user-supplied tsunami arrival time. Outputs are five
figures, five CSV tables and an automated PDF report.

### Design commitments

These are the principles the release is built around, and the reason for most
of the behaviour described below.

- **Results are reported against the tsunami arrival time.** Anyone still
  walking when the wave arrives is counted as **not evacuated**. Reaching a safe
  zone afterwards is not safety.
- **Every person is accounted for.** Each agent ends in exactly one of
  *evacuated before the wave*, *caught in transit*, or *stranded with no route*,
  and the three are asserted to sum to the population simulated. A violation
  fails the run rather than being reported.
- **Silence is informative.** Problems found in input data are reported to the
  console, written to `warnings.log`, and reproduced in the PDF. When there are
  none, the report says so explicitly.
- **A refusal beats a wrong answer.** Invalid configuration is rejected before
  the engine starts, naming the parameter and its acceptable range. No invalid
  input produces an output folder that could be mistaken for a result.
- **No user edits Python.** Every parameter comes from an external
  configuration file, and a copy of the resolved settings is written into each
  run folder so any result traces back to what produced it.

### Included

- Cross-platform: Windows, macOS and Linux.
- `main.py` for a single run; `batch_main.py` for many, with mean ± SD per
  scenario, an accumulated-CV convergence analysis, and per-run timing.
- **Two PDF reports.** A run report for a single simulation, and a batch report
  that presents means with their spread, compares scenarios, and states whether
  enough replicates were run. An optional time-margin analysis reports how much
  longer a full evacuation would need and what each extra minute is worth.
- `check_environment.py` and `check_inputs.py`, to be run before anything else.
- Route pre-computation by a single multi-source Dijkstra, cached and keyed by a
  hash of the network. Study-area data is never written to.
- 90 automated tests, of which 66 need no simulation engine, plus a continuous
  integration workflow.
- Ten study areas, including three synthetic ones with analytically known
  answers, and a documented input schema for preparing your own.
- A user manual, [docs/manual/GTEM_Manual.pdf](docs/manual/GTEM_Manual.pdf),
  written for local-government staff rather than modellers, with its editable
  Typst source alongside it, and a full Spanish edition,
  [docs/manual/GTEM_Manual_ES.pdf](docs/manual/GTEM_Manual_ES.pdf).
- Figures and both PDF reports can be written in Spanish (`language = es`, or
  `--language es`). Configuration keys, CSV column headers and output file names
  stay English in every language, so results remain directly comparable.
- Documentation covering limitations, data preparation, verification evidence
  and the roadmap, including a comparison against the 2012 ancestor
  TUNAMI-EVAC1 on its validated Arahama scenario. Under matched assumptions
  GTEM gives 83.4% against the ancestor's 81.5% and an observed ~90%. Recorded
  in [validation/](validation/), together with the departure-time mixture the
  ancestor used and GTEM does not.

### Final review before release

A last pass over every file after the comparison against TUNAMI-EVAC1 (2012):

- `tools/time_gtem.py` carried an absolute path to the author's home directory,
  which both leaked a local path and made the tool unusable elsewhere. It now
  derives the project root from its own location.
- `tools/time_tunami.py` and `tools/capture_tunami_positions.py` hard-coded
  NetLogo locations; they honour `NETLOGO_622_HOME` and `NETLOGO_JVM`.
- `src/figures.py` called `legend()` unconditionally on the safe-zone figure,
  which warns when every zone received someone — as on a clean Arahama run.
- A Spanish string, `"Modelo.mp4"`, survived in a NetLogo GUI button. The
  English-only gate misses it because the word carries no accent and appears
  alone on the line.
- `docs/LIMITATIONS.md` and `docs/VERIFICATION.md` still said the comparison
  against an observed evacuation had not been attempted. It has; both now
  report the result, including where GTEM does not match.
- `docs/VERIFICATION.md` reported 60 tests; there are 90, and `test_text_strings`
  was missing from the table.
- `benchmarks/RUNTIME_VS_ANCESTOR.md` told the reader to run
  `examples/arahama_matched.txt`, which was not shipped. It is now.
- Nine of the seventeen tools were undocumented in `tools/README.md`.

### Known limitations

Stated in full in [docs/LIMITATIONS.md](docs/LIMITATIONS.md). In brief:
pedestrians only; agents know the whole network and walk the shortest route;
nobody re-routes; safe zones have unlimited capacity; the population is a
night-time spatial estimate; and the tsunami is a single number supplied by the
user.

**GTEM has not been validated against an observed evacuation.** See
[validation/](validation/).

### Provenance

GTEM derives from [TUNAMI-EVAC](https://github.com/erick2307/TUNAMI-EVAC).
Earlier internal revisions are not public and their results are not comparable
to this release.
