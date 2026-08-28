# GTEM — Global Tsunami Evacuation Model

**Version 1.0.0**

An agent-based model of **pedestrian tsunami evacuation**, built for staff in
coastal local governments rather than for modelling specialists.

You give it a road network, where people live, and the minute the wave arrives.
It tells you who reaches safety in time, who does not, **where they were when
they ran out of time**, and which streets jammed.

> **Before using a result in a decision, read [docs/LIMITATIONS.md](docs/LIMITATIONS.md).**
> GTEM compares options well. It does not predict casualties, and it has **not**
> been validated against an observed evacuation — see [validation/](validation/).

---

## Install and run — 8 steps

**You need:** Windows 10/11, macOS or Linux · NetLogo 7.0.4 · Miniconda/Miniforge

1. **Install NetLogo 7.0.4** from <https://ccl.northwestern.edu/netlogo/>.
   Java comes bundled with it; no separate install is needed.
2. **Get GTEM** — clone or download this folder.
3. **Create the environment:**
   ```bash
   conda env create -f environment.yml
   conda activate gtem
   ```
4. **Check the machine is ready:**
   ```bash
   python check_environment.py
   ```
   It lists what it needs and, for anything missing, the command to fix it.
5. **Check the example data:**
   ```bash
   python check_inputs.py Chimbote_Zona1
   ```
6. **Copy a configuration** and edit the copy:
   ```bash
   cp examples/config_example.txt my_run.txt
   ```
   Every setting is commented. You never edit Python.
7. **Run:**
   ```bash
   python main.py --config my_run.txt
   ```
8. **Read the results** in `Outputs/<area>/<seed>/` — start with the PDF.

---

## How to interpret your results

### The four numbers that matter

On page 1 of the PDF and in `Run_Summary.csv`.

| number | meaning |
|---|---|
| **Evacuated before the tsunami** | Reached a safe zone *before* the wave. The only people who are actually safe. |
| **NOT evacuated** | Everyone else. Always look at this one. |
| **Caught in transit** | Still walking when the wave arrived. Usually improved by earlier departure or nearer safe zones. |
| **Stranded (no route)** | No path to any safe zone from where they started. **A network problem, not a behaviour problem** — no amount of preparedness fixes it. |

The three always sum to the population simulated. Nobody is left out.

### The figures

| figure | what to look for |
|---|---|
| **1 — Evacuation progress** | One panel per age group. A group that lags needs different measures, not more signage. Anything right of the red line did not happen in time. |
| **2 — Walking speed** | Dips below free-flow mean crowding. Sustained dips indicate a network capacity problem, not slow walkers. |
| **3 — Vulnerability** | Where people started, coloured by how long they took. **Black points never reached safety.** Black clusters are your priority areas. |
| **4 — Safe-zone demand** | How many arrived at each safe zone. **Check the busiest against its real capacity** — GTEM assumes safe zones are infinitely large. A zone receiving nobody may be unreachable. |
| **5 — Congestion** | Streets ranked by accumulated crowding, so a long moderate jam outranks a brief severe one. Candidates for widening or clearing. |

### What a good result looks like

There is no absolute pass mark. Useful readings are comparative:

- **Not-evacuated near zero with time to spare** — the constraint is elsewhere.
- **A large "caught in transit" share** — people started too late or had too far
  to go. Test earlier departure and additional safe zones.
- **Any "stranded" at all** — fix the network first.
- **One safe zone taking most arrivals** — check it can physically hold them.

### One run is not a result

The model is stochastic. On the reference area individual runs range from 80.1%
to 84.5% evacuated. **Always run replicates and report the mean.** About 40
replicates give the mean to within ±0.25 percentage points; see
[benchmarks/](benchmarks/).

```bash
python batch_main.py --input examples/scenario_list.csv --seed 2026 --workers 4
```

Report from `Aggregated_Summary.csv`, never from one run.

### Always read `warnings.log`

Every run writes it, and its contents also appear in the PDF. It reports
problems found in your input data — missing population attributes, disconnected
networks, people starting far from any road. It says "No input warnings." when
there are none, so silence is informative.

---

## Repository layout

```
main.py                run one simulation
batch_main.py          run many, with statistics
check_environment.py   is this machine ready?
check_inputs.py        is this area's data usable?

src/                   simulation engine and library modules
  gtem_model.nlogox      the NetLogo engine
data/                  study areas
examples/              ready-to-run configurations
docs/                  documentation
  manual/              the user manual (PDF plus its Typst source)
benchmarks/            how to reproduce the performance figures
validation/            status of validation (none yet)
tests/                 automated tests
tools/                 one-off helpers, not needed to run GTEM
```

## Documentation

| document | for |
|---|---|
| [docs/manual/GTEM_Manual.pdf](docs/manual/GTEM_Manual.pdf) | **The user manual — start here.** Installation to analysis, written for non-specialists. |
<!-- BEGIN TRANSLATED CONTENT: one deliberate Spanish line, so a Spanish
     reader recognises their manual in this table. See tests/test_english_only.py -->
| [docs/manual/GTEM_Manual_ES.pdf](docs/manual/GTEM_Manual_ES.pdf) | **El manual del usuario, en español.** De la instalación al análisis. |
<!-- END TRANSLATED CONTENT -->
| [docs/LIMITATIONS.md](docs/LIMITATIONS.md) | **What GTEM can and cannot answer. Read first.** |
| [docs/PREPARING_YOUR_CITY.md](docs/PREPARING_YOUR_CITY.md) | Input data schema and QGIS steps |
| [docs/VERIFICATION.md](docs/VERIFICATION.md) | Evidence that the model computes what it claims |
| [docs/ROADMAP.md](docs/ROADMAP.md) | Known limitations and what comes next |
| [validation/](validation/) | Why GTEM is not yet validated, and what that needs |
| [CHANGELOG.md](CHANGELOG.md) | Release history |

## How GTEM works, briefly

1. Route tables are computed once per network: a single multi-source Dijkstra
   from every safe zone gives each intersection its next step toward the nearest
   one. Cached in `cache/`, keyed by a hash of the network.
2. People are placed inside census blocks in proportion to population.
3. Each person waits a random time (Rayleigh, mean `departure_mean`), then walks
   their route. Speed depends on age group and on how crowded the street is,
   following Mas et al. (2015).
4. The run stops at the tsunami arrival time. Anyone still walking is **not**
   evacuated.
5. Figures, CSVs and a PDF are written.

## Tests

```bash
python -m pytest tests/ -m "not engine"   # fast, no NetLogo needed
python -m pytest tests/                   # everything, ~30 minutes
```

---

## Authors

- **Dr Erick Mas** — International Research Institute of Disaster Science
  (IRIDeS), Tohoku University, Japan
- **Dr Luis Moya** — Pontificia Universidad Catolica del Peru (PUCP), Peru
- **M.Sc. Jheyder Perez** — Pontificia Universidad Catolica de Chile (PUC), Chile

GTEM derives from [TUNAMI-EVAC1](https://github.com/erick2307/TUNAMI-EVAC) by
Erick Mas — a NetLogo model built in 2011–2012 and validated against the 2011
Arahama evacuation. GTEM inherits its Rayleigh departure-time sampler, its
1.33 m/s free-flow walking speed and its age factors directly from that work.
Under matched assumptions it lands within a few points of the ancestor's
validated Arahama result, which is a starting point rather than a validation;
see [validation/](validation/). The first round of improvements was by Jheyder Perez under the
supervision of Erick Mas and Luis Moya; the final version was modified and
verified by Erick Mas.

## Licence

MIT — see [LICENSE](LICENSE). The study-area data under `data/` is released for
free redistribution alongside the software.

## Citing GTEM

See [CITATION.cff](CITATION.cff). Please also cite the source of the
density–speed relation:

> Mas, E., Suppasri, A., Imamura, F. & Koshimura, S. (2015). Agent-based
> Simulation of the 2011 Great East Japan Earthquake/Tsunami Evacuation: An
> Integrated Model of Tsunami Inundation and Evacuation.
> *Journal of Natural Disaster Science*, 34, 41.

## Acknowledgements

Funded by the **Coalition for Disaster Resilient Infrastructure (CDRI)** under
the CDRI Fellowship Programme 2025–2026. Built on
[NetLogo](https://ccl.northwestern.edu/netlogo/) (Wilensky, 1999).
