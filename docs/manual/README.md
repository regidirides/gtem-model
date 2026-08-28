# GTEM User Manual — source

`GTEM_Manual.pdf` is built from `manual.typ` with [Typst](https://typst.app)
(tested with Typst 0.15.1):

```bash
typst compile manual.typ GTEM_Manual.pdf
```

Use `typst watch` instead of `compile` while editing to rebuild on save.

## What is where

| Path | Contents |
|---|---|
| `manual.typ` | The whole manual. Plain text; headings are `=`, `==`, `===`. |
| `figures/` | Figures. `fig_*.png` are real model outputs, not mock-ups. |
| `transcripts/` | Terminal output, read into the manual at build time by `#term(...)`. |

Terminal listings are read from `transcripts/` rather than typed into the
manual, so they cannot drift away from what the code actually prints. To refresh
one, re-run the command and overwrite the file — then check it contains no
machine-specific absolute paths.

## Screenshots

Nine screenshots are still to be taken. Each is marked in the PDF by an orange
dashed box stating what to capture and why; the appendix at the end lists all
nine together. Search `manual.typ` for `todo-shot` to find them.

To add one, save it as `figures/S<n>.png` and replace the `#todo-shot(...)`
block with:

```typst
#figure(image("figures/S1.png", width: 90%), caption: [...])
```

## The Spanish edition

`manual_es.typ` → `GTEM_Manual_ES.pdf` is a full translation of `manual.typ`.
The two are separate files: when you change one, check the other.

Figures are **not** shared. The Spanish manual uses `figures/*_es.png`, produced
by running the model with `--language es`; the English manual uses the
unsuffixed files. Screenshots (`S1.png` … `S9.png`) *are* shared — take them
once.

Terminal transcripts are shared and stay in English, because GTEM's console
output is not translated. Both manuals say so where the transcripts appear.

```bash
typst compile manual_es.typ GTEM_Manual_ES.pdf
```
