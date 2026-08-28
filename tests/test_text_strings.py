"""The string tables must stay in step with each other.

A translation drifts in three ways, and all three surface only when a report is
generated - long after the run that produced it:

* a key is added to EN and forgotten in ES, so the report raises KeyError;
* a ``{placeholder}`` is mistyped in a translation, so ``.format`` raises;
* a CSV column header gets translated, so two runs of the same scenario produce
  tables that cannot be compared.

These tests catch all three at commit time instead.
"""

from __future__ import annotations

import string
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pdf_report  # noqa: E402
import text_strings  # noqa: E402
from text_strings import (  # noqa: E402
    ACTIVE,
    EN,
    SAME_IN_EVERY_LANGUAGE,
    TABLES,
    UNTRANSLATED_KEYS,
    normalise_language,
    set_language,
    strings,
)

#: Every table except the reference one.
TRANSLATIONS = [code for code in TABLES if TABLES[code] is not EN]


@pytest.fixture(autouse=True)
def _restore_language():
    """Leave the module-level selection as we found it."""
    yield
    set_language("en")


def _placeholders(value: str) -> set[str]:
    """The field names in a format string, ignoring their format specs."""
    return {name for _, name, _, _ in string.Formatter().parse(value)
            if name is not None}


@pytest.mark.parametrize("code", TRANSLATIONS)
def test_translation_has_exactly_the_same_keys(code):
    table = TABLES[code]
    missing = sorted(set(EN) - set(table))
    extra = sorted(set(table) - set(EN))
    assert not missing, f"{code} is missing: {missing}"
    assert not extra, f"{code} has keys EN does not: {extra}"


@pytest.mark.parametrize("code", TRANSLATIONS)
def test_translation_preserves_every_placeholder(code):
    table = TABLES[code]
    for key, original in EN.items():
        assert _placeholders(table[key]) == _placeholders(original), (
            f"{code}[{key!r}] does not use the same placeholders as EN. "
            f"EN: {original!r}  {code}: {table[key]!r}"
        )


@pytest.mark.parametrize("code", TRANSLATIONS)
def test_csv_headers_are_never_translated(code):
    """Machine-readable keys must be byte-identical across languages."""
    for key in UNTRANSLATED_KEYS:
        assert TABLES[code][key] == EN[key], (
            f"{key!r} is a CSV column header and must not be translated; "
            "results in different languages would no longer be comparable."
        )


@pytest.mark.parametrize("code", TRANSLATIONS)
def test_translation_leaves_nothing_in_english(code):
    """A forgotten value is a copy of the English one. Catch the obvious cases."""
    table = TABLES[code]
    exempt = UNTRANSLATED_KEYS | SAME_IN_EVERY_LANGUAGE
    identical = [k for k, v in table.items() if k not in exempt and v == EN[k]]
    assert not identical, f"{code} left untranslated: {sorted(identical)}"


@pytest.mark.parametrize("code", sorted(TABLES))
def test_every_string_survives_the_pdf_encoder(code):
    """fpdf writes Latin-1. A string that loses characters would ship broken."""
    for key, value in TABLES[code].items():
        encoded = pdf_report.pdf_text(value)
        assert "?" not in encoded or "?" in value, (
            f"{code}[{key!r}] gained a '?' when encoded for the PDF: {encoded!r}"
        )
        # Placeholders must not be mangled by the encoder either.
        assert _placeholders(encoded) == _placeholders(value), (
            f"{code}[{key!r}] lost a placeholder in the PDF encoder."
        )


def test_accents_survive_the_pdf_encoder():
    """The regression this fix was made for: NFKD+ASCII deleted every accent."""
    assert pdf_report.pdf_text("Población niños ¿cuántos?") == (
        "Población niños ¿cuántos?"
    )


def test_characters_latin1_lacks_are_replaced_not_dropped():
    assert pdf_report.pdf_text("a — b ± c ≤ d") == "a - b +/- c <= d"


def test_active_table_follows_the_selection():
    """The consumer modules bind ACTIVE once at import; it must stay live."""
    set_language("en")
    english = ACTIVE["fig1_title"]
    set_language("es")
    assert ACTIVE["fig1_title"] != english
    assert ACTIVE["fig1_title"] == TABLES["es"]["fig1_title"]


def test_figures_and_report_share_the_live_table():
    """Both consumers must see the same selection, not private snapshots."""
    import figures

    set_language("es")
    assert figures.T["fig1_title"] == TABLES["es"]["fig1_title"]
    assert pdf_report.T["pdf_title"] == TABLES["es"]["pdf_title"]


@pytest.mark.parametrize("name", ["es", "ES", "Spanish", "espanol", "español"])
def test_language_names_are_accepted_liberally(name):
    assert normalise_language(name) == "es"


def test_unknown_language_is_rejected_with_a_useful_message():
    with pytest.raises(ValueError) as exc:
        normalise_language("fr")
    message = str(exc.value)
    assert "fr" in message
    assert "en" in message and "es" in message


def test_strings_returns_the_requested_table():
    assert strings("es") is TABLES["es"]
    assert strings() is EN


def test_untranslated_keys_all_exist():
    """Guard against a typo in UNTRANSLATED_KEYS silently disabling a check."""
    assert UNTRANSLATED_KEYS <= set(EN)
    assert text_strings.UNTRANSLATED_KEYS  # non-empty


def test_same_in_every_language_keys_all_exist():
    """A typo here would quietly excuse a real missing translation."""
    assert SAME_IN_EVERY_LANGUAGE <= set(EN)


@pytest.mark.parametrize("code", TRANSLATIONS)
def test_exempt_keys_really_are_identical(code):
    """If one of these ever diverges, it should leave the exemption list."""
    for key in SAME_IN_EVERY_LANGUAGE:
        assert TABLES[code][key] == EN[key], (
            f"{key!r} now differs between languages; remove it from "
            "SAME_IN_EVERY_LANGUAGE."
        )


# --- the wiring that carries a language into a run --------------------------

def test_language_is_a_python_only_setting():
    """It configures the report, not the model.

    Pushing it to NetLogo fails the run at setup with "Nothing named LANGUAGE
    has been defined" - which is exactly what happened when three separate
    copies of this set existed and only one was updated.
    """
    from config import PYTHON_ONLY, SCHEMA

    assert "language" in SCHEMA
    parameter_name = SCHEMA["language"][0]
    assert parameter_name in PYTHON_ONLY


def test_both_drivers_share_one_exclusion_set():
    """Neither driver may keep its own copy; they drift."""
    import batch_main
    import config
    import main

    assert main.NOT_MODEL_PARAMETERS is config.PYTHON_ONLY
    assert batch_main.NOT_MODEL_PARAMETERS is config.PYTHON_ONLY


def test_every_python_only_name_is_a_real_parameter():
    """A typo here would silently push the misspelt key to NetLogo."""
    from config import PYTHON_ONLY, SCHEMA

    known = {param for param, _, _ in SCHEMA.values()}
    known.add("run_id")  # added by the batch driver, not by load_config
    unknown = sorted(PYTHON_ONLY - known)
    assert not unknown, f"PYTHON_ONLY names nothing in SCHEMA: {unknown}"


def test_an_unknown_language_is_rejected_before_the_run():
    """Exit code 2, not a crash ten minutes into a simulation."""
    from validation import ConfigError, validate_config

    with pytest.raises(ConfigError) as exc:
        validate_config({"language": "fr"})
    assert "fr" in str(exc.value)


def test_a_valid_language_passes_validation():
    from validation import validate_config

    for code in TABLES:
        validate_config({"language": code})


# --- no user-facing English may be left hardcoded ---------------------------

#: Literals that legitimately stay English: console diagnostics aimed at whoever
#: is debugging GTEM, not at the reader of a report. Keeping them in one
#: language keeps them searchable.
ALLOWED_LITERALS = {
    "   PDF generation failed: ",
    ". The model and the reporting layer are out of step.",
}

#: Every module that writes text a user reads. Adding a new one here is
#: cheaper than discovering an untranslated figure in a delivered report -
#: which is how src/aggregate.py was found.
REPORTING_MODULES = ("src/pdf_report.py", "src/figures.py",
                     "src/aggregate.py")


def _docstring_ids(tree):
    import ast

    found = set()
    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        if not isinstance(node, (ast.Module, ast.FunctionDef,
                                 ast.AsyncFunctionDef, ast.ClassDef)) or not body:
            continue
        first = body[0]
        if (isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant)
                and isinstance(first.value.value, str)):
            found.add(id(first.value))
    return found


@pytest.mark.parametrize("relative", REPORTING_MODULES)
def test_no_hardcoded_prose_in_the_reporting_modules(relative):
    """Prose must come from the string tables, or it cannot be translated.

    This is the check that was missing when the tables were first added: the
    string table held 48 keys while the PDF body carried about eighty English
    sentences inline, so a Spanish run produced a half-translated report.
    """
    import ast

    path = Path(__file__).resolve().parents[1] / relative
    tree = ast.parse(path.read_text(encoding="utf-8"))
    skip = _docstring_ids(tree)

    offenders = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Constant) or id(node) in skip:
            continue
        value = node.value
        if not isinstance(value, str) or len(value) < 25 or " " not in value:
            continue
        if value.startswith(("Figure", "%")) or value in ALLOWED_LITERALS:
            continue
        offenders.append(f"{relative}:{node.lineno}: {value[:60]!r}")

    assert not offenders, (
        "User-facing prose is hardcoded instead of coming from text_strings:\n  "
        + "\n  ".join(offenders)
    )
