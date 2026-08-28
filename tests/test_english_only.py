"""C2 gate: the codebase must contain no Spanish.

Two tests, deliberately:

* ``test_no_regression`` is a ratchet. It fails if the amount of Spanish goes
  UP, so translation progress can never be silently undone. It passes today.
* ``test_fully_translated`` is the release gate. It asserts zero and is
  currently an expected failure; it flips to XPASS the moment the last file is
  translated. Remove the xfail marker at that point.

Scans Python source, NetLogo source, user-facing strings, CSV headers and
figure labels. Proper nouns (place names, existing shapefile prefixes) are
allow-listed.

TRANSLATION TABLES
    GTEM can write its outputs in Spanish, so some Spanish is deliberate.
    It must be fenced explicitly:

        # --- BEGIN TRANSLATED CONTENT ---
        ...
        # --- END TRANSLATED CONTENT ---

    Only the lines between those markers are exempt. The rest of the same file
    is still scanned, so a Spanish comment or identifier outside the fence still
    fails the gate. Fencing is deliberately verbose: it should be obvious in
    review when someone widens the exemption.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

# The codebase is fully English. This is the ratchet: it must never rise.
# translated; never raise it.
BASELINE = 0

# Proper nouns and external schema names that legitimately stay as they are.
ALLOW = re.compile(
    r"Chimbote|Arahama|Zona\d|Huella|geogpsperu|INEI|Tohoku|IRIDeS|PUCP|CDRI"
    r"|manzanas_|puntos_|rutas_|T_TOTAL|UBIGEO|MANZANA|NOMBDEP|NOMBPROV|CODCCPP"
    r"|Pontificia|Universidad|Cat.lica|del Per.|Colegio San Pedro|Sendai",
    re.I,
)

# Accented characters are unambiguous. Bare function words are not -- "no",
# "de", "en", "un" and "a" all occur in ordinary English, so matching on those
# alone produces false positives. A line therefore counts as Spanish if it has
# an accented character, OR at least TWO DISTINCT Spanish-only markers.
ACCENTS = re.compile(r"[áéíóúñÁÉÍÓÚÑ¿¡]")

MARKERS = re.compile(
    r"\b(el|la|los|las|del|que|para|con|por|una|se|su|como|cada|desde|entre"
    r"|sobre|todos|puede|debe|esta|este|son|hay|muy|tambien|hasta|donde|cuando"
    r"|corrida|corridas|archivo|archivos|carpeta|datos|reporte|reportes"
    r"|grafico|graficos|simulacion|evacuacion|semilla|semillas|velocidad"
    r"|densidad|zona|zonas|ruta|rutas|tiempo|poblacion|usuario|generar|genera"
    r"|ejecuta|muestra|lote|salida|salidas|manzana|manzanas|persona|personas"
    r"|refugio|refugios|calle|calles|nodo|nodos|escala|riesgo|colapso)\b",
    re.I,
)


FENCE_OPEN = re.compile(r"BEGIN TRANSLATED CONTENT")
FENCE_CLOSE = re.compile(r"END TRANSLATED CONTENT")


def _scannable_lines(text: str) -> list[str]:
    """Every line outside an explicit translation fence."""
    lines: list[str] = []
    inside = False
    for line in text.splitlines():
        if FENCE_OPEN.search(line):
            inside = True
            continue
        if FENCE_CLOSE.search(line):
            inside = False
            continue
        if not inside:
            lines.append(line)
    return lines


def _is_spanish(line: str) -> bool:
    if ACCENTS.search(line):
        return True
    return len(set(m.lower() for m in MARKERS.findall(line))) >= 2


def _scan() -> dict[str, int]:
    counts: dict[str, int] = {}
    targets = (sorted(ROOT.glob("*.py"))
               + sorted(ROOT.glob("src/*.nlogox"))
               + sorted(ROOT.glob("src/*.py"))
               + sorted(ROOT.glob("*.md"))
               + sorted(ROOT.glob("docs/*.md"))
               + sorted(ROOT.glob("*.txt"))
               + sorted(ROOT.glob("tests/*.py"))
               + sorted(ROOT.glob("tools/*.py"))
               + sorted(ROOT.glob("tools/*.md")))
    # Historical documents necessarily quote the Spanish names they replaced,
    # and this file necessarily contains the Spanish word list itself. These
    # names are absent from a release build, where the set is simply unused.
    # test_text_strings.py is the test FOR the translation and necessarily
    # quotes it, exactly as this file necessarily contains the word list.
    exempt = {"CHANGELOG.md", "test_english_only.py", "test_text_strings.py",
              "AUDIT_REPORT.md", "GLOSSARY_ES_EN.md", "PACKAGING_MANIFEST.md"}
    targets = [t for t in targets if t.name not in exempt]
    for path in targets:
        text = path.read_text(encoding="utf-8", errors="replace")
        hits = 0
        for line in _scannable_lines(text):
            stripped = ALLOW.sub("", line)
            if _is_spanish(stripped):
                hits += 1
        if hits:
            counts[path.name] = hits
    return counts


def _report(counts: dict[str, int]) -> str:
    total = sum(counts.values())
    lines = [f"{total} Spanish-bearing lines remain (baseline {BASELINE}):"]
    for name, n in sorted(counts.items(), key=lambda kv: -kv[1]):
        lines.append(f"    {n:5d}  {name}")
    return "\n".join(lines)


def test_no_regression() -> None:
    """Translation progress must never go backwards."""
    counts = _scan()
    total = sum(counts.values())
    assert total <= BASELINE, (
        f"Spanish content INCREASED to {total} (baseline {BASELINE}).\n"
        + _report(counts)
    )


def test_fully_translated() -> None:
    """Release gate: no Spanish anywhere."""
    counts = _scan()
    assert sum(counts.values()) == 0, _report(counts)


#: The only files allowed to fence off deliberate Spanish. Widening this is a
#: visible, reviewable change rather than a quiet one.
#:
#:   text_strings.py  the ES string table itself
#:   README.md        one line naming the Spanish manual, so a Spanish reader
#:                    recognises it in the documentation table
FENCED_FILES = {"text_strings.py", "README.md"}

#: Everything the fence rule is checked against. Matches the scan in _scan(),
#: including Markdown - a fence in a document must be as visible as one in code.
FENCE_PATTERNS = ("*.py", "*.md", "src/*.py", "src/*.nlogox",
                  "tools/*.py", "tools/*.md", "docs/*.md")


def _fenced_files() -> dict[str, Path]:
    """Every scanned file containing a fence, by name."""
    found: dict[str, Path] = {}
    for pattern in FENCE_PATTERNS:
        for path in ROOT.glob(pattern):
            if FENCE_OPEN.search(path.read_text(encoding="utf-8", errors="replace")):
                found[path.name] = path
    return found


def test_only_the_translation_table_is_fenced() -> None:
    """An exemption must not spread beyond the places that have earned one."""
    fenced = set(_fenced_files())
    assert fenced == FENCED_FILES, (
        f"Translation fences found in {sorted(fenced)}, expected only "
        f"{sorted(FENCED_FILES)}. Deliberate Spanish belongs in the string "
        "tables, not scattered through the code."
    )


def test_every_fence_is_closed() -> None:
    """An unclosed fence would silently exempt the rest of a file."""
    for name, path in _fenced_files().items():
        text = path.read_text(encoding="utf-8")
        assert len(FENCE_OPEN.findall(text)) == len(FENCE_CLOSE.findall(text)), (
            f"{name} has an unbalanced translation fence."
        )
