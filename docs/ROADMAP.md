# Roadmap and known gaps

What GTEM does not yet do, and why. Read it to judge whether GTEM fits your
problem, or to find something worth contributing.

Where an indication of scale is given, it is a rough guide for a contributor,
not a commitment or a schedule.

---

## Before relying on GTEM in a published study

### Validation against an observed evacuation
The largest scientific gap. Everything in
[VERIFICATION.md](VERIFICATION.md) shows the model computes correctly; nothing
shows it reproduces reality.

**A benchmark now exists.** GTEM's ancestor, TUNAMI-EVAC1 (Mas, 2012), was
validated against the 2011 Arahama evacuation: about 90% of 2,271 people saved,
520 sheltered in the evacuation building. Re-running both models under matched
assumptions gives 81.5% for the ancestor and **83.4% for GTEM**, with the
observed figure above both. That is a reasonable starting point, not a
validation: one scenario, one seed, one aggregate number. See
[validation/](../validation/).

### Confirmation on Windows and Linux
The code is platform-aware and a continuous-integration workflow is provided,
but GTEM has so far been run end to end only on macOS. If you are the first to
run it on Windows or Linux, reporting what happens would be a useful
contribution.

---

## Modelling gaps, in order of how much they could mislead

### Restore what the ancestor already had

Three capabilities present in TUNAMI-EVAC1 (2012) were lost on the way to GTEM.
They are listed first because each is a known-good design, not a research
problem, and because the Arahama comparison suggests they explain most of the
gap between GTEM and the observed record.

| capability | in the ancestor | effort |
|---|---|---|
| **Vehicles** | A `cars` breed with a car-following speed rule; 410 vehicles carrying four each in the validated Arahama scenario | Large. A new breed, its own speed law, and shared road capacity. |
| **Reduced mobility** | A `handicap` flag halving speed, applied to a settable share of the population | Small. One agent variable, one config key, one line in the speed function. |
| **Mixed departure curves** | Each agent drew its own Rayleigh mean uniformly from the whole-minute range between `u` and the arrival time, rather than sharing one mean | Small, and the most likely of the four to change results. See [validation/](../validation/). |
| **Time-varying inundation** | 301 gridded inundation surfaces read over the run, resolving per agent whether the wave overtook them — this is how casualties were counted rather than "caught in transit" | Large, but the Arahama grids are public and already in the ancestor's repository. |


### Safe zones have unlimited capacity
An agent reaching a safe zone is counted safe however many are already there.
A plan could be approved on the basis of a site that cannot physically hold the
arrivals. The demand figure shows the numbers; checking them against real
capacity is currently a manual step.
*An optional capacity column and an over-capacity warning: about one day.*

### Crowd density is not directional
Density is computed over a whole street segment regardless of direction of
travel or position along it, so two groups walking in opposite directions slow
each other even if they never meet. Congestion is therefore mis-shaped, not
merely mis-scaled. *One to two weeks.*

### Everyone walks to the nearest safe zone by distance
Not the emptiest, and not the fastest under congestion. Demand concentrates as a
result: on the reference area one safe zone receives over a thousand people
while another receives none. *A time-weighted or capacity-aware assignment is
about one week.*

### No re-routing
An agent walking into a jam keeps walking into it. *Best addressed together with
directional density.*

### Vehicles and bicycles
Not modelled at all. Adding them means directed links, turn restrictions,
junction capacity, vehicle–pedestrian interaction and a second fundamental
diagram — effectively a second model. *Several months, and a deliberate scope
decision rather than an oversight.*

### Vulnerable groups beyond age
Only three age groups. No representation of disability, mobility aids, carers or
people assisting others. *Best added as a speed-and-assistance class rather than
more age groups: one to two weeks.*

### Time-of-day population
The population distribution is a night-time, everyone-at-home estimate. Daytime
distributions — schools, workplaces, markets, beaches — are entirely different.
*Mostly a data problem.*

---

## Usability

### Automated preparation of a new area
Preparing a new city is currently several hours of manual GIS work.
[PREPARING_YOUR_CITY.md](PREPARING_YOUR_CITY.md) and `check_inputs.py` make the
gap navigable, not absent. An automated preprocessor — including pulling the
road network from OpenStreetMap — is the largest usability win available.
*Three to four weeks.*

### Interactive map export
Roughly half the intended users have no GIS software. A self-contained HTML map
opens in any browser, can be emailed, and can be projected in a community
meeting. *About one week, and the best value-for-effort feature on this list.*

### Two-scenario comparison mode
Comparison is the actual decision workflow — "what if we open this road?" —
and is currently done by running twice and comparing by hand. *About one week.*

### A dependency-free engine
GTEM requires NetLogo and a Java runtime. Porting the engine to Python would
remove both and reduce installation to `pip install`. This is the single largest
adoption barrier for the intended audience. *Six to ten weeks.*

---

## Smaller items

- **Inundation polygon and vertical evacuation.** Safe zones are whatever the
  user flags; the model does not read an inundation footprint, and
  vertical-evacuation buildings are not represented.
- **Damage scenarios as data.** Road damage is currently expressed by preparing
  an edited network. A per-link capacity file, folded into routing cost and
  crowd density, would make damage scenarios editable rather than requiring GIS
  work.
- **Per-run figures in batch mode.** Batches produce summary, aggregate and
  convergence outputs, but not per-run figures.
- **Video recording.** The code path exists and defaults to off; it is not
  exercised by the test suite.
- **Street segments below one metre** produce implausible densities. Reported as
  a warning; merging them in preparation would be better.

---

## Contributing

The most useful contributions, in order:

1. **Observed evacuation data** for any coastal area, enabling validation.
2. **A safe-zone capacity check.**
3. **An automated preprocessor** for new study areas.
4. **A study area from a new country**, which tests assumptions the current two
   do not.
