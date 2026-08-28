# Preparing your own city

To run GTEM on a new area you need four shapefiles in a folder named after the
area. This page lists exactly what each one must contain, and the QGIS steps to
produce them.

**Check your work before running anything:**

```bash
python check_inputs.py My_City_Zone1
```

That reports missing layers, a wrong coordinate system, missing attributes, and
how much of your road network can actually reach a safe zone. Fix what it
reports before you simulate. A confusing failure halfway through a simulation is
almost always something this check would have caught in five seconds.

> **This is manual work.** GTEM has no automated preprocessing. Building a
> new area is a few hours of GIS work. An automated `preprocess.py` — including
> pulling the road network from OpenStreetMap — is the main planned addition for
> the next version.

---

## Folder layout

Everything lives in `data/<zone name>/`. The zone name is used in filenames
and in the configuration, and must match exactly:

```
data/My_City_Zone1/
    My_City_Zone1.shp        zone boundary        (polygon)
    puntos_My_City_Zone1.shp intersections        (points)
    rutas_My_City_Zone1.shp  road network         (lines)
    manzanas_My_City_Zone1.shp census blocks      (polygons)
```

Each `.shp` needs its companions (`.dbf`, `.shx`, `.prj`, `.cpg`) beside it.

> The `puntos_`, `rutas_` and `manzanas_` prefixes are Spanish. They were kept
> deliberately: renaming them would invalidate every dataset already prepared by
> the team and its partners. They are file naming only — everything inside GTEM
> is English.

---

## Coordinate reference system — get this right first

**Every layer must use the same PROJECTED, metric CRS.** UTM is the usual
choice: Peru's coast is UTM 17S or 18S; Sendai is JGD2011 Zone 10.

A geographic CRS (EPSG:4326, "WGS 84", plain latitude/longitude) **will be
rejected**. GTEM measures distances in metres; in a geographic CRS the numbers
are degrees, and every result would be meaningless. `check_inputs.py` catches
this, and so does the model at startup.

In QGIS: *Layer ▸ Export ▸ Save Features As…*, and set the CRS there.

---

## Layer 1 — zone boundary (`<zone>.shp`)

One polygon covering the study area. GTEM uses only its extent, to establish the
scale, so a rectangle is fine.

| attribute | required | meaning |
|---|---|---|
| *(none)* | — | geometry only |

**Make it tight.** The extent sets metres-per-patch. A boundary with a large
empty margin wastes spatial resolution.

## Layer 2 — intersections (`puntos_<zone>.shp`)

Points where roads meet, plus the safe zones. These are the nodes of the graph.

| attribute | type | required | meaning |
|---|---|---|---|
| `fid` | integer | **yes** | Unique node ID. Must be unique — duplicates cause silent, seed-dependent errors. |
| `is_shelter` | integer | **yes** | `1` = safe zone, `0` = ordinary intersection. |
| `name` | text | optional | Human name, e.g. "Colegio San Pedro". Used to label the busiest safe zones. Without it they are labelled by number. |

**At least one point must have `is_shelter = 1`**, or nobody can evacuate and
GTEM stops with an error.

Safe zones should be points **outside the expected inundation area**, or
designated vertical-evacuation buildings. GTEM does not read an inundation
polygon; deciding what is safe is your judgement, expressed through this column.

## Layer 3 — road network (`rutas_<zone>.shp`)

One line per street segment, connecting two intersections.

| attribute | type | required | meaning |
|---|---|---|---|
| `start_node` | integer | **yes** | `fid` of the intersection at one end. |
| `end_node` | integer | **yes** | `fid` of the intersection at the other end. |
| `cost` | number | **yes** | Segment length in **metres**. Walking distance along the street, not straight-line. |
| `lanes` | integer | **yes** | Number of lanes. Multiplied by `road_width` to get walkable width, which sets crowd density. A narrow alley is 1. |

Both `start_node` and `end_node` must exist in the intersections layer, or the
segment is skipped silently.

**Avoid segments shorter than about 1 metre.** A single person on a 0.1 m
segment produces an absurd density and a false congestion hotspot.
`check_inputs.py` counts these.

## Layer 4 — census blocks (`manzanas_<zone>.shp`)

Polygons where people start. Agents are placed at random inside them, in
proportion to the population attribute.

| attribute | type | required | meaning |
|---|---|---|---|
| `T_TOTAL` | number | strongly recommended | Resident population of the block. `Population` and `POP` are also accepted. |

**Without a population field, population is spread uniformly** — ignoring where
people actually live. GTEM warns loudly, but the results are not worth much.
This is the single most common preparation mistake.

Clip these blocks to the area at risk. GTEM creates agents everywhere you supply
a block, so an unclipped layer simulates people who were never in danger.

---

## Step by step in QGIS

1. **Set the project CRS** to your metric CRS first, before anything else.
2. **Get a road centreline layer** — municipal data, or OpenStreetMap via the
   QuickOSM plugin.
3. **Clip roads** to your study area.
4. **Split lines at intersections** (*Processing ▸ Vector geometry ▸ Split lines
   by maximum length* first if segments are very long, then *Vector ▸ Geometry
   Tools ▸ Split with lines*). Aim for segments of roughly 10–25 m.
5. **Extract nodes** (*Vector ▸ Geometry Tools ▸ Extract Vertices*), then remove
   duplicates. This becomes `puntos_`.
6. **Add `fid`** as a unique integer to the points.
7. **Join node IDs to the lines**: use *Join attributes by nearest* twice, once
   for each end, to populate `start_node` and `end_node`.
8. **Add `cost`** with the field calculator: `$length`. Confirm the units are
   metres.
9. **Add `lanes`**, defaulting to 1 and raising it for main roads.
10. **Mark safe zones**: set `is_shelter = 1` on points outside the inundation
    area or on vertical-evacuation buildings. Add `name` if you can.
11. **Prepare census blocks** with a population column, clipped to the risk area.
12. **Export all four layers** into `data/<zone>/` with the required names.
13. **Run `python check_inputs.py <zone>`** and fix what it reports.

---

## Reading the check

| message | what to do |
|---|---|
| `geographic CRS` | Reproject every layer to UTM. Nothing else matters until this is fixed. |
| `missing 'start_node'` | The join in step 7 did not run or produced a different column name. |
| `no safe zones` | No point has `is_shelter = 1`. |
| `X% cannot reach ANY safe zone` | Your network is fragmented, or a safe zone sits on an isolated node. Anyone starting there is counted as stranded before the simulation begins. Above ~10% this is worth fixing. |
| `network is in N disconnected pieces` | Usually unsplit lines or nodes that do not coincide. Snap the geometry and re-extract. |
| `links shorter than 1 m` | Over-splitting. Merge or drop them. |
| `no population field` | Add `T_TOTAL` to the blocks. |

---

## A worked example

`data/Chimbote_Zona1/` is a complete, working area. It is also a realistic one
— `check_inputs.py` reports four warnings on it, including that 19.8% of its
starting points cannot reach a safe zone. Compare your own folder against it.
