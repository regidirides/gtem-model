"""The PDF a municipal officer actually reads.

Three principles shape it:

* A missing figure is an explicit, visible box saying so. A report must never
  look complete while omitting an analysis.
* The headline gives *evacuated* and *NOT evacuated* equal prominence. Reaching
  a safe zone after the wave is not safety.
* Every run parameter is listed, so the run can be reproduced from its own
  report.
"""

from __future__ import annotations

import csv
import os
import unicodedata
from datetime import datetime
from pathlib import Path

from fpdf import FPDF

from text_strings import ACTIVE, active_language
from version import VERSION_STAMP, provenance_line

#: A live view of the selected language, not a snapshot - see text_strings.
T = ACTIVE
def _find_logo_dir() -> Path:
    """Locate assets/logos whether this module sits at the project root or in src/.

    Resolving relative to this file alone silently drops the logo when the module
    is moved, and the "skip if absent" guard makes that invisible.
    """
    here = Path(__file__).resolve().parent
    for base in (here, here.parent):
        candidate = base / "assets" / "logos"
        if candidate.is_dir():
            return candidate
    return here / "assets" / "logos"


LOGO_DIR = _find_logo_dir()

INK = (33, 33, 33)
MUTED = (110, 110, 110)
RULE = (200, 200, 200)
GOOD = (46, 125, 50)
BAD = (198, 40, 40)
WARN_BG = (255, 248, 225)
SOFT = (245, 245, 245)

#: figure file -> (heading, what the reader should take from it)
#: (file name, title key, caption key). Text is looked up when the report is
#: built, not when this module is imported, so the selected language applies.
FIGURES = [
    ("Figure1_Dynamics.png", "cap_fig1_title", "cap_fig1"),
    ("Figure2_Speed.png", "cap_fig2_title", "cap_fig2"),
    ("Figure3_Vulnerability.png", "cap_fig3_title", "cap_fig3"),
    ("Figure4_SafeZones.png", "cap_fig4_title", "cap_fig4"),
    ("Figure5_Congestion.png", "cap_fig5_title", "cap_fig5"),
]


#: Characters fpdf's Latin-1 core fonts cannot encode, and a readable stand-in
#: for each. Accented letters are deliberately absent from this table: Latin-1
#: covers the whole of Spanish (acutes, n-tilde, u-diaeresis, inverted ? and !),
#: so those must survive intact.
_UNENCODABLE = {
    "—": "-", "–": "-", "‘": "'", "’": "'", "“": '"', "”": '"',
    "²": "2", "±": "+/-", "≤": "<=", "≥": ">=", "×": "x", "·": ".",
    "…": "...", "→": "->", "€": "EUR", "™": "(TM)",
}


def pdf_text(value: object) -> str:
    """Make a string safe for fpdf 1.7.2, which writes Latin-1 core fonts.

    Substitutes the handful of characters Latin-1 genuinely lacks, then drops
    anything still unencodable.

    Accents are NOT stripped. An earlier version normalised to ASCII, which
    turned "Poblacion evacuada" into "Poblacin evacuada" and would have made a
    Spanish report unreadable. Latin-1 encodes every character Spanish needs.
    """
    text = str(value)
    for bad, replacement in _UNENCODABLE.items():
        text = text.replace(bad, replacement)
    # Compose accents into single Latin-1 code points; a decomposed "a" + U+0301
    # would otherwise lose its accent in the encode below.
    text = unicodedata.normalize("NFC", text)
    return text.encode("latin-1", "ignore").decode("latin-1")


#: Kept so any existing caller or downstream script keeps working.
ascii_only = pdf_text


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    """Read a CSV into a list of dicts; empty list if the file is absent."""
    if not path.is_file():
        return []
    with open(path, newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class Report(FPDF):
    """A4 report with a versioned footer and helpers for the layout used here."""

    def __init__(self) -> None:
        super().__init__(orientation="P", unit="mm", format="A4")
        self.set_auto_page_break(auto=True, margin=18)
        self.set_margins(16, 14, 16)
        self.alias_nb_pages()

    @property
    def usable_width(self) -> float:
        return self.w - self.l_margin - self.r_margin

    def footer(self) -> None:
        self.set_y(-14)
        self.set_font("Helvetica", "", 7.5)
        self.set_text_color(*MUTED)
        self.cell(0, 5, pdf_text(T["pdf_footer"].format(
            provenance=provenance_line(),
            page=f"{self.page_no()}/{{nb}}",
            timestamp=f"{datetime.now():%Y-%m-%d %H:%M}")), 0, 0, "C")

    def heading(self, text: str) -> None:
        self.ln(3)
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(*INK)
        self.cell(0, 8, ascii_only(text), 0, 1, "L")
        self.set_draw_color(*RULE)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(3)

    def subheading(self, text: str) -> None:
        self.set_font("Helvetica", "B", 10.5)
        self.set_text_color(*INK)
        self.cell(0, 6, ascii_only(text), 0, 1, "L")

    def body(self, text: str, size: float = 9.5) -> None:
        self.set_font("Helvetica", "", size)
        self.set_text_color(*INK)
        self.multi_cell(self.usable_width, 4.8, ascii_only(text))
        self.ln(1)

    def key_values(self, items: list[tuple[str, object]],
                   label_width: float = 42, columns: int = 2) -> None:
        """Label/value rows, laid out in columns so long tables stay on one page.

        A single column of twenty rows spills over a page boundary and strands a
        handful of rows on an otherwise empty sheet, which reads as an error.
        """
        if columns < 1:
            columns = 1
        rows = (len(items) + columns - 1) // columns
        column_width = self.usable_width / columns
        value_width = column_width - label_width - 3
        top = self.get_y()
        self.set_font("Helvetica", "", 8.5)

        for column in range(columns):
            block = items[column * rows:(column + 1) * rows]
            x = self.l_margin + column * column_width
            self.set_y(top)
            for label, value in block:
                if self.get_y() > self.h - 24:
                    break
                self.set_x(x)
                self.set_fill_color(*SOFT)
                self.set_text_color(*MUTED)
                self.cell(label_width, 5.6, ascii_only(label), 0, 0, "L", True)
                self.set_text_color(*INK)
                self.cell(value_width, 5.6, ascii_only(value), 0, 1, "L")
        self.set_y(top + rows * 5.6 + 2)

    def table(self, headers: list[str], rows: list[list[object]],
              widths: list[float], keep_together: bool = False) -> None:
        """Bordered table. ``keep_together`` moves a short table to the next page
        rather than splitting it and stranding a row or two."""
        if keep_together:
            needed = 6.5 + len(rows) * 5.8 + 4
            if self.get_y() + needed > self.h - 22:
                self.add_page()
        self.set_font("Helvetica", "B", 8.5)
        self.set_fill_color(230, 230, 230)
        self.set_text_color(*INK)
        for header, width in zip(headers, widths):
            self.cell(width, 6.5, ascii_only(header), 1, 0, "C", True)
        self.ln()
        self.set_font("Helvetica", "", 8.5)
        for row in rows:
            if self.get_y() > self.h - 30:
                self.add_page()
            for value, width in zip(row, widths):
                self.cell(width, 5.8, ascii_only(value), 1, 0, "C")
            self.ln()
        self.ln(2)

    def outcome_banner(self, evacuated: int, not_evacuated: int, total: int) -> None:
        """The headline. Both numbers, equally prominent."""
        half = self.usable_width / 2 - 2
        pct_ok = evacuated / total * 100 if total else 0
        pct_bad = not_evacuated / total * 100 if total else 0
        top = self.get_y()

        self.set_fill_color(232, 245, 233)
        self.rect(self.l_margin, top, half, 24, "F")
        self.set_xy(self.l_margin, top + 3)
        self.set_font("Helvetica", "B", 20)
        self.set_text_color(*GOOD)
        self.cell(half, 10, f"{pct_ok:.1f}%", 0, 2, "C")
        self.set_font("Helvetica", "", 8.5)
        self.cell(half, 5, pdf_text(T["pdf_banner_evacuated"].format(
            label=T["evacuated"], n=evacuated)), 0, 0, "C")

        self.set_fill_color(255, 235, 238)
        self.rect(self.l_margin + half + 4, top, half, 24, "F")
        self.set_xy(self.l_margin + half + 4, top + 3)
        self.set_font("Helvetica", "B", 20)
        self.set_text_color(*BAD)
        self.cell(half, 10, f"{pct_bad:.1f}%", 0, 2, "C")
        self.set_font("Helvetica", "", 8.5)
        self.cell(half, 5, pdf_text(T["pdf_banner_evacuated"].format(
            label=T["not_evacuated"], n=not_evacuated)), 0, 0, "C")

        self.set_y(top + 28)
        self.set_text_color(*INK)

    def figure_block(self, path: Path, title: str, caption: str) -> None:
        # A figure needs roughly 150 mm once its heading and caption are counted.
        # Checking only the image height strands the heading at the foot of a
        # page with the figure overleaf.
        if self.get_y() > self.h - 150:
            self.add_page()
        self.subheading(title)
        self.set_font("Helvetica", "I", 8.5)
        self.set_text_color(*MUTED)
        self.multi_cell(self.usable_width, 4.2, ascii_only(caption))
        self.set_text_color(*INK)
        self.ln(1.5)
        if path.is_file():
            self.image(str(path), x=self.l_margin, w=self.usable_width)
        else:
            # Never skip a missing figure silently.
            self.set_fill_color(255, 235, 238)
            self.set_font("Helvetica", "B", 9)
            self.set_text_color(*BAD)
            self.multi_cell(self.usable_width, 8, pdf_text(
                T["pdf_figure_missing"].format(name=path.name)), 1, "C", True)
            self.set_text_color(*INK)
        self.ln(4)



def _milestones(rows: list[dict[str, str]], requested: int) -> list[tuple[str, str]]:
    """Time at which each share of the population had reached safety.

    Answers the question a planner actually asks - "when is half the town out?" -
    which a cumulative curve makes you read off by eye.
    """
    if not rows or not requested:
        return []
    out = []
    for share in (0.25, 0.50, 0.75, 0.90, 0.95):
        target = share * requested
        reached = next((float(r["Time_Minutes"]) for r in rows
                        if float(r.get("Evacuated", 0)) >= target), None)
        out.append((T["pdf_milestone"].format(share=share),
                    T["pdf_milestone_minutes"].format(minutes=reached)
                    if reached is not None else T["pdf_milestone_never"]))
    return out


def _flow_summary(rows: list[dict[str, str]]) -> list[tuple[str, str]]:
    """Peak evacuation rate, and how fast people were still arriving at the end."""
    if len(rows) < 2:
        return []
    times = [float(r["Time_Minutes"]) for r in rows]
    evacuated = [float(r.get("Evacuated", 0)) for r in rows]
    best_rate, best_time = 0.0, 0.0
    for i in range(1, len(rows)):
        minutes = times[i] - times[i - 1]
        if minutes <= 0:
            continue
        rate = (evacuated[i] - evacuated[i - 1]) / minutes
        if rate > best_rate:
            best_rate, best_time = rate, times[i]
    tail = 0.0
    if times[-1] > times[0]:
        window = [i for i, t in enumerate(times) if t >= times[-1] - 1.0]
        if len(window) > 1:
            span = times[window[-1]] - times[window[0]]
            if span > 0:
                tail = (evacuated[window[-1]] - evacuated[window[0]]) / span
    return [
        (T["pdf_flow_peak"],
         T["pdf_flow_peak_value"].format(rate=best_rate, minutes=best_time)),
        (T["pdf_flow_tail"], T["pdf_flow_tail_value"].format(rate=tail)),
    ]


def _age_group_table(rows: list[dict[str, str]], summary: dict) -> list[list[object]]:
    """Outcome per age group. The figure shows it; a table can be quoted."""
    if not rows:
        return []
    last = rows[-1]
    groups = [(T["adults"], "Evac_Adults", "Pop_Adults"),
              (T["elderly"], "Evac_Elderly", "Pop_Elderly"),
              (T["children"], "Evac_Children", "Pop_Children")]
    table = []
    for label, evac_key, pop_key in groups:
        total = _int(summary.get(pop_key))
        evacuated = int(float(last.get(evac_key, 0) or 0))
        if not total:
            continue
        table.append([label, f"{total:,}", f"{evacuated:,}",
                      f"{total - evacuated:,}", f"{evacuated / total * 100:.1f}%"])
    return table


def _int(value: object, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def generate_pdf_report(run_path: str, summary: dict,
                        margin: dict | None = None) -> bool:
    """Build the PDF. Returns True on success."""
    folder = Path(run_path)
    try:
        zone = str(summary.get("Zone", "unknown"))
        seed = summary.get("Seed", "n/a")
        requested = _int(summary.get("Agents_Requested"))
        evacuated = _int(summary.get("Evacuated_Before_ETA"))
        not_evacuated = _int(summary.get("Not_Evacuated"))
        caught = _int(summary.get("Caught_In_Transit"))
        stranded = _int(summary.get("Stranded_No_Route"))

        pdf = Report()
        pdf.add_page()

        # --- cover ---------------------------------------------------------
        logo = LOGO_DIR / "logo_gtem.png"
        if logo.is_file():
            pdf.image(str(logo), x=pdf.l_margin, y=12, w=26)
        pdf.set_xy(pdf.l_margin + 30, 14)
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 8, ascii_only(T["pdf_title"]), 0, 2, "L")
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*MUTED)
        pdf.cell(0, 5.5, pdf_text(T["pdf_subtitle"].format(
            zone=zone, seed=seed, version=VERSION_STAMP)), 0, 1, "L")
        pdf.set_text_color(*INK)
        pdf.ln(10)

        pdf.heading(T["pdf_headline_heading"])
        pdf.outcome_banner(evacuated, not_evacuated, requested)
        if not not_evacuated:
            breakdown = T["pdf_breakdown_none"]
        elif caught and stranded:
            breakdown = T["pdf_breakdown_both"].format(caught=caught, stranded=stranded)
        elif stranded:
            breakdown = T["pdf_breakdown_stranded"].format(stranded=stranded)
        else:
            breakdown = T["pdf_breakdown_caught"]
        eta_text = summary.get("Tsunami_ETA_Min", T["batch_not_available"])
        key = "pdf_headline_some" if not_evacuated else "pdf_headline_all"
        pdf.body(T[key].format(
            requested=requested, evacuated=evacuated, eta=eta_text,
            not_evacuated=not_evacuated, breakdown=breakdown))
        pdf.body(T["pdf_limitations"], size=8.5)

        # --- warnings ------------------------------------------------------
        pdf.heading(T["pdf_warnings_heading"])
        warnings_file = folder / "warnings.log"
        warning_lines = []
        if warnings_file.is_file():
            warning_lines = [line.strip() for line in
                             warnings_file.read_text(encoding="utf-8").splitlines()
                             if line.strip() and line.strip()[0].isdigit()
                             and "." in line]
        if warning_lines:
            pdf.body(T["pdf_warnings_intro"])
            # The engine emits warnings in English only. Say so rather than
            # letting a Spanish reader wonder whether something went wrong.
            if active_language() != "en":
                pdf.body(T["pdf_warnings_untranslated"], size=8.5)
            pdf.set_fill_color(*WARN_BG)
            pdf.set_font("Helvetica", "", 8.5)
            for line in warning_lines:
                pdf.multi_cell(pdf.usable_width, 4.6, ascii_only(line), 0, "L", True)
                pdf.ln(0.6)
        else:
            pdf.body(T["pdf_no_warnings"])

        # --- timing and per-group outcome, from the dynamics table -----------
        dynamics = read_csv_rows(folder / "Report1_Dynamics.csv")

        milestones = _milestones(dynamics, requested)
        flow = _flow_summary(dynamics)
        if milestones or flow:
            if pdf.get_y() > pdf.h - 80:
                pdf.add_page()
            pdf.heading(T["pdf_unfolded_heading"])
            pdf.body(T["pdf_unfolded_intro"], size=8.5)
            pdf.key_values(milestones + flow, label_width=62, columns=1)

        ages = _age_group_table(dynamics, summary)
        if ages:
            if pdf.get_y() > pdf.h - 60:
                pdf.add_page()
            pdf.heading(T["pdf_ages_heading"])
            pdf.body(T["pdf_ages_intro"], size=8.5)
            pdf.table([T["th_group"], T["th_people"], T["th_evacuated"],
                       T["th_not_evacuated"], T["th_evacuated_pct"]],
                      ages, [34, 34, 34, 38, 34], keep_together=True)

        # --- how much more time would have been needed ----------------------
        if margin:
            eta = float(summary.get("Tsunami_ETA_Min", 0) or 0)
            required = float(margin["total_minutes"])
            deficit = required - eta
            if pdf.get_y() > pdf.h - 90:
                pdf.add_page()
            pdf.heading(T["pdf_margin_heading"])
            pdf.body(T["pdf_margin_intro"].format(
                required=required, eta=eta, deficit=deficit))
            minutes = margin["minutes"]
            evacuated = margin["evacuated"]
            at_eta = 0.0
            for t, e in zip(minutes, evacuated):
                if t <= eta:
                    at_eta = e
            rows = []
            for extra in (1, 2, 3, 5, 10):
                gained = 0.0
                for t, e in zip(minutes, evacuated):
                    if t <= eta + extra:
                        gained = e
                extra_people = max(0, int(round(gained - at_eta)))
                rows.append([T["pdf_extra_minutes"].format(minutes=extra),
                             f"{int(round(gained)):,}",
                             f"{extra_people:,}",
                             f"{extra_people / requested * 100:.1f}%" if requested else "-"])
            pdf.table([T["th_extra_time"], T["th_reached_safety"],
                       T["th_additional_people"], T["th_share_of_population"]],
                      rows, [30, 44, 44, 44], keep_together=True)
            pdf.body(T["pdf_margin_note"], size=8.5)

        # --- every parameter, so the run is reproducible from the report ---
        if pdf.get_y() > pdf.h - 120:
            pdf.add_page()
        pdf.heading(T["pdf_config_heading"])
        pdf.body(T["pdf_config_intro"], size=8.5)
        if active_language() != "en":
            pdf.body(T["pdf_config_untranslated"], size=8)
        skip = {"Zone", "Seed", "GTEM_Version"}
        pdf.key_values([(T["label_area"], zone), (T["label_seed"], seed),
                        (T["label_version"], VERSION_STAMP)]
                       + [(key.replace("_", " "), value)
                          for key, value in summary.items() if key not in skip])

        # --- safe zones ----------------------------------------------------
        safe_rows = read_csv_rows(folder / "Report4_SafeZones.csv")
        if safe_rows:
            pdf.add_page()
            pdf.heading(T["pdf_zones_heading"])
            pdf.body(T["pdf_zones_intro"])
            pdf.table([T["th_rank"], T["th_safe_zone"], T["th_name"],
                       T["th_people_received"]],
                      [[r.get("Rank"), r.get("Safe_Zone_ID"), r.get("Name"),
                        r.get("People_Received")] for r in safe_rows[:15]],
                      [18, 30, 90, 40], keep_together=True)

        # --- congestion ----------------------------------------------------
        congestion_rows = read_csv_rows(folder / "Report5_Congestion.csv")
        if congestion_rows:
            pdf.heading(T["pdf_congestion_heading"])
            pdf.body(T["pdf_congestion_intro"])
            pdf.table([T["th_rank"], T["th_from_node"], T["th_to_node"],
                       T["th_accumulated_crowding"], T["th_peak_density"],
                       T["th_seconds_congested"]],
                      [[r.get("Rank"), r.get("start_node"), r.get("end_node"),
                        f"{float(r.get('Exposure', 0)):.1f}",
                        f"{float(r.get('Peak_Density', 0)):.2f}",
                        f"{float(r.get('Congested_Seconds', 0)):.0f}"]
                       for r in congestion_rows[:10]],
                      [16, 28, 28, 42, 30, 34], keep_together=True)

        # --- figures -------------------------------------------------------
        pdf.add_page()
        pdf.heading(T["pdf_figures_heading"])
        for filename, title_key, caption_key in FIGURES:
            pdf.figure_block(folder / filename, T[title_key], T[caption_key])

        # --- traceability --------------------------------------------------
        pdf.heading(T["pdf_files_heading"])
        produced = sorted(p.name for p in folder.iterdir() if p.is_file())
        pdf.body(", ".join(produced), size=8)

        safe_zone = "".join(c if c.isalnum() or c in "._-" else "_" for c in zone)
        safe_seed = "".join(c if c.isalnum() or c in "._-" else "_" for c in str(seed))
        output = folder / f"Report_{safe_zone}_ID{safe_seed}.pdf"
        pdf.output(str(output))
        print(f"   PDF report: {output.name}")
        return True

    except Exception as exc:  # noqa: BLE001 - reported to the caller, which fails the run
        print(f"   PDF generation failed: {type(exc).__name__}: {exc}")
        return False




# ---------------------------------------------------------------------------
# Batch report
# ---------------------------------------------------------------------------

BATCH_FIGURES = [
    ("Figure_Convergence.png", "cap_batch_convergence_title", "cap_batch_convergence"),
    ("Figure_Runtime_Benchmark.png", "cap_batch_runtime_title", "cap_batch_runtime"),
]


def generate_batch_pdf(batch_path: str, runs, aggregated,
                       settled: dict | None = None,
                       master_seed: object = None) -> bool:
    """One report for a whole batch, reporting means rather than single runs.

    A single run is not a result: the model is stochastic, and quoting one run
    invites a reader to treat seed noise as signal. This report exists so that
    the number leaving the building is a mean over replicates with its spread
    attached.
    """
    folder = Path(batch_path)
    try:
        import math

        ok = runs.loc[runs.get("Status", "OK") == "OK"]
        failed = len(runs) - len(ok)

        pdf = Report()
        pdf.add_page()

        logo = LOGO_DIR / "logo_gtem.png"
        if logo.is_file():
            pdf.image(str(logo), x=pdf.l_margin, y=12, w=26)
        pdf.set_xy(pdf.l_margin + 30, 14)
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 8, pdf_text(T["batch_title"]), 0, 2, "L")
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*MUTED)
        pdf.cell(0, 5.5, pdf_text(T["batch_subtitle"].format(
            runs=len(ok), scenarios=ok["Zone"].nunique(),
            version=VERSION_STAMP)), 0, 1, "L")
        pdf.set_text_color(*INK)
        pdf.ln(8)

        # --- results, as means -------------------------------------------
        pdf.heading(T["batch_results_heading"])
        pdf.body(T["batch_results_intro"])

        rows = []
        for _, r in aggregated.iterrows():
            sd = r.get("Pct_Evacuated_SD")
            sd_text = T["batch_not_available"] \
                if sd is None or (isinstance(sd, float) and math.isnan(sd)) \
                else f"+/- {sd:.2f}"
            not_sd = r.get("Pct_Not_Evacuated_SD")
            not_sd_text = T["batch_not_available"] \
                if not_sd is None or (isinstance(not_sd, float) and math.isnan(not_sd)) \
                else f"+/- {not_sd:.2f}"
            rows.append([
                str(r["Zone"])[:26], int(r["N_Runs"]),
                f"{r['Pct_Evacuated_Mean']:.2f}% {sd_text}",
                f"{r['Pct_Not_Evacuated_Mean']:.2f}% {not_sd_text}",
                f"{r.get('Stranded_No_Route_Mean', 0):,.0f}",
            ])
        pdf.table([T["th_scenario"], T["th_runs"], T["th_evacuated_mean"],
                   T["th_not_evacuated_mean"], T["th_stranded"]],
                  rows, [46, 14, 42, 46, 24], keep_together=True)

        # --- comparison between scenarios --------------------------------
        if len(aggregated) > 1:
            best = aggregated.loc[aggregated["Pct_Evacuated_Mean"].idxmax()]
            pdf.heading(T["batch_compare_heading"])
            pdf.body(T["batch_compare_intro"].format(
                best=best["Zone"], pct=best["Pct_Evacuated_Mean"]))
            comparison = []
            for _, r in aggregated.iterrows():
                delta = r["Pct_Evacuated_Mean"] - best["Pct_Evacuated_Mean"]
                comparison.append([
                    str(r["Zone"])[:32],
                    f"{r['Pct_Evacuated_Mean']:.2f}%",
                    T["batch_baseline"] if abs(delta) < 1e-9 else f"{delta:+.2f} pp",
                    f"{r.get('Not_Evacuated_Mean', 0):,.0f}",
                ])
            pdf.table([T["th_scenario"], T["th_evacuated"], T["th_difference"],
                       T["th_people_not_evacuated"]],
                      comparison, [58, 34, 34, 46], keep_together=True)

        # --- was the batch big enough? -----------------------------------
        pdf.heading(T["batch_size_heading"])
        summary_file = folder / "Convergence_Summary.txt"
        if summary_file.is_file():
            pdf.body(T["batch_size_intro"], size=9)
            pdf.set_font("Courier", "", 8)
            for line in summary_file.read_text(encoding="utf-8").splitlines():
                if line.strip() and not line.startswith("#"):
                    pdf.cell(0, 4.4, ascii_only("  " + line), 0, 1, "L")
            pdf.ln(2)
        else:
            pdf.body(T["batch_size_unavailable"], size=9)
        if settled:
            weak = [z for z, n in settled.items() if not n]
            if weak:
                pdf.body(T["batch_not_settled"].format(
                    scenarios=", ".join(weak)), size=9)

        # --- reproducibility and cost ------------------------------------
        pdf.heading(T["batch_repro_heading"])
        seconds = ok["Seconds_Total"] if "Seconds_Total" in ok else None
        pdf.key_values([
            (T["label_master_seed"], master_seed if master_seed is not None
             else T["label_no_master_seed"]),
            (T["label_successful_runs"], len(ok)),
            (T["label_failed_runs"], failed),
            (T["label_total_compute"], f"{seconds.sum() / 60:.1f} min"
             if seconds is not None else T["batch_not_available"]),
            (T["label_mean_per_run"], f"{seconds.mean():.1f} s"
             if seconds is not None else T["batch_not_available"]),
            (T["label_timestep"], f"{ok['DT_Seconds'].iloc[0]:g} s"
             if "DT_Seconds" in ok and len(ok) else T["batch_not_available"]),
            (T["label_version"], VERSION_STAMP),
        ], label_width=46, columns=2)
        if master_seed is None:
            pdf.body(T["batch_no_seed_note"], size=8.5)

        if failed:
            pdf.heading(T["batch_failed_heading"])
            bad = runs.loc[runs["Status"] != "OK"]
            pdf.table([T["th_run"], T["th_scenario"], T["th_error"]],
                      [[r["Run_ID"], str(r["Zone"])[:24], str(r.get("Error", ""))[:60]]
                       for _, r in bad.iterrows()], [18, 46, 108])

        # --- figures ------------------------------------------------------
        pdf.add_page()
        pdf.heading(T["batch_figures_heading"])
        for filename, title_key, caption_key in BATCH_FIGURES:
            if (folder / filename).is_file():
                pdf.figure_block(folder / filename, T[title_key], T[caption_key])

        pdf.heading(T["batch_limitations_heading"])
        pdf.body(T["pdf_limitations"], size=9)

        output = folder / "Batch_Report.pdf"
        pdf.output(str(output))
        print(f"   Batch report: {output.name}")
        return True

    except Exception as exc:  # noqa: BLE001 - reported to the caller
        print(f"   Batch report failed: {type(exc).__name__}: {exc}")
        return False


__all__ = ["generate_pdf_report", "generate_batch_pdf"]
_ = os
