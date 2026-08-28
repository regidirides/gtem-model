# What GTEM can and cannot tell you

**Read this before you use a GTEM result in a decision.**

GTEM produces confident-looking maps and numbers. That confidence comes from the
model's assumptions, not from reality. This page states those assumptions in
plain language so you can judge how much weight a result deserves.

If you take one thing from this page: **GTEM is a tool for comparing options,
not for predicting what will happen.** "Route A leaves 400 more people exposed
than route B" is a defensible use. "1,847 people will die" is not.

---

## Questions GTEM can help you answer

These are comparative questions, where both scenarios share the same
assumptions and the assumptions therefore largely cancel out.

- **Which parts of town are hardest to evacuate on foot?**
  The vulnerability map shows where people start and how long they take.
  Black points are people who never reached safety.
- **Would an additional safe zone here help, and how much?**
  Run the scenario twice, with and without it, and compare.
- **Which streets become bottlenecks, and for how long?**
  The congestion map ranks stretches by accumulated crowding.
- **How much does earlier departure buy us?**
  Lower `departure_mean` and compare. This is the single most powerful lever in
  the model, and it is a preparedness and education question.
- **What happens if these roads are blocked?**
  Prepare a damaged version of the network and compare.
- **Is our assumed tsunami arrival time survivable at all?**
  Sweep `tsunami_eta` and watch the evacuated fraction.

## Questions GTEM cannot answer

- **How many people will die.** GTEM reports who did not reach a safe zone in
  time under its assumptions. That is not a casualty estimate. It ignores
  inundation depth, building collapse, debris, injury, water velocity and
  people sheltering in place successfully.
- **What any individual will do.** Agents are statistical, not real people.
- **Whether a specific building is safe.** GTEM does not model structures.
- **Anything about vehicles.** See below.
- **What happens after the first wave.**

---

## The assumptions, and why each one matters

### 1. Pedestrians only. No vehicles, no bicycles.
Every agent walks. In a real coastal evacuation some people drive, which can
help them personally and can block everyone else. GTEM models neither effect.
**Consequence:** in a town where many people would drive, GTEM's road congestion
is optimistic and its clearance times may be too short.

> **This is a regression, not an unimplemented feature.** GTEM's ancestor,
> TUNAMI-EVAC1 (Mas, 2012), had a `cars` breed with its own car-following speed
> rule. In the validated Arahama scenario **1,640 of the 2,271 people were in
> vehicles** — the majority. How much this matters is not yet quantified: on
> that network the ancestor's pedestrian-only run finished *below* its
> with-vehicle run, so vehicles helped there rather than hindered. See
> [`validation/`](../validation/).

### 2. Everyone knows the whole road network and walks the shortest route.
Routes are computed before the simulation using Dijkstra's algorithm from every
starting point to the *nearest safe zone by distance*. Agents follow that route
exactly.
**Consequence:** real people take familiar routes, follow crowds, go the wrong
way, and go to collect family first. GTEM's evacuation is therefore **more
efficient than reality**. Treat its clearance times as a best case.

### 3. Nobody re-routes. Ever.
An agent walking into a jammed street keeps walking into it. There is no
congestion avoidance and no re-planning.
**Consequence:** congestion is somewhat overstated on the bottleneck itself and
understated on the alternatives that real people would divert to.

### 4. Everyone heads for the *nearest* safe zone, not the *emptiest*.
Distance decides, not queueing time.
**Consequence:** demand concentrates. In the shipped Chimbote example one safe
zone receives over a thousand people while another receives **none**. Read the
safe-zone demand figure as "where the distance rule sends people", not "where
people would sensibly go".

> **This is the assumption that failed the one reality check available.** On
> Arahama, GTEM sent 68% of arrivals to a single destination (1,290 of 1,895).
> The 2011 record and the ancestor — which modelled shelter *choice* rather than
> nearest-by-distance — both spread arrivals across three destinations, and the
> ancestor matched the observed shelter count to within 5%. Aggregate agreement
> hid a distribution that is wrong. See [`validation/`](../validation/).

### 5. Safe zones have unlimited capacity.
An agent that reaches a safe zone is counted as safe, however many are already
there. GTEM will not tell you that a plaza rated for 500 received 1,200.
**Consequence:** always check the demand figure against the real capacity of
each site. This is a manual step GTEM cannot do for you.

### 6. People start walking at random times drawn from one distribution.
Departure times follow a Rayleigh distribution with mean `departure_mean`.
Everyone eventually leaves. There is no milling, no returning home, no waiting
for relatives, no refusal to evacuate, and no household coordination.
**Consequence:** the *shape* of the departure curve is a modelling assumption,
not an observation of your town. It is also the assumption results are most
sensitive to — measurably so: on Arahama, moving the mean from 40 to 14 minutes
takes GTEM from 83.4% evacuated to 100%.

> **A fourth regression.** TUNAMI-EVAC1 did not give the whole population one
> curve. It built the list of whole minutes between a lower bound `u` and the
> tsunami arrival time, and each agent drew *its own* Rayleigh mean from that
> list — the "Time Decision Curves" construction in Mas (2012). The result has a
> much heavier tail than a single Rayleigh: on the Arahama scenario, 27% had left
> within 20 minutes against 80% for a single curve of the same nominal
> parameter. GTEM has no equivalent, and restoring it is the cheapest of the
> outstanding items in [`docs/ROADMAP.md`](ROADMAP.md).

### 7. Walking speed depends on age group and crowding only.
Three groups — adults, elderly, children — each with a free-flow speed reduced
by local crowd density. No slopes, stairs, surface condition, disability,
luggage, carrying children, darkness or injury.

The density–speed relation is taken from **Mas et al. (2015)**, cited at the
foot of this page. Free-flow speed is 1.33 m/s for adults, scaled by 0.8 for
children and 0.7 for the elderly, falling linearly to a 0.2 m/s crush speed
between 0.3 and 3.0 people per square metre. All six constants are configurable
rather than fixed in the code.

**Consequence:** GTEM has no representation of disability or reduced mobility
beyond the elderly group. For a town with a large care population this is a
material omission.

> **Also a regression.** TUNAMI-EVAC1 carried a `handicap` flag that halved an
> agent's walking speed, and a settable share of the population to apply it to.
> It also had a fourth age group, `teens`. Restoring the mobility flag is a
> small change and would remove this omission.

### 8. The tsunami is a single number you supply.
`tsunami_eta` is the minute the wave arrives. GTEM does not simulate the wave,
the inundation extent, or the depth.

> **A third regression.** TUNAMI-EVAC1 read a time series of inundation grids
> (301 of them for Arahama, 5 m cells) and resolved, per agent, whether the wave
> overtook them — which is how it produced casualty counts rather than a
> "caught in transit" tally. GTEM's single arrival time is a simplification of
> a capability that already existed.
**Consequence:** the result is only as good as that number, and it is binary —
one minute before is "safe", one minute after is "not". Always run a range of
arrival times, never a single value.

### 9. The population is a spatial guess.
People are scattered inside census blocks in proportion to a population
attribute. Where they are *within* a block is random, and the totals you request
are not reconciled against the census.
**Consequence:** this is a night-time, everyone-at-home assumption. Daytime
distributions (schools, workplaces, markets, beaches) are entirely different and
GTEM does not model them.

### 10. The road network is whatever you supply.
GTEM does not check that your network is complete or sensible, beyond warning
you about obvious problems.
**Consequence:** read `warnings.log` for every run. In the shipped Chimbote
example, **884 of 4,468 road nodes (19.8%) have no route to any safe zone** —
anyone starting there is counted as stranded before the simulation even begins.

---

## The state of validation

**GTEM has not been validated against an observed evacuation.**

A benchmark now exists and the first comparison has been made. GTEM's ancestor,
TUNAMI-EVAC1 (Mas, 2012), was validated against the 2011 Tohoku evacuation of
Arahama: about **90% of 2,271 people saved** and **520 sheltered** at the
Elementary School. Running GTEM on that scenario under matched assumptions gives
**83.4% evacuated**, against 79.5–81.5% for the ancestor.

The aggregate is in the right region. The **distribution is not**: GTEM sends
68% of everyone to a single destination, where the record and the earlier model
both show arrivals spread across three. See [validation/](../validation/) for
the full comparison and the four candidate causes.

One scenario, one seed, one aggregate, and a population spread uniformly because
Arahama has no population attribute — that is a first measurement, not a
validation. Until a real one exists:

- Do not present absolute GTEM numbers as predictions.
- Do present comparisons between scenarios, stating the assumptions.
- Do state, in any report or presentation, that the model is unvalidated.

---

## Known accuracy limits

| item | status |
|---|---|
| Crowd density | Measured over a whole street segment, not directionally. Two groups walking in opposite directions slow each other even if they never meet. |
| Reproducibility | A given seed and configuration reproduce exactly. Different seeds vary: on the reference case, +/- 0.82 pp (SD over 100 replicates). Always report a mean over replicates, never one run. |
| Street segments below 1 m | Produce implausible densities. Reported as a warning. |

---

## How to describe GTEM results responsibly

**Instead of:** "The model shows 1,847 people will die."
**Say:** "Under this model's assumptions — everyone on foot, everyone taking the
shortest route to the nearest safe zone, average 7-minute departure — about 18%
of residents in this area do not reach a safe zone before a 23-minute wave.
Averaged over 40 simulations. The model has not yet been validated against an
observed evacuation."

**Instead of:** "Street X is the worst bottleneck."
**Say:** "Street X accumulates the most crowding in these simulations. That
depends on the routing assumption that everyone takes the shortest path, so
treat it as a candidate for inspection rather than a finding."

---

## Source for the density–speed relation

> Mas, E., Suppasri, A., Imamura, F. & Koshimura, S. (2015). Agent-based
> Simulation of the 2011 Great East Japan Earthquake/Tsunami Evacuation: An
> Integrated Model of Tsunami Inundation and Evacuation.
> *Journal of Natural Disaster Science*, 34, 41.

GTEM derives from **TUNAMI-EVAC** (<https://github.com/erick2307/TUNAMI-EVAC>).

---

*Questions this page does not answer are probably answered in
[PREPARING_YOUR_CITY.md](PREPARING_YOUR_CITY.md) (input data) or the
[README](../README.md) (running the model).*
