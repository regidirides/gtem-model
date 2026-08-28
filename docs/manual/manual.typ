// =============================================================================
// GTEM — User Manual
//
// Build:   typst compile manual.typ GTEM_Manual.pdf
// Watch:   typst watch manual.typ GTEM_Manual.pdf
//
// Editing notes for the team:
//   - Text is plain; headings are = / == / ===.
//   - Screenshots still to be taken are marked with #todo-shot(...). Each one
//     states exactly what to capture. Replace the call with #figure(image(...))
//     once you have the file. Search for "todo-shot" to find them all.
//   - Terminal output is read from transcripts/ so it stays true to the code.
// =============================================================================

#let version = "1.0.0"
#let manual-date = "August 2026"

#set document(title: "GTEM " + version + " — User Manual",
              author: ("Erick Mas", "Luis Moya", "Jheyder Perez"))

#set page(
  paper: "a4",
  margin: (top: 2.4cm, bottom: 2.2cm, x: 2.3cm),
  numbering: "1",
  number-align: center,
  header: context {
    if counter(page).get().first() > 1 [
      #set text(8pt, fill: luma(120))
      GTEM #version — User Manual
      #h(1fr)
      #counter(page).display()
    ]
  },
  footer: none,
)

#set text(font: ("Helvetica Neue", "Helvetica", "Arial"), size: 10pt, lang: "en")
#set par(justify: true, leading: 0.62em)
#show heading: set block(above: 1.5em, below: 0.9em)
#set heading(numbering: "1.1")

#show heading.where(level: 1): it => {
  pagebreak(weak: true)
  block[
    #set text(20pt, weight: "bold")
    #if it.numbering != none [
      #text(fill: rgb("#1565c0"))[Part #counter(heading).display()] #linebreak()
    ]
    #it.body
  ]
  line(length: 100%, stroke: 0.6pt + luma(180))
  v(0.4em)
}
#show heading.where(level: 2): set text(14pt, weight: "bold")
#show heading.where(level: 3): set text(11.5pt, weight: "bold")

#show link: it => text(fill: rgb("#1565c0"), it)
#show raw.where(block: false): it => box(
  fill: luma(240), inset: (x: 3pt, y: 0pt), outset: (y: 3pt),
  radius: 2pt, text(9pt, font: "Menlo", it)
)

// ---------------------------------------------------------------- helpers ---

#let callout(title, body, colour: rgb("#1565c0"), bg: rgb("#eef4fb")) = block(
  width: 100%, fill: bg, stroke: (left: 3pt + colour),
  inset: 10pt, radius: 2pt, above: 1em, below: 1em,
)[
  #text(weight: "bold", fill: colour)[#title] \
  #body
]

#let warn(title, body) = callout(title, body,
  colour: rgb("#c62828"), bg: rgb("#fdeeee"))

#let tip(title, body) = callout(title, body,
  colour: rgb("#2e7d32"), bg: rgb("#eef7ef"))

// A screenshot you still need to take. States exactly what to capture.
#let todo-shot(id, what, why) = block(
  width: 100%, fill: rgb("#fffbe6"), stroke: (paint: rgb("#f9a825"), dash: "dashed", thickness: 1pt),
  inset: 10pt, radius: 3pt, above: 1em, below: 1em,
)[
  #text(weight: "bold", fill: rgb("#b58100"))[SCREENSHOT #id — to be added] \
  #text(9.5pt)[*Capture:* #what] \
  #text(9.5pt, fill: luma(90))[*Why:* #why] \
  #v(0.3em)
  #text(8.5pt, style: "italic", fill: luma(110))[
    Save as #raw("figures/" + id + ".png") and replace this box with
    #raw("#figure(image(\"figures/" + id + ".png\"), caption: [...])")
    — see the appendix at the end of this manual.
  ]
]

#let term(path, caption: none) = figure(
  block(width: 100%, fill: luma(28), inset: 9pt, radius: 3pt)[
    #set align(left)
    #set text(8pt, font: "Menlo", fill: rgb("#e8e8e8"))
    // block: true is essential - an inline raw would be caught by the
    // inline-code show rule above and rendered dark-on-dark.
    #raw(read(path).trim("\n"), block: true)
  ],
  caption: caption, supplement: [Terminal],
)

// ============================================================== title page ===

#page(numbering: none, header: none)[
  #v(2cm)
  #align(center)[
    #image("figures/logo_gtem.png", width: 5.5cm)
    #v(1.2cm)
    #text(30pt, weight: "bold")[GTEM]
    #v(0.1cm)
    #text(15pt)[Global Tsunami Evacuation Model]
    #v(0.5cm)
    #line(length: 45%, stroke: 0.8pt + luma(150))
    #v(0.5cm)
    #text(17pt, weight: "medium")[User Manual]
    #v(0.3cm)
    #text(12pt, fill: luma(90))[Version #version · #manual-date]
    #v(2.5cm)
    #block(width: 82%)[
      #set text(10.5pt)
      #set par(justify: false)
      An agent-based model of pedestrian tsunami evacuation, written for staff in
      coastal local governments rather than for modelling specialists.
    ]
    #v(2.2cm)
    #grid(columns: 3, column-gutter: 1.1cm, align: horizon,
      image("figures/logo_irides.png", width: 3.1cm),
      image("figures/logo_pucp.png", width: 2.2cm),
      image("figures/logo_cdri.png", width: 2.6cm),
    )
    #v(1.4cm)
    #text(9.5pt, fill: luma(90))[
      Erick Mas · Luis Moya · Jheyder Perez \
      Funded by the Coalition for Disaster Resilient Infrastructure \
      CDRI Fellowship Programme 2025–2026
    ]
  ]
]

// ================================================================ contents ===

#page(numbering: none, header: none)[
  #text(18pt, weight: "bold")[Contents]
  #v(0.6em)
  #outline(title: none, indent: 1.2em, depth: 2)
]

#counter(page).update(1)

// =============================================================== preface =====

#heading(level: 1, numbering: none)[Before you begin]

== Who this manual is for

You do not need to be a programmer or a modeller. The manual assumes you can
install software, open a terminal window, and edit a text file. Everything else
is explained.

If you have used a geographic information system such as QGIS, @part-city will
make more sense — but you can run GTEM on the areas supplied with it without
touching a GIS at all.

== What GTEM does

You give GTEM three things:

+ a road network for a coastal area,
+ where people are, and
+ the number of minutes between the earthquake and the arrival of the wave.

GTEM simulates every person walking to the nearest safe zone and reports who
reaches safety in time, who does not, *where they were when they ran out of
time*, and which streets became bottlenecks.

== What GTEM is for, and what it is not for

#warn("Read this before you use a result in a decision")[
  GTEM is a tool for *comparing options*, not for predicting what will happen.

  "Opening this road leaves 400 fewer people exposed" is a defensible use of the
  model. "1,847 people will die" is not.

  GTEM has *not been validated against an observed evacuation.* Until it has,
  treat every absolute number as provisional. The full statement of what the
  model can and cannot answer is in `docs/LIMITATIONS.md`, and you should read
  it before presenting results to anyone.
]

== How to use this manual

#table(
  columns: (auto, 1fr),
  stroke: 0.4pt + luma(200),
  inset: 7pt,
  table.header([*If you want to…*], [*Read*]),
  [install GTEM and see it work], [@part-start],
  [understand what the results mean], [@part-results],
  [run realistic studies], [@part-scenarios],
  [use GTEM on your own town], [@part-city],
  [know how the model works inside], [@part-model],
  [look something up], [@part-reference],
)

#tip("A note on commands")[
  Anything in a dark box is typed into a terminal. Type the command, press
  Enter, and compare what you see with what the manual shows. Text after a `#`
  in a configuration file is a comment and is ignored.
]

// ========================================================= PART I: START =====

= Getting started <part-start>

== What you need

#table(
  columns: (auto, 1fr),
  stroke: 0.4pt + luma(200), inset: 7pt,
  table.header([*Item*], [*Notes*]),
  [A computer running Windows 10/11, macOS or Linux],
    [Any machine from the last few years is enough. A full run of a
     17,000-person area takes about 90 seconds.],
  [NetLogo 7.0.4], [Free. This is the simulation engine GTEM drives.
     Java is bundled with it — you do *not* need to install Java separately.],
  [Miniforge, Miniconda or Anaconda], [Free. Used to install the Python packages
     GTEM needs, without disturbing anything else on your machine.],
  [About 1 GB of free disk space], [The download is small; results accumulate.],
)

== Installing

=== Step 1 — Install NetLogo

Download NetLogo 7.0.4 from #link("https://ccl.northwestern.edu/netlogo/")[ccl.northwestern.edu/netlogo] and
install it in the default location.

#table(
  columns: (auto, 1fr), stroke: 0.4pt + luma(200), inset: 7pt,
  table.header([*System*], [*Default location GTEM looks in*]),
  [Windows], [`C:\Program Files\NetLogo 7.0.4`],
  [macOS], [`/Applications/NetLogo 7.0.4`],
  [Linux], [`/opt/netlogo-7.0.4`],
)

If you install it somewhere else, set an environment variable named
`NETLOGO_HOME` to that folder. GTEM will tell you if it cannot find NetLogo, and
will list the places it looked.

#todo-shot("S1",
  [The NetLogo download page, with the 7.0.4 download button visible.],
  [New users often download the newest version rather than 7.0.4. A picture of
   the right button prevents the most common installation mistake.])

=== Step 2 — Get GTEM

Download or clone the GTEM folder and put it somewhere with a short path — for
example `C:\GTEM` on Windows, or your home folder on macOS or Linux.

#warn("Avoid long folder paths on Windows")[
  Windows has a 260-character limit on file paths. GTEM writes results into
  nested folders, so placing it inside a deeply nested location such as
  `C:\Users\...\OneDrive\Documents\Projects\2026\...` can cause errors that look
  unrelated. A short path avoids the problem entirely.
]

#todo-shot("S2",
  [The unzipped GTEM folder open in Windows Explorer or macOS Finder, showing
   `main.py`, `data`, `examples`, `docs` and `src`.],
  [Confirms the reader has unzipped to the right level. A common error is a
   folder containing only another folder.])

=== Step 3 — Create the environment

Open a terminal — on Windows this is the *Miniforge Prompt* or *Anaconda
Prompt* from the Start menu, not the ordinary Command Prompt. Move into the
GTEM folder and run:

```bash
conda env create -f environment.yml
conda activate gtem
```

The first command downloads and installs everything GTEM needs and takes a few
minutes. The second switches your terminal into that environment.

#tip("You must activate the environment in every new terminal")[
  `conda activate gtem` applies only to the window you type it in. If you close
  the terminal and open a new one, run it again. If a command suddenly reports
  that a package is missing, this is almost always the reason.
]

#todo-shot("S3",
  [The Miniforge Prompt on Windows immediately after `conda activate gtem`,
   with the prompt showing `(gtem)` at the start of the line.],
  [The `(gtem)` prefix is the visual confirmation that the environment is
   active. Readers who miss it hit confusing errors later.])

== Checking that it worked

Run:

```bash
python check_environment.py
```

This imports every package GTEM needs, finds NetLogo, and confirms the model
and data are present. You should see something close to this:

#term("transcripts/check_environment.txt",
  caption: [`check_environment.py` on a correctly installed machine.])

If anything is wrong, the tool prints the exact command to fix it and exits with
an error. It checks by *importing* each package rather than merely looking for
it on disk, because a package can be present and still fail to load.

== Your first run

Start with the built-in test area `Synthetic_Corridor`. It is deliberately
artificial: two straight 1,000-metre corridors, each ending at a safe zone. A
person walking at the free-flow speed of 1.33 m/s covers 1,000 m in
*12.53 minutes* — so you know in advance what the answer should be.

Create a file called `my_first_run.txt` containing:

```
zone              = Synthetic_Corridor
adults            = 50
elderly           = 0
children          = 0
tsunami_eta       = 30
departure_mean    = 0
dt                = 5
seed              = 1
recompute_routes  = true
```

Then run:

```bash
python main.py --config my_first_run.txt
```

The run finishes in under a minute and ends with everyone safe at about
12.5 minutes — matching the hand calculation. If you see that, GTEM is working
correctly on your machine.

Results are written to `Outputs/Synthetic_Corridor/1/`. Open the PDF first.

#todo-shot("S4",
  [The `Outputs/Synthetic_Corridor/1/` folder showing the 14 output files.],
  [Shows the reader where results appear and what a complete set looks like,
   so they can tell at a glance if something is missing.])

== A real area

Now run one of the supplied Peruvian study areas. First check its data:

```bash
python check_inputs.py Chimbote_Zona1
```

#term("transcripts/check_inputs.txt",
  caption: [Checking a real study area. Warnings are normal — real data is
            rarely perfect. What matters is that you read them.])

Then run it:

```bash
python main.py --config examples/config_example.txt
```

This simulates 17,261 people with a 23-minute tsunami arrival time, and takes
about 90 seconds.

// ======================================================= PART II: RESULTS ====

= Reading your results <part-results>

Every run writes fourteen files into `Outputs/<area>/<seed>/`. Start with the
PDF; the CSV files are there when you need the numbers behind it.

== The four numbers that matter

They appear on page 1 of the PDF and in `Run_Summary.csv`.

#table(
  columns: (auto, 1fr), stroke: 0.4pt + luma(200), inset: 7pt,
  table.header([*Number*], [*What it means*]),
  [*Evacuated before the tsunami*],
    [Reached a safe zone *before* the wave. These are the only people who are
     actually safe.],
  [*NOT evacuated*],
    [Everybody else. Always look at this number, not only the first one.],
  [*Caught in transit*],
    [Still walking when the wave arrived. Usually improved by earlier departure
     or by placing safe zones closer.],
  [*Stranded (no route)*],
    [No path to any safe zone from where they started — before the simulation
     even began. This is a *network* problem, not a behaviour problem. No amount
     of preparedness or warning time fixes it.],
)

The three outcomes always add up to the number of people simulated. GTEM
enforces this while it runs: if they ever failed to add up, the run would stop
with an error rather than report a number that leaves people out.

#warn("Reaching a safe zone after the wave is not safety")[
  GTEM stops the simulation at the tsunami arrival time. Anyone still walking is
  counted as *not evacuated*, however close they were. This is deliberate. A
  model that counts late arrivals as survivors flatters the plan being tested.
]

== The five figures

=== Figure 1 — Evacuation progress by age group

#figure(image("figures/fig_dynamics.png", width: 82%),
  caption: [Each age group has its own panel, shown as a percentage of that
            group. The vertical red line is the tsunami arrival time.])

*What to look for.* Compare the three panels. In the example above, adults reach
68.9% but the elderly reach only 52.5% — a 16-point gap. That gap is an
actionable finding: it points to assisted evacuation or targeted outreach, not
to more signage.

Anything to the right of the red line did not happen in time.

=== Figure 2 — Walking speed by age group

#figure(image("figures/fig_speed.png", width: 82%),
  caption: [Mean walking speed for each group. The dotted line is that group's
            free-flow speed — the speed with the street to themselves.])

*What to look for.* A curve sitting on the dotted line means people are walking
freely. A curve falling away from it means crowding. In the example, all three
groups drop sharply after about minute 12, which is congestion building on the
approaches to the safe zones, not people becoming tired — GTEM has no fatigue.

=== Figure 3 — Vulnerability by starting location

#figure(image("figures/fig_vulnerability.png", width: 80%),
  caption: [Where each person *started*, coloured by how long they took to
            reach safety. Black points never reached safety at all.])

*What to look for.* Black clusters. These are the priority areas: places where
evacuation *fails*, not merely where it is slow. In the example the whole
south-western district is black.

#tip("This map shows everybody, including the people who did not make it")[
  A blank area on this map means nobody started there. It does *not* mean
  everybody there was safe. Places where evacuation failed are drawn in black
  precisely so that they cannot be mistaken for empty space.
]

=== Figure 4 — Demand on each safe zone

#figure(image("figures/fig_safezones.png", width: 78%),
  caption: [Marker size and colour show how many people arrived. The busiest
            are labelled.])

*What to look for.* Two things.

First, *concentration*. In the example one safe zone receives 4,873 people while
another receives none. GTEM sends everyone to the nearest safe zone by distance,
so demand piles up wherever that rule points.

Second, *capacity*. GTEM assumes safe zones are infinitely large. It will not
warn you that a plaza rated for 500 people received 1,200. Checking the numbers
on this figure against the real capacity of each site is a manual step, and an
important one.

A safe zone that receives nobody is worth investigating: it may be unreachable,
badly placed, or simply redundant.

=== Figure 5 — Street congestion

#figure(image("figures/fig_congestion.png", width: 82%),
  caption: [Streets ranked by accumulated crowding over time, with the ten most
            critical stretches numbered and listed.])

*What to look for.* The ranked list names streets by the pair of intersections
at their ends. These are the stretches where widening, clearing obstacles or
signposting an alternative would save the most time.

Criticality here is *accumulated* crowding, not the single worst moment. A
street that was briefly very busy ranks below one that was moderately crowded
for many minutes — because the second one delays far more people.

== The other files

#table(
  columns: (auto, 1fr), stroke: 0.4pt + luma(200), inset: 7pt,
  table.header([*File*], [*Contents*]),
  [`Run_Summary.csv`], [One row: every headline number for this run.],
  [`Report1_Dynamics.csv`], [The evacuation curve, minute by minute.],
  [`Report2_Speeds.csv`], [Mean speed per age group over time.],
  [`Report3_Vulnerability.csv`], [One row per person: where they started, how
     long they took, and their outcome.],
  [`Report4_SafeZones.csv`], [Arrivals at each safe zone.],
  [`Report5_Congestion.csv`], [Every street, ranked by accumulated crowding.],
  [`resolved_config.txt`], [Every setting actually used, including defaults you
     did not write. Keep this: it is what makes a result reproducible.],
  [`warnings.log`], [Problems found in your input data. See below.],
)

== Always read `warnings.log`

Every run writes it, and the same contents appear in the PDF. It reports things
GTEM found wrong with your *input data* — not with the simulation.

When there is nothing to report it says `No input warnings.` explicitly, so
silence always means "checked and clean", never "not checked".

On the supplied Chimbote area, five warnings appear. The most serious is:

#block(fill: rgb("#fffbe6"), inset: 9pt, radius: 3pt, width: 100%)[
  #text(9pt, font: "Menlo")[
    DISCONNECTED NETWORK: 884 of 4468 road nodes (19.8%) have no route to any
    safe zone. Anyone starting there is counted as stranded.
  ]
]

Nearly a fifth of that road network cannot reach safety at all. That is a
finding about the *town*, and it deserves attention before any conclusion is
drawn about behaviour or warning times.

== One run is not a result

GTEM is stochastic: departure times and starting positions are drawn at random.
Two runs with different seeds give different answers. Across 100 replicates of
one Chimbote scenario, individual runs ranged from 80.1% to 84.5% evacuated —
a spread of more than four percentage points from chance alone.

#warn("Never quote a single run")[
  Run replicates and report the mean with its spread. @part-scenarios explains
  how, and how many replicates you need. A single run tells you what one
  possible evening looked like, not what the town can expect.
]

// ===================================================== PART III: SCENARIOS ===

= Running real studies <part-scenarios>

== The configuration file

Every setting lives in a plain text file. You never edit any Python file.

Copy `examples/config_example.txt`, edit the copy, and pass it with `--config`.
Every line is `setting = value`; anything after `#` is a comment.

=== Settings you must provide

#table(
  columns: (auto, auto, 1fr), stroke: 0.4pt + luma(200), inset: 6pt,
  table.header([*Setting*], [*Example*], [*Meaning*]),
  [`zone`], [`Chimbote_Zona1`],
    [Folder name inside `data/`. Must match exactly, including capitals.],
  [`adults`], [`11328`], [Number of adults to simulate.],
  [`elderly`], [`1917`], [Number of elderly people.],
  [`children`], [`4016`], [Number of children.],
  [`tsunami_eta`], [`23`],
    [*The single most important number.* Minutes from the earthquake to the
     arrival of the wave. The simulation stops here.],
)

=== Settings with sensible defaults

#table(
  columns: (auto, auto, 1fr), stroke: 0.4pt + luma(200), inset: 6pt,
  table.header([*Setting*], [*Default*], [*Meaning*]),
  [`departure_mean`], [`7`],
    [Average minutes before a person starts to move. The most influential
     behavioural assumption in the model.],
  [`dt`], [`10`],
    [Seconds of simulated time per step. Must be above 0 and at most 10.
     Smaller is more accurate and slower.],
  [`end_of_simulation`], [`0`],
    [Extra hard stop in minutes. `0` means "stop at the tsunami arrival time",
     which is almost always what you want.],
  [`road_width`], [`2.8`], [Usable width of one lane, in metres.],
  [`capacity_multiplier`], [`1`],
    [Scales effective road width. `1` is undamaged; `0.5` is half.],
  [`max_snap_distance`], [`50`],
    [How far a person may start from the road network before it is reported.],
  [`vulnerability_low` / `_high`], [`11` / `17`],
    [Colour bands on the vulnerability map, in minutes.],
  [`density_low` / `_high`], [`0.3` / `3`],
    [Congestion colour bands, in people per square metre.],
  [`seed`], [`0`],
    [`0` picks a random seed and records it. Any other number reproduces that
     exact run.],
  [`recompute_routes`], [`false`],
    [Rebuild the route table. Needed only after the road network changes.],
  [`time_margin_analysis`], [`false`],
    [Measure how much more time a full evacuation would need. Roughly doubles
     the runtime. See @sec-margin.],
  [`record_video`], [`false`], [Record an MP4. Slow, and produces a large file.],
)

#todo-shot("S5",
  [A configuration file open in a text editor (Notepad, TextEdit or VS Code),
   with a couple of values highlighted.],
  [Many readers have never edited a plain-text configuration file and are unsure
   what "edit the copy" means in practice.])

== When something is wrong

GTEM refuses to run rather than produce a plausible but wrong answer. Every
rejection names the setting and the acceptable range:

#term("transcripts/error_invalid_dt.txt",
  caption: [A rejected configuration. Nothing is written; nothing needs
            cleaning up.])

No invalid input ever produces an output folder that could be mistaken for a
result. If a run fails part-way through, GTEM leaves a file called `FAILED.txt`
in the output folder so that a half-finished folder can never be read as a
finished one.

== Replicates: how many runs do you need? <sec-replicates>

Because the model is stochastic, a defensible result is a *mean over
replicates*. Batch runs do this for you.

Edit `examples/scenario_list.csv`. Each row is a scenario; the `Count` column
says how many replicates to run:

```
Zone,Adults,Elderly,Children,TR,Count,Vuln_Low,Vuln_High,Tsunami_ETA,...
Chimbote_Zona1,11328,1917,4016,7,40,11,17,23,...
```

Then:

```bash
python batch_main.py --input examples/scenario_list.csv --seed 2026 --workers 4
```

`--seed` makes the whole batch reproducible. `--workers` sets how many runs
happen at once; each one needs its own Java process, so start with 2–4.

=== What a batch produces

#table(
  columns: (auto, 1fr), stroke: 0.4pt + luma(200), inset: 7pt,
  table.header([*File*], [*Contents*]),
  [*`Batch_Report.pdf`*],
    [*Start here.* Means with their spread, a comparison between scenarios, and
     an explicit verdict on whether you ran enough replicates.],
  [`Aggregated_Summary.csv`], [Mean, standard deviation and count per scenario.],
  [`Master_Summary.csv`], [One row per individual run.],
  [`Convergence.csv`, `Figure_Convergence.png`],
    [How the estimate settled as replicates accumulated.],
  [`Convergence_Summary.txt`],
    [The number of replicates needed for a stated precision.],
)

=== How many is enough?

GTEM answers this from your own data rather than asking you to guess. It
accumulates the coefficient of variation from run 1 onward — runs 1–2, 1–3,
1–4 and so on — and reports where it settles.

On the reference area, two independent criteria agree on about *40 replicates*:

#table(
  columns: (1fr, auto), stroke: 0.4pt + luma(200), inset: 7pt,
  table.header([*Criterion*], [*Replicates*]),
  [Coefficient of variation stays within 10% of its final value], [40],
  [95% confidence interval of the mean within ±0.25 percentage points], [41],
  [95% confidence interval within ±0.50 percentage points], [11],
  [95% confidence interval within ±0.10 percentage points], [256],
)

The batch report states plainly when a batch was *too small*, naming the
scenarios whose estimates have not settled. Take that seriously: it is the
difference between a result and an anecdote.

=== What an unfinished batch looks like

#figure(
  image("figures/fig_convergence.png", width: 88%),
  caption: [`Figure_Convergence.png` from a deliberately short batch of 14
    replicates. The curve is still moving at the right-hand edge, and
    `Convergence_Summary.txt` reports #raw("CV settles at n = not reached").
    The estimate has not stabilised.],
)

A converged curve flattens and stays flat. If yours is still rising, falling or
jumping at the right-hand edge, the batch is too small — whatever the mean
happens to say. In the batch above, the achieved precision was ±0.661
percentage points, and reaching ±0.25 would need 98 replicates.

== How much time was missing? <sec-margin>

A run bounded by the tsunami arrival time can tell you that the town ran out of
time, but not by how much. Setting `time_margin_analysis = true` repeats the
simulation once with the same seed and no time limit, and adds a section to the
report:

#block(fill: luma(245), inset: 10pt, radius: 3pt, width: 100%)[
  #text(9.5pt)[
    On the reference area, a full evacuation needs *56.7 minutes*. The wave
    arrives at *23.0 minutes*. The shortfall is *33.7 minutes*.
  ]
  #v(0.4em)
  #table(
    columns: (auto, auto, auto, auto), stroke: 0.4pt + luma(200), inset: 5pt,
    align: (left, right, right, right),
    table.header([Extra time], [Reached safety], [Additional people], [Share]),
    [+1 min], [11,846], [573], [3.3%],
    [+2 min], [12,295], [1,022], [5.9%],
    [+3 min], [12,853], [1,580], [9.2%],
    [+5 min], [13,862], [2,589], [15.0%],
    [+10 min], [15,505], [4,232], [24.5%],
  )
]

Roughly 500 people per additional minute. Because the model treats a longer
warning and an earlier departure identically, this table is also a measure of
what *preparedness* is worth: persuading people to leave two minutes sooner has
the same effect as two minutes of extra warning.

== Comparing scenarios

Comparison is the strongest use of GTEM, because both scenarios share the same
assumptions and much of the uncertainty cancels out.

The supplied areas include a worked example: `Chimbote_Zona1` and
`Chimbote_Zona1_colapso1`, the same town with earthquake damage to the road
network. Put both in one scenario file and run them together.

Ten replicates of each, at the full population of 17,261:

#table(
  columns: (1fr, auto, auto, auto), stroke: 0.4pt + luma(200), inset: 7pt,
  align: (left, right, right, right),
  table.header([*Scenario*], [*Evacuated (mean ± SD)*], [*Stranded*], [*Difference*]),
  [Chimbote_Zona1], [64.95% ± 0.72], [0], [baseline],
  [Chimbote_Zona1_colapso1], [29.50% ± 0.43], [7,194], [−35.45 points],
)

The `Stranded` column explains the mechanism, and it is the more useful finding.
Road damage does not merely slow people down: it cuts 7,194 people off from any
safe zone at all. Those people cannot be helped by more warning time. They need
either a route that survives the earthquake or a safe zone on their side of the
damage.

#tip("How to tell a real difference from noise")[
  Compare the difference against the standard deviations. Here the gap is 35.45
  points against spreads under one point, so the difference is unmistakably
  real. A difference *smaller* than the spread is indistinguishable from the
  luck of the random seed, and should not be reported as a finding.
]

Note that ten replicates were enough to establish *this* difference but not to
pin down either mean precisely: `Convergence_Summary.txt` for this batch asks
for 32 replicates of the baseline to reach ±0.25 percentage points. A large
difference needs fewer replicates than a precise absolute number.

// ======================================================== PART IV: YOUR CITY =

= Using GTEM on your own town <part-city>

This is the most demanding part of the work. GTEM does not yet build a study
area for you; you assemble four map layers in a GIS, and GTEM checks them.

Budget a few hours the first time. The second town is much faster.

== What GTEM needs

Four shapefiles, in a folder named after your area, inside `data/`:

```
data/My_City_Zone1/
    My_City_Zone1.shp            zone boundary        (polygon)
    puntos_My_City_Zone1.shp     intersections        (points)
    rutas_My_City_Zone1.shp      road network         (lines)
    manzanas_My_City_Zone1.shp   census blocks        (polygons)
```

#tip("Why some names are in Spanish")[
  `puntos`, `rutas` and `manzanas` mean points, routes and blocks. They were
  kept because the project's partners already hold data under those names.
  They are file names only — everything inside GTEM is in English.
]

Each `.shp` needs its companion files (`.dbf`, `.shx`, `.prj`, `.cpg`) beside
it. Copy them all.

== Get the coordinate system right first

#warn("A geographic coordinate system will be rejected")[
  Every layer must use the same *projected, metric* coordinate reference system
  — normally a UTM zone. GTEM measures distances in metres.

  If you supply latitude and longitude (EPSG:4326, often shown as "WGS 84"),
  distances would be measured in *degrees* and every result would be
  meaningless. GTEM refuses to run rather than let that happen.

  In QGIS: *Layer ▸ Export ▸ Save Features As…*, and set the CRS there.
]

#todo-shot("S6",
  [The QGIS *Save Features As…* dialog with the CRS selector showing a UTM zone.],
  [Reprojection is the single most common preparation error, and the dialog is
   not obvious to a first-time user.])

== What each layer must contain

=== Zone boundary — `<zone>.shp`

One polygon covering the study area. GTEM uses only its extent, so a rectangle
is fine. No attributes are needed.

Keep it tight: the extent sets the spatial resolution, so a boundary with a
large empty margin wastes it.

=== Intersections — `puntos_<zone>.shp`

Points where roads meet, plus the safe zones. These are the nodes of the
network.

#table(
  columns: (auto, auto, auto, 1fr), stroke: 0.4pt + luma(200), inset: 6pt,
  table.header([*Attribute*], [*Type*], [*Required*], [*Meaning*]),
  [`fid`], [integer], [yes],
    [Unique identifier. Duplicates cause silent, seed-dependent errors.],
  [`is_shelter`], [integer], [yes],
    [`1` marks a safe zone, `0` an ordinary intersection.],
  [`name`], [text], [optional],
    [A human name such as "Colegio San Pedro". Used to label the busiest safe
     zones; without it they are labelled by number.],
)

#warn("Deciding what counts as a safe zone is your judgement, not a dataset")[
  GTEM does not read an inundation map. It simply trusts your `is_shelter`
  flags. That one decision drives the entire result, so it should come from your
  hazard map and civil-protection plan.

  At least one point must have `is_shelter = 1`, or nobody can evacuate — GTEM
  stops with an error rather than reporting that everyone died.
]

=== Road network — `rutas_<zone>.shp`

One line per street segment, joining two intersections.

#table(
  columns: (auto, auto, auto, 1fr), stroke: 0.4pt + luma(200), inset: 6pt,
  table.header([*Attribute*], [*Type*], [*Required*], [*Meaning*]),
  [`start_node`], [integer], [yes], [`fid` of the intersection at one end.],
  [`end_node`], [integer], [yes], [`fid` of the intersection at the other end.],
  [`cost`], [number], [yes],
    [Length in *metres*, following the street rather than straight-line.],
  [`lanes`], [integer], [yes],
    [Number of lanes. Multiplied by `road_width` to give walkable width, which
     determines crowding. A narrow alley is `1`.],
)

Avoid segments shorter than about one metre: a single person on a 0.1 m segment
produces an absurd density and a false congestion hotspot. `check_inputs.py`
counts them for you.

=== Census blocks — `manzanas_<zone>.shp`

Polygons where people start. GTEM scatters people inside them in proportion to
population.

#table(
  columns: (auto, auto, 1fr), stroke: 0.4pt + luma(200), inset: 6pt,
  table.header([*Attribute*], [*Required*], [*Meaning*]),
  [`T_TOTAL`], [strongly recommended],
    [Resident population of the block. `Population` and `POP` are also accepted.],
)

#warn("Without a population attribute the results are not worth much")[
  GTEM will still run, spreading people *uniformly* and ignoring where they
  actually live. It says so loudly in `warnings.log` and in the report. This is
  the most common preparation mistake.
]

Clip the blocks to the area at risk. GTEM creates people wherever you supply a
block, so an unclipped layer simulates people who were never in danger.

== Where to get the data

#table(
  columns: (auto, 1fr), stroke: 0.4pt + luma(200), inset: 6pt,
  table.header([*Layer*], [*Open sources*]),
  [Road network],
    [OpenStreetMap, via the QuickOSM plugin in QGIS, Geofabrik extracts, or
     Overpass. Municipal cadastre if you have it.],
  [Intersections], [Derived from the road network — see below.],
  [Census blocks],
    [Your national statistics agency (INEI in Peru, INE in Chile, e-Stat in
     Japan, IBGE in Brazil, BPS in Indonesia, Eurostat in the EU). Global
     fallbacks: WorldPop, the Global Human Settlement Layer, or Meta's High
     Resolution Settlement Layer via the Humanitarian Data Exchange.],
  [Zone boundary],
    [Draw it yourself, or use an administrative boundary from OpenStreetMap or
     GADM.],
  [Tsunami arrival time],
    [Your national tsunami warning agency (DHN in Peru, JMA in Japan, SHOA in
     Chile), national hazard studies, or the NOAA historical tsunami database.],
  [Inundation extent],
    [National hazard maps. Failing that, a conservative elevation threshold from
     a free digital elevation model: Copernicus DEM GLO-30, NASADEM or ALOS
     World 3D.],
)

== Building the layers in QGIS

+ *Set the project coordinate system* to your metric CRS before anything else.
+ *Load a road centreline layer* — municipal data, or OpenStreetMap through the
  QuickOSM plugin.
+ *Clip the roads* to your study area.
+ *Split the lines at intersections*, aiming for segments of roughly 10–25 m.
+ *Extract the vertices* (*Vector ▸ Geometry Tools ▸ Extract Vertices*) and
  remove duplicates. This becomes `puntos_`.
+ *Add `fid`* as a unique integer on the points.
+ *Join the node identifiers to the lines*, using *Join attributes by nearest*
  twice — once for each end — to fill `start_node` and `end_node`.
+ *Add `cost`* with the field calculator: `$length`. Confirm the units are
  metres.
+ *Add `lanes`*, defaulting to 1 and raising it for main roads.
+ *Mark the safe zones*: set `is_shelter = 1` on points outside the inundation
  area or on vertical-evacuation buildings. Add `name` if you can.
+ *Prepare the census blocks* with a population column, clipped to the risk area.
+ *Export all four layers* into `data/<zone>/` with the required names.

#todo-shot("S7",
  [QGIS *Extract Vertices* running on the road layer, with the result visible.],
  [Step 5 is where most people get lost. A picture of the menu path and the
   resulting point layer removes the ambiguity.])

#todo-shot("S8",
  [The QGIS field calculator creating `cost` with the expression `$length`.],
  [Shows both where the calculator is and what the expression looks like.])

#todo-shot("S9",
  [The attribute table of `puntos_` with `fid` and `is_shelter` visible, and at
   least one row where `is_shelter` is 1.],
  [Readers need to see that `is_shelter` is an ordinary integer column they
   edit by hand, not something GTEM computes.])

== Check before you simulate

```bash
python check_inputs.py My_City_Zone1
```

This is the step that turns a confusing mid-simulation failure into a
checklist. Run it every time you change the data.

Here it is on a deliberately broken area supplied with GTEM:

#term("transcripts/check_inputs_broken.txt",
  caption: [`Synthetic_Broken` is included so you can see what a bad folder
            looks like before you meet one of your own.])

=== What the messages mean

#table(
  columns: (auto, 1fr), stroke: 0.4pt + luma(200), inset: 6pt,
  table.header([*Message*], [*What to do*]),
  [geographic CRS], [Reproject every layer to UTM. Nothing else matters until
     this is fixed.],
  [missing `start_node`], [The join in step 7 did not run, or produced a
     differently named column.],
  [no safe zones], [No point has `is_shelter = 1`.],
  [*X% cannot reach any safe zone*],
    [The network is fragmented, or a safe zone sits on an isolated node. Anyone
     starting there is counted as stranded before the simulation begins. Above
     roughly 10% this is worth fixing.],
  [network is in N disconnected pieces],
    [Usually unsplit lines, or endpoints that do not quite coincide. Snap the
     geometry and extract the vertices again.],
  [links shorter than 1 m], [Over-splitting. Merge or delete them.],
  [no population field], [Add `T_TOTAL` to the census blocks.],
)

== A worked example to compare against

`data/Chimbote_Zona1` is a complete, working area — and a realistic one.
`check_inputs.py` reports four warnings on it, including that 19.8% of its
starting points cannot reach a safe zone. Compare your own folder against it
rather than against an imaginary perfect dataset.

// ======================================================== PART V: THE MODEL ==

= How the model works <part-model>

This part explains what happens inside a run. You do not need it to use GTEM,
but you do need it to defend a result.

== The sequence of a run

+ *Routes are computed once.* A single shortest-path search, seeded
  simultaneously from every safe zone, gives each intersection the next step
  towards the nearest one. The result is cached, so later runs on the same
  network are instant.
+ *People are placed.* Each person is put at a random point inside a census
  block, chosen in proportion to the population of that block, and attached to
  the nearest usable intersection.
+ *Each person waits.* A departure delay is drawn at random (see below).
+ *Each person walks* their route, one step per timestep, at a speed set by
  their age group and by how crowded the street is.
+ *The run stops* at the tsunami arrival time, or earlier if everyone has been
  resolved.
+ *Every person is classified* as evacuated, caught in transit, or stranded.
+ *Figures, tables and the report are written.*

== Walking speed

Each age group has a free-flow speed — the speed with the street to itself:

#table(
  columns: (auto, auto, auto), stroke: 0.4pt + luma(200), inset: 7pt,
  table.header([*Group*], [*Factor*], [*Free-flow speed*]),
  [Adults], [1.00], [1.33 m/s],
  [Children], [0.80], [1.06 m/s],
  [Elderly], [0.70], [0.93 m/s],
)

As a street becomes crowded, speed falls. Below 0.3 people per square metre
everyone moves freely. Above 3.0 people per square metre movement is reduced to
a crawl of 0.2 m/s. Between those two densities speed falls linearly.

The relation is scaled by each group's own free-flow speed, so the ordering
between groups is preserved under congestion.

#block(fill: luma(245), inset: 10pt, radius: 3pt, width: 100%)[
  *Source of the density–speed relation*

  Mas, E., Suppasri, A., Imamura, F. & Koshimura, S. (2015). Agent-based
  Simulation of the 2011 Great East Japan Earthquake/Tsunami Evacuation: An
  Integrated Model of Tsunami Inundation and Evacuation. _Journal of Natural
  Disaster Science_, 34, 41.

  All six constants are configurable rather than fixed in the code.
]

== Departure times

Nobody starts moving at the instant of the earthquake. Each person waits a
random time drawn from a Rayleigh distribution whose *mean* is
`departure_mean`. The distribution is right-skewed: most people leave sooner
than the mean, and a tail leaves much later.

#warn("This is the assumption results are most sensitive to")[
  The shape of the departure curve is a modelling choice, not an observation of
  your town. If you have survey data on how quickly people actually left during
  a drill or a real event, it is the single most valuable thing you can
  contribute to the model.
]

== Routing

Routes are computed *before* the simulation and never change.

Every person is assumed to know the whole road network and to walk the shortest
route to the *nearest safe zone by distance* — not the emptiest one, and not the
fastest one under congestion.

#table(
  columns: (auto, 1fr), stroke: 0.4pt + luma(200), inset: 7pt,
  table.header([*Consequence*], [*What it means for your results*]),
  [Nobody re-routes],
    [A person walking into a jam keeps walking into it. Congestion is somewhat
     overstated at the bottleneck and understated on the alternatives real
     people would divert to.],
  [Perfect knowledge],
    [Real people take familiar routes, follow crowds, go the wrong way and
     collect family first. GTEM's evacuation is therefore *more efficient than
     reality*. Treat clearance times as a best case.],
  [Nearest, not emptiest],
    [Demand concentrates. One safe zone can receive thousands while another
     receives nobody.],
)

== Termination and outcome accounting

The run ends at whichever comes first: everybody resolved, or the tsunami
arrival time.

Every person ends in exactly one of three states, and GTEM checks while running
that the three add up to the number of people simulated. If they ever did not,
the run would stop with an error rather than report a number that quietly leaves
people out.

== What GTEM does not model

#table(
  columns: (auto, 1fr), stroke: 0.4pt + luma(200), inset: 7pt,
  table.header([*Not modelled*], [*Consequence*]),
  [Vehicles and bicycles],
    [In a town where many people would drive, congestion is optimistic.],
  [Safe-zone capacity],
    [A site is counted as safe however many people arrive. Check the demand
     figure against real capacity yourself.],
  [Inundation],
    [The tsunami is one number you supply. GTEM does not simulate the wave, its
     extent or its depth.],
  [Disability and reduced mobility],
    [Only three age groups exist. A town with a large care population is not
     well represented.],
  [Households and group behaviour],
    [Everyone evacuates alone. Nobody waits for or collects anybody.],
  [Time of day],
    [The population is a night-time, everyone-at-home estimate. Schools,
     workplaces and beaches are not represented.],
  [Buildings, debris and injury],
    [Nothing obstructs movement except other people.],
)

== The state of validation

#warn("GTEM has not been validated, and the one benchmark available says it is optimistic")[
  Everything above describes what GTEM *computes*. Whether that matches a real
  evacuation is a separate and harder question.

  GTEM descends from TUNAMI-EVAC1 (Mas, 2012), which *was* validated against the
  2011 evacuation of Arahama, Sendai: about *90% of 2,271 people saved*, and 520
  sheltered in the evacuation building. Under matched assumptions the ancestor
  gives *81.5%* and GTEM *83.4%* — close to each other, both below the observed
  figure.

  That is a starting point, not a validation: one scenario, one seed, one
  aggregate number. The comparison is also acutely sensitive to the departure
  assumption — the same GTEM run with a 26-minute-earlier mean departure
  evacuates *100%*. `validation/README.md` sets this out in full.

  Until a real validation exists: use GTEM to compare options, state the
  assumptions, and say in any report that the model is unvalidated.
]

// ==================================================== PART VI: REFERENCE =====

= Reference <part-reference>

== Writing the report in Spanish

The figures and both PDF reports can be produced in Spanish. Either set it in
the configuration file:

```
language = es
```

or override it on the command line, which is convenient when you want the same
scenario in both languages:

```bash
python main.py --config my_run.txt --language es
```

`batch_main.py` takes the same option.

#table(
  columns: (1fr, 1fr), stroke: 0.4pt + luma(200), inset: 7pt,
  table.header([*Translated*], [*Always English*]),
  [Figure titles, axis labels and legends; every heading, table and sentence in
   the single-run and batch PDF reports.],
  [Configuration keys, CSV column headers, output file names, and the settings
   listed in the report's configuration table.],
)

#tip("Why the data tables stay in English")[
  So that two runs can be compared column by column whatever language their
  reports were written in, and so a script written against your results keeps
  working when a colleague runs the model in the other language. The Spanish
  report says this on the page where it matters.
]

Two parts of a Spanish report remain in English: the warnings raised by the
simulation engine, and the console output. The report states this where the
warnings appear, so a reader is not left wondering.

To add another language, copy the `EN` table in `src/text_strings.py`, translate
the values, and register it in `TABLES`. The test suite checks that every
language has the same keys and the same `{placeholders}` as English.

== Command reference

#term("transcripts/main_help.txt", caption: [`python main.py --help`])

#term("transcripts/batch_help.txt", caption: [`python batch_main.py --help`])

#table(
  columns: (auto, 1fr), stroke: 0.4pt + luma(200), inset: 7pt,
  table.header([*Command*], [*Purpose*]),
  [`python check_environment.py`], [Is this machine able to run GTEM?],
  [`python check_inputs.py <zone>`], [Is this area's data usable?],
  [`python main.py --config <file>`], [Run one simulation.],
  [`python main.py --config <file> --language es`], [The same run, reported in Spanish.],
  [`python batch_main.py --input <csv>`], [Run many, with statistics.],
  [`python -m pytest tests/ -m "not engine"`], [Fast self-test, about a minute.],
  [`python -m pytest tests/`], [Full self-test, about half an hour.],
)

== Exit codes

#table(
  columns: (auto, 1fr), stroke: 0.4pt + luma(200), inset: 7pt,
  table.header([*Code*], [*Meaning*]),
  [`0`], [Finished; all outputs written.],
  [`1`], [The run failed. A `FAILED.txt` marker is left in the output folder.],
  [`2`], [The configuration or the input data is invalid. Nothing was run.],
)

== Folder layout

#term("transcripts/folder_tree.txt", caption: [The top level of a GTEM folder.])

== Troubleshooting

#table(
  columns: (auto, 1fr), stroke: 0.4pt + luma(200), inset: 6pt,
  table.header([*Symptom*], [*Cause and cure*]),
  [`No NetLogo installation was found`],
    [NetLogo is missing or installed elsewhere. Install 7.0.4, or set
     `NETLOGO_HOME` to its folder. The error lists the places GTEM looked.],
  [A package is reported missing],
    [You have not activated the environment. Run `conda activate gtem` in this
     terminal.],
  [`Zone folder not found`],
    [The `zone` setting does not match a folder inside `data/`. Capitals matter.],
  [`uses a geographic (lat/lon) CRS`],
    [Reproject every layer to a metric CRS such as UTM.],
  [`is out of range`],
    [The message names the setting and its acceptable values. Nothing was run.],
  [The run seems to hang on macOS or Linux],
    [Should not occur in this version, which starts the Java engine in headless
     mode. If it does, report it — include your operating system version.],
  [Results differ between two identical runs],
    [Check that `seed` is not `0`. A seed of `0` deliberately picks a new random
     seed each time, and records it in the results.],
  [Errors mentioning very long file paths on Windows],
    [Move the GTEM folder somewhere with a short path, such as `C:\GTEM`.],
)

== Glossary

#table(
  columns: (auto, 1fr), stroke: 0.4pt + luma(200), inset: 6pt,
  table.header([*Term*], [*Meaning*]),
  [Agent], [One simulated person.],
  [Caught in transit], [Still walking when the wave arrived.],
  [Coefficient of variation],
    [The spread of a set of results divided by their mean, as a percentage. Used
     to judge whether enough replicates were run.],
  [CRS], [Coordinate reference system. GTEM requires a projected, metric one.],
  [ETA], [Estimated time of arrival — of the tsunami, in minutes.],
  [Free-flow speed], [Walking speed with the street to yourself.],
  [Replicate], [One run of the same scenario with a different random seed.],
  [Safe zone], [A point flagged `is_shelter = 1`, where people are counted safe.],
  [Seed], [The number that fixes the random draws, making a run repeatable.],
  [Stranded], [No route to any safe zone from the starting point.],
  [Timestep (`dt`)], [Seconds of simulated time advanced in each step.],
)

== Licence, citation and credits

GTEM is released under the MIT licence. The study-area data supplied with it is
released for free redistribution alongside the software.

*Authors.* Erick Mas (IRIDeS, Tohoku University, Japan), Luis Moya (Pontificia
Universidad Catolica del Peru), Jheyder Perez (Pontificia Universidad Catolica
de Chile).

GTEM derives from TUNAMI-EVAC
(#link("https://github.com/erick2307/TUNAMI-EVAC")[github.com/erick2307/TUNAMI-EVAC]).
Funded by the Coalition for Disaster Resilient Infrastructure under the CDRI
Fellowship Programme 2025–2026. Built on NetLogo (Wilensky, 1999).

*If you use GTEM,* please cite both the software — see `CITATION.cff` — and the
source of the density–speed relation, Mas et al. (2015).

== Further reading in the GTEM folder

#table(
  columns: (auto, 1fr), stroke: 0.4pt + luma(200), inset: 7pt,
  table.header([*Document*], [*Contents*]),
  [`docs/LIMITATIONS.md`],
    [The full statement of what GTEM can and cannot answer. Read before
     presenting results.],
  [`docs/PREPARING_YOUR_CITY.md`], [The input schema in reference form.],
  [`docs/VERIFICATION.md`], [Evidence that the model computes what it claims.],
  [`docs/ROADMAP.md`], [Known gaps and what is planned.],
  [`validation/README.md`], [Why GTEM is not yet validated, and what that needs.],
  [`CHANGELOG.md`], [Release history.],
)

// ================================================= APPENDIX: SCREENSHOTS =====

#pagebreak()

#heading(level: 1, numbering: none)[Appendix — screenshots still to be captured]

This manual is written so that it is complete and usable *without* screenshots.
Nine places would nonetheless be clearer with one, and each is marked in the
text by an orange dashed box.

To add one: take the screenshot, save it in `docs/manual/figures/` under the
filename below, and in `manual.typ` replace the whole `#todo-shot(...)` block
with

```
#figure(image("figures/S1.png", width: 90%),
        caption: [NetLogo 7.0.4 on the downloads page.])
```

Then recompile:

```bash
typst compile docs/manual/manual.typ docs/manual/GTEM_Manual.pdf
```

#table(
  columns: (auto, auto, 1fr), stroke: 0.4pt + luma(200), inset: 6pt,
  table.header([*No.*], [*Filename*], [*What to capture*]),
  [S1], [`S1.png`],
    [The NetLogo downloads page with version 7.0.4 visible. Readers often
     install the newest version instead.],
  [S2], [`S2.png`],
    [The unzipped GTEM folder in Windows Explorer or macOS Finder, showing
     `main.py`, `data`, `examples`, `docs` and `src` at the top level.],
  [S3], [`S3.png`],
    [A Miniforge Prompt immediately after `conda activate gtem`, with the
     `(gtem)` prefix at the start of the line.],
  [S4], [`S4.png`],
    [The `Outputs/Synthetic_Corridor/1/` folder showing all 14 output files.],
  [S5], [`S5.png`],
    [A configuration file open in a plain-text editor (Notepad, TextEdit or
     VS Code), so readers see the `key = value` layout.],
  [S6], [`S6.png`],
    [The QGIS *Save Features As…* dialog with the CRS selector showing a UTM
     zone. Reprojection is the commonest preparation error.],
  [S7], [`S7.png`],
    [QGIS *Vector ▸ Geometry Tools ▸ Extract Vertices*, used to derive the
     intersection points from the road network.],
  [S8], [`S8.png`],
    [The QGIS field calculator creating the `cost` field from `$length`.],
  [S9], [`S9.png`],
    [The intersections attribute table with the `is_shelter` column, showing
     both `0` and `1` values.],
)

#v(0.6em)

Take every screenshot at a comfortable reading size, on a light background if
possible, and crop to the dialog or window concerned rather than the whole
desktop.
