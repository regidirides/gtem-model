from argparse import ArgumentParser
from pathlib import Path


def build_parser() -> ArgumentParser:
    parser = ArgumentParser(
        description="Rename files ending in colapso1 or colpaso1 to colapso2."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply the changes. Without this flag it only shows a dry run.",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Incluye archivos dentro de subcarpetas.",
    )
    parser.add_argument(
        "--to",
        default="colapso2",
        help="Texto final nuevo. Por defecto: colapso2.",
    )
    parser.add_argument(
        "--from",
        dest="from_values",
        nargs="+",
        default=["colapso1", "colpaso1"],
        help="Textos finales a reemplazar. Por defecto: colapso1 colpaso1.",
    )
    return parser


def replacement_for(path: Path, from_values: list[str], to_value: str) -> Path | None:
    stem_lower = path.stem.lower()

    for old_suffix in from_values:
        old_suffix_lower = old_suffix.lower()
        if stem_lower.endswith(old_suffix_lower):
            prefix = path.stem[: -len(old_suffix)]
            return path.with_name(f"{prefix}{to_value}{path.suffix}")

    return None


def main() -> int:
    args = build_parser().parse_args()
    root = Path(__file__).resolve().parent
    files = root.rglob("*") if args.recursive else root.iterdir()

    changes: list[tuple[Path, Path]] = []
    for path in files:
        if not path.is_file():
            continue

        new_path = replacement_for(path, args.from_values, args.to)
        if new_path is not None and new_path != path:
            changes.append((path, new_path))

    if not changes:
        print(f"No files found ending in: {', '.join(args.from_values)}")
        return 0

    conflicts = [(old, new) for old, new in changes if new.exists()]
    if conflicts:
        print("Cannot continue: these target names already exist:")
        for old, new in conflicts:
            print(f"  {old.name} -> {new.name}")
        return 1

    if not args.apply:
        print("Dry run. To apply: python rename_collapse_scenario.py --apply")
        for old, new in changes:
            print(f"  {old.name} -> {new.name}")
        return 0

    for old, new in changes:
        old.rename(new)
        print(f"Renombrado: {old.name} -> {new.name}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
