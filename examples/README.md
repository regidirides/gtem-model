# Examples

Ready-to-run configurations. Copy one, edit the copy, and run it.

| file | what it is |
|---|---|
| `config_example.txt` | A single run, fully commented. **Start here.** Every setting explains what it does and what a sensible value is. |
| `scenario_list.csv` | Three scenarios for `batch_main.py`: an intact network and two road-collapse variants of the same area. |
| `convergence_study.csv` | One scenario repeated 100 times, used to establish how many replicates a result needs. Takes about 35 minutes on four workers. |

## A first run

```bash
python main.py --config examples/config_example.txt
```

Results appear in `Outputs/<zone>/<seed>/`. Open the PDF first.

## A first batch

```bash
python batch_main.py --input examples/scenario_list.csv --seed 2026 --workers 2
```

Report from `Aggregated_Summary.csv` — mean and standard deviation across
replicates — never from a single run.

## The fastest possible check that everything works

`Synthetic_Corridor` is a small artificial area whose answer is known by hand:
two straight 1,000 m corridors, which an adult walks in 12.53 minutes.

```bash
printf 'zone = Synthetic_Corridor\nadults = 50\nelderly = 0\nchildren = 0\ntsunami_eta = 30\ndeparture_mean = 0\ndt = 5\nseed = 1\nrecompute_routes = true\n' > my_check.txt
python main.py --config my_check.txt
```

The run should end at about 12.5 minutes with everyone evacuated.
