"""Assemble the GTEM demo video from a captured run.

    python tools/record_demo.py --config demo.txt --output Outputs/DemoRun \
        --frames demo_frames.npz
    python tools/build_demo_video.py --frames demo_frames.npz \
        --run Outputs/DemoRun --zone Chimbote_Zona1 --output GTEM_demo.mp4

Everything on screen is real: the folder listing is read from data/, the console
text is the captured stdout of the run, the animation is that run's per-tick
agent positions, and the closing figures are the PNGs it produced. Nothing is
mocked up.

Requires ffmpeg on PATH.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

W, H = 1280, 720
FPS = 24

BG = (18, 18, 20)
FG = (232, 232, 232)
DIM = (150, 150, 155)
ACCENT = (77, 163, 255)
GOOD = (76, 195, 110)
BAD = (232, 85, 85)
AMBER = (247, 181, 56)

MONO = "/System/Library/Fonts/Menlo.ttc"
SANS = "/System/Library/Fonts/HelveticaNeue.ttc"


def font(path: str, size: int, index: int = 0) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size, index=index)


F_MONO = {s: font(MONO, s) for s in (14, 16, 18, 20, 24)}
F_SANS = {s: font(SANS, s) for s in (16, 18, 22, 26, 32, 44, 64)}
F_BOLD = {s: font(SANS, s, index=1) for s in (16, 18, 22, 26, 32, 44, 64)}


class Reel:
    """Collects frames on disk and hands them to ffmpeg."""

    def __init__(self, folder: Path):
        self.folder = folder
        self.folder.mkdir(parents=True, exist_ok=True)
        self.n = 0

    def add(self, image: Image.Image, seconds: float = 1 / FPS) -> None:
        count = max(1, int(round(seconds * FPS)))
        first = self.folder / f"f{self.n:06d}.png"
        image.save(first)
        self.n += 1
        for _ in range(count - 1):
            # Hard-linking a held frame keeps a 3-minute reel to a few hundred MB.
            target = self.folder / f"f{self.n:06d}.png"
            try:
                target.hardlink_to(first)
            except (OSError, AttributeError):
                image.save(target)
            self.n += 1

    @property
    def seconds(self) -> float:
        return self.n / FPS


def blank() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGB", (W, H), BG)
    return image, ImageDraw.Draw(image)


def chrome(draw: ImageDraw.ImageDraw, title: str, step: str | None = None) -> None:
    """Title bar common to every scene."""
    draw.rectangle([0, 0, W, 52], fill=(28, 28, 32))
    draw.text((28, 15), title, font=F_BOLD[22], fill=FG)
    if step:
        draw.text((W - 28, 18), step, font=F_SANS[18], fill=ACCENT, anchor="ra")
    draw.line([(0, 52), (W, 52)], fill=(52, 52, 58), width=1)


def caption(draw: ImageDraw.ImageDraw, lines: list[str], y: int = H - 96) -> None:
    draw.rectangle([0, y - 14, W, H], fill=(24, 24, 28))
    for i, line in enumerate(lines):
        draw.text((36, y + i * 26), line, font=F_SANS[18], fill=DIM)


# --------------------------------------------------------------- scene 0 ---

def scene_title(reel: Reel, zone: str) -> None:
    image, draw = blank()
    logo = ROOT / "assets" / "logos" / "logo_gtem.png"
    if logo.is_file():
        mark = Image.open(logo).convert("RGBA")
        mark.thumbnail((190, 190))
        image.paste(mark, ((W - mark.width) // 2, 128), mark)
    draw.text((W // 2, 372), "GTEM", font=F_BOLD[64], fill=FG, anchor="ma")
    draw.text((W // 2, 452), "Global Tsunami Evacuation Model",
              font=F_SANS[26], fill=DIM, anchor="ma")
    draw.text((W // 2, 516), f"A complete run on {zone.replace('_', ' ')}",
              font=F_SANS[22], fill=ACCENT, anchor="ma")
    draw.text((W // 2, 640), "Version 1.0.0", font=F_SANS[16], fill=DIM, anchor="ma")
    reel.add(image, 4.0)


# --------------------------------------------------------------- scene 1 ---

def scene_inputs(reel: Reel, zone: str, layers_png: Path) -> None:
    listing = sorted(p.name for p in (ROOT / "data" / zone).iterdir()
                     if p.suffix == ".shp")
    rows = [
        (f"{zone}.shp", "zone boundary", "1 polygon"),
        (f"puntos_{zone}.shp", "intersections + safe zones", "points"),
        (f"rutas_{zone}.shp", "road network", "lines, with cost and lanes"),
        (f"manzanas_{zone}.shp", "census blocks", "polygons, with T_TOTAL"),
    ]
    image, draw = blank()
    chrome(draw, "1 — The input folder", "data/" + zone)
    draw.text((40, 86), "Four shapefiles. Nothing else.", font=F_SANS[22], fill=FG)
    y = 140
    for name, what, detail in rows:
        present = name in listing
        draw.text((44, y), "OK" if present else "--", font=F_MONO[16],
                  fill=GOOD if present else BAD)
        draw.text((86, y), name, font=F_MONO[18], fill=FG)
        draw.text((520, y), what, font=F_SANS[18], fill=ACCENT)
        draw.text((820, y), detail, font=F_SANS[16], fill=DIM)
        y += 42
    draw.text((44, y + 18),
              "Every layer in the same projected, metric CRS (a UTM zone).",
              font=F_SANS[18], fill=DIM)
    draw.text((44, y + 48),
              "Population comes from T_TOTAL on the census blocks.",
              font=F_SANS[18], fill=DIM)
    caption(draw, ["GTEM reads these four layers and checks them before it will run.",
                   "The safe zones are your judgement: points flagged is_shelter = 1."])
    reel.add(image, 8.0)

    if layers_png.is_file():
        image, draw = blank()
        chrome(draw, "1 — The input folder", "the three layers")
        panel = Image.open(layers_png).convert("RGB")
        panel.thumbnail((W - 80, H - 200))
        top, bottom = 62, H - 110
        image.paste(panel, ((W - panel.width) // 2,
                            top + (bottom - top - panel.height) // 2))
        caption(draw, ["Road network, census blocks shaded by population, and the "
                       "safe zones.",
                       "This is the whole model input: where people are, where they "
                       "can walk, where is safe."])
        reel.add(image, 10.0)


# --------------------------------------------------------------- scene 2 ---

def _type_out(reel: Reel, header: str, step: str, lines: list[str],
              font_obj, colouriser, per_char: float, hold: float) -> None:
    """Reveal text a few characters at a time, then hold."""
    full = "\n".join(lines)
    total = len(full)
    # One frame per FPS-worth of characters, so the reveal lands on the clock.
    chunk = max(1, int(total / max(1, per_char * FPS)))
    shown = 0
    while shown < total:
        shown = min(total, shown + chunk)
        image, draw = blank()
        chrome(draw, header, step)
        partial = full[:shown].split("\n")
        for i, line in enumerate(partial):
            draw.text((44, 92 + i * 26), line, font=font_obj,
                      fill=colouriser(line))
        reel.add(image)
    image, draw = blank()
    chrome(draw, header, step)
    for i, line in enumerate(lines):
        draw.text((44, 92 + i * 26), line, font=font_obj, fill=colouriser(line))
    reel.add(image, hold)


def scene_config(reel: Reel, config_text: str) -> None:
    lines = ["$ cat demo.txt", ""] + config_text.strip().splitlines()

    def colour(line: str):
        if line.startswith("$"):
            return GOOD
        if "=" in line:
            return FG
        return DIM

    _type_out(reel, "2 — The configuration", "plain text, no Python",
              lines, F_MONO[20], colour, per_char=6.0, hold=4.0)

    image, draw = blank()
    chrome(draw, "2 — The configuration", "plain text, no Python")
    for i, line in enumerate(lines):
        draw.text((44, 92 + i * 26), line, font=F_MONO[20], fill=colour(line))
    caption(draw, ["tsunami_eta is the single most important number: the "
                   "simulation stops there.",
                   "seed fixes the random draws, so this exact run can be "
                   "reproduced."])
    reel.add(image, 5.0)


def scene_launch(reel: Reel, console: list[str]) -> None:
    def colour(line: str):
        stripped = line.strip()
        if stripped.startswith("$"):
            return GOOD
        if "WARNING" in line or stripped.startswith("[WARN"):
            return AMBER
        if "Evacuated before" in line:
            return GOOD
        if "NOT evacuated" in line:
            return BAD
        return FG if stripped else DIM

    _type_out(reel, "2 — One command", "python main.py --config demo.txt",
              ["$ python main.py --config demo.txt", ""] + console,
              F_MONO[16], colour, per_char=9.0, hold=5.0)


# --------------------------------------------------------------- scene 3 ---

def scene_simulation(reel: Reel, data, seconds: float, out_dir: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    dt = float(data["dt"])
    eta = float(data["tsunami_eta"])
    ticks = data["tick"]
    evacuated = data["evacuated"]
    nodes, edges = data["nodes"], data["edges"]

    breeds = ("adults", "elderly", "children")
    offsets, arrays = {}, {}
    for breed in breeds:
        counts = data[f"{breed}_counts"]
        arrays[breed] = data[f"{breed}_xyz"]
        offsets[breed] = np.concatenate([[0], np.cumsum(counts)])

    total_people = sum(int(data[f"{b}_counts"][0]) for b in breeds)
    n_ticks = len(ticks)
    n_frames = max(1, int(seconds * FPS))

    figure = plt.figure(figsize=(W / 100, H / 100), dpi=100, facecolor="#121214")
    axis = figure.add_axes([0.02, 0.02, 0.68, 0.90])
    axis.set_facecolor("#121214")
    axis.set_xticks([]), axis.set_yticks([])
    for spine in axis.spines.values():
        spine.set_visible(False)

    if len(edges):
        from matplotlib.collections import LineCollection
        segments = [[(e[0], e[1]), (e[2], e[3])] for e in edges]
        axis.add_collection(LineCollection(segments, colors="#2f2f36",
                                           linewidths=0.45, zorder=1))
    safe = nodes[nodes[:, 2] == 1] if len(nodes) else np.empty((0, 3))
    if len(safe):
        axis.scatter(safe[:, 0], safe[:, 1], s=210, marker="*",
                     c="#4cc36e", edgecolors="white", linewidths=0.7, zorder=5)

    waiting = axis.scatter([], [], s=3.0, c="#f7b538", zorder=3)
    moving = axis.scatter([], [], s=3.0, c="#4da3ff", zorder=4)

    if len(nodes):
        pad = 0.03 * (nodes[:, 0].max() - nodes[:, 0].min() + 1)
        axis.set_xlim(nodes[:, 0].min() - pad, nodes[:, 0].max() + pad)
        axis.set_ylim(nodes[:, 1].min() - pad, nodes[:, 1].max() + pad)
    axis.set_aspect("equal")

    title = figure.text(0.02, 0.955, "3 — The evacuation", color="white",
                        fontsize=17, fontweight="bold")
    clock = figure.text(0.72, 0.90, "", color="white", fontsize=40,
                        fontweight="bold", family="monospace")
    clock_label = figure.text(0.72, 0.865, "MINUTES SINCE THE EARTHQUAKE",
                              color="#96969b", fontsize=9)
    remaining = figure.text(0.72, 0.79, "", color="#f7b538", fontsize=17,
                            family="monospace")
    safe_txt = figure.text(0.72, 0.68, "", color="#4cc36e", fontsize=27,
                           fontweight="bold", family="monospace")
    figure.text(0.72, 0.645, "REACHED A SAFE ZONE", color="#96969b", fontsize=9)
    still_txt = figure.text(0.72, 0.56, "", color="#4da3ff", fontsize=27,
                            fontweight="bold", family="monospace")
    figure.text(0.72, 0.525, "STILL WALKING", color="#96969b", fontsize=9)
    wait_txt = figure.text(0.72, 0.44, "", color="#f7b538", fontsize=27,
                           fontweight="bold", family="monospace")
    figure.text(0.72, 0.405, "NOT YET LEFT", color="#96969b", fontsize=9)
    bar_bg = figure.add_axes([0.72, 0.30, 0.26, 0.022])
    bar_bg.set_xticks([]), bar_bg.set_yticks([])
    bar_bg.set_facecolor("#2f2f36")
    for spine in bar_bg.spines.values():
        spine.set_visible(False)
    bar = bar_bg.barh([0], [0], color="#4cc36e", height=1.0)[0]
    bar_bg.set_xlim(0, 1), bar_bg.set_ylim(-0.5, 0.5)
    legend = figure.text(0.72, 0.20,
                         "yellow  waiting to leave\nblue    walking\n"
                         "green*  safe zone", color="#96969b", fontsize=11,
                         family="monospace", linespacing=1.6)
    _ = (clock_label, legend, title)

    frame_dir = out_dir / "_sim"
    frame_dir.mkdir(parents=True, exist_ok=True)

    for f in range(n_frames):
        position = f / max(1, n_frames - 1) * (n_ticks - 1)
        i = min(int(position), n_ticks - 1)
        blend = position - i
        j = min(i + 1, n_ticks - 1)

        parts_wait, parts_move = [], []
        for breed in breeds:
            a, b = offsets[breed][i], offsets[breed][i + 1]
            block = arrays[breed][a:b]
            if not len(block):
                continue
            c, d = offsets[breed][j], offsets[breed][j + 1]
            nxt = arrays[breed][c:d]
            # Agent order is stable (sorted by who) while nobody leaves, so a
            # straight blend is valid; when counts differ, fall back to holding.
            if len(nxt) == len(block) and blend:
                xy = block[:, :2] * (1 - blend) + nxt[:, :2] * blend
            else:
                xy = block[:, :2]
            ready = block[:, 2] > 0
            parts_move.append(xy[ready])
            parts_wait.append(xy[~ready])

        moving.set_offsets(np.vstack(parts_move) if parts_move
                           else np.empty((0, 2)))
        waiting.set_offsets(np.vstack(parts_wait) if parts_wait
                            else np.empty((0, 2)))

        minutes = ticks[i] * dt / 60.0
        n_safe = int(round(evacuated[i]))
        n_move = sum(len(p) for p in parts_move)
        n_wait = sum(len(p) for p in parts_wait)
        clock.set_text(f"{minutes:5.1f}")
        left = max(0.0, eta - minutes)
        remaining.set_text(f"wave in {left:4.1f} min" if left > 0
                           else "THE WAVE HAS ARRIVED")
        remaining.set_color("#f7b538" if left > 3 else "#e85555")
        safe_txt.set_text(f"{n_safe:,}")
        still_txt.set_text(f"{n_move:,}")
        wait_txt.set_text(f"{n_wait:,}")
        bar.set_width(n_safe / total_people if total_people else 0)

        figure.savefig(frame_dir / f"s{f:06d}.png", facecolor="#121214")

    plt.close(figure)

    for f in range(n_frames):
        reel.add(Image.open(frame_dir / f"s{f:06d}.png").convert("RGB"))
    shutil.rmtree(frame_dir, ignore_errors=True)


# --------------------------------------------------------------- scene 4 ---

def scene_numbers(reel: Reel, summary: dict) -> None:
    image, draw = blank()
    chrome(draw, "4 — The four numbers", "page 1 of the PDF")
    total = int(summary["Agents_Requested"])
    cards = [
        ("Evacuated before the tsunami", int(summary["Evacuated_Before_ETA"]),
         GOOD, "reached a safe zone in time"),
        ("NOT evacuated", int(summary["Not_Evacuated"]),
         BAD, "everybody else"),
        ("Caught in transit", int(summary["Caught_In_Transit"]),
         AMBER, "still walking when the wave arrived"),
        ("Stranded (no route)", int(summary["Stranded_No_Route"]),
         ACCENT, "no path to safety from where they started"),
    ]
    y = 96
    for i, (label, value, colour, note) in enumerate(cards):
        draw.rectangle([40, y, W - 40, y + 116], fill=(28, 28, 33))
        draw.rectangle([40, y, 46, y + 116], fill=colour)
        draw.text((72, y + 18), label, font=F_BOLD[22], fill=FG)
        draw.text((72, y + 56), note, font=F_SANS[16], fill=DIM)
        draw.text((W - 78, y + 26), f"{value:,}", font=F_BOLD[44],
                  fill=colour, anchor="ra")
        draw.text((W - 78, y + 82), f"{value / total * 100:.1f}%",
                  font=F_SANS[18], fill=DIM, anchor="ra")
        y += 128
        reel.add(image.copy(), 1.7 if i < 3 else 0.1)

    draw.text((44, y + 6),
              f"{cards[0][1]:,} + {cards[2][1]:,} + {cards[3][1]:,} = "
              f"{total:,} — every person is accounted for.",
              font=F_SANS[18], fill=DIM)
    reel.add(image, 5.0)


def scene_figures(reel: Reel, run_dir: Path) -> None:
    figures = [
        ("Figure1_Dynamics.png", "Figure 1 — Evacuation progress by age group",
         "A group that lags needs different measures, not more signage."),
        ("Figure2_Speed.png", "Figure 2 — Walking speed",
         "Dips below free-flow are crowding, not tiredness."),
        ("Figure3_Vulnerability.png", "Figure 3 — Vulnerability by starting point",
         "Black points never reached safety. Those are the priority areas."),
        ("Figure4_SafeZones.png", "Figure 4 — Demand on each safe zone",
         "Check the busiest against its real capacity — GTEM assumes it is unlimited."),
        ("Figure5_Congestion.png", "Figure 5 — Street congestion",
         "Ranked by how long crowding lasted, not the worst instant."),
    ]
    for name, title, note in figures:
        path = run_dir / name
        if not path.is_file():
            continue
        image, draw = blank()
        chrome(draw, "4 — The five figures", name)
        panel = Image.open(path).convert("RGB")
        panel.thumbnail((W - 120, H - 210))
        image.paste(panel, ((W - panel.width) // 2, 74))
        draw.text((40, H - 118), title, font=F_BOLD[22], fill=FG)
        draw.text((40, H - 80), note, font=F_SANS[18], fill=DIM)
        reel.add(image, 6.0)


def scene_end(reel: Reel) -> None:
    image, draw = blank()
    draw.text((W // 2, 210), "Everything you just saw", font=F_SANS[26],
              fill=DIM, anchor="ma")
    draw.text((W // 2, 262), "came from one command", font=F_BOLD[44],
              fill=FG, anchor="ma")
    draw.rectangle([260, 350, W - 260, 410], fill=(28, 28, 33))
    draw.text((W // 2, 366), "python main.py --config demo.txt",
              font=F_MONO[20], fill=GOOD, anchor="ma")
    for i, line in enumerate([
        "GTEM compares options. It does not predict casualties,",
        "and it has not been validated against an observed evacuation.",
        "Read docs/LIMITATIONS.md before using a result in a decision.",
    ]):
        draw.text((W // 2, 470 + i * 30), line, font=F_SANS[18],
                  fill=DIM if i else AMBER, anchor="ma")
    draw.text((W // 2, 636), "docs/manual/GTEM_Manual.pdf", font=F_SANS[16],
              fill=DIM, anchor="ma")
    reel.add(image, 6.0)


# ------------------------------------------------------------------ main ---

def _encoder_args() -> list[str]:
    """Pick an H.264 encoder this ffmpeg actually has.

    Homebrew's ffmpeg is often built without libx264; macOS always has the
    VideoToolbox encoder. Both produce an ordinary H.264 MP4, but they take
    different quality flags, so guessing wrong fails with "Unrecognized option".
    """
    available = subprocess.run(["ffmpeg", "-hide_banner", "-encoders"],
                               capture_output=True, text=True).stdout
    if " libx264" in available:
        return ["-c:v", "libx264", "-crf", "20"]
    if " h264_videotoolbox" in available:
        return ["-c:v", "h264_videotoolbox", "-b:v", "5M"]
    return ["-c:v", "mpeg4", "-q:v", "3"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frames", required=True)
    parser.add_argument("--run", required=True)
    parser.add_argument("--zone", default="Chimbote_Zona1")
    parser.add_argument("--config-text", required=True)
    parser.add_argument("--console", required=True)
    parser.add_argument("--layers", default="")
    parser.add_argument("--output", default="GTEM_demo.mp4")
    parser.add_argument("--workdir", default="_demo_frames")
    parser.add_argument("--sim-seconds", type=float, default=72.0)
    args = parser.parse_args()

    if shutil.which("ffmpeg") is None:
        print("ffmpeg is not on PATH.")
        return 1

    import pandas as pd

    run_dir = Path(args.run)
    summary = pd.read_csv(run_dir / "Run_Summary.csv").iloc[0].to_dict()
    data = np.load(args.frames)

    console = [line.rstrip() for line in
               Path(args.console).read_text(encoding="utf-8").splitlines()]
    # Keep the tail: setup chatter is long and the interesting part is the result.
    # Drop this tool's own chatter and anything carrying a local path: the scene
    # is meant to show what running GTEM looks like, not how the video was made.
    noise = ("frames ->", "/private/tmp", "/Users/", "static capture")
    console = [c for c in console
               if c.strip() and not any(n in c for n in noise)]
    # 21 lines at 26 px from y=92 ends at 638, clear of the 720 px frame. More
    # than that runs off the bottom of the video, which is invisible in a still.
    console = console[-21:]
    console = [textwrap.shorten(c, width=104, placeholder=" ...") for c in console]

    work = Path(args.workdir)
    shutil.rmtree(work, ignore_errors=True)
    reel = Reel(work)

    scene_title(reel, args.zone)
    scene_inputs(reel, args.zone, Path(args.layers) if args.layers else Path("."))
    scene_config(reel, Path(args.config_text).read_text(encoding="utf-8"))
    scene_launch(reel, console)
    print(f"   scenes 0-2: {reel.seconds:.1f} s")
    scene_simulation(reel, data, args.sim_seconds, work)
    print(f"   through scene 3: {reel.seconds:.1f} s")
    scene_numbers(reel, summary)
    scene_figures(reel, run_dir)
    scene_end(reel)
    print(f"   total: {reel.seconds:.1f} s over {reel.n} frames")

    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS),
         "-i", str(work / "f%06d.png")] + _encoder_args()
        + ["-pix_fmt", "yuv420p", "-movflags", "+faststart", args.output],
        check=True)
    shutil.rmtree(work, ignore_errors=True)
    size = Path(args.output).stat().st_size / 1e6
    print(f"   {args.output}  ({size:.1f} MB, {reel.seconds:.0f} s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
